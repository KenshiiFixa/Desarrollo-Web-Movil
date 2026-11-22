"""Funciones comunes a todos los servicios: TLS, lectura de secretos desde Vault, verificacion del secreto
de quien llama, llamadas a otros servicios, conexion a MongoDB y logs.

Cada par de servicios tiene su propio secreto: el que usa el gateway para llamar a orders no sirve para inventory."""
import contextvars
import os
import re
import secrets
import ssl
import time
import uuid
from urllib.parse import quote_plus

import httpx
import grpc
from fastapi import Header, HTTPException, Request
from pymongo import MongoClient

# Identificador de correlacion de la solicitud actual (lo crea el gateway y viaja en X-Request-ID)
ID_SOLICITUD = contextvars.ContextVar("id_solicitud", default="-")

# Local (iniciar.py): cada servicio escucha en 127.0.0.1 con su puerto.
# Docker (EN_DOCKER=1): cada servicio es un contenedor en el puerto 8000 y se llama por su nombre.
EN_DOCKER = os.getenv("EN_DOCKER") == "1"
VAULT_ADDR = os.getenv("VAULT_ADDR", "https://127.0.0.1:8200")
# Archivo con el token de Vault de este servicio
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "")

# Puerto de cada servicio (solo el gateway es la entrada para el navegador)
PUERTOS = {"gateway": 8000, "auth": 8001, "inventory": 8002, "orders": 8003, "clients": 8004,
           "payments": 8005, "graphql": 8006, "analitica": 8007, "notificaciones": 8008, "proveedor": 8009}

# Direccion interna de cada servicio
if EN_DOCKER:
    URLS = {s: f"https://{s}:8000" for s in PUERTOS}
else:
    URLS = {s: f"https://127.0.0.1:{p}" for s, p in PUERTOS.items()}
# gRPC de inventory (solo lo usa orders)
GRPC_INVENTORY = "inventory:50051" if EN_DOCKER else "127.0.0.1:50051"
GRPC_ESCUCHA = "0.0.0.0:50051" if EN_DOCKER else GRPC_INVENTORY

# Certificados TLS: ca.crt (CA local), servidor.crt/.key y vault/vault-ca.pem (CA de Vault en modo local)
CERTS = os.getenv("CERTS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs"))
CA = os.path.join(CERTS, "ca.crt")
CA_VAULT = os.path.join(CERTS, "vault", "vault-ca.pem")


def contexto_tls():
    """Contexto TLS que solo confia en la CA local y en la de Vault."""
    contexto = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()
    if os.path.exists(CA_VAULT):
        contexto.load_verify_locations(CA_VAULT)
    return contexto


# Cliente HTTPS compartido para las llamadas a otros servicios
CLIENTE_HTTP = httpx.Client(timeout=8.0, verify=contexto_tls())


def canal_inventory():
    """Canal gRPC cifrado con TLS hacia inventory (verifica el certificado con la CA local)."""
    return grpc.secure_channel(GRPC_INVENTORY, grpc.ssl_channel_credentials(root_certificates=open(CA, "rb").read()))


def credenciales_grpc_servidor():
    """Certificado y clave del servidor gRPC de inventory."""
    clave = open(os.path.join(CERTS, "servidor.key"), "rb").read()
    certificado = open(os.path.join(CERTS, "servidor.crt"), "rb").read()
    return grpc.ssl_server_credentials([(clave, certificado)])

# Secretos de este servicio (los llena leer_secretos)
SECRETOS = {}
# Nombre de este servicio, para los mensajes del log
SERVICIO = {"nombre": "-"}


def log(mensaje):
    """Escribe en el log un paso de la solicitud actual, con su id de correlacion (sin tokens, claves ni secretos)."""
    print(f"[{SERVICIO['nombre']}] req={ID_SOLICITUD.get()} {mensaje}", flush=True)


def registrar_logs(app, nombre_servicio, aceptar_id_entrante=True):
    """Escribe una linea de log por solicitud con su id de correlacion (sin cuerpos, cabeceras ni tokens).
    Con aceptar_id_entrante=False (gateway) siempre crea un id nuevo."""
    @app.middleware("http")
    async def log_solicitud(request: Request, call_next):
        recibido = request.headers.get("x-request-id", "") if aceptar_id_entrante else ""
        id_sol = recibido if re.fullmatch(r"[A-Za-z0-9-]{1,32}", recibido) else uuid.uuid4().hex[:12]
        ID_SOLICITUD.set(id_sol)
        inicio = time.time()
        respuesta = await call_next(request)
        if request.url.path != "/health":
            ms = int((time.time() - inicio) * 1000)
            print(f"[{nombre_servicio}] req={id_sol} {request.method} {request.url.path} "
                  f"-> {respuesta.status_code} ({ms} ms)", flush=True)
        respuesta.headers["X-Request-ID"] = id_sol
        return respuesta


