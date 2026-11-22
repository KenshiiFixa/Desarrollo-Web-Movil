# Imagen unica de los servicios del backend; la variable SERVICIO elige cual ejecuta cada contenedor.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
ENV PYTHONUNBUFFERED=1 EN_DOCKER=1 CERTS_DIR=/certs VAULT_ADDR=https://vault:8200 \
    VAULT_TOKEN_FILE=/run/vault/token MONGO_HOST=mongo:27017
# Los servicios no corren como root (uid 1000)
RUN useradd -m -u 1000 app
USER app
EXPOSE 8000
# HTTPS con el certificado de la CA local; cada servicio escribe su propio log (comun.registrar_logs)
CMD ["sh", "-c", "exec uvicorn ${SERVICIO}.main:app --host 0.0.0.0 --port 8000 --no-access-log --ssl-certfile /certs/servidor.crt --ssl-keyfile /certs/servidor.key"]
