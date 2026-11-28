# 1. Línea base, entorno y alcance

## Caso y equipo

| | |
|---|---|
| Caso | N° 4 – Cafetería "Aroma & Café" (Maipú), basado en el Caso 19 "Sistema de Ventas On-line Fukusuke Sushi-Delivery" |
| Integrantes | Ian Arroyo · Alejandro Martínez (NRC 8479) |
| Frontend inicial | `Solemne 2/Frontend` del repositorio `Desarrollo-Web-Movil`, commit `c51e899` ("Evaluacion 2 - Frontend y Backend", 2026-11-09) |
| Backend inicial | `Solemne 2/Backend` del mismo commit: backend seguro de la Unidad 2 (gateway, Auth, Vault, GraphQL, inventory, orders, clients, payments, analítica, notificaciones, gRPC) |
| Versión evaluada | Carpeta `Evaluacion 3 - Integracion`, commit `61efbab` (ver [registro de ejecuciones](05_ejecuciones.md)) |

## Estado inicial (registrado con evidencia)

La línea base se midió con `Backend/pruebas/linea_base.js` sobre el frontend del commit `c51e899`, servido sin cambios
(evidencias en [`docs/evidencias/LB`](../Backend/docs/evidencias/LB/resultados.json)).

| ID | Qué se comprobó | Observado | Solicitudes al backend |
|---|---|---|---|
| LB01 | Origen de los productos de la carta | 8 tarjetas escritas a mano en `catalogo.php` | 0 |
| LB02 | Botones Iniciar sesión y Registrarse | Los dos con `href="#"` (sin destino) | 0 |
| LB03 | Botón Pagar pedido del carrito | Solo borra el carrito del navegador y muestra "Pedido enviado" | 0 |
| LB04 | Formulario de contacto | Muestra "Gracias, tu mensaje quedó registrado" sin guardar nada | 0 |
| LB05 | Pantallas de cuenta, pedidos y paneles | No existían (404) | 0 |

**Integrado al inicio:** nada; el frontend no llamaba al backend. **Backend:** completo y probado en la Unidad 2 (42 pruebas de
scripts, colección de Postman), sin consumidor real. **Problemas conocidos al inicio:**

- DC01: nombres con tilde distintos entre frontend y backend ("Frappé de Mocha" / "Frappe de Mocha").
- Sin CORS en el gateway: un navegador en otro origen no podía leer sus respuestas.
- El backend solo corría en local (`iniciar.py`); la Unidad 3 pide demostrar cada contenedor.

## Componentes reales, sandbox y dobles de prueba

| Componente | Tipo | Comentario |
|---|---|---|
| Frontend (PHP + JavaScript) | Real | Contenedor `frontend` |
| API Gateway, Auth Service, GraphQL Gateway | Reales | Contenedores propios |
| inventory, orders, clients, payments, notificaciones, analítica | Reales | Contenedores propios, una base de MongoDB cada uno |
| Administrador de secretos (Vault) | Real, modo desarrollo | Secretos aleatorios en memoria; no es una instalación de producción |
| MongoDB | Real | Contenedor `mongo:7` |
| gRPC orders → inventory | Real | ReservarStock y LiberarStock con TLS |
| Proveedor de pagos | **Doble de prueba** (`proveedor_pagos`) | Respeta el contrato de checkout y webhook firmado con HMAC. Limita las conclusiones al contrato simulado: no demuestra interoperabilidad con un proveedor real |
| Envío de correo | **Doble de prueba** (bandeja en `notificaciones.correos`) | El código de verificación y la boleta se guardan en vez de enviarse |

**Analítica y gRPC (componentes condicionales):** se mantiene la decisión de la Unidad 2 (ADR-01 y ADR-02 del README del backend).
Analítica está separada de los servicios transaccionales y recibe cada pedido pagado sin datos personales. gRPC se usa entre orders e inventory
para reservar y devolver stock con un plazo de 3 s. En esta unidad se integran con sus consumidores: el reporte del dueño (F12, P27 y P28) y la creación
y anulación de pedidos (F05 y F08, P03, P08 y P12).

