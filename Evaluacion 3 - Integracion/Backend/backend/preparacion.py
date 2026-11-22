"""Preparacion del backend antes de que arranquen los servicios. La usan los dos modos:
  - iniciar.py (todo en local): importa estas funciones.
  - Docker (docker-compose.yml): los contenedores 'certificados' y 'preparar' ejecutan este archivo:
        python preparacion.py certificados   -> genera la CA local y el certificado TLS en /certs
        python preparacion.py secretos       -> crea secretos, politicas y tokens en Vault y los usuarios de MongoDB

Lo que hace:
  1. Certificados TLS: una CA local y un certificado del servidor (localhost, 127.0.0.1 y el nombre de cada contenedor).
  2. Secretos ALEATORIOS en Vault: uno por cada par de servicios y una clave de MongoDB por servicio.
  3. Una politica y un token de Vault por servicio (cada uno solo puede leer su propio secreto).
  4. Un usuario de MongoDB por servicio, con permiso solo sobre su base.
"""
import datetime
import ipaddress
import os
import secrets
import ssl
import sys
import time

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pymongo import MongoClient
from pymongo.errors import OperationFailure

SERVICIOS = ["gateway", "auth", "inventory", "orders", "clients", "payments", "graphql", "analitica",
             "notificaciones", "proveedor"]
CON_BASE = ["auth", "inventory", "orders", "clients", "payments", "notificaciones", "analitica"]
# Nombres que van en el certificado: los de este computador y el de cada contenedor (vault incluido)
NOMBRES_CERTIFICADO = ["localhost", *SERVICIOS, "vault"]


