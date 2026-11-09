"""Auth Service: registro, verificacion de correo, login, introspect, logout y mantenedor de usuarios.

Basado en auth_service.py del ejemplo de clase (Semana 9). Cambios:
  - Los usuarios y sesiones se guardan en MongoDB (no en un diccionario en memoria).
  - Las claves se guardan con hash argon2id (con sal), nunca en texto plano.
  - En la base se guarda el SHA-256 del token, no el token (si se filtra la base, no sirve).
  - Caso 19 (RF5, RF6, RF11): el correo del cliente se valida con un codigo enviado por el servicio de
    notificaciones (API de mensajeria simulada). Sin correo verificado no se puede iniciar sesion.
  - Caso 19 (RF10, RF12): el administrador mantiene los usuarios y les asigna el perfil (rol).
  - Solo el gateway puede llamar a este servicio (secreto propio del par gateway -> auth).
"""
import hashlib
import re
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from comun import (registrar_logs, SECRETOS, conectar_mongo, exigir_rol, leer_secretos, llamar_servicio, usuario_actual,
                   verificar_servicio)

TOKEN_LIFETIME_MINUTES = 15
MINUTOS_CODIGO = 30
hasher = PasswordHasher()   # argon2id por defecto
db = None


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def correo_valido(correo):
    return re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,190}\.[a-zA-Z]{2,}", correo) is not None


def ahora():
    return datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    leer_secretos("auth")
    db = conectar_mongo("auth")
    db.usuarios.create_index("email", unique=True)
    # Usuarios de prueba FICTICIOS (uno por perfil del Caso 19). Su clave viene de Vault, no del codigo.
    for user_id, email, rol in [("USR-001", "admin@aromaycafe.test", "admin"),
                                ("USR-002", "despacho@aromaycafe.test", "despacho"),
                                ("USR-003", "ana@aromaycafe.test", "cliente"),
                                ("USR-004", "pedro@aromaycafe.test", "cliente"),
                                ("USR-005", "dueno@aromaycafe.test", "dueno"),
                                ("USR-006", "cajero@aromaycafe.test", "cajero")]:
        if db.usuarios.find_one({"_id": user_id}) is None:
            db.usuarios.insert_one({"_id": user_id, "email": email, "rol": rol, "correo_verificado": True,
                                    "clave_hash": hasher.hash(SECRETOS["clave_usuarios_prueba"])})
    yield


app = FastAPI(title="Authentication Service", lifespan=lifespan, docs_url=None, redoc_url=None)
registrar_logs(app, "auth")
solo_gateway = Depends(verificar_servicio("gateway"))


class RegistroRequest(BaseModel):
    """Datos del cliente del Caso 19 (RF5). Los opcionales tambien se pueden completar despues en el perfil."""
    email: str = Field(max_length=254)
    nombre: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    run: Optional[str] = Field(default=None, max_length=14)
    telefono: Optional[str] = Field(default=None, max_length=20)
    direccion: Optional[str] = Field(default=None, max_length=150)
    comuna: Optional[str] = Field(default=None, max_length=60)
    provincia: Optional[str] = Field(default=None, max_length=60)
    region: Optional[str] = Field(default=None, max_length=60)
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)
    sexo: Optional[Literal["femenino", "masculino", "otro"]] = None


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class VerificacionRequest(BaseModel):
    email: str = Field(max_length=254)
    codigo: str = Field(pattern=r"^\d{6}$")


def registrar_cliente(datos: RegistroRequest):
    """Lo usan el registro web (S03) y el administrador en el local (S31). En ambos casos se valida el correo."""
    email = datos.email.strip().lower()
    if not correo_valido(email):
        raise HTTPException(status_code=422, detail="Correo invalido")
    if db.usuarios.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="No fue posible registrar con esos datos")
    user_id = "USR-" + secrets.token_hex(4).upper()
    codigo = f"{secrets.randbelow(1_000_000):06d}"   # codigo de 6 digitos para validar el correo
    db.usuarios.insert_one({"_id": user_id, "email": email, "rol": "cliente", "correo_verificado": False,
                            "clave_hash": hasher.hash(datos.password),
                            "codigo_hash": hash_token(codigo),
                            "codigo_expira": ahora() + timedelta(minutes=MINUTOS_CODIGO)})
    # El perfil (RUN, direccion, etc.) lo guarda el servicio clients, que tambien valida esos datos
    perfil = datos.model_dump(exclude={"password"})
    perfil.update({"user_id": user_id, "email": email})
    respuesta = llamar_servicio("auth", "clients", "POST", "/internal/clients", json=perfil)
    if respuesta.status_code != 201:
        db.usuarios.delete_one({"_id": user_id})   # se deshace el registro
        detalle = respuesta.json().get("detail") if respuesta.status_code == 422 else None
        raise HTTPException(status_code=422 if detalle else 503,
                            detail=detalle or "No fue posible completar el registro")
    # El codigo se envia al correo mediante el servicio de notificaciones (API de mensajeria)
    llamar_servicio("auth", "notificaciones", "POST", "/internal/verificacion",
                    json={"email": email, "nombre": datos.nombre, "codigo": codigo})
    return {"user_id": user_id, "message": "Te enviamos un codigo a tu correo para activar la cuenta"}


