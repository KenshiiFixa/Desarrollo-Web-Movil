"""API Gateway: unico servicio publicado hacia afuera (puerto 8000).

- Busca cada ruta en la tabla RUTAS; lo que no esta responde 404.
- En las rutas con sesion valida el token con el Auth Service (/introspect) y revisa el rol.
- Llama al servicio interno con su secreto de Vault y cabeceras nuevas (no reenvia las del navegador).
- Limita las solicitudes por IP y el tamano del cuerpo, aplica CORS y crea el id de correlacion (X-Request-ID)."""
import json
import os
import re
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from comun import ID_SOLICITUD, SECRETOS, URLS, contexto_tls, leer_secretos, log, registrar_logs

security = HTTPBearer(auto_error=False)

# Roles que puede exigir cada ruta
PUBLICO = None                       # no exige sesion
CUALQUIERA = ("cliente", "cajero", "despacho", "dueno", "admin")
CLIENTE = ("cliente",)
DESPACHO = ("despacho", "admin")     # encargado de despacho
CAJA = ("cajero", "admin")           # cajero virtual
DUENO = ("dueno", "admin")           # dueno del restaurant
ADMIN = ("admin",)

# Tabla de rutas: (ID servicio, verbo, ruta externa, servicio destino, ruta interna, quien puede)
RUTAS = [
    ("S01", "GET", "/products", "inventory", "/products", PUBLICO),
    ("S02", "GET", "/products/{id}", "inventory", "/products/{id}", PUBLICO),
    ("S03", "POST", "/auth/register", "auth", "/register", PUBLICO),
    ("S04", "POST", "/auth/login", "auth", "/login", PUBLICO),
    ("S05", "POST", "/auth/logout", "auth", "/logout", CUALQUIERA),
    ("S06", "GET", "/clients/me", "clients", "/clients/me", CUALQUIERA),
    ("S07", "PUT", "/clients/me", "clients", "/clients/me", CUALQUIERA),
    ("S08", "POST", "/contact", "clients", "/contact", PUBLICO),
    ("S09", "POST", "/orders", "orders", "/orders", CLIENTE),
    ("S10", "GET", "/orders", "orders", "/orders", CUALQUIERA),
    ("S11", "GET", "/orders/{id}", "orders", "/orders/{id}", CUALQUIERA),
    ("S12", "POST", "/orders/{id}/cancel", "orders", "/orders/{id}/cancel", CUALQUIERA),
    ("S13", "GET", "/orders/{id}/receipt", "orders", "/orders/{id}/receipt", CUALQUIERA),
    ("S14", "POST", "/payments", "payments", "/payments", CLIENTE),
    ("S15", "GET", "/payments/{id}", "payments", "/payments/{id}", CUALQUIERA),
    ("S16", "POST", "/payments/{id}/simular", "payments", "/payments/{id}/simular", CLIENTE),
    ("S17", "POST", "/payments/webhook", "payments", "/webhook", PUBLICO),   # lo protege la firma HMAC
    ("S18", "POST", "/graphql", "graphql", "/graphql", CUALQUIERA),
    ("S19", "GET", "/admin/products", "inventory", "/admin/products", DUENO),
    ("S20", "POST", "/admin/products", "inventory", "/products", DUENO),
    ("S21", "PUT", "/admin/products/{id}", "inventory", "/products/{id}", DUENO),
    ("S22", "DELETE", "/admin/products/{id}", "inventory", "/products/{id}", DUENO),
    ("S23", "PUT", "/admin/orders/{id}/status", "orders", "/orders/{id}/status", DESPACHO),
    ("S24", "GET", "/admin/clients/{id}", "clients", "/clients/{id}", DESPACHO),
    ("S25", "GET", "/admin/contact", "clients", "/contact", ADMIN),
    ("S26", "GET", "/admin/reports/sales", "analitica", "/reportes/ventas", DUENO),
    ("S27", "GET", "/admin/notifications", "notificaciones", "/notificaciones", ADMIN),
    ("S28", "POST", "/auth/verify-email", "auth", "/verificar-correo", PUBLICO),
    ("S29", "GET", "/admin/dispatch-orders", "orders", "/despacho", DESPACHO),
    ("S30", "GET", "/admin/sales", "orders", "/ventas", CAJA),
    ("S31", "POST", "/admin/clients", "auth", "/admin/clientes", ADMIN),
    ("S32", "PUT", "/admin/clients/{id}", "clients", "/clients/{id}", ADMIN),
    ("S33", "GET", "/admin/users", "auth", "/usuarios", ADMIN),
    ("S34", "POST", "/admin/users", "auth", "/usuarios", ADMIN),
    ("S35", "PUT", "/admin/users/{id}/role", "auth", "/usuarios/{id}/rol", ADMIN),
]

LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "120"))   # solicitudes por IP por minuto
LIMITE_LOGIN_POR_MINUTO = 10     # login, registro, contacto y verificacion: mas estricto
MAX_CUERPO = 64 * 1024
solicitudes = {}                 # {(ip, grupo): [tiempos]}
# Cliente HTTPS hacia los servicios internos
cliente_backend = httpx.AsyncClient(timeout=10.0, verify=contexto_tls())


def buscar_ruta(metodo, ruta):
    """Busca la ruta en la tabla. Los {id} solo aceptan letras, numeros, guion y guion bajo."""
    for sid, verbo, patron, destino, interna, roles in RUTAS:
        regex = "^" + re.sub(r"\{id\}", r"(?P<id>[A-Za-z0-9_-]{1,64})", patron) + "$"
        encontrada = re.match(regex, ruta)
        if verbo == metodo and encontrada:
            if "{id}" in patron:
                interna = interna.replace("{id}", encontrada.group("id"))
            return sid, destino, interna, roles
    return None


