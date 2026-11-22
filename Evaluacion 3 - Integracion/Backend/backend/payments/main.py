"""Payments: inicia el cobro con el proveedor de pagos y confirma el resultado.

Reglas de seguridad:
  - El MONTO lo saca payments del pedido (servicio orders), nunca del navegador.
  - Un pedido solo pasa a PAGADO cuando llega el aviso (webhook) del proveedor con una firma
    HMAC-SHA256 valida. El navegador no puede "decir" que pago.
  - Cada aviso tiene un event_id unico: si el proveedor lo manda dos veces, se procesa una sola vez.
"""
import hashlib
import hmac
import json
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from comun import registrar_logs, SECRETOS, conectar_mongo, exigir_rol, leer_secretos, llamar_servicio, usuario_actual, verificar_servicio

db = None


def firma_valida(cuerpo: bytes, firma: str) -> bool:
    """Calcula el HMAC-SHA256 del cuerpo con la clave compartida con el proveedor y lo compara."""
    esperada = hmac.new(SECRETOS["webhook_clave"].encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperada, firma)


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pago_para_cliente(pago):
    return {"id": pago["_id"], "order_id": pago["order_id"], "estado": pago["estado"], "monto": pago["monto"]}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("payments")
    db = conectar_mongo("payments")
    db.pagos.create_index("order_id")
    yield


app = FastAPI(title="Payments Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "payments")
gateway_o_graphql = Depends(verificar_servicio("gateway", "graphql"))


class PagoNuevo(BaseModel):
    order_id: str = Field(pattern=r"^ORD-[A-Z0-9]{4,12}$")   # el navegador NO envia el monto


@app.post("/payments", status_code=201, dependencies=[gateway_o_graphql])
def iniciar_pago(datos: PagoNuevo, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "cliente")
    r = llamar_servicio("payments", "orders", "GET", f"/internal/orders/{datos.order_id}")
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    pedido = r.json()
    if pedido["user_id"] != usuario["user_id"]:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")   # pedido ajeno
    if pedido["estado"] != "PENDIENTE_PAGO":
        raise HTTPException(status_code=409, detail="El pedido no esta pendiente de pago")
    existente = db.pagos.find_one({"order_id": datos.order_id, "estado": "PENDIENTE"})
    if existente:
        return pago_para_cliente(existente)
    payment_id = "PAY-" + secrets.token_hex(4).upper()
    # Se pide al proveedor un "checkout" con el monto del SERVIDOR
    r = llamar_servicio("payments", "proveedor", "POST", "/checkout",
                        json={"payment_id": payment_id, "monto": pedido["total"]})
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Proveedor de pagos no disponible")
    db.pagos.insert_one({"_id": payment_id, "order_id": datos.order_id, "user_id": usuario["user_id"],
                         "monto": pedido["total"], "estado": "PENDIENTE",
                         "checkout_id": r.json()["checkout_id"], "creado_en": ahora()})
    return {"id": payment_id, "order_id": datos.order_id, "estado": "PENDIENTE", "monto": pedido["total"],
            "url_pago": r.json()["url_pago"]}


def buscar_pago(payment_id, usuario):
    pago = db.pagos.find_one({"_id": payment_id})
    if pago is None or (usuario["rol"] == "cliente" and pago["user_id"] != usuario["user_id"]):
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@app.get("/payments/by-orders", dependencies=[Depends(verificar_servicio("graphql"))])
def pagos_de_pedidos(ids: str = Query(max_length=1000), usuario=Depends(usuario_actual)):
    """Para el GraphQL gateway: los pagos de varios pedidos en una sola llamada."""
    exigir_rol(usuario)
    filtro = {"order_id": {"$in": ids.split(",")[:50]}}
    if usuario["rol"] == "cliente":
        filtro["user_id"] = usuario["user_id"]
    return [pago_para_cliente(p) for p in db.pagos.find(filtro)]


@app.get("/payments/{payment_id}", dependencies=[gateway_o_graphql])
def ver_pago(payment_id: str, usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    return pago_para_cliente(buscar_pago(payment_id, usuario))


class Simulacion(BaseModel):
    resultado: Literal["aprobado", "rechazado"] = "aprobado"
    repetir_aviso: int = Field(default=1, ge=1, le=3)


@app.post("/payments/{payment_id}/simular", status_code=202, dependencies=[gateway_o_graphql])
def simular_pago(payment_id: str, datos: Simulacion, usuario=Depends(usuario_actual)):
    """SOLO PRUEBAS: hace como si el cliente hubiera pagado en la pagina del proveedor.
    El proveedor (simulado) envia entonces el webhook firmado, igual que uno real."""
    exigir_rol(usuario, "cliente")
    pago = buscar_pago(payment_id, usuario)
    if pago["estado"] != "PENDIENTE":
        raise HTTPException(status_code=409, detail="El pago ya fue procesado")
    r = llamar_servicio("payments", "proveedor", "POST", f"/checkout/{pago['checkout_id']}/pagar",
                        json=datos.model_dump())
    return r.json()


class Aviso(BaseModel):
    event_id: str = Field(max_length=60)
    payment_id: str = Field(max_length=30)
    checkout_id: str = Field(max_length=60)
    resultado: Literal["aprobado", "rechazado"]
    monto: int
    creado_en: int


@app.post("/webhook", dependencies=[Depends(verificar_servicio("gateway"))])
async def webhook(request: Request, x_firma: str = Header(default="")):
    """Aviso del proveedor, recibido a traves del gateway. Lo que lo autentica es la firma HMAC."""
    cuerpo = await request.body()
    if not firma_valida(cuerpo, x_firma):
        raise HTTPException(status_code=401, detail="Firma invalida")
    try:
        aviso = Aviso(**json.loads(cuerpo))
    except Exception:
        raise HTTPException(status_code=400, detail="Aviso invalido")
    if abs(time.time() - aviso.creado_en) > 300:
        raise HTTPException(status_code=400, detail="Aviso vencido")   # evita reenviar avisos antiguos
    pago = db.pagos.find_one({"_id": aviso.payment_id})
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago desconocido")
    if pago["checkout_id"] != aviso.checkout_id or pago["monto"] != aviso.monto:
        raise HTTPException(status_code=400, detail="El aviso no coincide con el pago")
    try:
        # event_id es el _id: MongoDB no deja guardar dos veces el mismo aviso
        db.avisos.insert_one({"_id": aviso.event_id, "payment_id": aviso.payment_id, "recibido_en": ahora()})
    except DuplicateKeyError:
        return {"ok": True, "repetido": True}
    if pago["estado"] != "PENDIENTE":
        return {"ok": True, "ignorado": True}
    if aviso.resultado == "rechazado":
        db.pagos.update_one({"_id": pago["_id"]}, {"$set": {"estado": "RECHAZADO"}})
        return {"ok": True, "estado": "RECHAZADO"}
    # payments es quien autoriza el cambio: le avisa a orders que el pedido esta pagado
    r = llamar_servicio("payments", "orders", "POST", f"/internal/orders/{pago['order_id']}/paid",
                        json={"payment_id": pago["_id"]})
    if r.status_code == 200:
        estado = "APROBADO"
    elif r.status_code == 409:
        estado = "REEMBOLSO_PENDIENTE"   # se pago un pedido que ya estaba anulado
    else:
        db.avisos.delete_one({"_id": aviso.event_id})   # el proveedor reintentara
        raise HTTPException(status_code=503, detail="No fue posible confirmar el pedido")
    db.pagos.update_one({"_id": pago["_id"]}, {"$set": {"estado": estado}})
    return {"ok": True, "estado": estado}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Payments Service"}
