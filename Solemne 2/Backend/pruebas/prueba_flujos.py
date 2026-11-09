"""Pruebas de los flujos del Caso 19 (RF1 a RF13): pedidos, pagos, boleta, despacho, registro, reportes, caja y
mantenedores.

Uso, con el backend corriendo (python iniciar.py en otra terminal):
    TEST_PASSWORD=<SEED_PASSWORD del .env> python pruebas/prueba_flujos.py
El resultado queda en docs/evidencias/prueba_flujos.txt.
"""
import os
import time
import uuid

from base import (CARPETA, Q, anular, api, crear_pedido, ejecutar, gql, leer_codigo_del_correo, login, pagar, stock)


def despacho_gratis_solo_dentro_del_radio(ana):
    """Caso 19: el despacho es gratuito y solo dentro de 3 km del local (comunas configuradas)."""
    r = crear_pedido(ana, tipo="delivery")
    assert r.status_code == 201 and r.json()["total"] == 2500   # sin costo de despacho
    item = [{"product_id": "croissant", "cantidad": 1}]
    fuera = api("POST", "/orders", ana, json={"items": item, "tipo_entrega": "delivery",
                                              "direccion": "Av. Apoquindo 3000", "comuna": "Las Condes"})
    assert fuera.status_code == 422 and "radio" in fuera.json()["detail"]
    sin_direccion = api("POST", "/orders", ana, json={"items": item, "tipo_entrega": "delivery"})
    assert sin_direccion.status_code == 422


def pago_completo_boleta_y_aviso_repetido(ana, admin):
    """RF2 y RF8: pago aprobado, boleta con caja web y aviso repetido sin duplicar."""
    order_id = crear_pedido(ana, [{"product_id": "cappuccino", "cantidad": 2}]).json()["id"]
    assert api("GET", f"/orders/{order_id}/receipt", ana).status_code == 409   # sin pago no hay boleta
    payment_id, resultado = pagar(ana, order_id, repetir=2)
    respuestas = [a["respuesta"] for a in resultado["avisos"]]
    assert respuestas[0]["estado"] == "APROBADO" and respuestas[1].get("repetido")   # el 2.o aviso no se procesa
    assert api("GET", f"/orders/{order_id}", ana).json()["estado"] == "PAGADO"
    assert api("GET", f"/payments/{payment_id}", ana).json()["estado"] == "APROBADO"
    boleta = api("GET", f"/orders/{order_id}/receipt", ana).json()
    assert boleta["folio"].startswith("B-") and boleta["neto"] + boleta["iva"] == boleta["total"] == 6000
    assert boleta["caja"] == "CAJA-WEB-01"                                     # RF4: venta asociada a la caja web
    # notificaciones envio la boleta (correo simulado, con el correo enmascarado para el admin)
    correos = api("GET", "/admin/notifications", admin).json()
    assert any(c["id"] == order_id and c["para"] == "a***@aromaycafe.test" for c in correos)


def pago_rechazado(ana):
    """Pago rechazado: el pedido sigue pendiente y se puede volver a pagar."""
    order_id = crear_pedido(ana).json()["id"]
    pago = api("POST", "/payments", ana, json={"order_id": order_id}).json()
    api("POST", f"/payments/{pago['id']}/simular", ana, json={"resultado": "rechazado"})
    assert api("GET", f"/payments/{pago['id']}", ana).json()["estado"] == "RECHAZADO"
    assert api("GET", f"/orders/{order_id}", ana).json()["estado"] == "PENDIENTE_PAGO"


def ciclo_de_vida_por_despacho(ana, despacho):
    """RF2: despacho solo avanza pedidos pagados y por transiciones validas."""
    order_id = crear_pedido(ana).json()["id"]
    assert api("PUT", f"/admin/orders/{order_id}/status", despacho, json={"estado": "EN_PREPARACION"}).status_code == 409
    pagar(ana, order_id)
    assert api("PUT", f"/admin/orders/{order_id}/status", despacho, json={"estado": "LISTO"}).status_code == 409
    for estado in ("EN_PREPARACION", "LISTO", "ENTREGADO"):   # retiro en el local
        assert api("PUT", f"/admin/orders/{order_id}/status", despacho, json={"estado": estado}).status_code == 200
    assert anular(ana, order_id).status_code == 409   # ya entregado


