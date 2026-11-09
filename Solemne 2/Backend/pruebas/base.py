"""Funciones que usan los scripts de prueba. No es una prueba: lo importan prueba_seguridad.py,
prueba_flujos.py y prueba_fallos.py.

Cada prueba es una funcion con assert. Si sus parametros se llaman ana, pedro, admin, despacho, cajero o
dueno, recibe el token de ese usuario. ejecutar() las corre en orden, imprime [OK] o [FALLA] y guarda
el resultado en docs/evidencias/.
"""
import inspect
import os
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime

import httpx

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(CARPETA, "datos")      # iniciar.py deja aqui los tokens de Vault y el archivo de control
CA = os.path.join(CARPETA, "certs", "ca.crt")
BASE = os.getenv("API_URL", "https://127.0.0.1:8000/api/v1")
CLAVE = os.environ.get("TEST_PASSWORD", "")
CORREOS = {"ana": "ana@aromaycafe.test", "pedro": "pedro@aromaycafe.test", "admin": "admin@aromaycafe.test",
           "despacho": "despacho@aromaycafe.test", "cajero": "cajero@aromaycafe.test",
           "dueno": "dueno@aromaycafe.test"}
_tokens = {}
_cliente = None


def cliente():
    """Cliente HTTPS que confia en la CA local (certs/ca.crt), como lo haria Postman o el navegador."""
    global _cliente
    if _cliente is None:
        import ssl
        _cliente = httpx.Client(verify=ssl.create_default_context(cafile=CA), timeout=30)
    return _cliente


def api(metodo, ruta, token=None, **kwargs):
    cabeceras = kwargs.pop("headers", {})
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    for _ in range(3):
        r = cliente().request(metodo, BASE + ruta, headers=cabeceras, **kwargs)
        if r.status_code != 429:
            return r
        # El gateway limita a 120 solicitudes por minuto por IP (10 en login y registro) y tambien cuenta
        # las rechazadas. Si las pruebas van muy rapido, se espera a que pase el minuto, sin subir el limite.
        time.sleep(61)
    return r


def login(email, clave=None):
    r = api("POST", "/auth/login", json={"email": email, "password": clave or CLAVE})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def token(nombre):
    if nombre not in _tokens:
        _tokens[nombre] = login(CORREOS[nombre])
    return _tokens[nombre]


def crear_pedido(token, items=None, tipo="retiro"):
    cuerpo = {"items": items or [{"product_id": "espresso-doble", "cantidad": 1}], "tipo_entrega": tipo}
    if tipo == "delivery":
        cuerpo["direccion"] = "Av. Pajaritos 1234"
        cuerpo["comuna"] = "Maipú"
    return api("POST", "/orders", token, json=cuerpo)


def pagar(token, order_id, repetir=1):
    pago = api("POST", "/payments", token, json={"order_id": order_id})
    assert pago.status_code == 201, pago.text
    r = api("POST", f"/payments/{pago.json()['id']}/simular", token, json={"repetir_aviso": repetir})
    assert r.status_code == 202, r.text
    return pago.json()["id"], r.json()


def anular(token, order_id, motivo="Me equivoque de producto"):
    return api("POST", f"/orders/{order_id}/cancel", token, json={"motivo": motivo})


def stock(admin, product_id):
    return next(p["stock"] for p in api("GET", "/admin/products", admin).json() if p["id"] == product_id)


Q = "query($id: String!) { resumenPedido(id: $id) { id estado total lineas { cantidad producto { nombre } } pago { estado } } }"


def gql(token, consulta, variables=None):
    return api("POST", "/graphql", token, json={"query": consulta, "variables": variables})


def en_servicio(servicio, codigo):
    """Ejecuta codigo Python con la identidad de un servicio (su token de Vault), como si fuera ese servicio."""
    env = dict(os.environ, VAULT_TOKEN_FILE=os.path.join(DATOS, "tokens", servicio))
    r = subprocess.run([sys.executable, "-c", codigo], cwd=os.path.join(CARPETA, "backend"), env=env,
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip() + r.stderr.strip()


def leer_codigo_del_correo(email):
    """Simula que el cliente abre su correo: lee el codigo en la bandeja simulada de notificaciones."""
    codigo = ("import re\nfrom comun import leer_secretos, conectar_mongo\nleer_secretos('notificaciones')\n"
              f"c = conectar_mongo('notificaciones').correos.find_one({{'para': '{email}', 'tipo': 'verificacion'}},"
              " sort=[('enviado_en', -1)])\nprint(re.search(r'es (\\d{6})', c['cuerpo']).group(1))")
    return en_servicio("notificaciones", codigo)


def detener_servicio(servicio):
    # iniciar.py deja detenido el servicio mientras exista este archivo
    open(os.path.join(DATOS, "control", f"detener-{servicio}"), "w").close()
    time.sleep(2)


def iniciar_servicio(servicio):
    os.remove(os.path.join(DATOS, "control", f"detener-{servicio}"))


def ip_de_red():
    """IP de este computador en la red (no 127.0.0.1). No envia nada, solo pregunta por que interfaz saldria."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]


def ejecutar(titulo, pruebas, archivo):
    """Corre las pruebas en orden, imprime el resultado de cada una y lo guarda en docs/evidencias/<archivo>."""
    if not CLAVE:
        sys.exit("Falta la variable TEST_PASSWORD (la SEED_PASSWORD del .env)")
    if not os.path.exists(os.path.join(DATOS, "en_ejecucion.json")):
        sys.exit("El backend no esta corriendo: primero ejecuta 'python iniciar.py' en otra terminal")
    lineas = [f"{titulo} ({datetime.now():%Y-%m-%d %H:%M})", ""]
    print(lineas[0] + "\n")
    ok = 0
    for prueba in pruebas:
        descripcion = " ".join((prueba.__doc__ or prueba.__name__).split())
        try:
            prueba(*[token(p) for p in inspect.signature(prueba).parameters])
            linea = f"  [OK]    {prueba.__name__}: {descripcion}"
            ok += 1
        except Exception as error:
            detalle = traceback.format_exception_only(type(error), error)[-1].strip()[:300]
            linea = f"  [FALLA] {prueba.__name__}: {descripcion}\n          {detalle}"
        print(linea)
        lineas.append(linea)
    resumen = f"Resultado: {ok} de {len(pruebas)} pruebas OK"
    print("\n" + resumen)
    lineas += ["", resumen]
    with open(os.path.join(CARPETA, "docs", "evidencias", archivo), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    sys.exit(0 if ok == len(pruebas) else 1)