## Cambios de arquitectura y su motivo

| Cambio | Motivo |
|---|---|
| Todo el sistema en contenedores (`docker-compose.yml`, `Dockerfile`) | Demostrar cada contenedor (frontend, gateway, Auth, servicios, Vault, MongoDB) y dar un despliegue reproducible. Solo se publican el 8080 y el 8000, en 127.0.0.1 |
| CORS en el gateway, limitado al origen del frontend | El navegador debe poder leer las respuestas del gateway, y ningún otro origen |
| Clave de idempotencia en `POST /orders` | Un reintento del mismo pedido no debe crear dos pedidos (R19) |
| Logs por paso con `X-Request-ID` en todos los servicios | Vincular la acción del frontend con la traza de cada servicio y con el efecto en los datos |
| Herramientas de prueba `inspeccionar.py`, `vencer_sesion.py`, `bandeja.py` y `llamada_sin_secreto.py` | Verificar la persistencia sin depender de la pantalla y preparar escenarios (sesión vencida, correo simulado, llamada sin secreto) |

El diagrama actualizado del recorrido de las solicitudes y del despliegue está en [10_diagramas.md](10_diagramas.md).

## Ficha del entorno

| | |
|---|---|
| Despliegue | Docker Compose (`Backend/docker-compose.yml`): frontend, gateway, 9 servicios, Vault, MongoDB y 2 contenedores de preparación |
| Imágenes | `aroma-cafe-backend:3.0` (python:3.12-slim), `php:8.3-cli-alpine`, `hashicorp/vault:1.15`, `mongo:7` |
| Dependencias de Python | `Backend/requirements.txt` con versiones fijas (FastAPI 0.162.0, uvicorn 0.54.0, httpx 0.28.1, pydantic 2.13.5, pymongo 4.19.0, argon2-cffi 25.1.0, strawberry-graphql 0.340.0, grpcio 1.85.1, cryptography 50.0.2) |
| Pruebas | Node.js 22 y Playwright 1.63.0 (`Backend/pruebas/package.json`); Chromium 153 |
| Configuración sin secretos | `Backend/.env.example` (se copia como `.env` y se cambian los valores; `.env` no se sube) |
| Migraciones | No hay: cada servicio crea sus índices y datos ficticios al partir si su base está vacía |
| Datos ficticios | 8 productos con stock 40 y 6 cuentas (`ana@` y `pedro@` como clientes, más `dueno@`, `admin@`, `despacho@` y `cajero@`, todas `@aromaycafe.test`) con la clave `SEED_PASSWORD` del `.env` |
| Certificados | CA local generada por el contenedor `certificados` en `Backend/certs/` (el navegador debe confiar en `ca.crt`) |
| Ejecución de las campañas | Entorno Linux de desarrollo con Docker 29.9.2, zona horaria UTC |

## Instrucciones de inicio

```bash
cd "Evaluacion 3 - Integracion/Backend"
cp .env.example .env              # y cambiar los tres valores
docker compose up -d --build
docker compose ps -a              # servicios "healthy"; certificados y preparar "Exited (0)"
```

Abrir `https://127.0.0.1:8000/health` y aceptar el certificado (o instalar `Backend/certs/ca.crt`); luego `http://localhost:8080`.

## Restauración del estado inicial

```bash
docker compose down -v            # borra la base de datos
docker compose up -d              # los servicios vuelven a crear los datos ficticios
```

La suite de integración hace esto mismo al empezar cada campaña.

## Limitaciones iniciales

- Un solo equipo; no se mide disponibilidad ni rendimiento en esta unidad.
- Vault en modo desarrollo: los secretos se crean de nuevo si se recrea su contenedor.
- Proveedor de pagos y correo son dobles de prueba.
- El navegador de las pruebas automáticas acepta el certificado de la CA local sin instalarlo; una persona debe aceptarlo una vez.