def leer_secretos(nombre_servicio):
    """Lee secret/<nombre_servicio> desde Vault. Cada servicio solo puede leer el suyo."""
    for intento in range(30):   # Vault puede tardar unos segundos en estar listo
        try:
            token = open(VAULT_TOKEN_FILE).read().strip()
            respuesta = CLIENTE_HTTP.get(f"{VAULT_ADDR}/v1/secret/data/{nombre_servicio}",
                                         headers={"X-Vault-Token": token}, timeout=5.0)
            if respuesta.status_code == 200:
                SECRETOS.clear()
                SECRETOS.update(respuesta.json()["data"]["data"])
                SERVICIO["nombre"] = nombre_servicio
                return SECRETOS
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"No fue posible leer los secretos de {nombre_servicio} desde Vault")


def verificar_servicio(*permitidos):
    """Dependencia de FastAPI: solo deja pasar a los servicios de la lista que traigan SU secreto.
    Uso:  @app.get("/ruta", dependencies=[Depends(verificar_servicio("gateway"))])"""
    def verificar(x_servicio: str = Header(default=""), x_servicio_secreto: str = Header(default="")):
        esperado = SECRETOS.get(f"desde_{x_servicio}", "")
        if x_servicio not in permitidos or not esperado:
            log(f"llamada RECHAZADA (403): '{x_servicio[:20] or 'sin nombre'}' no puede llamar a este servicio")
            raise HTTPException(status_code=403, detail="No autorizado")
        if not secrets.compare_digest(x_servicio_secreto, esperado):
            log(f"llamada RECHAZADA (403): el secreto de {x_servicio} no coincide con el guardado en Vault")
            raise HTTPException(status_code=403, detail="No autorizado")
        log(f"secreto de {x_servicio} verificado con el de Vault: OK, se permite la llamada")
        return x_servicio
    return verificar


def usuario_actual(x_servicio: str = Header(default=""),
                   x_authenticated_user: str = Header(default=""),
                   x_authenticated_roles: str = Header(default="")):
    """Identidad del usuario que verifico el gateway. Solo se acepta si la llamada viene del gateway o de graphql."""
    if x_servicio not in ("gateway", "graphql") or not x_authenticated_user:
        return None
    return {"user_id": x_authenticated_user, "rol": x_authenticated_roles}


def exigir_rol(usuario, *roles):
    """401 si no hay usuario; 403 si su rol no esta en la lista (lista vacia = cualquier rol)."""
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sesion requerida")
    if roles and usuario["rol"] not in roles:
        raise HTTPException(status_code=403, detail="Permiso insuficiente")


def llamar_servicio(yo, destino, metodo, ruta, usuario=None, **kwargs):
    """Llama a otro servicio con el secreto del par (yo -> destino), guardado en Vault como 'hacia_<destino>'."""
    cabeceras = {"X-Servicio": yo, "X-Servicio-Secreto": SECRETOS[f"hacia_{destino}"],
                 "X-Request-ID": ID_SOLICITUD.get()}
    if usuario:
        cabeceras["X-Authenticated-User"] = usuario["user_id"]
        cabeceras["X-Authenticated-Roles"] = usuario["rol"]
    try:
        return CLIENTE_HTTP.request(metodo, URLS[destino] + ruta, headers=cabeceras, **kwargs)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"Servicio {destino} no disponible")


def conectar_mongo(nombre_servicio):
    """Conecta a la base de este servicio con su propio usuario de MongoDB (la clave viene de Vault)."""
    host = os.getenv("MONGO_HOST", "127.0.0.1:27018")
    url = (f"mongodb://{nombre_servicio}:{quote_plus(SECRETOS['mongo_clave'])}@{host}/"
           f"{nombre_servicio}?authSource={nombre_servicio}")
    cliente = MongoClient(url, serverSelectionTimeoutMS=5000)
    return cliente[nombre_servicio]
