"""Pruebas de fallos, desconexiones y concurrencia (Modulos 3, 9 y 10):
  1. inventory detenido: error controlado, GraphQL parcial y recuperacion.
  2. auth detenido: las rutas protegidas fallan cerradas, el catalogo sigue y la sesion sobrevive.
  3. compras simultaneas: con stock 2, de 10 compras al mismo tiempo solo se crean 2 pedidos.

Uso, con el backend corriendo (python iniciar.py en otra terminal):
    TEST_PASSWORD=<SEED_PASSWORD del .env> python pruebas/prueba_fallos.py
El resultado queda en docs/evidencias/prueba_fallos.txt.
"""
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from base import Q, api, crear_pedido, detener_servicio, ejecutar, gql, iniciar_servicio, stock


def esperar_que_vuelva(ruta, token=None):
    for _ in range(45):
        estado = api("GET", ruta, token).status_code
        if estado == 200:
            return estado
        time.sleep(2)
    return estado


def inventory_caido_error_controlado_y_recuperacion(ana):
    """Con inventory apagado: el catalogo responde un error controlado (sin datos falsos) y GraphQL
    entrega lo de orders con un aviso de respuesta incompleta. Al restaurarlo, todo vuelve a funcionar."""
    order_id = crear_pedido(ana).json()["id"]
    detener_servicio("inventory")
    try:
        r = api("GET", "/products")
        assert r.status_code == 502 and r.json() == {"detail": "Backend no disponible"}
        datos = gql(ana, Q, {"id": order_id}).json()
        assert datos["data"]["resumenPedido"]["estado"] == "PENDIENTE_PAGO"        # orders si respondio
        assert datos["data"]["resumenPedido"]["lineas"][0]["producto"] is None     # inventory no
        assert any("incompleta" in e["message"] for e in datos["errors"])          # y se avisa
    finally:
        iniciar_servicio("inventory")
    assert esperar_que_vuelva("/products") == 200


def auth_caido_falla_cerrado_y_recuperacion(ana):
    """Con auth apagado las rutas protegidas se rechazan (falla cerrado), el catalogo publico sigue y,
    al volver auth, la misma sesion sigue valida porque vive en MongoDB."""
    assert api("GET", "/orders", ana).status_code == 200
    detener_servicio("auth")
    try:
        r = api("GET", "/orders", ana)
        assert r.status_code == 503 and "no disponible" in r.json()["detail"]
        assert api("GET", "/products").status_code == 200
    finally:
        iniciar_servicio("auth")
    assert esperar_que_vuelva("/orders", ana) == 200


def compras_simultaneas_con_poco_stock(ana, admin):
    """10 compras al mismo tiempo sobre un producto con stock 2: se crean exactamente 2 pedidos y el
    stock queda en 0 (la reserva es atomica: $inc con la condicion stock >= cantidad)."""
    product_id = "simultaneo-" + uuid.uuid4().hex[:6]
    nuevo = {"id": product_id, "nombre": "Producto concurrencia", "descripcion": "Solo prueba", "categoria": "cafe",
             "precio": 1000, "stock": 2}
    assert api("POST", "/admin/products", admin, json=nuevo).status_code == 201
    try:
        with ThreadPoolExecutor(10) as pool:
            codigos = list(pool.map(lambda _: crear_pedido(ana, [{"product_id": product_id, "cantidad": 1}]).status_code,
                                    range(10)))
        assert codigos.count(201) == 2 and codigos.count(409) == 8, codigos
        assert stock(admin, product_id) == 0
    finally:
        api("DELETE", f"/admin/products/{product_id}", admin)


if __name__ == "__main__":
    ejecutar("Prueba de fallos, desconexiones y concurrencia", [
        inventory_caido_error_controlado_y_recuperacion,
        auth_caido_falla_cerrado_y_recuperacion,
        compras_simultaneas_con_poco_stock,
    ], "prueba_fallos.txt")