def limite_superado(ip, grupo, limite):
    ahora = time.time()
    tiempos = [t for t in solicitudes.get((ip, grupo), []) if t > ahora - 60]
    tiempos.append(ahora)
    solicitudes[(ip, grupo)] = tiempos
    return len(tiempos) > limite


@asynccontextmanager
async def lifespan(app: FastAPI):
    leer_secretos("gateway")
    yield


app = FastAPI(title="API Gateway Aroma & Cafe", lifespan=lifespan, docs_url=None, redoc_url=None)

# CORS: el navegador solo puede llamar al gateway desde el frontend, con los metodos de la tabla y las cabeceras
# Authorization y Content-Type. El token va en Authorization, no en cookies.
FRONTEND_ORIGENES = os.getenv("FRONTEND_ORIGENES", "http://localhost:8080,http://127.0.0.1:8080").split(",")
app.add_middleware(CORSMiddleware, allow_origins=FRONTEND_ORIGENES, allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["X-Request-ID"], max_age=600)
# Log por solicitud; el id de correlacion lo crea siempre el gateway
registrar_logs(app, "gateway", aceptar_id_entrante=False)


async def authenticate_client(credentials: HTTPAuthorizationCredentials):
    """Pregunta al Auth Service si el token esta activo y devuelve el usuario y su rol."""
    if credentials is None:
        log("sin token: se responde 401 sin llamar al Auth Service")
        raise HTTPException(status_code=401, detail="Bearer token requerido")
    log("pidiendo validacion del token al Auth Service (POST /introspect)")
    try:
        response = await cliente_backend.post(
            f"{URLS['auth']}/introspect", json={"token": credentials.credentials[:200]}, timeout=5.0,
            headers={"X-Servicio": "gateway", "X-Servicio-Secreto": SECRETOS["hacia_auth"],
                     "X-Request-ID": ID_SOLICITUD.get()})
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Authentication Service no disponible")
    if response.status_code == 422:
        # Auth responde 422 si el token no tiene un formato valido: se trata como token invalido
        log("Auth Service respondio: el token no tiene un formato valido -> 401")
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Error consultando Authentication Service")
    identity = response.json()
    if not identity.get("active", False):
        log("Auth Service respondio: token invalido o expirado -> 401")
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    log(f"Auth Service respondio: token valido, rol={identity['rol']}")
    return {"user_id": identity["user_id"], "rol": identity["rol"]}


@app.get("/health")
def health():
    return {"status": "ok", "service": "API Gateway"}


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request,
                credentials: HTTPAuthorizationCredentials = Depends(security)):
    ruta = buscar_ruta(request.method, "/" + path)
    if ruta is None:
        log(f"{request.method} /{path[:60]} no esta en la tabla de rutas -> 404")
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    sid, destino, ruta_interna, roles = ruta
    origen = request.headers.get("origin", "")[:60] or "sin Origin"
    log(f"ruta {sid}: {request.method} /{path[:60]} -> {destino} ({'publica' if roles is PUBLICO else 'requiere sesion'}, "
        f"origen {origen})")

    ip = request.client.host if request.client else "desconocida"
    if sid == "S04":   # login: evita adivinar claves
        if limite_superado(ip, "login", LIMITE_LOGIN_POR_MINUTO):
            raise HTTPException(status_code=429, detail="Demasiados intentos, espera un minuto")
    elif sid in ("S03", "S08", "S28"):   # registro, contacto y verificacion: evita spam y adivinar codigos
        if limite_superado(ip, "registro", LIMITE_LOGIN_POR_MINUTO):
            raise HTTPException(status_code=429, detail="Demasiados intentos, espera un minuto")
    elif limite_superado(ip, "general", LIMITE_POR_MINUTO):
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes, espera un minuto")

    body = await request.body()
    if len(body) > MAX_CUERPO:
        raise HTTPException(status_code=413, detail="Cuerpo demasiado grande")

    # Cabeceras nuevas: no se reenvia nada de lo que manda el navegador
    gateway_headers = {"X-Servicio": "gateway", "X-Servicio-Secreto": SECRETOS[f"hacia_{destino}"],
                       "Content-Type": "application/json", "X-Request-ID": ID_SOLICITUD.get()}
    if roles is not PUBLICO:
        auth = await authenticate_client(credentials)
        if auth["rol"] not in roles:
            log(f"rol {auth['rol']} no tiene permiso para {sid} -> 403 (no se enruta)")
            raise HTTPException(status_code=403, detail="Permiso insuficiente")
        gateway_headers["X-Authenticated-User"] = auth["user_id"]
        gateway_headers["X-Authenticated-Roles"] = auth["rol"]
    if sid == "S05":   # logout: el Auth Service necesita el token para borrarlo
        body = json.dumps({"token": credentials.credentials[:200]}).encode()
    if sid == "S17":   # webhook: se reenvia la firma del proveedor (la valida payments)
        gateway_headers["X-Firma"] = request.headers.get("x-firma", "")[:128]

    log(f"enrutando a {destino} {request.method} {ruta_interna} con el secreto gateway->{destino} leido de Vault")
    try:
        upstream = await cliente_backend.request(method=request.method, url=URLS[destino] + ruta_interna,
                                                 params=request.query_params, content=body,
                                                 headers=gateway_headers)
    except httpx.RequestError:
        log(f"{destino} no responde -> 502")
        raise HTTPException(status_code=502, detail="Backend no disponible")
    log(f"{destino} respondio {upstream.status_code}")
    if upstream.status_code >= 500:
        # No se muestran errores internos al cliente
        raise HTTPException(status_code=502, detail="Error en el servicio interno")
    return Response(content=upstream.content, status_code=upstream.status_code,
                    media_type="application/json")
