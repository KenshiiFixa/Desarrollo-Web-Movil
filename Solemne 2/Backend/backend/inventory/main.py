"""Inventory: catalogo, precios y stock de Aroma & Cafe.

- REST (como la API de la Semana 6): catalogo publico (con ofertas) y administracion de productos.
- gRPC (puerto 50051): ReservarStock y LiberarStock. Solo lo puede llamar orders.
Inventory es el UNICO que decide el precio y el stock de un producto.
"""
import re
import secrets
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Literal, Optional

import grpc
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from comun import GRPC_INVENTORY, credenciales_grpc_servidor, registrar_logs, SECRETOS, conectar_mongo, exigir_rol, leer_secretos, usuario_actual, verificar_servicio
from proto import inventario_pb2, inventario_pb2_grpc

db = None
servidor_grpc = None

# Carta FICTICIA de prueba (la misma que muestra el frontend en catalogo.php)
PRODUCTOS_INICIALES = [
    {"_id": "espresso-doble", "nombre": "Espresso Doble", "categoria": "cafe", "precio": 2500, "imagen": "espresso.png",
     "descripcion": "Doble shot de cafe de especialidad, intenso y de cuerpo completo."},
    {"_id": "latte-art", "nombre": "Latte Art", "categoria": "cafe", "precio": 3200, "imagen": "latte.png",
     "descripcion": "Espresso con leche texturizada y arte en la espuma."},
    {"_id": "cappuccino", "nombre": "Cappuccino", "categoria": "cafe", "precio": 3000, "imagen": "cappuccino.png",
     "descripcion": "Espresso, leche vaporizada y una capa generosa de espuma."},
    {"_id": "cold-brew", "nombre": "Cold Brew", "categoria": "frio", "precio": 3500, "imagen": "cold-brew.png",
     "descripcion": "Cafe extraido en frio durante 18 horas, suave y refrescante."},
    {"_id": "frappe-mocha", "nombre": "Frappe de Mocha", "categoria": "frio", "precio": 3900, "imagen": "frappe-mocha.png",
     "descripcion": "Cafe helado batido con chocolate y crema.", "precio_oferta": 3400},
    {"_id": "croissant", "nombre": "Croissant de Mantequilla", "categoria": "reposteria", "precio": 2800,
     "imagen": "croissant.png", "descripcion": "Hojaldrado, horneado cada manana."},
    {"_id": "tarta-frambuesa", "nombre": "Tarta de Frambuesa", "categoria": "reposteria", "precio": 4500,
     "imagen": "tarta-frambuesa.png", "descripcion": "Base de almendras con crema pastelera y frambuesas."},
    {"_id": "cheesecake-maracuya", "nombre": "Cheesecake de Maracuya", "categoria": "reposteria", "precio": 4800,
     "imagen": "cheesecake-maracuya.png", "descripcion": "Cheesecake cremoso con cobertura de maracuya."},
]


def precio_vigente(doc):
    """Si el producto esta en oferta se cobra el precio de oferta."""
    return doc.get("precio_oferta") or doc["precio"]


def producto_publico(doc):
    """Lo que ve cualquier visitante: SIN el stock exacto."""
    return {"id": doc["_id"], "nombre": doc["nombre"], "descripcion": doc["descripcion"],
            "categoria": doc["categoria"], "precio": doc["precio"], "precio_oferta": doc.get("precio_oferta"),
            "imagen": doc["imagen"], "disponible": doc["activo"] and doc["stock"] > 0}


def producto_admin(doc):
    """El administrador ademas ve el stock y si esta activo."""
    return {**producto_publico(doc), "stock": doc["stock"], "activo": doc["activo"]}


# ------------------------------------------------------------------ Reserva de stock (la usa gRPC)
def reservar_stock(order_id, items):
    """Descuenta el stock de cada producto. Si uno no alcanza, devuelve lo ya descontado (todo o nada).
    Si el pedido ya tenia reserva, devuelve la misma (asi un reintento no descuenta dos veces)."""
    reserva = db.reservas.find_one({"_id": order_id})
    if reserva is None:
        descontados = []
        for product_id, cantidad in items:
            # Operacion atomica: solo descuenta si hay stock suficiente
            r = db.productos.update_one({"_id": product_id, "activo": True, "stock": {"$gte": cantidad}},
                                        {"$inc": {"stock": -cantidad}})
            if r.modified_count == 0:
                for pid, cant in descontados:   # se devuelve lo que ya se habia descontado
                    db.productos.update_one({"_id": pid}, {"$inc": {"stock": cant}})
                raise ValueError(f"Stock insuficiente o producto no disponible: {product_id}")
            descontados.append((product_id, cantidad))
        reserva = {"_id": order_id, "items": descontados, "estado": "RESERVADA"}
        db.reservas.insert_one(reserva)
    lineas = []
    for product_id, cantidad in reserva["items"]:
        p = db.productos.find_one({"_id": product_id})
        lineas.append({"product_id": product_id, "nombre": p["nombre"], "precio": precio_vigente(p),
                       "cantidad": cantidad})
    return lineas


def liberar_stock(order_id):
    """Devuelve el stock de un pedido anulado. Si ya se libero, no hace nada."""
    r = db.reservas.update_one({"_id": order_id, "estado": "RESERVADA"}, {"$set": {"estado": "LIBERADA"}})
    if r.modified_count == 0:
        return 0
    reserva = db.reservas.find_one({"_id": order_id})
    for product_id, cantidad in reserva["items"]:
        db.productos.update_one({"_id": product_id}, {"$inc": {"stock": cantidad}})
    return len(reserva["items"])


