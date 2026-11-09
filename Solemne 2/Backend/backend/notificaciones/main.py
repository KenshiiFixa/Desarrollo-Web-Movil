"""Notificaciones (mensajeria/correo): la "API de mensajeria" del Caso 19.

- auth llama POST /internal/verificacion: envia el codigo para validar que el correo existe (RF11).
- orders llama POST /internal/boletas con el pedido pagado: envia la boleta digital (RF8).
- Este servicio pide a clients SOLO el nombre y correo del cliente.
- El envio de correo es SIMULADO: el correo se guarda en la base 'notificaciones' en vez de
  mandarlo por SMTP (no hay un servidor de correo en el proyecto). El contrato queda listo para
  cambiarlo por un proveedor real.
- El administrador puede revisar los correos enviados (GET /notificaciones), con el correo enmascarado.
"""
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from comun import registrar_logs, conectar_mongo, exigir_rol, leer_secretos, llamar_servicio, usuario_actual, verificar_servicio

db = None


def armar_correo(cliente, boleta):
    """Texto del correo con la boleta. No incluye RUN ni direccion."""
    lineas = "\n".join(f"  {d['cantidad']} x {d['producto']}: ${d['total']}" for d in boleta["detalle"])
    return {"para": cliente["email"],
            "asunto": f"Aroma & Cafe - Boleta {boleta['folio']}",
            "cuerpo": (f"Hola {cliente['nombre']}, gracias por tu compra.\n"
                       f"Pedido {boleta['pedido']}\n{lineas}\n"
                       f"Neto: ${boleta['neto']}  IVA: ${boleta['iva']}\nTotal: ${boleta['total']}\n"
                       f"Caja: {boleta['caja']}")}


def enmascarar(correo):
    """ana@aromaycafe.test -> a***@aromaycafe.test"""
    usuario, _, dominio = correo.partition("@")
    return f"{usuario[:1]}***@{dominio}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("notificaciones")
    db = conectar_mongo("notificaciones")
    yield


app = FastAPI(title="Notificaciones Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "notificaciones")


class Boleta(BaseModel):
    order_id: str = Field(max_length=30)
    user_id: str = Field(max_length=30)
    boleta: dict


@app.post("/internal/boletas", status_code=201, dependencies=[Depends(verificar_servicio("orders"))])
def enviar_boleta(datos: Boleta):
    if db.correos.find_one({"_id": datos.order_id}):
        return {"ok": True, "repetido": True}   # si orders reintenta, no se envia dos veces
    r = llamar_servicio("notificaciones", "clients", "GET", f"/internal/clients/{datos.user_id}/email")
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    correo = armar_correo(r.json(), datos.boleta)
    db.correos.insert_one({"_id": datos.order_id, "tipo": "boleta", **correo, "estado": "ENVIADO_SIMULADO",
                           "enviado_en": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    print(f"[BOLETA] {datos.boleta.get('folio')} enviada (simulado) para el pedido {datos.order_id}")
    return {"ok": True}


class Verificacion(BaseModel):
    email: str = Field(max_length=254)
    nombre: str = Field(max_length=80)
    codigo: str = Field(pattern=r"^\d{6}$")


@app.post("/internal/verificacion", status_code=201, dependencies=[Depends(verificar_servicio("auth"))])
def enviar_codigo(datos: Verificacion):
    """Envia (simulado) el codigo de verificacion. El codigo solo va en el cuerpo del correo."""
    db.correos.insert_one({"_id": "VER-" + secrets.token_hex(6), "tipo": "verificacion", "para": datos.email,
                           "asunto": "Aroma & Cafe - Verifica tu correo",
                           "cuerpo": f"Hola {datos.nombre}, tu codigo de verificacion es {datos.codigo}. Vence en 30 minutos.",
                           "estado": "ENVIADO_SIMULADO",
                           "enviado_en": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return {"ok": True}


@app.get("/notificaciones", dependencies=[Depends(verificar_servicio("gateway"))])
def listar_correos(usuario=Depends(usuario_actual), limit: int = Query(20, ge=1, le=50)):
    exigir_rol(usuario, "admin")
    # El admin no ve el cuerpo del correo (ahi va el codigo de verificacion) y el correo va enmascarado
    return [{"id": c["_id"], "tipo": c["tipo"], "para": enmascarar(c["para"]), "asunto": c["asunto"],
             "estado": c["estado"], "enviado_en": c["enviado_en"]}
            for c in db.correos.find().sort("enviado_en", -1).limit(limit)]


@app.get("/health")
def health():
    return {"status": "ok", "service": "Notificaciones Service"}
