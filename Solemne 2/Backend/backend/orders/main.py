"""Orders: pedidos de Aroma & Cafe, sus estados y la boleta digital.

- Reserva el stock en inventory por gRPC (los precios los entrega inventory, no el navegador).
- Un pedido solo pasa a PAGADO cuando lo confirma el servicio payments.
- Cuando un pedido se paga, avisa por HTTP (con su secreto de servicio) a:
    notificaciones -> envia la boleta al cliente por correo (simulado).
    analitica      -> registra la venta para los reportes (sin datos personales).
"""
import os
import secrets
import threading
import unicodedata
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import grpc
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from comun import (ID_SOLICITUD, canal_inventory, registrar_logs, SECRETOS, conectar_mongo, exigir_rol, leer_secretos, llamar_servicio, usuario_actual,
                   verificar_servicio)
from proto import inventario_pb2, inventario_pb2_grpc

# Caso 19: el despacho es GRATIS y solo dentro de 3 km del local. Se controla con la lista de comunas
# que quedan dentro de ese radio (configurable con la variable COMUNAS_DESPACHO).
COMUNAS_DESPACHO = [c.strip() for c in os.getenv("COMUNAS_DESPACHO", "maipu").split(",")]
CAJA_WEB = "CAJA-WEB-01"   # RF4: las ventas web se asocian a la caja del cajero virtual
MINUTOS_PARA_PAGAR = 30
# Cambios de estado que puede hacer el encargado de despacho (o el admin)
TRANSICIONES = {"PAGADO": ["EN_PREPARACION"], "EN_PREPARACION": ["LISTO"],
                "LISTO": ["EN_CAMINO", "ENTREGADO"], "EN_CAMINO": ["ENTREGADO"]}

db = None


# ------------------------------------------------------------------ Reglas de negocio
def calcular_total(lineas):
    """Total con los precios de inventory (nunca los del navegador). El despacho es gratis."""
    return sum(l["precio"] * l["cantidad"] for l in lineas)


def comuna_con_despacho(comuna):
    """True si la comuna esta dentro del radio de despacho. Ignora mayusculas y tildes (Maipu = Maipú)."""
    sin_tildes = unicodedata.normalize("NFD", comuna or "").encode("ascii", "ignore").decode()
    return sin_tildes.strip().lower() in COMUNAS_DESPACHO


def transicion_valida(estado_actual, estado_nuevo, tipo_entrega):
    """LISTO -> EN_CAMINO solo si es delivery; LISTO -> ENTREGADO solo si es retiro en el local."""
    if estado_nuevo not in TRANSICIONES.get(estado_actual, []):
        return False
    if estado_actual == "LISTO":
        return (estado_nuevo == "EN_CAMINO") == (tipo_entrega == "delivery")
    return True


def armar_boleta(pedido):
    """Boleta digital. Los precios de la carta incluyen IVA (19 %)."""
    neto = round(pedido["total"] / 1.19)
    return {"folio": pedido["folio"], "fecha": pedido["pagado_en"], "pedido": pedido["_id"], "caja": pedido["caja"],
            "detalle": [{"producto": l["nombre"], "cantidad": l["cantidad"], "precio": l["precio"],
                         "total": l["precio"] * l["cantidad"]} for l in pedido["lineas"]],
            "neto": neto, "iva": pedido["total"] - neto, "total": pedido["total"]}


def pedido_para_cliente(pedido, ver_dueno=False):
    """Lo que se devuelve al frontend. El user_id solo lo ve el personal del local."""
    datos = {"id": pedido["_id"], "estado": pedido["estado"], "tipo_entrega": pedido["tipo_entrega"],
             "direccion": pedido["direccion"], "comuna": pedido["comuna"], "lineas": pedido["lineas"],
             "total": pedido["total"], "creado_en": pedido["creado_en"], "pagado_en": pedido.get("pagado_en")}
    if ver_dueno:
        datos["user_id"] = pedido["user_id"]
    return datos


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ gRPC hacia inventory
_stub_inventario = None


def inventario():
    """Cliente gRPC hacia inventory, con TLS. Se crea una vez y se reutiliza (como el cliente HTTP)."""
    global _stub_inventario
    if _stub_inventario is None:
        _stub_inventario = inventario_pb2_grpc.InventarioStub(canal_inventory())
    return _stub_inventario


def metadata_grpc():
    return [("x-servicio", "orders"), ("x-servicio-secreto", SECRETOS["hacia_inventory"]),
            ("x-request-id", ID_SOLICITUD.get())]


