"""Inspeccion de persistencia para las pruebas: lee documentos de la base de ESTE servicio, con su propio
usuario de MongoDB, y oculta los campos sensibles (hashes de claves, codigos y tokens).

Uso con Docker (desde la carpeta Backend):
    docker compose exec orders python inspeccionar.py pedidos '{"_id": "ORD-1234ABCD"}'
    docker compose exec inventory python inspeccionar.py productos '{"_id": "latte-art"}' nombre,stock
"""
import json
import os
import sys

from comun import conectar_mongo, leer_secretos

# Carpeta del servicio (variable SERVICIO del contenedor) -> nombre de su secreto y de su base
NOMBRES = {"auth_service": "auth", "graphql_gateway": "graphql", "proveedor_pagos": "proveedor"}
SENSIBLES = ("clave", "codigo", "token", "secreto", "hash", "cuerpo")

servicio = NOMBRES.get(os.getenv("SERVICIO", ""), os.getenv("SERVICIO", ""))
coleccion = sys.argv[1]
filtro = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
campos = sys.argv[3].split(",") if len(sys.argv) > 3 else None


def ocultar(doc):
    limpio = {}
    for clave, valor in doc.items():
        if clave == "_id" and coleccion == "sesiones":
            valor = "*** (hash del token)"
        elif any(s in clave.lower() for s in SENSIBLES):
            valor = "***"
        limpio[clave] = valor
    return limpio


leer_secretos(servicio)
proyeccion = {c: 1 for c in campos} if campos else None
datos = conectar_mongo(servicio)[coleccion]
docs = list(datos.find(filtro, proyeccion).limit(20))
print(json.dumps({"servicio": servicio, "coleccion": coleccion, "filtro": filtro, "total": datos.count_documents(filtro),
                  "resultado": [ocultar(d) for d in docs]}, ensure_ascii=False, default=str, indent=1))
