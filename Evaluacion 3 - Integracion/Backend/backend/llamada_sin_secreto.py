"""Demostracion: un contenedor que NO es el gateway intenta llamar directo a inventory.

Uso con Docker (desde la carpeta Backend):
    docker compose exec clients python llamada_sin_secreto.py

Hace dos intentos desde dentro de la red privada de Docker:
  1. sin ningun secreto;
  2. diciendo que es el gateway, pero con un secreto inventado.
En los dos casos inventory compara con el secreto que tiene en Vault y responde 403.
En el log de inventory queda cada intento como "llamada RECHAZADA (403)".
"""
import ssl
import urllib.error
import urllib.request

URL = "https://inventory:8000/products"
CONTEXTO = ssl.create_default_context(cafile="/certs/ca.crt")
INTENTOS = [
    ("Sin secreto", {}),
    ("Haciendose pasar por el gateway con un secreto falso",
     {"X-Servicio": "gateway", "X-Servicio-Secreto": "secreto-inventado-123"}),
]

for descripcion, cabeceras in INTENTOS:
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers=cabeceras), context=CONTEXTO, timeout=5) as r:
            print(f"{descripcion}: inventory respondio {r.status} (no deberia pasar)")
    except urllib.error.HTTPError as error:
        print(f"{descripcion}: inventory respondio {error.code} {error.reason}")
