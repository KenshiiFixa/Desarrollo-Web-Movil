"""Pruebas de seguridad: los casos de validacion del Modulo 7, permisos, GraphQL, TLS y aislamiento de
secretos y bases de datos.

Uso, con el backend corriendo (python iniciar.py en otra terminal):
    TEST_PASSWORD=<SEED_PASSWORD del .env> python pruebas/prueba_seguridad.py
El resultado queda en docs/evidencias/prueba_seguridad.txt.
"""
import socket

import httpx

from base import (BASE, Q, anular, api, crear_pedido, ejecutar, en_servicio, gql, ip_de_red)


def m7_1_catalogo_anonimo():
    """CASO M7-1: un visitante sin sesion ve el catalogo, solo con campos publicos (sin stock)."""
    r = api("GET", "/products")
    assert r.status_code == 200 and len(r.json()) >= 8
    assert "stock" not in r.json()[0] and "activo" not in r.json()[0]


def m7_2_operacion_protegida_sin_sesion():
    """CASO M7-2: crear pedido sin token o con token falso -> 401."""
    assert crear_pedido(None).status_code == 401
    assert api("GET", "/orders", "token-inventado-1234567890").status_code == 401


def m7_3_administracion_desde_rol_sin_permiso(ana, despacho, cajero):
    """CASO M7-3: un cliente (y otros funcionarios) no pueden administrar productos ni usuarios -> 403."""
    nuevo = {"id": "hack", "nombre": "Hack", "descripcion": "x", "categoria": "cafe", "precio": 1, "stock": 1}
    assert api("POST", "/admin/products", ana, json=nuevo).status_code == 403
    assert api("DELETE", "/admin/products/latte-art", ana).status_code == 403
    assert api("GET", "/admin/products", despacho).status_code == 403
    assert api("GET", "/admin/reports/sales", ana).status_code == 403
    assert api("GET", "/admin/reports/sales", cajero).status_code == 403
    assert api("GET", "/admin/users", despacho).status_code == 403
    assert api("PUT", "/admin/users/USR-004/role", ana, json={"rol": "admin"}).status_code == 403


def m7_4_pedido_ajeno(ana, pedro):
    """CASO M7-4: Pedro no puede ver, anular ni pagar el pedido de Ana (404, no revela que existe)."""
    order_id = crear_pedido(ana).json()["id"]
    assert api("GET", f"/orders/{order_id}", ana).status_code == 200
    assert api("GET", f"/orders/{order_id}", pedro).status_code == 404
    assert anular(pedro, order_id).status_code == 404
    assert api("POST", "/payments", pedro, json={"order_id": order_id}).status_code == 404
    assert order_id not in [p["id"] for p in api("GET", "/orders", pedro).json()]


def m7_5_acceso_directo_a_servicio_interno():
    """CASO M7-5: los servicios internos no se publican y rechazan llamadas sin su secreto."""
    # (a) los servicios escuchan solo en 127.0.0.1: desde otro equipo de la red no se alcanzan
    ip = ip_de_red()
    if not ip.startswith("127."):
        try:   # conexion directa (sin proxy) a la IP de red del equipo
            socket.create_connection((ip, 8002), timeout=3).close()
            raise AssertionError("inventory acepto una conexion desde la red")
        except OSError:
            pass
    # (b) llamando directo al servicio, sin secreto de servicio -> 403
    codigo = ("from comun import URLS, CLIENTE_HTTP\n"
              "print(CLIENTE_HTTP.get(URLS['inventory'] + '/admin/products').status_code)")
    assert en_servicio("gateway", codigo) == "403"
    # (c) con cabeceras de identidad falsas pero sin secreto -> 403
    codigo = ("from comun import URLS, CLIENTE_HTTP\n"
              "print(CLIENTE_HTTP.get(URLS['orders'] + '/orders', headers={'X-Servicio': 'gateway',"
              " 'X-Servicio-Secreto': 'adivinado', 'X-Authenticated-User': 'USR-001', 'X-Authenticated-Roles': 'admin'}).status_code)")
    assert en_servicio("gateway", codigo) == "403"


def m7_5_grpc_sin_credencial():
    """CASO M7-5 (gRPC): llamar a inventory por gRPC (con TLS) sin el secreto de orders -> PERMISSION_DENIED."""
    codigo = ("import grpc\nfrom comun import canal_inventory\nfrom proto import inventario_pb2 as pb, inventario_pb2_grpc as g\n"
              "stub = g.InventarioStub(canal_inventory())\n"
              "try:\n    stub.ReservarStock(pb.ReservaRequest(order_id='ORD-X', items=[pb.Item(product_id='latte-art', cantidad=1)]),"
              " timeout=3, metadata=[('x-servicio','orders'),('x-servicio-secreto','falso')]); print('abierto')\n"
              "except grpc.RpcError as e: print(e.code().name)")
    assert en_servicio("gateway", codigo).endswith("PERMISSION_DENIED")


