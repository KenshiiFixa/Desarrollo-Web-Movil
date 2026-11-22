# Evaluación 3 - Integración frontend y backend

| Avance | Qué se hizo |
|---|---|
| 1 | La página **Carta** (`Frontend/catalogo.php`) ya no tiene los productos escritos a mano: los pide al API Gateway (`GET https://127.0.0.1:8000/api/v1/products`). CORS en el gateway y logs de cada paso. |
| 2 | **Todo el sistema en contenedores Docker**: frontend, API Gateway, los 9 servicios del backend, Vault y MongoDB. |
| 3 | **Usuarios e inventario desde el frontend**: iniciar sesión, registro con verificación del correo, cerrar sesión, sesión vencida, mi cuenta, inventario del dueño y formulario de contacto. |

## Índice

1. [Cómo correrlo con Docker](#cómo-correrlo-con-docker)
2. [Contenedores](#contenedores)
3. [Páginas conectadas al backend](#páginas-conectadas-al-backend)
4. [Qué cambió](#qué-cambió)
5. [Evidencia por contenedor (video)](#evidencia-por-contenedor-video)
6. [Modo local y pruebas](#modo-local-y-pruebas)

## Cómo correrlo con Docker

Requisito: Docker Desktop abierto (que diga *Engine running*).

1. En `Backend/`, copiar `.env.example` como `.env` y cambiar los valores (no se sube al repositorio).
2. Levantar todo (la primera vez se demora porque construye la imagen del backend y descarga las de Vault, MongoDB y PHP):

   ```bash
   cd Backend
   docker compose up -d --build
   ```

3. Revisar que todo esté arriba. Los servicios deben decir `healthy`, y `certificados` y `preparar` deben decir `Exited (0)` porque solo se ejecutan una vez:

   ```bash
   docker compose ps -a
   ```

4. Que el navegador confíe en el certificado: abrir una vez `https://127.0.0.1:8000/health` y aceptar el aviso,
   o importar `Backend/certs/ca.crt` (lo genera el contenedor `certificados`). Si no, la llamada HTTPS falla antes de llegar al CORS.
5. Abrir el frontend en `http://localhost:8080/catalogo.php`.

Detener: `docker compose down` (los datos de MongoDB quedan guardados). Borrar también la base: `docker compose down -v`.

## Contenedores

| Contenedor | Imagen | Red | Qué hace |
|---|---|---|---|
| `frontend` | `php:8.3-cli-alpine` | publica | Sirve la carpeta `Frontend/` en `http://localhost:8080` |
| `gateway` | `aroma-cafe-backend:3.0` | publica + privada | API Gateway, único punto de entrada al backend: `https://127.0.0.1:8000` |
| `auth`, `inventory`, `orders`, `clients`, `payments`, `graphql`, `analitica`, `notificaciones`, `proveedor` | `aroma-cafe-backend:3.0` | privada | Un contenedor por servicio. Cada uno solo tiene montado **su** token de Vault |
| `vault` | `hashicorp/vault:1.15` | privada | Secret Manager (modo desarrollo, con HTTPS) |
| `mongo` | `mongo:7` | privada | Persistencia: una base y un usuario por servicio |
| `certificados` | `aroma-cafe-backend:3.0` | sin red | Se ejecuta una vez: crea la CA local y el certificado TLS en `Backend/certs/` |
| `preparar` | `aroma-cafe-backend:3.0` | privada | Se ejecuta una vez: secretos aleatorios, políticas y un token por servicio en Vault, y un usuario de MongoDB por servicio |

- Solo se publican en el computador el frontend (8080) y el gateway (8000), y solo en `127.0.0.1`. MongoDB también se publica en `127.0.0.1:27018`, pero solo lo usa el modo local.
- La red `privada` es `internal`: desde el computador no se puede llamar directo a `inventory`, `auth`, etc.
- Todo el tráfico entre contenedores va con TLS, incluido gRPC entre `orders` e `inventory` y las llamadas a Vault.
- Los servicios corren con un usuario sin privilegios (`app`), no como root.

## Páginas conectadas al backend

Todas las llamadas van solo al API Gateway (`https://127.0.0.1:8000/api/v1`). El token se guarda en `sessionStorage`
(se borra al cerrar el navegador) y dura 15 minutos: si el gateway responde 401, la página manda a iniciar sesión de nuevo.

| Página | Qué hace | Rutas del gateway | Servicios |
|---|---|---|---|
| `catalogo.php` | Carta con precios, ofertas y "Agotado" | `GET /products` (pública) | inventory |
| `login.php` | Iniciar sesión. Errores: clave incorrecta (401), correo sin verificar (403, con enlace para verificar), demasiados intentos (429), sesión vencida | `POST /auth/login`, `GET /clients/me` | auth, clients |
| `registro.php` | Paso 1: datos del cliente (Caso 19). Paso 2: código de 6 dígitos que llega al correo | `POST /auth/register`, `POST /auth/verify-email` | auth, clients, notificaciones |
| `cuenta.php` | Ver y editar los datos personales (RUN, teléfono, dirección, comuna...) | `GET` y `PUT /clients/me` | clients |
| `inventario.php` | Solo dueño y admin: cambiar precio, oferta y stock, agregar productos, dar de baja y reactivar. Un cliente que entra escribiendo la dirección recibe 403 del backend y ve "No tienes permiso" | `GET`, `POST`, `PUT` y `DELETE /admin/products` | inventory |
| `Contacto.php` | Formulario de contacto (público) | `POST /contact` | clients |
| Encabezado (todas) | Con sesión: "Hola, nombre", "Inventario" (dueño o admin) y "Cerrar sesión" (borra la sesión en el backend) | `POST /auth/logout` | auth |

Usuarios de prueba (clave = `SEED_PASSWORD` del `.env`): `ana@aromaycafe.test` (cliente) y `dueno@aromaycafe.test` (dueño).

**Código de verificación del registro.** El envío de correo es simulado: el correo queda guardado en la base de
notificaciones. Para "abrir el correo":

```bash
docker compose exec notificaciones python bandeja.py correo@delregistro.cl
```

El script corre dentro del contenedor de notificaciones con su propio token de Vault y solo puede leer esa base.

## Qué cambió

| Dónde | Cambio |
|---|---|
| `Backend/docker-compose.yml`, `Backend/Dockerfile`, `Backend/vault/tls.hcl` | Todo el sistema en contenedores (antes solo MongoDB). |
| `Backend/backend/preparacion.py` | Certificados, secretos de Vault y usuarios de Mongo. Lo usan los contenedores `certificados` y `preparar` y también `iniciar.py`, así no hay código repetido. El certificado ahora incluye el nombre de cada contenedor. |
| `Backend/backend/comun.py` | Con `EN_DOCKER=1` cada servicio llama a los otros por el nombre del contenedor (`https://inventory:8000`). Función `log()`: cada servicio escribe si el secreto del que lo llama coincide con el de Vault (OK o RECHAZADA 403). |
| `Backend/backend/gateway/main.py` | CORS: solo se permite el origen del frontend (`http://localhost:8080`), los métodos GET, POST, PUT, DELETE y las cabeceras `Authorization` y `Content-Type`. Log de cada paso: ruta encontrada, validación con el Auth Service y a qué servicio enruta. Un token con formato inválido ahora responde 401 (antes 502). |
| `Backend/backend/auth_service/main.py` | Log del `/introspect`: sesión válida (con rol), inexistente o expirada. |
| `Backend/backend/inventory/main.py` | Log de la consulta a MongoDB (`inventory.productos`). Nombres con tilde: "Frappé de Mocha" y "Cheesecake de Maracuyá". |
| `Frontend/catalogo.php` y `Frontend/app.js` | La carta se arma con lo que responde la API. Muestra "Cargando la carta…", el precio de oferta, "Agotado" si no hay stock y un mensaje con "Reintentar" si el backend no responde. |
| `Frontend/login.php`, `registro.php`, `cuenta.php`, `inventario.php` | Páginas nuevas, con el mismo encabezado y pie del sitio. Los botones "Iniciar sesión" y "Registrarse" de todas las páginas ahora llevan a ellas. |
| `Frontend/app.js` | Sesión, una sola función para llamar al gateway, encabezado según la sesión, y la lógica de cada página. Los datos de la API se muestran con `textContent` (nunca como HTML). |
| `Frontend/index.css` | Estilos de formularios, avisos y tabla de inventario, también para celular. |
| `Backend/backend/auth_service`, `clients`, `inventory`, `notificaciones` | Logs de login, registro, verificación, logout, lectura y cambios en MongoDB. Nunca se escriben claves, tokens ni el código de verificación. |
| `Backend/backend/clients/main.py` | Nombres de prueba con tilde: "Ana Pérez" y "Dueña Aroma". |
| `Backend/backend/bandeja.py` | Bandeja de correo simulada (ver arriba). |
| `Backend/backend/llamada_sin_secreto.py` | Demostración del rechazo: un contenedor llama a inventory sin secreto o con uno falso y recibe 403. |
| `Backend/pruebas/prueba_frontend.js` | Prueba en Chromium de todo lo anterior (ver abajo). |

## Evidencia por contenedor (video)

Cada solicitud tiene un id (`req=`) que crea el gateway y que aparece en el log de todos los contenedores por los que pasa.
Para ver los logs: `docker compose logs -f gateway` (o `auth`, `inventory`, `frontend`...). Varios a la vez: `docker compose logs gateway auth inventory | grep <id>` (en PowerShell: `| Select-String <id>`).

1. **Contenedor Frontend.** F12 → Red (Network) → recargar la carta. Se ve `GET https://127.0.0.1:8000/api/v1/products` con estado 200, la cabecera `access-control-allow-origin: http://localhost:8080` y el `x-request-id`. En `docker compose logs frontend` se ven las páginas e imágenes que sirvió PHP.
2. **Contenedor ApiGateway** (`docker compose logs gateway`):

   ```
   [gateway] req=7173b6f98172 ruta S01: GET /products -> inventory (publica, origen http://localhost:8080)
   [gateway] req=7173b6f98172 enrutando a inventory GET /products con el secreto gateway->inventory leido de Vault
   [gateway] req=7173b6f98172 inventory respondio 200
   ```

   La carta es pública, así que no pasa por el Auth Service. La validación se ve al iniciar sesión en `login.php`:
   después del login la página pide el perfil (`GET /clients/me`) con el token:

   ```
   [gateway] req=e049f35ada88 ruta S06: GET /clients/me -> clients (requiere sesion, origen http://localhost:8080)
   [gateway] req=e049f35ada88 pidiendo validacion del token al Auth Service (POST /introspect)
   [gateway] req=e049f35ada88 Auth Service respondio: token valido, rol=cliente
   [gateway] req=e049f35ada88 enrutando a clients GET /clients/me con el secreto gateway->clients leido de Vault
   ```

3. **Contenedor Auth Service** (`docker compose logs auth`). Primero el login y después la validación del token:

   ```
   [auth] req=827ea4484fc2 login correcto: clave verificada (argon2id), sesion de USR-003 creada en auth.sesiones, rol=cliente, dura 15 min
   [auth] req=e049f35ada88 secreto de gateway verificado con el de Vault: OK, se permite la llamada
   [auth] req=e049f35ada88 introspect: sesion valida en auth.sesiones, rol=cliente -> autenticado
   ```

4. **Contenedor Backend** (`docker compose logs inventory`): permite la llamada del gateway y rechaza una que no trae el secreto.
   Para mostrar el rechazo, otro contenedor de la red privada llama directo a inventory, primero sin secreto
   y después haciéndose pasar por el gateway con un secreto falso (`backend/llamada_sin_secreto.py`):

   ```bash
   docker compose exec clients python llamada_sin_secreto.py
   ```

   ```
   Sin secreto: inventory respondio 403 Forbidden
   Haciendose pasar por el gateway con un secreto falso: inventory respondio 403 Forbidden
   ```

   En el log de inventory (`docker compose logs inventory`) queda:

   ```
   [inventory] req=7173b6f98172 secreto de gateway verificado con el de Vault: OK, se permite la llamada
   [inventory] req=22d102bc030c llamada RECHAZADA (403): 'sin nombre' no puede llamar a este servicio
   [inventory] req=f78102b13f58 llamada RECHAZADA (403): el secreto de gateway no coincide con el guardado en Vault
   ```

5. **Contenedor Persistencia** (`docker compose logs inventory` o `clients`). Consulta y modificación:

   ```
   [inventory] req=7173b6f98172 MongoDB: consulta inventory.productos (filtro: activo) -> 8 documentos
   [clients]   req=e049f35ada88 MongoDB: lee clients.clientes del usuario de la sesion (USR-003)
   [inventory] req=ef43b448c75d MongoDB: actualiza inventory.productos latte-art (precio=3200, oferta=2900, stock=15) por rol=dueno
   ```

## Modo local y pruebas

`python iniciar.py` sigue funcionando igual que en la Evaluación 2 (servicios y Vault en el computador, solo `mongo` en Docker).
Es el modo que usan los scripts de `pruebas/`, porque algunas pruebas detienen servicios o leen el correo simulado como si fueran un servicio.
No se pueden usar los dos modos a la vez (ocupan los mismos puertos): antes de `iniciar.py`, hacer `docker compose down`.

**Prueba del frontend (Playwright).** Con Docker corriendo, desde `Backend/pruebas`:

```bash
npm install
npx playwright install chromium
TEST_PASSWORD=<SEED_PASSWORD del .env> npm test
```

En PowerShell la última línea es `$env:TEST_PASSWORD="..."; npm test`. Recorre en Chromium (escritorio y celular emulado Pixel 7)
el login, el registro con el código, mi cuenta, el inventario, cerrar sesión, la sesión vencida y el contacto.
Deja el resultado en `docs/evidencias/prueba_frontend.txt` y capturas en `docs/evidencias/capturas/`.
El navegador de la prueba acepta el certificado de la CA local sin instalarlo (`ignoreHTTPSErrors`); una persona lo acepta una vez.
La prueba crea datos (un usuario y un producto nuevos, y cambia la oferta del Latte): antes de grabar un video conviene
partir con la base limpia (`docker compose down -v` y `docker compose up -d`).

Resultados de esta versión:

- Modo local: seguridad 22/22, flujos 17/17, fallos 3/3.
- Frontend en Chromium contra Docker: 30/30 (`docs/evidencias/prueba_frontend.txt`).
- Docker: catálogo, pedido (orders reserva stock en inventory por gRPC), pago con el proveedor simulado y su aviso al gateway,
  GraphQL, reporte del dueño, 403 por rol, 401 con token falso, CORS y la carta en Chromium (Playwright) con los 8 productos.
- CORS con curl: el origen `http://localhost:8080` recibe `access-control-allow-origin`. Un origen no permitido no la recibe
  (el navegador bloquea la respuesta) y su preflight `OPTIONS` responde 400.