@app.post("/register", status_code=201, dependencies=[solo_gateway])
def register(request: RegistroRequest):
    return registrar_cliente(request)


@app.post("/admin/clientes", status_code=201, dependencies=[solo_gateway])
def registrar_en_local(request: RegistroRequest, usuario=Depends(usuario_actual)):
    """RF6: el administrador registra al cliente en el restaurant. Igual se valida su correo."""
    exigir_rol(usuario, "admin")
    return registrar_cliente(request)


@app.post("/verificar-correo", dependencies=[solo_gateway])
def verificar_correo(request: VerificacionRequest):
    usuario = db.usuarios.find_one({"email": request.email.strip().lower(), "correo_verificado": False})
    if (usuario is None or usuario["codigo_expira"].replace(tzinfo=timezone.utc) < ahora()
            or not secrets.compare_digest(usuario["codigo_hash"], hash_token(request.codigo))):
        raise HTTPException(status_code=400, detail="Codigo invalido o vencido")
    db.usuarios.update_one({"_id": usuario["_id"]}, {"$set": {"correo_verificado": True},
                                                     "$unset": {"codigo_hash": "", "codigo_expira": ""}})
    return {"message": "Correo verificado, ya puedes iniciar sesion"}


@app.post("/login", dependencies=[solo_gateway])
def login(request: LoginRequest):
    usuario = db.usuarios.find_one({"email": request.email.strip().lower()})
    if usuario is None:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    try:
        hasher.verify(usuario["clave_hash"], request.password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not usuario["correo_verificado"]:
        raise HTTPException(status_code=403, detail="Debes verificar tu correo antes de iniciar sesion")
    access_token = secrets.token_urlsafe(32)
    expiration = ahora() + timedelta(minutes=TOKEN_LIFETIME_MINUTES)
    db.sesiones.insert_one({"_id": hash_token(access_token), "user_id": usuario["_id"],
                            "rol": usuario["rol"], "expires_at": expiration})
    return {"access_token": access_token, "token_type": "bearer",
            "expires_in": TOKEN_LIFETIME_MINUTES * 60, "rol": usuario["rol"]}


@app.post("/introspect", dependencies=[solo_gateway])
def introspect(request: TokenRequest):
    session = db.sesiones.find_one({"_id": hash_token(request.token)})
    if session is None:
        return {"active": False}
    expires_at = session["expires_at"].replace(tzinfo=timezone.utc)
    if ahora() > expires_at:
        db.sesiones.delete_one({"_id": session["_id"]})
        return {"active": False}
    return {"active": True, "user_id": session["user_id"], "rol": session["rol"],
            "expires_at": expires_at.isoformat()}


@app.post("/logout", dependencies=[solo_gateway])
def logout(request: TokenRequest):
    db.sesiones.delete_one({"_id": hash_token(request.token)})
    return {"message": "Sesion finalizada"}


# ------------------------------------------------------------------ Mantenedor de usuarios (RF10, RF12)
class FuncionarioNuevo(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    rol: Literal["cajero", "despacho", "dueno", "admin"]


class CambioRol(BaseModel):
    rol: Literal["cliente", "cajero", "despacho", "dueno", "admin"]


@app.get("/usuarios", dependencies=[solo_gateway])
def listar_usuarios(usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "admin")
    return [{"user_id": u["_id"], "email": u["email"], "rol": u["rol"], "correo_verificado": u["correo_verificado"]}
            for u in db.usuarios.find().sort("_id", 1)]   # nunca se devuelve el hash de la clave


@app.post("/usuarios", status_code=201, dependencies=[solo_gateway])
def crear_funcionario(datos: FuncionarioNuevo, usuario=Depends(usuario_actual)):
    """El administrador crea las cuentas de los funcionarios (cajero, despacho, dueno, admin)."""
    exigir_rol(usuario, "admin")
    email = datos.email.strip().lower()
    if not correo_valido(email):
        raise HTTPException(status_code=422, detail="Correo invalido")
    if db.usuarios.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo")
    user_id = "USR-" + secrets.token_hex(4).upper()
    db.usuarios.insert_one({"_id": user_id, "email": email, "rol": datos.rol, "correo_verificado": True,
                            "clave_hash": hasher.hash(datos.password)})
    return {"user_id": user_id, "email": email, "rol": datos.rol}


@app.put("/usuarios/{user_id}/rol", dependencies=[solo_gateway])
def cambiar_rol(user_id: str, datos: CambioRol, usuario=Depends(usuario_actual)):
    exigir_rol(usuario, "admin")
    if user_id == usuario["user_id"]:
        raise HTTPException(status_code=409, detail="No puedes cambiar tu propio perfil")
    r = db.usuarios.update_one({"_id": user_id}, {"$set": {"rol": datos.rol}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.sesiones.delete_many({"user_id": user_id})   # debe volver a iniciar sesion con su nuevo perfil
    return {"user_id": user_id, "rol": datos.rol}


@app.get("/health")
def health():
    return {"status": "OK", "service": "Authentication Service"}
