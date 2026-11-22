"""Analitica: reportes de ventas para el administrador. Separado de los servicios transaccionales.

- Origen de los datos: orders envia cada pedido pagado a POST /internal/ventas.
- Actualizacion: inmediata; si analitica no responde, orders reintenta cada 30 s (retraso aceptado).
- Datos personales: NINGUNO. El mensaje no trae user_id, nombre ni direccion.
- Agregaciones: total vendido, cantidad de pedidos, ticket promedio, ventas por dia, productos mas vendidos.
"""
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel, Field

from comun import registrar_logs, conectar_mongo, exigir_rol, leer_secretos, usuario_actual, verificar_servicio

db = None


def resumir_ventas(ventas):
    """Calcula el reporte a partir de una lista de ventas."""
    total = sum(v["total"] for v in ventas)
    por_dia = defaultdict(lambda: {"pedidos": 0, "total": 0})
    productos = defaultdict(lambda: {"nombre": "", "cantidad": 0, "total": 0})
    for v in ventas:
        dia = v["pagado_en"][:10]
        por_dia[dia]["pedidos"] += 1
        por_dia[dia]["total"] += v["total"]
        for l in v["lineas"]:
            productos[l["product_id"]]["nombre"] = l["nombre"]
            productos[l["product_id"]]["cantidad"] += l["cantidad"]
            productos[l["product_id"]]["total"] += l["cantidad"] * l["precio"]
    mas_vendidos = sorted(productos.items(), key=lambda p: p[1]["cantidad"], reverse=True)[:5]
    return {"pedidos": len(ventas), "total_vendido": total,
            "ticket_promedio": round(total / len(ventas)) if ventas else 0,
            "por_dia": [{"dia": d, **valores} for d, valores in sorted(por_dia.items())],
            "mas_vendidos": [{"product_id": pid, **valores} for pid, valores in mas_vendidos]}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("analitica")
    db = conectar_mongo("analitica")
    yield


app = FastAPI(title="Analitica Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "analitica")


class LineaVenta(BaseModel):
    product_id: str = Field(max_length=40)
    nombre: str = Field(max_length=80)
    cantidad: int = Field(ge=1)
    precio: int = Field(ge=0)


class Venta(BaseModel):
    """Lo unico que recibe analitica de un pedido pagado. Sin user_id, nombre ni direccion."""
    order_id: str = Field(max_length=30)
    pagado_en: str = Field(max_length=30)
    total: int = Field(ge=0)
    tipo_entrega: str = Field(max_length=20)
    lineas: list[LineaVenta]


@app.post("/internal/ventas", status_code=201, dependencies=[Depends(verificar_servicio("orders"))])
def registrar_venta(venta: Venta):
    # _id = order_id: si orders reintenta el mismo pedido, se reemplaza (no se cuenta dos veces)
    db.ventas.replace_one({"_id": venta.order_id}, venta.model_dump(), upsert=True)
    return {"ok": True}


@app.get("/reportes/ventas", dependencies=[Depends(verificar_servicio("gateway", "graphql"))])
def reporte_ventas(usuario=Depends(usuario_actual),
                   desde: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                   hasta: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    exigir_rol(usuario, "dueno", "admin")
    filtro = {}
    if desde or hasta:
        filtro["pagado_en"] = {}
        if desde:
            filtro["pagado_en"]["$gte"] = desde
        if hasta:
            filtro["pagado_en"]["$lte"] = hasta + "T23:59:59"
    return resumir_ventas(list(db.ventas.find(filtro)))


@app.get("/health")
def health():
    return {"status": "ok", "service": "Analitica Service"}
