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
import datetime
import glob
import ipaddress
import json
import os
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import time

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pymongo import MongoClient
from pymongo.errors import OperationFailure

CARPETA = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(CARPETA, "backend")
DATOS = os.path.join(CARPETA, "datos")       # tokens de Vault y archivos de control (no se sube)
LOGS = os.path.join(CARPETA, "logs")         # un log por servicio (no se sube)
CERTS = os.path.join(CARPETA, "certs")       # CA local y certificado TLS (no se sube)

sys.path.insert(0, BACKEND)
from comun import PUERTOS   # noqa: E402  (los mismos puertos que usan los servicios)

VAULT = "https://127.0.0.1:8200"
MONGO_PUERTO = 27018        # puerto publicado por docker-compose.yml (no el 27017, por si ya hay un MongoDB instalado)
GRPC_PUERTO = 50051

# Carpeta de codigo de cada servicio
CARPETAS = {"gateway": "gateway", "auth": "auth_service", "inventory": "inventory", "orders": "orders",
            "clients": "clients", "payments": "payments", "graphql": "graphql_gateway",
            "analitica": "analitica", "notificaciones": "notificaciones", "proveedor": "proveedor_pagos"}
CON_BASE = ["auth", "inventory", "orders", "clients", "payments", "notificaciones", "analitica"]


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
    """CA local + certificado del servidor para localhost y 127.0.0.1 (lo usan los 10 servicios y gRPC).
    Se generan solo si no existen o vencen en menos de 7 dias. Las claves privadas no se suben (.gitignore)."""
    os.makedirs(CERTS, exist_ok=True)
    ruta_crt = os.path.join(CERTS, "servidor.crt")
    if os.path.exists(ruta_crt):
        actual = x509.load_pem_x509_certificate(open(ruta_crt, "rb").read())
        if actual.not_valid_after_utc - datetime.datetime.now(datetime.timezone.utc) > datetime.timedelta(days=7):
            return
    ahora = datetime.datetime.now(datetime.timezone.utc)

    def certificado(sujeto, clave_publica, emisor, clave_firma, es_ca, dias):
        constructor = (x509.CertificateBuilder().subject_name(sujeto).issuer_name(emisor)
                       .public_key(clave_publica).serial_number(x509.random_serial_number())
                       .not_valid_before(ahora - datetime.timedelta(minutes=5))
                       .not_valid_after(ahora + datetime.timedelta(days=dias))
                       .add_extension(x509.BasicConstraints(ca=es_ca, path_length=None), critical=True)
                       .add_extension(x509.SubjectKeyIdentifier.from_public_key(clave_publica), critical=False)
                       .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(clave_firma.public_key()),
                                      critical=False))
        if es_ca:
            constructor = constructor.add_extension(x509.KeyUsage(
                digital_signature=True, key_cert_sign=True, crl_sign=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False, key_agreement=False, encipher_only=False,
                decipher_only=False), critical=True)
        else:
            constructor = (constructor
                           .add_extension(x509.SubjectAlternativeName(
                               [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
                               critical=False)
                           .add_extension(x509.KeyUsage(
                               digital_signature=True, key_encipherment=True, key_cert_sign=False, crl_sign=False,
                               content_commitment=False, data_encipherment=False, key_agreement=False,
                               encipher_only=False, decipher_only=False), critical=True)
                           .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
                                          critical=False))
        return constructor.sign(clave_firma, hashes.SHA256())

    clave_ca = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre_ca = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Aroma y Cafe - CA local")])
    ca = certificado(nombre_ca, clave_ca.public_key(), nombre_ca, clave_ca, True, 365)
    clave_srv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre_srv = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    srv = certificado(nombre_srv, clave_srv.public_key(), nombre_ca, clave_ca, False, 90)

    def guardar(nombre, datos):
        with open(os.path.join(CERTS, nombre), "wb") as f:
            f.write(datos)

    sin_cifrar = serialization.NoEncryption()
    guardar("ca.crt", ca.public_bytes(serialization.Encoding.PEM))
    guardar("servidor.crt", srv.public_bytes(serialization.Encoding.PEM))
    guardar("servidor.key", clave_srv.private_bytes(serialization.Encoding.PEM,
                                                    serialization.PrivateFormat.TraditionalOpenSSL, sin_cifrar))
    # La clave de la CA no se guarda: solo se necesitaba para firmar. Para renovar se genera todo de nuevo.
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


def rnd():
    return secrets.token_hex(32)


def preparar_vault(root, seed):
    """Genera los secretos y los guarda en Vault, usando su API HTTPS. Cada vez que se inicia se crean
    secretos nuevos (Vault en modo desarrollo los guarda en memoria)."""
    cab = {"X-Vault-Token": root}
    vault = httpx.Client(verify=contexto_tls(), timeout=10)
    par = {k: rnd() for k in ["GW_AUTH", "GW_INV", "GW_ORD", "GW_CLI", "GW_PAY", "GW_GQL", "GW_ANA", "GW_NOT",
                              "GQL_ORD", "GQL_INV", "GQL_CLI", "GQL_PAY", "GQL_ANA", "ORD_INV", "ORD_NOT",
                              "ORD_ANA", "PAY_ORD", "PAY_PRV", "AUTH_CLI", "AUTH_NOT", "NOT_CLI", "WEBHOOK"]}
    mongo = {s: rnd() for s in CON_BASE}
    secretos = {
        "gateway": {"hacia_auth": par["GW_AUTH"], "hacia_inventory": par["GW_INV"], "hacia_orders": par["GW_ORD"],
                    "hacia_clients": par["GW_CLI"], "hacia_payments": par["GW_PAY"], "hacia_graphql": par["GW_GQL"],
                    "hacia_analitica": par["GW_ANA"], "hacia_notificaciones": par["GW_NOT"]},
        "auth": {"mongo_clave": mongo["auth"], "desde_gateway": par["GW_AUTH"], "hacia_clients": par["AUTH_CLI"],
                 "hacia_notificaciones": par["AUTH_NOT"], "clave_usuarios_prueba": seed},
        "inventory": {"mongo_clave": mongo["inventory"], "desde_gateway": par["GW_INV"],
                      "desde_graphql": par["GQL_INV"], "desde_orders": par["ORD_INV"]},
        "orders": {"mongo_clave": mongo["orders"], "desde_gateway": par["GW_ORD"], "desde_graphql": par["GQL_ORD"],
                   "desde_payments": par["PAY_ORD"], "hacia_inventory": par["ORD_INV"],
                   "hacia_notificaciones": par["ORD_NOT"], "hacia_analitica": par["ORD_ANA"]},
        "clients": {"mongo_clave": mongo["clients"], "desde_gateway": par["GW_CLI"], "desde_graphql": par["GQL_CLI"],
                    "desde_auth": par["AUTH_CLI"], "desde_notificaciones": par["NOT_CLI"]},
        "payments": {"mongo_clave": mongo["payments"], "desde_gateway": par["GW_PAY"], "desde_graphql": par["GQL_PAY"],
                     "hacia_orders": par["PAY_ORD"], "hacia_proveedor": par["PAY_PRV"], "webhook_clave": par["WEBHOOK"]},
        "proveedor": {"desde_payments": par["PAY_PRV"], "webhook_clave": par["WEBHOOK"]},
        "graphql": {"desde_gateway": par["GW_GQL"], "hacia_orders": par["GQL_ORD"], "hacia_inventory": par["GQL_INV"],
                    "hacia_clients": par["GQL_CLI"], "hacia_payments": par["GQL_PAY"], "hacia_analitica": par["GQL_ANA"]},
        "notificaciones": {"mongo_clave": mongo["notificaciones"], "desde_gateway": par["GW_NOT"],
                           "desde_orders": par["ORD_NOT"], "desde_auth": par["AUTH_NOT"], "hacia_clients": par["NOT_CLI"]},
        "analitica": {"mongo_clave": mongo["analitica"], "desde_gateway": par["GW_ANA"],
                      "desde_graphql": par["GQL_ANA"], "desde_orders": par["ORD_ANA"]},
    }
    carpeta_tokens = os.path.join(DATOS, "tokens")
    os.makedirs(carpeta_tokens, exist_ok=True)
    for servicio, datos in secretos.items():
        vault.post(f"{VAULT}/v1/secret/data/{servicio}", headers=cab, json={"data": datos}).raise_for_status()
        politica = f'path "secret/data/{servicio}" {{\n  capabilities = ["read"]\n}}\n'
        vault.put(f"{VAULT}/v1/sys/policies/acl/{servicio}", headers=cab, json={"policy": politica}).raise_for_status()
        r = vault.post(f"{VAULT}/v1/auth/token/create", headers=cab,
                       json={"policies": [servicio], "no_default_policy": True, "ttl": "720h"})
        r.raise_for_status()
        with open(os.path.join(carpeta_tokens, servicio), "w") as f:
            f.write(r.json()["auth"]["client_token"])
    return mongo


def preparar_mongo(root_clave, claves):
    """Un usuario de MongoDB por servicio, con readWrite solo sobre su base."""
    # El usuario root lo crea el contenedor de MongoDB la primera vez, con MONGO_ROOT_PASSWORD del .env
    url = f"mongodb://127.0.0.1:{MONGO_PUERTO}/"
    root = MongoClient(url, username="root", password=root_clave, authSource="admin", serverSelectionTimeoutMS=5000)
    try:
        root.admin.command("ping")
        root.admin.command("listDatabases", nameOnly=True)
    except OperationFailure:
        sys.exit("La clave MONGO_ROOT_PASSWORD no coincide con la de la base de Docker. "
                 "Si la cambiaste, ejecuta: python iniciar.py --limpiar")
    for servicio, clave in claves.items():
        db = root[servicio]
        if db.command("usersInfo", servicio)["users"]:
            db.command("updateUser", servicio, pwd=clave)
        else:
            db.command("createUser", servicio, pwd=clave, roles=[{"role": "readWrite", "db": servicio}])


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
