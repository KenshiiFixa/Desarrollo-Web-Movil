"""Bandeja de correo SIMULADA: muestra los ultimos correos que guardo el servicio notificaciones
(por ejemplo, el codigo para verificar el correo al registrarse). Simula que el cliente abre su correo.

Uso con Docker:
    docker compose exec notificaciones python bandeja.py               # ultimos 5 correos
    docker compose exec notificaciones python bandeja.py correo@x.cl   # solo los de ese correo

Se ejecuta DENTRO del contenedor de notificaciones, con su token de Vault y su usuario de MongoDB:
no usa ninguna clave extra y solo puede leer la base de notificaciones.
"""
import sys

from comun import conectar_mongo, leer_secretos

leer_secretos("notificaciones")
filtro = {"para": sys.argv[1].strip().lower()} if len(sys.argv) > 1 else {}
correos = list(conectar_mongo("notificaciones").correos.find(filtro).sort("enviado_en", -1).limit(5))
if not correos:
    print("No hay correos" + (f" para {sys.argv[1]}" if filtro else ""))
for c in correos:
    print(f"--- {c['enviado_en']}  para: {c['para']}\nAsunto: {c['asunto']}\n{c['cuerpo']}\n")
