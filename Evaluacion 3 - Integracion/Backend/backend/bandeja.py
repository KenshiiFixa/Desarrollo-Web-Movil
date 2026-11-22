"""Bandeja de correo simulada: muestra los ultimos correos que guardo notificaciones
(por ejemplo, el codigo de verificacion del registro).

Uso:
    docker compose exec notificaciones python bandeja.py               # ultimos 5 correos
    docker compose exec notificaciones python bandeja.py correo@x.cl   # solo los de ese correo"""
import sys

from comun import conectar_mongo, leer_secretos

leer_secretos("notificaciones")
filtro = {"para": sys.argv[1].strip().lower()} if len(sys.argv) > 1 else {}
correos = list(conectar_mongo("notificaciones").correos.find(filtro).sort("enviado_en", -1).limit(5))
if not correos:
    print("No hay correos" + (f" para {sys.argv[1]}" if filtro else ""))
for c in correos:
    print(f"--- {c['enviado_en']}  para: {c['para']}\nAsunto: {c['asunto']}\n{c['cuerpo']}\n")
