"""Clients: perfil de los clientes y mensajes de contacto.

Datos del cliente segun el Caso 19 (RF5): run, nombre completo, direccion, comuna, provincia, region,
fecha de nacimiento, sexo, correo electronico y telefono.
Son datos personales: solo los ve el propio cliente, el encargado de despacho (lo necesario para
entregar el pedido) y el administrador. Nunca aparecen en el catalogo ni en la analitica.
"""
import re
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from comun import registrar_logs, conectar_mongo, exigir_rol, leer_secretos, usuario_actual, verificar_servicio

db = None
CAMPOS_PERFIL = ["nombre", "email", "telefono", "run", "direccion", "comuna", "provincia", "region",
                 "fecha_nacimiento", "sexo"]


def validar_run(run):
    """Valida un RUN chileno con su digito verificador (modulo 11). Devuelve '12345678-5' o None."""
    run = run.replace(".", "").replace("-", "").replace(" ", "").upper()
    if not re.fullmatch(r"\d{7,8}[0-9K]", run):
        return None
    cuerpo, dv = run[:-1], run[-1]
    suma, multiplicador = 0, 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - suma % 11
    esperado = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return f"{cuerpo}-{dv}" if dv == esperado else None


def telefono_valido(telefono):
    return telefono is None or re.fullmatch(r"[+0-9 ()-]{6,20}", telefono) is not None


def fecha_nacimiento_valida(fecha):
    """Formato AAAA-MM-DD y una fecha pasada."""
    if fecha is None:
        return True
    try:
        return date.fromisoformat(fecha) < date.today()
    except ValueError:
        return False


def validar_datos(datos):
    """Valida los datos personales y devuelve el RUN normalizado (o None si no viene)."""
    if not telefono_valido(datos.telefono):
        raise HTTPException(status_code=422, detail="Telefono invalido")
    if not fecha_nacimiento_valida(datos.fecha_nacimiento):
        raise HTTPException(status_code=422, detail="Fecha de nacimiento invalida")
    if not datos.run:
        return None
    run = validar_run(datos.run)
    if run is None:
        raise HTTPException(status_code=422, detail="RUN invalido")
    return run


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("clients")
    db = conectar_mongo("clients")
    # Perfiles FICTICIOS de los usuarios de prueba
    for user_id, nombre, email in [("USR-001", "Admin Aroma", "admin@aromaycafe.test"),
                                   ("USR-002", "Encargado Despacho", "despacho@aromaycafe.test"),
                                   ("USR-003", "Ana Perez", "ana@aromaycafe.test"),
                                   ("USR-004", "Pedro Soto", "pedro@aromaycafe.test"),
                                   ("USR-005", "Duena Aroma", "dueno@aromaycafe.test"),
                                   ("USR-006", "Cajero Virtual", "cajero@aromaycafe.test")]:
        if db.clientes.find_one({"_id": user_id}) is None:
            db.clientes.insert_one({"_id": user_id, **{c: None for c in CAMPOS_PERFIL},
                                    "nombre": nombre, "email": email})
    yield


app = FastAPI(title="Clients Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "clients")
solo_gateway = Depends(verificar_servicio("gateway"))


def perfil(user_id):
    doc = db.clientes.find_one({"_id": user_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    doc.pop("_id")
    return doc


class Perfil(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    telefono: Optional[str] = Field(default=None, max_length=20)
    run: Optional[str] = Field(default=None, max_length=14)
    direccion: Optional[str] = Field(default=None, max_length=150)
    comuna: Optional[str] = Field(default=None, max_length=60)
    provincia: Optional[str] = Field(default=None, max_length=60)
    region: Optional[str] = Field(default=None, max_length=60)
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)
    sexo: Optional[Literal["femenino", "masculino", "otro"]] = None


class ClienteNuevo(Perfil):
    user_id: str = Field(pattern=r"^USR-[A-Z0-9]{3,12}$")
    email: str = Field(max_length=254)


@app.post("/internal/clients", status_code=201, dependencies=[Depends(verificar_servicio("auth"))])
def crear_perfil(cliente: ClienteNuevo):
    """Lo llama el Auth Service cuando alguien se registra (en la web o en el local)."""
    run = validar_datos(cliente)
    db.clientes.insert_one({"_id": cliente.user_id, **cliente.model_dump(exclude={"user_id"}), "run": run})
    return {"user_id": cliente.user_id}


@app.get("/internal/clients/{user_id}/email", dependencies=[Depends(verificar_servicio("notificaciones"))])
def correo_cliente(user_id: str):
    """Para notificaciones: SOLO nombre y correo (lo minimo para enviar la boleta)."""
    datos = perfil(user_id)
    return {"nombre": datos["nombre"], "email": datos["email"]}


def guardar_perfil(user_id, datos: Perfil):
    run = validar_datos(datos)
    perfil(user_id)
    db.clientes.update_one({"_id": user_id}, {"$set": {**datos.model_dump(), "run": run}})
    return perfil(user_id)


@app.get("/clients/me", dependencies=[solo_gateway])
def mi_perfil(usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    return perfil(usuario["user_id"])   # siempre el del usuario de la sesion, nunca otro


@app.put("/clients/me", dependencies=[solo_gateway])
def actualizar_perfil(datos: Perfil, usuario=Depends(usuario_actual)):
    exigir_rol(usuario)
    return guardar_perfil(usuario["user_id"], datos)


@app.get("/clients/{user_id}", dependencies=[Depends(verificar_servicio("gateway", "graphql"))])
def ver_cliente(user_id: str, usuario=Depends(usuario_actual)):
    """Despacho ve nombre, telefono y direccion de entrega. Solo el admin ve todo (RUN, fecha de nacimiento...)."""
    exigir_rol(usuario, "despacho", "admin")
    datos = perfil(user_id)
    if usuario["rol"] != "admin":
        datos = {c: datos.get(c) for c in ("nombre", "email", "telefono", "direccion", "comuna")}
    return datos


@app.put("/clients/{user_id}", dependencies=[solo_gateway])
def editar_cliente(user_id: str, datos: Perfil, usuario=Depends(usuario_actual)):
    """Mantenedor de clientes (RF10): el administrador corrige los datos de un cliente."""
    exigir_rol(usuario, "admin")
    return guardar_perfil(user_id, datos)


class Contacto(BaseModel):
    """Formulario de Contacto.php"""
    nombre: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
    telefono: Optional[str] = Field(default=None, max_length=20)
    motivo: Literal["pedido", "sugerencia", "reclamo", "eventos"]
    mensaje: str = Field(min_length=5, max_length=2000)


@app.post("/contact", status_code=201, dependencies=[solo_gateway])
def enviar_contacto(contacto: Contacto):
    if not telefono_valido(contacto.telefono):
        raise HTTPException(status_code=422, detail="Telefono invalido")
    db.contacto.insert_one({**contacto.model_dump(), "creado_en": ahora()})
    return {"message": "Mensaje recibido"}


@app.get("/contact", dependencies=[solo_gateway])
def listar_contacto(usuario=Depends(usuario_actual), limit: int = Query(20, ge=1, le=50),
                    skip: int = Query(0, ge=0)):
    exigir_rol(usuario, "admin")
    mensajes = []
    for doc in db.contacto.find().sort("creado_en", -1).skip(skip).limit(limit):
        doc["id"] = str(doc.pop("_id"))
        mensajes.append(doc)
    return mensajes


@app.get("/health")
def health():
    return {"status": "ok", "service": "Clients Service"}
