# 8. Contratos que usa el frontend

Todas las llamadas van al API Gateway (`https://127.0.0.1:8000/api/v1`), con `Content-Type: application/json` y, si requieren sesión, con
`Authorization: Bearer <token>`. Cada respuesta trae `X-Request-ID`. El catálogo completo de servicios (S01–S35) y los ejemplos de
la Unidad 2 están en `Backend/README.md`. Aquí se listan solo los que consume la interfaz, con los errores que la interfaz trata.

**Errores comunes:**
- 401: sin token o sesión vencida. La página borra la sesión y lleva a `login.php?expirada=1`.
- 403: rol sin permiso. Aviso "No tienes permiso para esta sección".
- 429: demasiados intentos.
- 502: servicio interno no disponible. Aviso con "Reintentar".

| Pantalla | Servicio | Ruta | Cuerpo enviado | Respuesta usada | Errores tratados en la interfaz |
|---|---|---|---|---|---|
| Carta, portada | S01 | `GET /products` | — | `id, nombre, categoria, precio, precio_oferta, imagen, disponible` | 502 → "No pudimos cargar la carta" + Reintentar |
| Login | S04, S06 | `POST /auth/login`, `GET /clients/me` | `email, password` | `access_token, expires_in, rol`; `nombre` | 401 credenciales, 403 correo sin verificar (enlace a verificar), 429 |
| Encabezado | S05 | `POST /auth/logout` | — (el gateway agrega el token) | 200 | — |
| Registro | S03, S28 | `POST /auth/register`, `POST /auth/verify-email` | Datos del cliente; `email, codigo` | 201; 200 | 409, 422 (RUN, teléfono), 400 código inválido |
| Mi cuenta | S06, S07 | `GET` y `PUT /clients/me` | `nombre, run, telefono, direccion, comuna, provincia, region, fecha_nacimiento, sexo` (vacíos = `null`) | Ficha | 422 RUN, teléfono o fecha |
| Carrito | S09 | `POST /orders` | `items[{product_id, cantidad}], tipo_entrega, direccion, comuna, clave` | 201 pedido; **200 con `repetido: true`** si la clave ya creó un pedido | 409 sin stock, 422 fuera del radio o sin dirección, 502 |
| Pedido | S11, S12, S13 | `GET /orders/{id}`, `POST /orders/{id}/cancel`, `GET /orders/{id}/receipt` | `motivo` (5–200) | Pedido; estado; boleta (`folio, detalle, neto, iva, total, caja`) | 404 pedido ajeno, 409 ya no se puede anular |
| Pedido (pago) | S14, S16 | `POST /payments`, `POST /payments/{id}/simular` | `order_id` (el monto lo pone el servidor); `resultado` | `id, monto`; 202 | 409 pago ya procesado |
| Mis pedidos | S18 | `POST /graphql` | `query { misPedidos(limite: 20) { id estado tipoEntrega total creadoEn lineas { cantidad precio producto { nombre } } pago { estado monto } } }` | `data` + `errors` (avisos de dependencia caída) | `errors` con data parcial → "Información incompleta" |
| Inventario | S19–S22 | `GET/POST/PUT/DELETE /admin/products` | Producto completo (`precio_oferta` vacío = `null`) | Productos con stock | 403, 409 id repetido, 422 oferta ≥ precio |
| Despacho | S29, S23, S24 | `GET /admin/dispatch-orders`, `PUT /admin/orders/{id}/status`, `GET /admin/clients/{id}` | `estado` | Órdenes; nombre y teléfono | 403, 409 transición inválida |
| Ventas | S30 | `GET /admin/sales` | — | `folio, pedido, fecha, total, estado` | 403 |
| Reportes | S26 | `GET /admin/reports/sales` | — | `pedidos, total_vendido, ticket_promedio, mas_vendidos, por_dia` | 403, 502 + Reintentar |
| Administración | S33–S35, S31, S25 | `GET/POST /admin/users`, `PUT /admin/users/{id}/role`, `POST /admin/clients`, `GET /admin/contact` | Funcionario; perfil; cliente | Usuarios (sin hash), mensajes | 409 propio perfil o correo repetido |
| Contacto | S08 | `POST /contact` | `nombre, email, telefono, motivo, mensaje` | 201 | 422, 429 |

## Cambios de contrato en esta unidad

| ID | Cambio | Motivo | Incremento |
|---|---|---|---|
| DC01 | Nombres de productos con tilde en el backend | Coincidir con el frontend | I1 |
| DC02 | Cabeceras CORS para `http://localhost:8080` (métodos GET, POST, PUT y DELETE; cabeceras Authorization y Content-Type; expone `X-Request-ID`) | El navegador debe poder leer las respuestas | I1 |
| DC03 | Token con formato inválido → 401 (antes 502) | Error correcto para la interfaz | I1 |
| DC07 | `POST /orders` acepta `clave` (8–64 caracteres `A-Z a-z 0-9 -`) y responde 200 con `repetido: true` si se repite | Idempotencia (R19) | I4 |
