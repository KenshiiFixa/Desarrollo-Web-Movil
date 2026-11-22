"""Levanta TODO el backend en este computador.

Uso (desde la carpeta del proyecto):
    python iniciar.py            # inicia; Ctrl+C detiene todo
    python iniciar.py --limpiar  # borra la base de datos local y parte de cero

Pasos:
  1. Genera los certificados TLS en certs/ si no existen: una CA local y un certificado para 127.0.0.1.
  2. Inicia MongoDB en Docker (docker compose, solo en 127.0.0.1:27018) y Vault en modo desarrollo con TLS.
  3. Genera secretos ALEATORIOS, uno por cada par de servicios, y una clave de Mongo por servicio.
  4. Crea una politica y un token de Vault por servicio (cada uno solo lee su propio secreto).
  5. Crea un usuario de MongoDB por servicio, con permiso solo sobre su base.
  6. Inicia los 10 servicios con uvicorn y HTTPS, cada uno en su puerto de 127.0.0.1 (el gateway en el 8000).

Requisitos: Python con requirements.txt instalado, Docker Desktop abierto y el programa `vault` instalado.
Si vault no esta en el PATH, se puede indicar su ruta con la variable VAULT_BIN.
"""
import glob
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import time

import httpx
from pymongo import MongoClient

CARPETA = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(CARPETA, "backend")
DATOS = os.path.join(CARPETA, "datos")       # tokens de Vault y archivos de control (no se sube)
LOGS = os.path.join(CARPETA, "logs")         # un log por servicio (no se sube)
CERTS = os.path.join(CARPETA, "certs")       # CA local y certificado TLS (no se sube)

sys.path.insert(0, BACKEND)
from comun import PUERTOS   # noqa: E402  (los mismos puertos que usan los servicios)
import preparacion   # noqa: E402  (certificados, Vault y MongoDB: lo mismo que usa Docker)

VAULT = "https://127.0.0.1:8200"
MONGO_PUERTO = 27018        # puerto publicado por docker-compose.yml (no el 27017, por si ya hay un MongoDB instalado)
GRPC_PUERTO = 50051

# Carpeta de codigo de cada servicio
CARPETAS = {"gateway": "gateway", "auth": "auth_service", "inventory": "inventory", "orders": "orders",
            "clients": "clients", "payments": "payments", "graphql": "graphql_gateway",
            "analitica": "analitica", "notificaciones": "notificaciones", "proveedor": "proveedor_pagos"}


def leer_env():
    """Lee el archivo .env (no se sube al repositorio)."""
    ruta = os.path.join(CARPETA, ".env")
    if not os.path.exists(ruta):
        sys.exit("Falta el archivo .env: copia .env.example como .env y cambia los valores.")
    valores = {}
    for linea in open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip()
    for clave in ("VAULT_ROOT_TOKEN", "MONGO_ROOT_PASSWORD", "SEED_PASSWORD"):
        if not valores.get(clave):
            sys.exit(f"Falta {clave} en .env")
    if len(valores["SEED_PASSWORD"]) < 8:
        sys.exit("SEED_PASSWORD debe tener al menos 8 caracteres")
    return valores


def buscar_programa(nombre, variable, rutas_windows):
    ruta = os.getenv(variable) or shutil.which(nombre)
    if not ruta:
        encontrados = sorted(glob.glob(rutas_windows))
        ruta = encontrados[-1] if encontrados else None
    if not ruta:
        sys.exit(f"No se encontro '{nombre}'. Instalalo o indica su ruta en la variable {variable}.")
    return ruta


def generar_certificados():
    """CA local + certificado del servidor (la funcion esta en backend/preparacion.py, la misma que usa Docker)."""
    if preparacion.generar_certificados(CERTS):
        print("Certificados TLS generados en certs/ (CA local valida por 1 ano, servidor por 90 dias).")


def contexto_tls():
    contexto = ssl.create_default_context(cafile=os.path.join(CERTS, "ca.crt"))
    ca_vault = os.path.join(CERTS, "vault", "vault-ca.pem")
    if os.path.exists(ca_vault):
        contexto.load_verify_locations(ca_vault)
    return contexto


def docker_compose(*argumentos):
    return subprocess.run(["docker", "compose", *argumentos], cwd=CARPETA, capture_output=True, text=True)


def puerto_ocupado(puerto):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def esperar(descripcion, prueba, segundos=60):
    for _ in range(segundos * 2):
        try:
            if prueba():
                return
        except Exception:
            pass
        time.sleep(0.5)
    sys.exit(f"{descripcion} no respondio a tiempo. Revisa los logs en logs/")


def iniciar_proceso(nombre, comando, env=None, cwd=None):
    log = open(os.path.join(LOGS, f"{nombre}.log"), "a", encoding="utf-8")
    return subprocess.Popen(comando, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=cwd)


def preparar_vault(root, seed):
    """Secretos, politicas y un token por servicio (backend/preparacion.py). Cada vez que se inicia se crean
    secretos nuevos (Vault en modo desarrollo los guarda en memoria)."""
    return preparacion.preparar_vault(VAULT, root, seed, lambda servicio: os.path.join(DATOS, "tokens", servicio),
                                      contexto_tls())


def preparar_mongo(root_clave, claves):
    preparacion.preparar_mongo(f"mongodb://127.0.0.1:{MONGO_PUERTO}/", root_clave, claves)


