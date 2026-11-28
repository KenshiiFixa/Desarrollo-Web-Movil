"""Prueba de sesion expirada: deja vencidas (expires_at en el pasado) las sesiones de un usuario, sin esperar
los 15 minutos. Corre dentro del contenedor de auth, con su propio usuario de MongoDB.

Uso con Docker (desde la carpeta Backend):
    docker compose exec auth python vencer_sesion.py ana@aromaycafe.test
"""
import sys
from datetime import datetime, timedelta, timezone

from comun import conectar_mongo, leer_secretos

leer_secretos("auth")
db = conectar_mongo("auth")
usuario = db.usuarios.find_one({"email": sys.argv[1].strip().lower()})
if usuario is None:
    sys.exit("No existe ese usuario")
r = db.sesiones.update_many({"user_id": usuario["_id"]},
                            {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}})
print(f"Sesiones vencidas de {usuario['_id']}: {r.modified_count}")
