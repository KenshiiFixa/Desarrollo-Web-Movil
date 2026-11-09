"""Funciones que usan todos los servicios.

Es lo mismo que vimos en el ejemplo de clase (Semana 9/apigateway), puesto en un solo lugar:
  - leer_secretos()      -> como get_gateway_secrets(): lee el secreto del servicio desde Vault.
  - verificar_servicio() -> como verify_gateway(): rechaza con 403 a quien no trae su secreto.
  - llamar_servicio()    -> como el proxy del gateway: llama a otro servicio agregando su secreto.
  - conectar_mongo()     -> como el MongoClient de la Semana 6, pero con usuario y clave propios.

Diferencia con el ejemplo de clase: aqui CADA par de servicios tiene su propio secreto.
Ej.: el secreto que usa el gateway para hablar con orders no sirve para hablar con inventory.
"""
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

# Todo corre en este computador (iniciar.py). Los servicios escuchan solo en 127.0.0.1, cada uno en su puerto,
# y todas las llamadas van cifradas con TLS.
VAULT_ADDR = os.getenv("VAULT_ADDR", "https://127.0.0.1:8200")
# El token de Vault NO esta en el codigo: iniciar.py lo deja en un archivo distinto para cada servicio.
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "")

# Puerto de cada servicio (solo el gateway es la entrada para el navegador)
PUERTOS = {"gateway": 8000, "auth": 8001, "inventory": 8002, "orders": 8003, "clients": 8004,
           "payments": 8005, "graphql": 8006, "analitica": 8007, "notificaciones": 8008, "proveedor": 8009}

# Direccion interna de cada servicio
URLS = {s: f"https://127.0.0.1:{p}" for s, p in PUERTOS.items()}
# gRPC de inventory (solo lo usa orders)
GRPC_INVENTORY = "127.0.0.1:50051"

# Certificados que genera iniciar.py en la carpeta certs/ (no se suben al repositorio):
#   ca.crt = nuestra autoridad certificadora local; servidor.crt/.key = certificado de 127.0.0.1 y localhost.
#   vault/vault-ca.pem = la CA que crea Vault en modo desarrollo con TLS.
CERTS = os.getenv("CERTS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs"))
CA = os.path.join(CERTS, "ca.crt")
CA_VAULT = os.path.join(CERTS, "vault", "vault-ca.pem")


def contexto_tls():
    """Contexto TLS que solo confia en nuestras CA (la local y la de Vault), no en cualquier certificado."""
    contexto = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()
    if os.path.exists(CA_VAULT):
        contexto.load_verify_locations(CA_VAULT)
    return contexto


# Un solo cliente HTTPS por servicio, reutilizado en todas las llamadas internas. Crear uno por llamada
# cuesta ~10 ms de CPU (carga los certificados cada vez) y lo medimos como cuello de botella en la prueba de carga.
CLIENTE_HTTP = httpx.Client(timeout=8.0, verify=contexto_tls())


def canal_inventory():
    """Canal gRPC cifrado con TLS hacia inventory (verifica el certificado con la CA local)."""
    return grpc.secure_channel(GRPC_INVENTORY, grpc.ssl_channel_credentials(root_certificates=open(CA, "rb").read()))


def credenciales_grpc_servidor():
    """Certificado y clave del servidor gRPC de inventory."""
    clave = open(os.path.join(CERTS, "servidor.key"), "rb").read()
    certificado = open(os.path.join(CERTS, "servidor.crt"), "rb").read()
    return grpc.ssl_server_credentials([(clave, certificado)])

# Secretos de ESTE servicio. Se llenan al iniciar con leer_secretos().
SECRETOS = {}


def registrar_logs(app, nombre_servicio, aceptar_id_entrante=True):
    """Escribe una linea de log por solicitud con el id de correlacion, para seguir una misma
    solicitud por todos los servicios. NO se registran cuerpos, cabeceras, tokens ni parametros.
    El gateway usa aceptar_id_entrante=False: siempre crea un id nuevo y no confia en el del navegador."""
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
            raise HTTPException(status_code=403, detail="No autorizado")
        if not secrets.compare_digest(x_servicio_secreto, esperado):
            raise HTTPException(status_code=403, detail="No autorizado")
        return x_servicio
    return verificar


def usuario_actual(x_servicio: str = Header(default=""),
                   x_authenticated_user: str = Header(default=""),
                   x_authenticated_roles: str = Header(default="")):
    """Identidad del usuario que verifico el gateway (mismas cabeceras del ejemplo de clase).
    Solo se cree si la llamada viene del gateway o del graphql (que ya pasaron verificar_servicio)."""
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
    """Cada servicio tiene SU base de datos y SU usuario de MongoDB (solo puede usar su base).
    La clave viene de Vault (secreto 'mongo_clave'), nunca del codigo."""
    host = os.getenv("MONGO_HOST", "127.0.0.1:27018")
    url = (f"mongodb://{nombre_servicio}:{quote_plus(SECRETOS['mongo_clave'])}@{host}/"
           f"{nombre_servicio}?authSource={nombre_servicio}")
    cliente = MongoClient(url, serverSelectionTimeoutMS=5000)
    return cliente[nombre_servicio]