def anular_devuelve_stock_y_no_borra(ana, admin):
    """RF3: anular con motivo devuelve el stock y no borra el pedido."""
    antes = stock(admin, "cold-brew")
    order_id = crear_pedido(ana, [{"product_id": "cold-brew", "cantidad": 2}]).json()["id"]
    assert stock(admin, "cold-brew") == antes - 2
    assert api("POST", f"/orders/{order_id}/cancel", ana, json={}).status_code == 422   # RF3: falta el motivo
    assert anular(ana, order_id).status_code == 200
    assert stock(admin, "cold-brew") == antes
    assert api("GET", f"/orders/{order_id}", ana).json()["estado"] == "ANULADO"   # sigue existiendo


def sin_stock_no_descuenta_nada(ana, admin):
    """RF7: si un producto no alcanza, no se descuenta nada (todo o nada)."""
    product_id = "prueba-" + uuid.uuid4().hex[:6]
    nuevo = {"id": product_id, "nombre": "Producto prueba", "descripcion": "x", "categoria": "cafe",
             "precio": 1000, "stock": 2}
    assert api("POST", "/admin/products", admin, json=nuevo).status_code == 201
    antes = stock(admin, "latte-art")
    items = [{"product_id": "latte-art", "cantidad": 1}, {"product_id": product_id, "cantidad": 3}]
    assert crear_pedido(ana, items).status_code == 409          # el 2.o producto no alcanza
    assert stock(admin, "latte-art") == antes                   # el 1.o se devolvio (todo o nada)
    assert crear_pedido(ana, [{"product_id": product_id, "cantidad": 2}]).status_code == 201
    assert api("DELETE", f"/admin/products/{product_id}", admin).status_code == 204   # baja logica
    assert product_id not in [p["id"] for p in api("GET", "/products").json()]


def registro_con_verificacion_de_correo_y_logout():
    """RF5 y RF11: registro con los datos del Caso 19; sin verificar el correo no se puede entrar."""
    email = f"cliente-{uuid.uuid4().hex[:6]}@correo.test"
    datos = {"email": email, "nombre": "Camila Rojas", "password": "ClaveSegura1", "run": "12.345.678-5",
             "telefono": "+56 9 5555 4444", "direccion": "Av. Pajaritos 500", "comuna": "Maipú",
             "provincia": "Santiago", "region": "Metropolitana", "fecha_nacimiento": "1998-05-10", "sexo": "femenino"}
    assert api("POST", "/auth/register", json={**datos, "run": "12.345.678-9"}).status_code == 422   # RUN invalido
    r = api("POST", "/auth/register", json=datos)
    assert r.status_code == 201, r.text
    entrar = api("POST", "/auth/login", json={"email": email, "password": "ClaveSegura1"})
    assert entrar.status_code == 403                                                     # correo sin verificar
    assert api("POST", "/auth/verify-email", json={"email": email, "codigo": "000000"}).status_code == 400
    codigo = leer_codigo_del_correo(email)
    assert api("POST", "/auth/verify-email", json={"email": email, "codigo": codigo}).status_code == 200
    token = login(email, "ClaveSegura1")
    perfil = api("GET", "/clients/me", token).json()
    assert perfil["email"] == email and perfil["run"] == "12345678-5" and perfil["region"] == "Metropolitana"
    assert "clave" not in str(perfil).lower()
    assert api("POST", "/auth/logout", token).status_code == 200
    assert api("GET", "/clients/me", token).status_code == 401   # token revocado


