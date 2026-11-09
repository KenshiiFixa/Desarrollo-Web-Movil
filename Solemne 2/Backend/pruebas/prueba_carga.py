"""Prueba de carga (Modulo 9). Mide latencia p50/p95, throughput, errores y CPU/memoria de cada servicio.

Escenarios (todos a traves del API Gateway, como un cliente real):
  1. catalogo   : GET /products sin sesion (la consulta de mayor demanda del caso).
  2. mis_pedidos: GET /orders con sesion (introspect contra Auth + consulta a orders).
  3. graphql    : POST /graphql misPedidos (agrega orders + inventory + payments).
  4. crear_pedido: POST /orders (usa gRPC orders -> inventory para reservar stock).

Uso, con el limite del gateway subido SOLO para esta prueba:
    LIMITE_POR_MINUTO=100000 python iniciar.py      (en otra terminal; despues se reinicia sin la variable)
    TEST_PASSWORD=<SEED_PASSWORD> python pruebas/prueba_carga.py
"""
import json
import os
import ssl
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = os.getenv("API_URL", "https://127.0.0.1:8000/api/v1")
CLAVE = os.environ["TEST_PASSWORD"]
USUARIOS_CONCURRENTES = int(os.getenv("CONCURRENCIA", "20"))
SEGUNDOS_POR_ESCENARIO = int(os.getenv("DURACION", "20"))
CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Se confia en la CA local (certs/ca.crt), igual que el resto de las pruebas
TLS = ssl.create_default_context(cafile=os.path.join(CARPETA, "certs", "ca.crt"))


def login(email):
    return httpx.post(f"{BASE}/auth/login", json={"email": email, "password": CLAVE}, verify=TLS).json()["access_token"]


ESTADO = os.path.join(CARPETA, "datos", "en_ejecucion.json")   # iniciar.py guarda aqui el PID de cada proceso


def medir_recursos(detener, muestras):
    """Mide CPU y memoria de cada proceso (Vault y los 10 servicios) y del contenedor de MongoDB cada ~2 s."""
    import psutil
    pids = json.load(open(ESTADO))["pids"]
    procesos = {nombre: psutil.Process(pid) for nombre, pid in pids.items()}
    for p in procesos.values():
        p.cpu_percent(None)   # la primera lectura solo inicia la medicion
    while not detener.wait(2):
        for nombre, p in procesos.items():
            try:
                muestras.setdefault(nombre, []).append(
                    (p.cpu_percent(None), f"{p.memory_info().rss / 1024 / 1024:.1f}MiB"))
            except psutil.Error:
                pass
        # MongoDB corre en Docker: se mide su contenedor con 'docker stats'
        r = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}};{{.MemUsage}}",
                            "aroma-cafe-mongo-1"], capture_output=True, text=True)
        if r.returncode == 0 and ";" in r.stdout:
            cpu, memoria = r.stdout.strip().split(";")
            muestras.setdefault("mongo", []).append((float(cpu.rstrip("%")), memoria.split("/")[0].strip()))


def escenario(nombre, hacer_solicitud):
    latencias, errores, codigos = [], 0, {}
    fin = time.time() + SEGUNDOS_POR_ESCENARIO
    candado = threading.Lock()

    def usuario_virtual():
        nonlocal errores
        with httpx.Client(timeout=10, verify=TLS) as cliente:
            while time.time() < fin:
                inicio = time.perf_counter()
                try:
                    codigo = hacer_solicitud(cliente).status_code
                except httpx.HTTPError:
                    codigo = 0
                duracion = (time.perf_counter() - inicio) * 1000
                with candado:
                    latencias.append(duracion)
                    codigos[codigo] = codigos.get(codigo, 0) + 1
                    if codigo == 0 or codigo >= 400:
                        errores += 1

    detener, muestras = threading.Event(), {}
    monitor = threading.Thread(target=medir_recursos, args=(detener, muestras))
    monitor.start()
    t0 = time.time()
    with ThreadPoolExecutor(USUARIOS_CONCURRENTES) as pool:
        for _ in range(USUARIOS_CONCURRENTES):
            pool.submit(usuario_virtual)
    total = time.time() - t0
    detener.set()
    monitor.join()
    latencias.sort()
    resultado = {
        "escenario": nombre, "concurrencia": USUARIOS_CONCURRENTES, "duracion_s": round(total, 1),
        "solicitudes": len(latencias), "throughput_rps": round(len(latencias) / total, 1),
        "p50_ms": round(statistics.median(latencias), 1),
        "p95_ms": round(latencias[int(len(latencias) * 0.95) - 1], 1),
        "max_ms": round(latencias[-1], 1), "errores": errores,
        "tasa_error_pct": round(100 * errores / len(latencias), 2), "codigos": codigos,
        "cpu_max_pct": {s: max(c for c, _ in v) for s, v in muestras.items()},
        "memoria_ultima": {s: v[-1][1] for s, v in muestras.items()},
    }
    print(json.dumps(resultado, ensure_ascii=False))
    return resultado


def main():
    token_cliente, token_admin = login("ana@aromaycafe.test"), login("admin@aromaycafe.test")
    cab_cliente = {"Authorization": f"Bearer {token_cliente}"}
    # Producto exclusivo para la prueba, con stock alto (no agota la carta de prueba)
    httpx.post(f"{BASE}/admin/products", headers={"Authorization": f"Bearer {token_admin}"}, verify=TLS,
               json={"id": "carga-test", "nombre": "Producto carga", "descripcion": "Solo prueba de carga",
                     "categoria": "cafe", "precio": 1000, "stock": 100000})
    consulta = {"query": "{ misPedidos(limite: 5) { id estado lineas { producto { nombre } } pago { estado } } }"}
    pedido = {"items": [{"product_id": "carga-test", "cantidad": 1}], "tipo_entrega": "retiro"}
    resultados = [
        escenario("catalogo", lambda c: c.get(f"{BASE}/products")),
        escenario("mis_pedidos", lambda c: c.get(f"{BASE}/orders", headers=cab_cliente)),
        escenario("graphql", lambda c: c.post(f"{BASE}/graphql", headers=cab_cliente, json=consulta)),
        escenario("crear_pedido", lambda c: c.post(f"{BASE}/orders", headers=cab_cliente, json=pedido)),
    ]
    entorno = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "cpus": os.cpu_count(), "python": sys.version.split()[0],
               "tipo": "MEDICION en un solo equipo, con TLS en todos los tramos HTTP y gRPC; no es una proyeccion de produccion"}
    salida = os.path.join(CARPETA, "docs", "evidencias", "carga-resultado.json")
    json.dump({"entorno": entorno, "resultados": resultados}, open(salida, "w"), indent=2, ensure_ascii=False)
    print(f"Resultados guardados en {salida}")


if __name__ == "__main__":
    main()