def m7_6_pago_alterado_desde_el_frontend(ana):
    """CASO M7-6: el navegador intenta marcar el pedido como pagado o falsificar el aviso del proveedor."""
    order_id = crear_pedido(ana).json()["id"]
    assert api("PUT", f"/admin/orders/{order_id}/status", ana, json={"estado": "EN_PREPARACION"}).status_code == 403
    assert api("PUT", f"/orders/{order_id}", ana, json={"estado": "PAGADO"}).status_code == 404   # ruta inexistente
    falso = b'{"event_id":"evt_x","payment_id":"PAY-X","checkout_id":"c","resultado":"aprobado","monto":1,"creado_en":1}'
    r = api("POST", "/payments/webhook", content=falso, headers={"X-Firma": "00" * 32})
    assert r.status_code == 401                                       # firma HMAC invalida
    assert api("GET", f"/orders/{order_id}", ana).json()["estado"] == "PENDIENTE_PAGO"


def precio_lo_decide_el_servidor(ana):
    """El precio y el total los calcula el servidor; un "precio" enviado se ignora."""
    r = crear_pedido(ana, [{"product_id": "espresso-doble", "cantidad": 2, "precio": 1}])
    assert r.status_code == 201 and r.json()["total"] == 5000   # 2 x $2.500, se ignora el "precio" enviado


def monto_del_pago_lo_decide_el_servidor(ana):
    """El monto del pago sale del pedido; un "monto" enviado se ignora."""
    order_id = crear_pedido(ana).json()["id"]
    r = api("POST", "/payments", ana, json={"order_id": order_id, "monto": 1})
    assert r.status_code == 201 and r.json()["monto"] == 2500


def rutas_no_listadas(ana):
    """Las rutas que no estan en la tabla del gateway (incluidas las /internal) responden 404."""
    assert api("GET", "/internal/products", ana).status_code == 404
    assert api("DELETE", "/orders/ORD-1", ana).status_code == 404


def login_incorrecto():
    """Login con clave incorrecta responde 401."""
    assert api("POST", "/auth/login", json={"email": "ana@aromaycafe.test", "password": "otra-clave"}).status_code == 401


def cabeceras_de_identidad_del_navegador_se_ignoran(ana):
    """Si el navegador manda X-Authenticated-Roles: admin, el gateway la descarta."""
    r = api("GET", "/admin/products", ana, headers={"X-Authenticated-Roles": "admin",
                                                    "X-Authenticated-User": "USR-001"})
    assert r.status_code == 403


def despacho_ve_datos_minimos_del_cliente(despacho, admin):
    """Despacho ve solo los datos de entrega del cliente; el admin ve la ficha completa."""
    datos = api("GET", "/admin/clients/USR-003", despacho).json()
    assert set(datos) == {"nombre", "email", "telefono", "direccion", "comuna"}   # sin RUN ni fecha de nacimiento
    assert "fecha_nacimiento" in api("GET", "/admin/clients/USR-003", admin).json()


def graphql_pedido_ajeno(ana, pedro):
    """GraphQL: un cliente no puede ver el pedido de otro."""
    order_id = crear_pedido(ana).json()["id"]
    assert gql(pedro, Q, {"id": order_id}).json()["data"]["resumenPedido"] is None


def graphql_campo_restringido(ana, despacho):
    """GraphQL: el campo cliente solo lo ven despacho y admin, y user_id no existe en el schema (es privado)."""
    order_id = crear_pedido(ana).json()["id"]
    consulta = "query($id: String!) { resumenPedido(id: $id) { id cliente { email } } }"
    datos = gql(ana, consulta, {"id": order_id}).json()
    assert datos["errors"] and datos["data"]["resumenPedido"]["cliente"] is None
    assert gql(despacho, consulta, {"id": order_id}).json()["data"]["resumenPedido"]["cliente"]["email"] == "ana@aromaycafe.test"
    assert gql(despacho, "{ misPedidos { userId } }").json()["errors"]                  # el campo no existe