def reservar(order_id, items):
    peticion = inventario_pb2.ReservaRequest(
        order_id=order_id, items=[inventario_pb2.Item(product_id=i.product_id, cantidad=i.cantidad) for i in items])
    try:
        # timeout = plazo maximo (deadline). Si inventory no responde en 3 s, no se crea el pedido.
        respuesta = inventario().ReservarStock(peticion, timeout=3, metadata=metadata_grpc())
    except grpc.RpcError as error:
        if error.code() == grpc.StatusCode.FAILED_PRECONDITION:
            raise HTTPException(status_code=409, detail=error.details())
        if error.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise HTTPException(status_code=422, detail="Pedido invalido")
        raise HTTPException(status_code=503, detail="Inventario no disponible")
    return [{"product_id": l.product_id, "nombre": l.nombre, "precio": l.precio, "cantidad": l.cantidad}
            for l in respuesta.lineas]


def liberar(order_id):
    """Devuelve el stock. Si inventory no responde, queda marcado y se reintenta despues."""
    try:
        inventario().LiberarStock(inventario_pb2.LiberarRequest(order_id=order_id), timeout=3,
                                  metadata=metadata_grpc())
        db.pedidos.update_one({"_id": order_id}, {"$set": {"stock_devuelto": True}})
    except grpc.RpcError:
        pass


# ------------------------------------------------------------------ Avisos a notificaciones y analitica
def avisar_pedido_pagado(pedido):
    """Envia la boleta a notificaciones y la venta a analitica.
    Si alguno no responde, el pedido queda marcado y se reintenta en segundo plano (no se pierde)."""
    boleta = {"order_id": pedido["_id"], "user_id": pedido["user_id"], "boleta": armar_boleta(pedido)}
    # Analitica NO recibe datos personales: ni user_id ni direccion
    venta = {"order_id": pedido["_id"], "pagado_en": pedido["pagado_en"], "total": pedido["total"],
             "tipo_entrega": pedido["tipo_entrega"],
             "lineas": [{"product_id": l["product_id"], "nombre": l["nombre"], "cantidad": l["cantidad"],
                         "precio": l["precio"]} for l in pedido["lineas"]]}
    try:
        r1 = llamar_servicio("orders", "notificaciones", "POST", "/internal/boletas", json=boleta)
        r2 = llamar_servicio("orders", "analitica", "POST", "/internal/ventas", json=venta)
        if r1.status_code == 201 and r2.status_code == 201:
            db.pedidos.update_one({"_id": pedido["_id"]}, {"$set": {"avisos_enviados": True}})
    except HTTPException:
        print(f"Notificaciones o analitica no disponible, se reintentara el pedido {pedido['_id']}")


