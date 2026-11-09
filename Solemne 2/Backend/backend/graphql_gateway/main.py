"""GraphQL Gateway PRIVADO (Strawberry). Misma idea que el servidor GraphQL de la Semana 5
(types + Query + resolvers), pero en Python y sin base de datos propia:
cada resolver le pregunta al servicio dueno del dato (orders, inventory, payments, clients, analitica).

Agregacion principal: resumenPedido / misPedidos = estado (orders) + productos (inventory) + pago (payments).

Seguridad:
  - Solo lo llama el API Gateway, que ya verifico el token (POST /api/v1/graphql).
  - Cada servicio vuelve a revisar la identidad: si un cliente pide un pedido ajeno, orders responde 404.
  - El campo 'cliente' (datos personales) solo lo ven despacho/admin; 'reporteVentas' solo dueno/admin.
  - Limite de profundidad, de alias y de tamano de la consulta, y sin introspeccion.
  - Si inventory o payments fallan, se responde lo que se pudo armar MAS un aviso en 'errors'
    (no se presenta una respuesta parcial como si estuviera completa).
"""
from contextlib import asynccontextmanager
from typing import Optional

import strawberry
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules, MaxAliasesLimiter, QueryDepthLimiter
from strawberry.types import Info

from comun import registrar_logs, exigir_rol, leer_secretos, llamar_servicio, usuario_actual, verificar_servicio


@strawberry.type
class Producto:
    id: str
    nombre: str
    categoria: str
    disponible: bool


@strawberry.type
class Linea:
    product_id: str
    cantidad: int
    precio: int
    producto: Optional[Producto]   # viene de inventory


@strawberry.type
class Pago:
    id: str
    estado: str
    monto: int


@strawberry.type
class Cliente:
    nombre: str
    email: str
    telefono: Optional[str]


@strawberry.type
class Pedido:
    id: str
    estado: str
    tipo_entrega: str
    total: int
    creado_en: str
    lineas: list[Linea]
    pago: Optional[Pago]           # viene de payments
    user_id: strawberry.Private[str]   # Private: nunca sale en la respuesta

    @strawberry.field
    def cliente(self, info: Info) -> Optional[Cliente]:
        """Datos personales: solo el encargado de despacho y el admin. A otros se les responde error y null."""
        usuario = info.context["usuario"]
        if usuario["rol"] not in ("despacho", "admin"):
            raise PermissionError("No autorizado para ver datos del cliente")
        r = llamar_servicio("graphql", "clients", "GET", f"/clients/{self.user_id}", usuario=usuario)
        if r.status_code != 200:
            return None
        d = r.json()
        return Cliente(nombre=d["nombre"], email=d["email"], telefono=d.get("telefono"))


@strawberry.type
class ProductoVendido:
    product_id: str
    nombre: str
    cantidad: int
    total: int


@strawberry.type
class ReporteVentas:
    pedidos: int
    total_vendido: int
    ticket_promedio: int
    mas_vendidos: list[ProductoVendido]


def consultar_parcial(info, destino, ruta, ids):
    """Consulta un servicio complementario (inventory o payments). Si falla, no se cae toda la consulta:
    se devuelve [] y se agrega un aviso en 'errors', para que la respuesta no parezca completa."""
    try:
        r = llamar_servicio("graphql", destino, "GET", ruta, usuario=info.context["usuario"],
                            params={"ids": ",".join(ids)})
        if r.status_code == 200:
            return r.json()
    except HTTPException:
        pass
    info.context["avisos"].append(f"Servicio {destino} no disponible: la respuesta esta incompleta")
    return []