def main():
    env_archivo = leer_env()
    vault_bin = buscar_programa("vault", "VAULT_BIN", r"C:\Program Files\HashiCorp\Vault\vault.exe")
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        sys.exit("Docker no esta corriendo: abre Docker Desktop y espera a que diga 'Engine running'.")
    if "--limpiar" in sys.argv:
        shutil.rmtree(DATOS, ignore_errors=True)
        docker_compose("down", "-v")
        print("Datos borrados (base de MongoDB en Docker y tokens).")

    ocupados = [p for p in [8200, GRPC_PUERTO, *PUERTOS.values()] if puerto_ocupado(p)]
    if ocupados:
        sys.exit(f"Estos puertos ya estan en uso: {ocupados}. Cierra el programa que los usa "
                 "(por ejemplo, otra ventana con iniciar.py) y vuelve a intentar.")

    for carpeta in (DATOS, LOGS, os.path.join(DATOS, "control")):
        os.makedirs(carpeta, exist_ok=True)
    generar_certificados()
    procesos = {}
    try:
        print("Iniciando MongoDB (Docker) y Vault...")
        r = docker_compose("up", "-d", "mongo")
        if r.returncode != 0:
            sys.exit("No se pudo iniciar MongoDB con docker compose:\n" + r.stderr[-500:])
        shutil.rmtree(os.path.join(CERTS, "vault"), ignore_errors=True)   # Vault crea una CA nueva en cada inicio
        os.makedirs(os.path.join(CERTS, "vault"))
        procesos["vault"] = iniciar_proceso("vault", [vault_bin, "server", "-dev", "-dev-tls",
                                                      f"-dev-tls-cert-dir={os.path.join(CERTS, 'vault')}",
                                                      f"-dev-root-token-id={env_archivo['VAULT_ROOT_TOKEN']}",
                                                      "-dev-listen-address=127.0.0.1:8200"])
        esperar("Vault", lambda: httpx.get(f"{VAULT}/v1/sys/health", verify=contexto_tls()).status_code == 200)
        esperar("MongoDB", lambda: MongoClient(f"mongodb://127.0.0.1:{MONGO_PUERTO}/",
                                               serverSelectionTimeoutMS=1000).admin.command("ping"))

        claves_mongo = preparar_vault(env_archivo["VAULT_ROOT_TOKEN"], env_archivo["SEED_PASSWORD"])
        preparar_mongo(env_archivo["MONGO_ROOT_PASSWORD"], claves_mongo)
        print("Vault y MongoDB listos: secretos, politicas, tokens y usuarios creados.")

        def env_de(servicio):
            env = dict(os.environ, PYTHONUNBUFFERED="1",
                       VAULT_TOKEN_FILE=os.path.join(DATOS, "tokens", servicio))
            env["LIMITE_POR_MINUTO"] = os.getenv("LIMITE_POR_MINUTO", env_archivo.get("LIMITE_POR_MINUTO", "120"))
            return env

        def iniciar_servicio(servicio):
            comando = [sys.executable, "-m", "uvicorn", f"{CARPETAS[servicio]}.main:app",
                       "--host", "127.0.0.1", "--port", str(PUERTOS[servicio]), "--no-access-log",
                       "--ssl-certfile", os.path.join(CERTS, "servidor.crt"),
                       "--ssl-keyfile", os.path.join(CERTS, "servidor.key")]
            return iniciar_proceso(servicio, comando, env=env_de(servicio), cwd=BACKEND)

        for servicio in PUERTOS:
            procesos[servicio] = iniciar_servicio(servicio)
        tls = contexto_tls()
        for servicio, puerto in PUERTOS.items():
            esperar(servicio, lambda p=puerto: httpx.get(f"https://127.0.0.1:{p}/health", verify=tls).status_code == 200)

        def guardar_estado():   # lo usan las pruebas (para saber que el backend corre) y la prueba de carga (PIDs)
            with open(os.path.join(DATOS, "en_ejecucion.json"), "w") as f:
                json.dump({"modo": "local", "puertos": PUERTOS,
                           "pids": {nombre: p.pid for nombre, p in procesos.items()}}, f)

        guardar_estado()
        print("\nBackend listo: https://127.0.0.1:8000/api/v1/products")
        print("(el navegador y Postman deben confiar en certs/ca.crt; ver el README)")
        print("Logs de cada servicio en logs/. Ctrl+C para detener todo.\n")

        # Vigila los servicios: si uno se cae, lo vuelve a levantar.
        # Si existe datos/control/detener-<servicio>, lo deja detenido (lo usa la prueba de caida).
        control = os.path.join(DATOS, "control")
        while True:
            for servicio in PUERTOS:
                detener = os.path.exists(os.path.join(control, f"detener-{servicio}"))
                vivo = procesos[servicio].poll() is None
                if detener and vivo:
                    procesos[servicio].terminate()
                    procesos[servicio].wait()
                    print(f"{servicio} detenido")
                elif not detener and not vivo:
                    procesos[servicio] = iniciar_servicio(servicio)
                    guardar_estado()
                    print(f"{servicio} iniciado de nuevo")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        try:
            os.remove(os.path.join(DATOS, "en_ejecucion.json"))
        except OSError:
            pass
        for proceso in reversed(list(procesos.values())):   # primero los servicios, al final Vault
            if proceso.poll() is None:
                proceso.terminate()
        for proceso in procesos.values():
            try:
                proceso.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proceso.kill()
        docker_compose("stop", "mongo")
        print("Todo detenido. Los datos de MongoDB quedan en el volumen de Docker (python iniciar.py --limpiar los borra).")


if __name__ == "__main__":
    main()