def generar_certificados(carpeta):
    """CA local + certificado del servidor. Se generan solo si no existen, si vencen en menos de 7 dias
    o si al certificado le falta algun nombre. Las claves privadas no se suben (.gitignore).
    Devuelve True si se generaron nuevos."""
    os.makedirs(carpeta, exist_ok=True)
    ruta_crt = os.path.join(carpeta, "servidor.crt")
    if os.path.exists(ruta_crt) and os.path.exists(os.path.join(carpeta, "ca.crt")):
        actual = x509.load_pem_x509_certificate(open(ruta_crt, "rb").read())
        nombres = actual.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(
            x509.DNSName)
        vigente = actual.not_valid_after_utc - datetime.datetime.now(datetime.timezone.utc) > datetime.timedelta(days=7)
        if vigente and set(NOMBRES_CERTIFICADO) <= set(nombres):
            return False
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
            nombres = [x509.DNSName(n) for n in NOMBRES_CERTIFICADO]
            constructor = (constructor
                           .add_extension(x509.SubjectAlternativeName(
                               nombres + [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
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
        with open(os.path.join(carpeta, nombre), "wb") as f:
            f.write(datos)

    guardar("ca.crt", ca.public_bytes(serialization.Encoding.PEM))
    guardar("servidor.crt", srv.public_bytes(serialization.Encoding.PEM))
    guardar("servidor.key", clave_srv.private_bytes(serialization.Encoding.PEM,
                                                    serialization.PrivateFormat.TraditionalOpenSSL,
                                                    serialization.NoEncryption()))
    # La clave de la CA no se guarda: solo se necesitaba para firmar. Para renovar se genera todo de nuevo.
    return True


def rnd():
    return secrets.token_hex(32)


def armar_secretos(seed):
    """Secretos ALEATORIOS: uno por cada par de servicios (quien llama -> a quien llama) y una clave de
    MongoDB por servicio. Cada servicio recibe SOLO lo que necesita."""
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
    return secretos, mongo


def preparar_vault(vault_url, root, seed, ruta_token, contexto_tls):
    """Guarda los secretos en Vault (API HTTPS), con una politica y un token por servicio.
    ruta_token(servicio) dice en que archivo queda el token de cada servicio. Devuelve las claves de MongoDB."""
    cab = {"X-Vault-Token": root}
    vault = httpx.Client(verify=contexto_tls, timeout=10)
    secretos, mongo = armar_secretos(seed)
    for servicio, datos in secretos.items():
        vault.post(f"{vault_url}/v1/secret/data/{servicio}", headers=cab, json={"data": datos}).raise_for_status()
        politica = f'path "secret/data/{servicio}" {{\n  capabilities = ["read"]\n}}\n'
        vault.put(f"{vault_url}/v1/sys/policies/acl/{servicio}", headers=cab, json={"policy": politica}).raise_for_status()
        r = vault.post(f"{vault_url}/v1/auth/token/create", headers=cab,
                       json={"policies": [servicio], "no_default_policy": True, "ttl": "720h"})
        r.raise_for_status()
        ruta = ruta_token(servicio)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w") as f:
            f.write(r.json()["auth"]["client_token"])
    return mongo


def preparar_mongo(url, root_clave, claves):
    """Un usuario de MongoDB por servicio, con readWrite solo sobre su base.
    El usuario root lo crea el contenedor de MongoDB la primera vez, con MONGO_ROOT_PASSWORD del .env."""
    root = MongoClient(url, username="root", password=root_clave, authSource="admin", serverSelectionTimeoutMS=5000)
    try:
        root.admin.command("ping")
        root.admin.command("listDatabases", nameOnly=True)
    except OperationFailure:
        sys.exit("La clave MONGO_ROOT_PASSWORD no coincide con la de la base de MongoDB. "
                 "Si la cambiaste, borra la base: 'docker compose down -v' (o 'python iniciar.py --limpiar').")
    for servicio, clave in claves.items():
        db = root[servicio]
        if db.command("usersInfo", servicio)["users"]:
            db.command("updateUser", servicio, pwd=clave)
        else:
            db.command("createUser", servicio, pwd=clave, roles=[{"role": "readWrite", "db": servicio}])


# ---------------------------------------------------------------------------------- Modo Docker
def entregar_a_app(ruta, modo):
    """En Docker los servicios corren con el usuario 'app' (uid 1000), no como root: se le entrega el archivo."""
    try:
        if hasattr(os, "chown") and os.geteuid() == 0:
            os.chown(ruta, 1000, 1000)
        os.chmod(ruta, modo)
    except OSError:
        pass   # en Docker Desktop (Windows) la carpeta certs/ no admite cambiar el dueno; ahi ya se puede leer


def docker_certificados():
    carpeta = os.getenv("CERTS_DIR", "/certs")
    nuevos = generar_certificados(carpeta)
    entregar_a_app(os.path.join(carpeta, "servidor.key"), 0o600)
    print("Certificados TLS generados en certs/" if nuevos else "Certificados TLS vigentes, se reutilizan", flush=True)


def docker_secretos():
    vault_url = os.getenv("VAULT_ADDR", "https://vault:8200")
    root = os.environ["VAULT_ROOT_TOKEN"]
    contexto = ssl.create_default_context(cafile=os.path.join(os.getenv("CERTS_DIR", "/certs"), "ca.crt"))
    for _ in range(60):
        try:
            if httpx.get(f"{vault_url}/v1/sys/health", verify=contexto, timeout=3).status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    else:
        sys.exit("Vault no respondio a tiempo")
    # Vault en modo desarrollo guarda todo en memoria: si ya tiene los secretos (por ejemplo al reiniciar solo
    # un contenedor) no se crean de nuevo, porque los servicios que ya estan corriendo usan los actuales.
    r = httpx.get(f"{vault_url}/v1/secret/data/gateway", headers={"X-Vault-Token": root}, verify=contexto)
    if r.status_code == 200:
        print("Vault ya estaba configurado: se mantienen los secretos y tokens actuales", flush=True)
        return

    def ruta_token(servicio):
        return f"/tokens/{servicio}/token"

    claves = preparar_vault(vault_url, root, os.environ["SEED_PASSWORD"], ruta_token, contexto)
    for servicio in SERVICIOS:
        entregar_a_app(ruta_token(servicio), 0o400)
    preparar_mongo(f"mongodb://{os.getenv('MONGO_HOST', 'mongo:27017')}/", os.environ["MONGO_ROOT_PASSWORD"], claves)
    print("Vault y MongoDB listos: secretos, politicas, un token por servicio y un usuario de MongoDB por servicio",
          flush=True)


if __name__ == "__main__":
    paso = sys.argv[1] if len(sys.argv) > 1 else ""
    if paso == "certificados":
        docker_certificados()
    elif paso == "secretos":
        docker_secretos()
    else:
        sys.exit("Uso: python preparacion.py certificados|secretos")