def contacto_publico_y_listado_admin(admin):
    """Formulario de contacto publico; solo el admin ve los mensajes."""
    msg = {"nombre": "Visitante", "email": "visita@correo.test", "motivo": "eventos", "mensaje": "Cotizar un evento"}
    assert api("POST", "/contact", json=msg).status_code == 201
    assert any(m["email"] == "visita@correo.test" for m in api("GET", "/admin/contact", admin).json())


def graphql_agrega_subsistemas(ana):
    """GraphQL resumenPedido junta pedidos, productos y pagos."""
    order_id = crear_pedido(ana, [{"product_id": "croissant", "cantidad": 2}]).json()["id"]
    pagar(ana, order_id)
    datos = gql(ana, Q, {"id": order_id}).json()
    assert "errors" not in datos, datos
    pedido = datos["data"]["resumenPedido"]
    assert pedido["estado"] == "PAGADO"                                           # orders
    assert pedido["lineas"][0]["producto"]["nombre"] == "Croissant de Mantequilla"  # inventory
    assert pedido["pago"]["estado"] == "APROBADO"                                 # payments


def graphql_sin_n_mas_1(ana):
    """GraphQL sin N+1: misPedidos con varios pedidos y productos hace UNA llamada a inventory y UNA a
    payments (se cuentan en los logs con el id de correlacion de la consulta)."""
    for producto in ("latte-art", "croissant", "cheesecake-maracuya"):
        crear_pedido(ana, [{"product_id": producto, "cantidad": 1}, {"product_id": "espresso-doble", "cantidad": 1}])
    r = gql(ana, "{ misPedidos(limite: 10) { id lineas { producto { nombre } } pago { estado } } }")
    assert r.status_code == 200 and len(r.json()["data"]["misPedidos"]) >= 3
    id_solicitud = r.headers["X-Request-ID"]
    time.sleep(0.5)

    def llamadas(servicio, ruta):
        with open(os.path.join(CARPETA, "logs", f"{servicio}.log"), encoding="utf-8") as f:
            return sum(1 for linea in f if f"req={id_solicitud} GET {ruta}" in linea)
    assert llamadas("inventory", "/internal/products") == 1
    assert llamadas("payments", "/payments/by-orders") == 1


def graphql_reporte_dueno(ana, dueno):
    """GraphQL: reporteVentas solo para dueno y admin."""
    time.sleep(1)
    assert gql(dueno, "{ reporteVentas { pedidos totalVendido } }").json()["data"]["reporteVentas"]["pedidos"] >= 1
    assert gql(ana, "{ reporteVentas { pedidos } }").json()["errors"]


def reporte_de_ventas_del_dueno(dueno):
    """RF9: el dueno ve las ventas de un periodo."""
    r = api("GET", "/admin/reports/sales", dueno, params={"desde": "2026-01-01", "hasta": "2030-12-31"}).json()
    assert r["pedidos"] >= 1 and r["mas_vendidos"]
    assert "user_id" not in str(r) and "direccion" not in str(r)   # analitica no tiene datos personales


def admin_registra_cliente_en_el_local(admin):
    """RF6: el administrador registra al cliente; igual queda pendiente la verificacion del correo."""
    email = f"local-{uuid.uuid4().hex[:6]}@correo.test"
    r = api("POST", "/admin/clients", admin, json={"email": email, "nombre": "Cliente Local", "password": "ClaveSegura1"})
    assert r.status_code == 201, r.text
    usuarios = api("GET", "/admin/users", admin).json()
    nuevo = next(u for u in usuarios if u["email"] == email)
    assert nuevo["rol"] == "cliente" and nuevo["correo_verificado"] is False
    assert "clave_hash" not in str(usuarios)
    # RF10: el admin corrige los datos del cliente
    editado = api("PUT", f"/admin/clients/{nuevo['user_id']}", admin, json={"nombre": "Cliente Local", "comuna": "Maipú"})
    assert editado.status_code == 200 and editado.json()["comuna"] == "Maipú"