def tareas_en_segundo_plano():
    """Cada 30 s: anula pedidos sin pagar despues de 30 min, reintenta devolver stock y enviar avisos."""
    while True:
        time.sleep(30)
        try:
            limite = (datetime.now(timezone.utc) - timedelta(minutes=MINUTOS_PARA_PAGAR)).isoformat(timespec="seconds")
            for p in db.pedidos.find({"estado": "PENDIENTE_PAGO", "creado_en": {"$lt": limite}}):
                db.pedidos.update_one({"_id": p["_id"], "estado": "PENDIENTE_PAGO"},
                                      {"$set": {"estado": "ANULADO", "motivo_anulacion": "Sin pago en 30 minutos"},
                                       "$push": {"historial": {"estado": "ANULADO", "por": "sistema", "en": ahora()}}})
            for p in db.pedidos.find({"estado": "ANULADO", "stock_devuelto": False}):
                liberar(p["_id"])
            for p in db.pedidos.find({"pagado_en": {"$ne": None}, "avisos_enviados": False}):
                avisar_pedido_pagado(p)
        except Exception as error:
            print(f"Error en tareas de segundo plano: {error}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("orders")
    db = conectar_mongo("orders")
    db.pedidos.create_index("user_id")
    threading.Thread(target=tareas_en_segundo_plano, daemon=True).start()
    yield


app = FastAPI(title="Orders Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "orders")
gateway_o_graphql = Depends(verificar_servicio("gateway", "graphql"))


class ItemPedido(BaseModel):
    product_id: str = Field(min_length=2, max_length=40)
    cantidad: int = Field(ge=1, le=20)


class PedidoNuevo(BaseModel):
    """El navegador solo envia QUE quiere y CUANTO. Nunca precios ni totales."""
    items: list[ItemPedido] = Field(min_length=1, max_length=20)
    tipo_entrega: Literal["retiro", "delivery"]
    direccion: Optional[str] = Field(default=None, max_length=200)
    comuna: Optional[str] = Field(default=None, max_length=60)


def buscar_pedido(order_id, usuario):
    """Un cliente solo puede ver SUS pedidos. Si es ajeno se responde 404 (no se revela que existe)."""
    pedido = db.pedidos.find_one({"_id": order_id})
    if pedido is None or (usuario["rol"] == "cliente" and pedido["user_id"] != usuario["user_id"]):
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@app.post("/orders", status_code=201, dependencies=[gateway_o_graphql])
def crear_pedido(pedido: PedidoNuevo, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "cliente")
    es_delivery = pedido.tipo_entrega == "delivery"
    if es_delivery and not (pedido.direccion and len(pedido.direccion.strip()) >= 5 and pedido.comuna):
        raise HTTPException(status_code=422, detail="Para delivery se requiere direccion y comuna")
    if es_delivery and not comuna_con_despacho(pedido.comuna):
        raise HTTPException(status_code=422, detail="La direccion esta fuera del radio de despacho (3 km)")
    order_id = "ORD-" + secrets.token_hex(4).upper()
    lineas = reservar(order_id, pedido.items)
    documento = {"_id": order_id, "user_id": usuario["user_id"], "estado": "PENDIENTE_PAGO",
                 "tipo_entrega": pedido.tipo_entrega,
                 "direccion": pedido.direccion if es_delivery else None,
                 "comuna": pedido.comuna if es_delivery else None,
                 "lineas": lineas, "total": calcular_total(lineas),
                 "creado_en": ahora(), "pagado_en": None, "folio": None, "caja": None,
                 "stock_devuelto": False, "avisos_enviados": False,
                 "historial": [{"estado": "PENDIENTE_PAGO", "por": usuario["user_id"], "en": ahora()}]}
    db.pedidos.insert_one(documento)
    return pedido_para_cliente(documento)


@app.get("/orders", dependencies=[gateway_o_graphql])
def listar_pedidos(usuario=Depends(usuario_actual), estado: Optional[str] = Query(None, max_length=20),
                   limit: int = Query(20, ge=1, le=50), skip: int = Query(0, ge=0)):
    exigir_rol(usuario)
    filtro = {}
    if usuario["rol"] == "cliente":
        filtro["user_id"] = usuario["user_id"]   # el cliente solo ve los suyos
    if estado:
        filtro["estado"] = estado
    cursor = db.pedidos.find(filtro).sort("creado_en", -1).skip(skip).limit(limit)
    return [pedido_para_cliente(p, usuario["rol"] != "cliente") for p in cursor]


@app.get("/orders/{order_id}", dependencies=[gateway_o_graphql])
def ver_pedido(order_id: str, usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    return pedido_para_cliente(buscar_pedido(order_id, usuario), usuario["rol"] != "cliente")


@app.get("/orders/{order_id}/receipt", dependencies=[gateway_o_graphql])
def ver_boleta(order_id: str, usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    pedido = buscar_pedido(order_id, usuario)
    if pedido["pagado_en"] is None:
        raise HTTPException(status_code=409, detail="El pedido aun no esta pagado")
    return armar_boleta(pedido)


class Anulacion(BaseModel):
    motivo: str = Field(min_length=5, max_length=200)   # RF3: se indica el motivo de la anulacion


@app.post("/orders/{order_id}/cancel", dependencies=[gateway_o_graphql])
def anular_pedido(order_id: str, anulacion: Anulacion, usuario=Depends(usuario_actual)):
    """Anular NO borra el pedido: queda guardado con su motivo e historial. Solo si aun no se paga."""
    exigir_rol(usuario, "cliente", "admin")
    buscar_pedido(order_id, usuario)
    r = db.pedidos.update_one({"_id": order_id, "estado": "PENDIENTE_PAGO"},
                              {"$set": {"estado": "ANULADO", "motivo_anulacion": anulacion.motivo},
                               "$push": {"historial": {"estado": "ANULADO", "por": usuario["user_id"],
                                                       "motivo": anulacion.motivo, "en": ahora()}}})
    if r.modified_count == 0:
        raise HTTPException(status_code=409, detail="El pedido ya no se puede anular")
    liberar(order_id)
    return {"id": order_id, "estado": "ANULADO"}


class CambioEstado(BaseModel):
    estado: Literal["EN_PREPARACION", "LISTO", "EN_CAMINO", "ENTREGADO"]


@app.put("/orders/{order_id}/status", dependencies=[gateway_o_graphql])
def cambiar_estado(order_id: str, cambio: CambioEstado, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "despacho", "admin")
    pedido = buscar_pedido(order_id, usuario)
    if not transicion_valida(pedido["estado"], cambio.estado, pedido["tipo_entrega"]):
        raise HTTPException(status_code=409, detail=f"No se puede pasar de {pedido['estado']} a {cambio.estado}")
    db.pedidos.update_one({"_id": order_id, "estado": pedido["estado"]},
                          {"$set": {"estado": cambio.estado},
                           "$push": {"historial": {"estado": cambio.estado, "por": usuario["user_id"], "en": ahora()}}})
    return {"id": order_id, "estado": cambio.estado}


@app.get("/despacho", dependencies=[Depends(verificar_servicio("gateway"))])
def ordenes_de_despacho(usuario=Depends(usuario_actual)):
    """RF13: ordenes de despacho para imprimir y llevar a cocina, en el orden en que se pagaron."""
    exigir_rol(usuario, "despacho", "admin")
    pendientes = db.pedidos.find({"estado": {"$in": ["PAGADO", "EN_PREPARACION", "LISTO", "EN_CAMINO"]}})
    return [{"id": p["_id"], "pagado_en": p["pagado_en"], "estado": p["estado"], "tipo_entrega": p["tipo_entrega"],
             "direccion": p["direccion"], "comuna": p["comuna"], "user_id": p["user_id"],
             "productos": [{"nombre": l["nombre"], "cantidad": l["cantidad"]} for l in p["lineas"]]}
            for p in pendientes.sort("pagado_en", 1)]


@app.get("/ventas", dependencies=[Depends(verificar_servicio("gateway"))])
def ventas_de_la_caja(usuario=Depends(usuario_actual), limit: int = Query(50, ge=1, le=200)):
    """RF4: ventas web registradas en la caja del cajero virtual (pedidos pagados con boleta)."""
    exigir_rol(usuario, "cajero", "admin")
    ventas = db.pedidos.find({"caja": CAJA_WEB}).sort("pagado_en", -1).limit(limit)
    return [{"folio": p["folio"], "pedido": p["_id"], "fecha": p["pagado_en"], "total": p["total"],
             "caja": p["caja"], "estado": p["estado"]} for p in ventas]


# ------------------------------------------------------------------ Rutas internas (solo payments)
solo_payments = Depends(verificar_servicio("payments"))


@app.get("/internal/orders/{order_id}", dependencies=[solo_payments])
def pedido_interno(order_id: str):
    pedido = db.pedidos.find_one({"_id": order_id})
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido_para_cliente(pedido, ver_dueno=True)


class Pagado(BaseModel):
    payment_id: str = Field(max_length=30)


@app.post("/internal/orders/{order_id}/paid", dependencies=[solo_payments])
def marcar_pagado(order_id: str, datos: Pagado):
    pedido = db.pedidos.find_one({"_id": order_id})
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido["pagado_en"]:
        return {"estado": pedido["estado"], "repetido": True}   # aviso repetido: no se hace nada
    if pedido["estado"] != "PENDIENTE_PAGO":
        raise HTTPException(status_code=409, detail="El pedido ya no admite pago")
    # El folio de la boleta es correlativo: $inc es atomico en MongoDB
    folio = db.contadores.find_one_and_update({"_id": "boleta"}, {"$inc": {"valor": 1}},
                                              upsert=True, return_document=True)["valor"]
    r = db.pedidos.update_one({"_id": order_id, "estado": "PENDIENTE_PAGO"},
                              {"$set": {"estado": "PAGADO", "pagado_en": ahora(), "payment_id": datos.payment_id,
                                        "folio": f"B-{folio:06d}", "caja": CAJA_WEB},
                               "$push": {"historial": {"estado": "PAGADO", "por": "payments", "en": ahora()}}})
    if r.modified_count == 0:
        raise HTTPException(status_code=409, detail="El pedido ya no admite pago")
    avisar_pedido_pagado(db.pedidos.find_one({"_id": order_id}))
    return {"estado": "PAGADO"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Orders Service"}
