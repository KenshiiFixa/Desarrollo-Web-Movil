"""Proveedor de pagos SIMULADO (no es parte de nuestro sistema; reemplaza a Webpay/Flow/etc. en pruebas).

Respeta el contrato tipico de un proveedor real:
  1. payments crea un "checkout" usando su API key (secreto del par payments -> proveedor).
  2. Cuando el cliente paga, el proveedor envia un aviso (webhook) a la URL PUBLICA del gateway,
     firmado con HMAC-SHA256. payments verifica la firma antes de creer el aviso.
"""
import hashlib
import hmac
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from comun import CLIENTE_HTTP, registrar_logs, SECRETOS, URLS, leer_secretos, verificar_servicio

checkouts = {}   # el proveedor real guarda esto en SU sistema, no en el nuestro


@asynccontextmanager
async def lifespan(app: FastAPI):
    leer_secretos("proveedor")
    yield


app = FastAPI(title="Proveedor de pagos (simulado)", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "proveedor")
solo_payments = Depends(verificar_servicio("payments"))


class Checkout(BaseModel):
    payment_id: str = Field(max_length=30)
    monto: int = Field(ge=1)


@app.post("/checkout", dependencies=[solo_payments])
def crear_checkout(datos: Checkout):
    checkout_id = "chk_" + secrets.token_hex(8)
    checkouts[checkout_id] = datos.model_dump()
    return {"checkout_id": checkout_id, "url_pago": f"https://sandbox.pagos.example/pagar/{checkout_id}"}


class Pagar(BaseModel):
    resultado: Literal["aprobado", "rechazado"] = "aprobado"
    repetir_aviso: int = Field(default=1, ge=1, le=3)   # para probar que un aviso repetido no se cobra 2 veces


@app.post("/checkout/{checkout_id}/pagar", dependencies=[solo_payments])
def pagar(checkout_id: str, datos: Pagar):
    checkout = checkouts.get(checkout_id)
    if checkout is None:
        raise HTTPException(status_code=404, detail="Checkout desconocido")
    aviso = {"event_id": "evt_" + uuid.uuid4().hex[:12], "payment_id": checkout["payment_id"],
             "checkout_id": checkout_id, "resultado": datos.resultado, "monto": checkout["monto"],
             "creado_en": int(time.time())}
    cuerpo = json.dumps(aviso).encode()
    firma = hmac.new(SECRETOS["webhook_clave"].encode(), cuerpo, hashlib.sha256).hexdigest()
    respuestas = []
    for _ in range(datos.repetir_aviso):
        # Se envia al gateway (la entrada publica), como lo haria un proveedor real desde Internet
        r = CLIENTE_HTTP.post(f"{URLS['gateway']}/api/v1/payments/webhook", content=cuerpo,
                              headers={"X-Firma": firma, "Content-Type": "application/json"}, timeout=10.0)
        respuestas.append({"status": r.status_code, "respuesta": r.json()})
    return {"avisos": respuestas}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Proveedor de pagos simulado"}