def mantenedor_de_usuarios_y_perfiles(admin):
    """RF10 y RF12: el admin crea funcionarios y cambia su perfil; el cambio cierra sus sesiones."""
    email = f"funcionario-{uuid.uuid4().hex[:6]}@aromaycafe.test"
    r = api("POST", "/admin/users", admin, json={"email": email, "password": "ClaveSegura1", "rol": "despacho"})
    assert r.status_code == 201 and r.json()["rol"] == "despacho"
    user_id = r.json()["user_id"]
    assert api("PUT", f"/admin/users/{user_id}/role", admin, json={"rol": "cajero"}).json()["rol"] == "cajero"
    assert api("PUT", "/admin/users/USR-001/role", admin, json={"rol": "cliente"}).status_code == 409   # a si mismo no
    assert api("PUT", f"/admin/users/{user_id}/role", admin, json={"rol": "superusuario"}).status_code == 422


def ordenes_de_despacho_en_orden_de_llegada(ana, despacho):
    """RF13: el encargado de despacho obtiene las ordenes pagadas, de la mas antigua a la mas nueva."""
    primero = crear_pedido(ana, tipo="delivery").json()["id"]
    segundo = crear_pedido(ana).json()["id"]
    pagar(ana, primero)
    pagar(ana, segundo)
    ordenes = api("GET", "/admin/dispatch-orders", despacho).json()
    ids = [o["id"] for o in ordenes]
    assert ids.index(primero) < ids.index(segundo)
    assert [o["pagado_en"] for o in ordenes] == sorted(o["pagado_en"] for o in ordenes)
    assert next(o for o in ordenes if o["id"] == primero)["comuna"] == "Maipú"
    assert api("GET", "/admin/dispatch-orders", ana).status_code == 403


def ventas_de_la_caja_del_cajero_virtual(ana, cajero):
    """RF4: las ventas web quedan asociadas a la caja del cajero virtual."""
    order_id = crear_pedido(ana).json()["id"]
    pagar(ana, order_id)
    ventas = api("GET", "/admin/sales", cajero).json()
    venta = next(v for v in ventas if v["pedido"] == order_id)
    assert venta["caja"] == "CAJA-WEB-01" and venta["folio"].startswith("B-")
    assert api("GET", "/admin/sales", ana).status_code == 403


def ofertas(ana, dueno):
    """El catalogo muestra ofertas y se cobra el precio de oferta. El dueno administra productos (CU4)."""
    ofertas = api("GET", "/products", params={"ofertas": "true"}).json()
    frappe = next(p for p in ofertas if p["id"] == "frappe-mocha")
    assert frappe["precio_oferta"] == 3400 and frappe["precio"] == 3900
    assert crear_pedido(ana, [{"product_id": "frappe-mocha", "cantidad": 1}]).json()["total"] == 3400
    mala = {"nombre": "Cappuccino", "descripcion": "x", "categoria": "cafe", "precio": 3000, "stock": 40,
            "precio_oferta": 3500}
    assert api("PUT", "/admin/products/cappuccino", dueno, json=mala).status_code == 422   # oferta mayor al precio


if __name__ == "__main__":
    ejecutar("Prueba de flujos del caso", [
        despacho_gratis_solo_dentro_del_radio,
        pago_completo_boleta_y_aviso_repetido,
        pago_rechazado,
        ciclo_de_vida_por_despacho,
        anular_devuelve_stock_y_no_borra,
        sin_stock_no_descuenta_nada,
        registro_con_verificacion_de_correo_y_logout,
        contacto_publico_y_listado_admin,
        graphql_agrega_subsistemas,
        graphql_sin_n_mas_1,
        graphql_reporte_dueno,
        reporte_de_ventas_del_dueno,
        admin_registra_cliente_en_el_local,
        mantenedor_de_usuarios_y_perfiles,
        ordenes_de_despacho_en_orden_de_llegada,
        ventas_de_la_caja_del_cajero_virtual,
        ofertas,
    ], "prueba_flujos.txt")