class InventarioGrpc(inventario_pb2_grpc.InventarioServicer):
    """Servidor gRPC. Igual que verify_gateway, pero el secreto viaja en la 'metadata' de gRPC."""

    def verificar(self, context):
        metadata = dict(context.invocation_metadata())
        if metadata.get("x-servicio") != "orders" or not secrets.compare_digest(
                metadata.get("x-servicio-secreto", ""), SECRETOS["desde_orders"]):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "No autorizado")
        print(f"[inventory-grpc] req={metadata.get('x-request-id', '-')[:32]} llamada de orders", flush=True)

    def ReservarStock(self, request, context):
        self.verificar(context)
        items = [(i.product_id, i.cantidad) for i in request.items]
        if not items or len(items) > 20 or any(c < 1 or c > 20 for _, c in items):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Pedido invalido")
        try:
            lineas = reservar_stock(request.order_id, items)
        except ValueError as error:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(error))
        return inventario_pb2.ReservaReply(lineas=[inventario_pb2.Linea(**l) for l in lineas])

    def LiberarStock(self, request, context):
        self.verificar(context)
        return inventario_pb2.LiberarReply(liberados=liberar_stock(request.order_id))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, servidor_grpc
    leer_secretos("inventory")
    db = conectar_mongo("inventory")
    if db.productos.count_documents({}) == 0:
        for p in PRODUCTOS_INICIALES:
            db.productos.insert_one({"precio_oferta": None, **p, "stock": 40, "activo": True})
    # El servidor gRPC corre en hilos, junto con la API REST
    servidor_grpc = grpc.server(ThreadPoolExecutor(max_workers=10))
    inventario_pb2_grpc.add_InventarioServicer_to_server(InventarioGrpc(), servidor_grpc)
    servidor_grpc.add_secure_port(GRPC_INVENTORY, credenciales_grpc_servidor())   # TLS, solo 127.0.0.1
    servidor_grpc.start()
    yield
    servidor_grpc.stop(grace=2)


app = FastAPI(title="Inventory Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "inventory")
solo_gateway = Depends(verificar_servicio("gateway"))


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str = Field(max_length=300)
    categoria: Literal["cafe", "frio", "reposteria"]
    precio: int = Field(ge=1, le=1_000_000)
    stock: int = Field(ge=0, le=100_000)
    imagen: str = Field(default="", pattern=r"^[A-Za-z0-9._-]{0,80}$")
    precio_oferta: Optional[int] = Field(default=None, ge=1)   # oferta: debe ser menor que el precio


class ProductoNuevo(ProductoIn):
    id: str = Field(pattern=r"^[a-z0-9-]{2,40}$")


@app.get("/products", dependencies=[solo_gateway])
def listar_productos(categoria: Optional[str] = Query(None, max_length=20),
                     q: Optional[str] = Query(None, max_length=40), ofertas: bool = False):
    filtro = {"activo": True}
    if ofertas:
        filtro["precio_oferta"] = {"$ne": None}
    if categoria:
        filtro["categoria"] = categoria
    if q:
        filtro["nombre"] = {"$regex": re.escape(q), "$options": "i"}   # re.escape evita inyectar regex
    return [producto_publico(d) for d in db.productos.find(filtro).sort("nombre", 1)]


@app.get("/products/{product_id}", dependencies=[solo_gateway])
def obtener_producto(product_id: str):
    doc = db.productos.find_one({"_id": product_id, "activo": True})
    if doc is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto_publico(doc)


@app.get("/admin/products", dependencies=[solo_gateway])
def listar_admin(usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "admin", "dueno")
    return [producto_admin(d) for d in db.productos.find().sort("nombre", 1)]


def validar_oferta(producto):
    if producto.precio_oferta is not None and producto.precio_oferta >= producto.precio:
        raise HTTPException(status_code=422, detail="El precio de oferta debe ser menor que el precio")


@app.post("/products", status_code=201, dependencies=[solo_gateway])
def crear_producto(producto: ProductoNuevo, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "admin", "dueno")
    validar_oferta(producto)
    if db.productos.find_one({"_id": producto.id}):
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese id")
    datos = producto.model_dump()
    datos["_id"] = datos.pop("id")
    db.productos.insert_one({**datos, "activo": True})
    return producto_admin(db.productos.find_one({"_id": producto.id}))


@app.put("/products/{product_id}", dependencies=[solo_gateway])
def actualizar_producto(product_id: str, producto: ProductoIn, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "admin", "dueno")
    validar_oferta(producto)
    r = db.productos.update_one({"_id": product_id}, {"$set": {**producto.model_dump(), "activo": True}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto_admin(db.productos.find_one({"_id": product_id}))


@app.delete("/products/{product_id}", status_code=204, dependencies=[solo_gateway])
def eliminar_producto(product_id: str, usuario=Depends(usuario_actual)):
    """Baja logica (activo=False): los pedidos antiguos siguen mostrando el producto."""
    exigir_rol(usuario, "admin", "dueno")
    r = db.productos.update_one({"_id": product_id}, {"$set": {"activo": False}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")


@app.get("/internal/products", dependencies=[Depends(verificar_servicio("graphql"))])
def productos_por_lote(ids: str = Query(max_length=1000)):
    """Para el GraphQL gateway: varios productos en UNA llamada (incluye los dados de baja)."""
    lista = [i for i in ids.split(",") if re.fullmatch(r"[a-z0-9-]{2,40}", i)][:50]
    return [producto_publico(d) for d in db.productos.find({"_id": {"$in": lista}})]


@app.get("/health")
def health():
    return {"status": "ok", "service": "Inventory Service"}