def armar_pedidos(info, pedidos_json):
    """Combina orders + inventory + payments. Hace UNA llamada a inventory y UNA a payments
    para todos los pedidos (no una por cada producto: evita el problema N+1)."""
    ids_productos = sorted({l["product_id"] for p in pedidos_json for l in p["lineas"]})
    ids_pedidos = [p["id"] for p in pedidos_json]
    productos, pagos = {}, {}
    if ids_productos:
        productos = {p["id"]: Producto(id=p["id"], nombre=p["nombre"], categoria=p["categoria"],
                                       disponible=p["disponible"])
                     for p in consultar_parcial(info, "inventory", "/internal/products", ids_productos)}
    if ids_pedidos:
        pagos = {p["order_id"]: Pago(id=p["id"], estado=p["estado"], monto=p["monto"])
                 for p in consultar_parcial(info, "payments", "/payments/by-orders", ids_pedidos)}
    return [Pedido(id=p["id"], estado=p["estado"], tipo_entrega=p["tipo_entrega"], total=p["total"],
                   creado_en=p["creado_en"], user_id=p.get("user_id", ""), pago=pagos.get(p["id"]),
                   lineas=[Linea(product_id=l["product_id"], cantidad=l["cantidad"], precio=l["precio"],
                                 producto=productos.get(l["product_id"])) for l in p["lineas"]])
            for p in pedidos_json]


@strawberry.type
class Query:
    @strawberry.field
    def resumen_pedido(self, info: Info, id: str) -> Optional[Pedido]:
        usuario = info.context["usuario"]
        # orders revisa que el pedido sea del usuario: si es ajeno responde 404 y aqui devolvemos null
        r = llamar_servicio("graphql", "orders", "GET", f"/orders/{id[:64]}", usuario=usuario)
        if r.status_code != 200:
            return None
        return armar_pedidos(info, [r.json()])[0]

    @strawberry.field
    def mis_pedidos(self, info: Info, limite: int = 10) -> list[Pedido]:
        usuario = info.context["usuario"]
        r = llamar_servicio("graphql", "orders", "GET", "/orders", usuario=usuario,
                            params={"limit": max(1, min(limite, 20))})   # paginacion con tope
        if r.status_code != 200:
            raise Exception("Servicio de pedidos no disponible")
        return armar_pedidos(info, r.json())

    @strawberry.field
    def reporte_ventas(self, info: Info) -> ReporteVentas:
        usuario = info.context["usuario"]
        if usuario["rol"] not in ("dueno", "admin"):
            raise PermissionError("Solo el dueno o el administrador pueden ver reportes")
        r = llamar_servicio("graphql", "analitica", "GET", "/reportes/ventas", usuario=usuario)
        if r.status_code != 200:
            raise Exception("Servicio de analitica no disponible")
        d = r.json()
        return ReporteVentas(pedidos=d["pedidos"], total_vendido=d["total_vendido"],
                             ticket_promedio=d["ticket_promedio"],
                             mas_vendidos=[ProductoVendido(**p) for p in d["mas_vendidos"]])


# Limites: profundidad maxima 5, maximo 5 alias por consulta y sin introspeccion (no se entrega el schema completo)
schema = strawberry.Schema(query=Query, extensions=[lambda: QueryDepthLimiter(max_depth=5),
                                                    lambda: MaxAliasesLimiter(max_alias_count=5),
                                                    lambda: AddValidationRules([NoSchemaIntrospectionCustomRule])])


@asynccontextmanager
async def lifespan(app: FastAPI):
    leer_secretos("graphql")
    yield


app = FastAPI(title="GraphQL Gateway", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "graphql")


class ConsultaGraphQL(BaseModel):
    query: str = Field(max_length=2000)   # consultas muy grandes se rechazan con 422
    variables: Optional[dict] = None


@app.post("/graphql", dependencies=[Depends(verificar_servicio("gateway"))])
def graphql(consulta: ConsultaGraphQL, usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    contexto = {"usuario": usuario, "avisos": []}
    resultado = schema.execute_sync(consulta.query, variable_values=consulta.variables, context_value=contexto)
    respuesta = {"data": resultado.data}
    errores = [{"message": e.message, "path": e.path} for e in (resultado.errors or [])]
    errores += [{"message": aviso, "path": None} for aviso in dict.fromkeys(contexto["avisos"])]
    if errores:
        respuesta["errors"] = errores
    return respuesta


@app.get("/health")
def health():
    return {"status": "ok", "service": "GraphQL Gateway"}