def graphql_sin_sesion_y_limites(ana):
    """GraphQL: exige sesion y aplica los limites de alias y de tamano."""
    assert gql(None, "{ misPedidos { id } }").status_code == 401
    alias = " ".join(f"a{i}: misPedidos {{ id }}" for i in range(6))
    assert gql(ana, "{ " + alias + " }").json().get("errors")                     # limite de alias
    assert api("POST", "/graphql", ana, json={"query": "{ misPedidos { id } }" + " " * 3000}).status_code == 422


def vault_cada_servicio_solo_lee_su_secreto():
    """Con el token de Vault del gateway se lee secret/gateway, pero NO secret/payments."""
    codigo = ("from comun import VAULT_ADDR, VAULT_TOKEN_FILE, CLIENTE_HTTP\ntoken = open(VAULT_TOKEN_FILE).read().strip()\n"
              "propio = CLIENTE_HTTP.get(VAULT_ADDR + '/v1/secret/data/gateway', headers={'X-Vault-Token': token})\n"
              "ajeno = CLIENTE_HTTP.get(VAULT_ADDR + '/v1/secret/data/payments', headers={'X-Vault-Token': token})\n"
              "print(propio.status_code, ajeno.status_code)")
    assert en_servicio("gateway", codigo) == "200 403"


def mongo_cada_servicio_solo_accede_a_su_base():
    """El usuario de MongoDB de orders puede leer la base orders, pero NO la base payments."""
    codigo = ("from comun import leer_secretos, conectar_mongo\nleer_secretos('orders')\n"
              "db = conectar_mongo('orders')\ndb.pedidos.find_one()\n"
              "try:\n    db.client['payments'].pagos.find_one(); print('abierto')\n"
              "except Exception as e: print(type(e).__name__)")
    assert en_servicio("orders", codigo) == "OperationFailure"

def graphql_sin_introspeccion(ana):
    """GraphQL: la introspeccion esta desactivada (no se puede pedir el schema completo)."""
    r = gql(ana, "{ __schema { types { name } } }").json()
    assert r.get("errors") and not r.get("data")


def tls_http_sin_cifrar_rechazado():
    """TLS: el gateway no atiende HTTP sin cifrar."""
    try:
        r = httpx.get(BASE.replace("https://", "http://") + "/products", timeout=5)
        raise AssertionError(f"respondio {r.status_code} por HTTP")
    except httpx.HTTPError:
        pass


def tls_certificado_no_confiable_rechazado():
    """TLS: un cliente que no confia en la CA local no puede conectarse (no se acepta cualquier certificado)."""
    try:
        httpx.get(BASE + "/products", timeout=5)          # usa solo las CA publicas del sistema
        raise AssertionError("se conecto sin confiar en la CA local")
    except httpx.ConnectError:
        pass


def tls_grpc_sin_cifrar_rechazado():
    """TLS: inventory no acepta llamadas gRPC sin cifrar."""
    codigo = ("import grpc\nfrom comun import GRPC_INVENTORY\nfrom proto import inventario_pb2 as pb, inventario_pb2_grpc as g\n"
              "stub = g.InventarioStub(grpc.insecure_channel(GRPC_INVENTORY))\n"
              "try:\n    stub.LiberarStock(pb.LiberarRequest(order_id='ORD-X'), timeout=3); print('abierto')\n"
              "except grpc.RpcError as e: print(e.code().name)")
    assert en_servicio("gateway", codigo).endswith("UNAVAILABLE")



if __name__ == "__main__":
    ejecutar("Prueba de seguridad y aislamiento", [
        m7_1_catalogo_anonimo,
        m7_2_operacion_protegida_sin_sesion,
        m7_3_administracion_desde_rol_sin_permiso,
        m7_4_pedido_ajeno,
        m7_5_acceso_directo_a_servicio_interno,
        m7_5_grpc_sin_credencial,
        m7_6_pago_alterado_desde_el_frontend,
        precio_lo_decide_el_servidor,
        monto_del_pago_lo_decide_el_servidor,
        rutas_no_listadas,
        login_incorrecto,
        cabeceras_de_identidad_del_navegador_se_ignoran,
        despacho_ve_datos_minimos_del_cliente,
        graphql_pedido_ajeno,
        graphql_campo_restringido,
        graphql_sin_sesion_y_limites,
        vault_cada_servicio_solo_lee_su_secreto,
        mongo_cada_servicio_solo_accede_a_su_base,
        graphql_sin_introspeccion,
        tls_http_sin_cifrar_rechazado,
        tls_certificado_no_confiable_rechazado,
        tls_grpc_sin_cifrar_rechazado,
    ], "prueba_seguridad.txt")
