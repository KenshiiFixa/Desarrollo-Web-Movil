"""Demostracion: otro contenedor llama directo a inventory sin el secreto del gateway y despues con uno falso.
En los dos casos inventory responde 403 y lo registra como "llamada RECHAZADA".

Uso:
    docker compose exec clients python llamada_sin_secreto.py"""
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
