# 3. Criterios de aceptación y protocolo de pruebas

**Versión del protocolo: 1.1.** Se definió y se subió al repositorio **antes** de la primera ejecución; los cambios posteriores quedan en la sección *Cambios del protocolo* con su motivo y las pruebas que se repitieron.

## Reglas comunes

- **Entorno:** sistema completo en Docker (`docker compose up -d` en `Backend/`), frontend en `http://localhost:8080`, gateway en `https://127.0.0.1:8000`. Versión: el commit indicado en cada ejecución.
- **Estado inicial controlado:** cada campaña parte de la base vacía (`docker compose down -v` y `docker compose up -d`); los servicios crean los datos ficticios de prueba (8 productos con stock 40 y 6 cuentas, una por perfil).
- **Cuentas:** `ana@` y `pedro@` (cliente), `dueno@`, `admin@`, `despacho@` y `cajero@` (`@aromaycafe.test`), clave = `SEED_PASSWORD` del `.env`.
- **Campañas:** C1 y C3 en escritorio (1366×768); C2 y C4 en móvil emulado (perfil Pixel 7 de Playwright: viewport 412×839, pantalla 412×915, táctil). Cada prueba se ejecuta en las cuatro.
- **Ejecución:** cada prueba se inicia desde el frontend en Chromium (Playwright), salvo P31, que es un control de backend. Las solicitudes directas desde la sesión del navegador (P07, P11, P16) se usan solo donde la interfaz no permite provocar el caso (doble envío, aviso repetido del proveedor, consultas GraphQL fuera de la pantalla).
- **Verificación independiente de la pantalla:** inspección de MongoDB con `inspeccionar.py` (dentro del contenedor del servicio, con su propio usuario) o lectura posterior en una sesión nueva.
- **Vinculación:** cada solicitud del frontend lleva el `X-Request-ID` que crea el gateway; con él se extraen los logs de cada servicio.
- **Estados:** *aprobada* (lo observado cumple el criterio), *fallida* (no lo cumple), *bloqueada* (no se pudo ejecutar por una causa externa a la prueba) y *no ejecutada*. Un rechazo previsto que el sistema aplica correctamente cuenta como aprobado.
- **Repeticiones e intermitencia:** una prueba distinta se considera aprobada en la versión final solo si se aprueba en las cuatro campañas; si falla en alguna, se informa como intermitente y no se cuenta como aprobada.
- **Rendimiento:** no se fijan objetivos de tiempo ni de carga en esta evaluación; solo se registra la duración de cada prueba como dato. Por eso el informe no saca conclusiones de rendimiento (la prueba de carga es de la Unidad 2).
- **Protección:** las evidencias enmascaran contraseñas, tokens y cabeceras `Authorization`.

## Fichas de prueba

### P01 · La carta se arma con los productos de la API

| Campo | Contenido |
|---|---|
| Identificación | P01 · CA01 · Flujos: F01 · Requisitos: R01, R07 · Recorrido crítico RC1 · Escenario: éxito |
| Criterio de aceptación (CA01) | La carta muestra exactamente los productos activos que entrega GET /products, con sus nombres y precios (oferta si existe) |
| Precondiciones | Base limpia; visitante sin sesión |
| Procedimiento | Abrir catalogo.php y esperar las tarjetas |
| Resultado esperado | GET https://127.0.0.1:8000/api/v1/products responde 200 con origen localhost:8080 y CORS; tarjetas = productos de la respuesta; precios iguales |
| Verificación | Red (solicitud, respuesta y X-Request-ID); log del gateway e inventory con el mismo id; conteo en inventory.productos (activo=true) |
| Restauración | No modifica datos |

### P02 · Carta con inventory detenido y recuperación

| Campo | Contenido |
|---|---|
| Identificación | P02 · CA02 · Flujos: F01 · Requisitos: R17 · Recorrido crítico RC1 · Escenario: fallo y recuperación |
| Criterio de aceptación (CA02) | Si inventory no responde, la carta no inventa productos: muestra un error comprensible con Reintentar; al volver inventory, Reintentar carga la carta |
| Precondiciones | Base limpia; contenedor inventory detenido (docker compose stop inventory) |
| Procedimiento | Abrir catalogo.php; iniciar inventory; presionar Reintentar |
| Resultado esperado | Con inventory detenido: respuesta 502, 0 tarjetas y mensaje 'No pudimos cargar la carta'. Despues de iniciarlo: 200 y todas las tarjetas |
| Verificación | Red (502 y luego 200); log del gateway ('inventory no responde -> 502') |
| Restauración | docker compose start inventory |

### P03 · Crear un pedido de retiro desde el carrito

| Campo | Contenido |
|---|---|
| Identificación | P03 · CA03 · Flujos: F05 · Requisitos: R01, R04 · Recorrido crítico RC1 · Escenario: éxito |
| Criterio de aceptación (CA03) | El pedido queda guardado con los precios del servidor, descuenta el stock una vez y se ve igual al recargar y en otra sesión |
| Precondiciones | Base limpia; cliente ana@aromaycafe.test; stock inicial 40 de cada producto |
| Procedimiento | Agregar 2 Latte Art y 1 Croissant; iniciar sesión; Confirmar pedido con Retiro en el local |
| Resultado esperado | POST /orders 201; pedido.php muestra Pendiente de pago y total $9.200; stock Latte 38 y Croissant 39 |
| Verificación | Red (POST /orders y X-Request-ID); logs de orders e inventory-grpc (ReservarStock); inspección de orders.pedidos y inventory.productos; lectura en una sesión nueva |
| Restauración | Base limpia en la siguiente campaña |

### P04 · Confirmar pedido sin sesión

| Campo | Contenido |
|---|---|
| Identificación | P04 · CA04 · Flujos: F05 · Requisitos: R04, R15 · Recorrido crítico RC1 · Escenario: rechazo |
| Criterio de aceptación (CA04) | Sin sesión no se crea pedido: la página lleva a iniciar sesión y vuelve al carrito |
| Precondiciones | Visitante sin sesión con productos en el carrito |
| Procedimiento | Presionar Confirmar pedido |
| Resultado esperado | Redirige a login.php?volver=carrito.php; no se envía POST /orders; orders.pedidos sin cambios |
| Verificación | Red (sin POST /orders); conteo de orders.pedidos antes y después |
| Restauración | No modifica datos |

### P05 · Despacho fuera del radio de 3 km

| Campo | Contenido |
|---|---|
| Identificación | P05 · CA05 · Flujos: F05 · Requisitos: R01 · Recorrido crítico RC1 · Escenario: rechazo |
| Criterio de aceptación (CA05) | Un despacho a una comuna fuera del radio se rechaza con un mensaje claro y sin crear pedido ni descontar stock |
| Precondiciones | Cliente ana con productos en el carrito |
| Procedimiento | Elegir Despacho a domicilio, comuna Providencia, Confirmar pedido |
| Resultado esperado | POST /orders 422; mensaje 'fuera del radio de despacho'; sin pedido nuevo; stock igual |
| Verificación | Red (422); conteo de orders.pedidos e inventory.productos antes y después |
| Restauración | No modifica datos |

### P06 · Pedido con más cantidad que el stock

| Campo | Contenido |
|---|---|
| Identificación | P06 · CA06 · Flujos: F05, F09 · Requisitos: R01, R07 · Recorrido crítico RC1 · Escenario: límite |
| Criterio de aceptación (CA06) | Si la cantidad supera el stock, el pedido se rechaza completo (todo o nada) y el stock no cambia |
| Precondiciones | Dueña deja el stock de Cappuccino en 1 desde Inventario |
| Procedimiento | Cliente ana agrega 2 Cappuccino y confirma |
| Resultado esperado | POST /orders 409; mensaje 'No hay stock suficiente'; Cappuccino sigue con stock 1; sin pedido nuevo |
| Verificación | Red (PUT del inventario y POST 409); log de inventory-grpc; inspección de inventory.productos |
| Restauración | Dueña vuelve el stock a 40 |

### P07 · Reintento del mismo pedido (doble envío)

| Campo | Contenido |
|---|---|
| Identificación | P07 · CA07 · Flujos: F05 · Requisitos: R19 · Recorrido crítico RC1 · Escenario: límite |
| Criterio de aceptación (CA07) | Dos envios con la misma clave de idempotencia crean un solo pedido y descuentan el stock una sola vez |
| Precondiciones | Cliente ana con sesión |
| Procedimiento | Desde la sesión del navegador enviar dos veces el mismo POST /orders (mismo cuerpo y clave) |
| Resultado esperado | Primera respuesta 201 y segunda 200 con repetido=true y el mismo id; un solo documento con esa clave; stock descontado una vez |
| Verificación | Respuestas; log de orders ('pedido repetido'); inspección de orders.pedidos por clave e inventory.productos |
| Restauración | No requiere |

### P08 · Crear pedido con inventory demorado (gRPC)

| Campo | Contenido |
|---|---|
| Identificación | P08 · CA08 · Flujos: F05 · Requisitos: R17 · Recorrido crítico RC1 · Escenario: fallo y recuperación |
| Criterio de aceptación (CA08) | Si inventory no responde dentro del plazo de gRPC (3 s), no se crea el pedido y se informa; al reintentar con inventory activo, se crea |
| Precondiciones | Cliente ana con productos en el carrito; inventory en pausa (docker compose pause inventory) |
| Procedimiento | Confirmar pedido; reanudar inventory; Confirmar pedido otra vez |
| Resultado esperado | Primer intento: 502 y mensaje de servicio no disponible, sin pedido; segundo intento: 201 y pedido creado |
| Verificación | Red (502 y 201); tiempo de respuesta del primer intento; log de orders; conteo de orders.pedidos |
| Restauración | docker compose unpause inventory |

### P09 · Pagar con el proveedor simulado y obtener la boleta

| Campo | Contenido |
|---|---|
| Identificación | P09 · CA09 · Flujos: F06 · Requisitos: R02, R04, R08 · Recorrido crítico RC2 · Escenario: éxito |
| Criterio de aceptación (CA09) | Con el pago aprobado por el proveedor, el pedido queda PAGADO con boleta y folio, el pago APROBADO con el monto del servidor, y se registran el correo de boleta y la venta en analítica |
| Precondiciones | Pedido de ana en Pendiente de pago |
| Procedimiento | Pagar; Pagar con tarjeta de prueba |
| Resultado esperado | POST /payments 201 con el monto del pedido; POST /simular 202; pedido Pagado; boleta con folio, neto, IVA y total |
| Verificación | Red; logs de payments, orders, notificaciones y analítica; inspección de payments.pagos, orders.pedidos, notificaciones.correos y analitica.ventas; lectura en sesión nueva |
| Restauración | Base limpia en la siguiente campaña |

### P10 · Pago rechazado por el proveedor y nuevo intento

| Campo | Contenido |
|---|---|
| Identificación | P10 · CA10 · Flujos: F06 · Requisitos: R02 · Recorrido crítico RC2 · Escenario: rechazo y recuperación |
| Criterio de aceptación (CA10) | Un pago rechazado no cambia el pedido (sigue pendiente) y se puede pagar de nuevo |
| Precondiciones | Pedido de ana en Pendiente de pago |
| Procedimiento | Pagar; Simular pago rechazado; Pagar; Pagar con tarjeta de prueba |
| Resultado esperado | Primer pago RECHAZADO y pedido Pendiente de pago; segundo pago APROBADO y pedido Pagado |
| Verificación | Red; log de payments; inspección de payments.pagos (uno RECHAZADO y uno APROBADO) y orders.pedidos |
| Restauración | No requiere |

### P11 · Aviso de pago repetido por el proveedor

| Campo | Contenido |
|---|---|
| Identificación | P11 · CA11 · Flujos: F06 · Requisitos: R19 · Recorrido crítico RC2 · Escenario: límite |
| Criterio de aceptación (CA11) | Si el proveedor envía dos veces el mismo aviso, se procesa una vez: un folio, una venta en analítica |
| Precondiciones | Pedido de ana en Pendiente de pago con pago iniciado |
| Procedimiento | Simular el pago aprobado con repetir_aviso=2 desde la sesión del navegador |
| Resultado esperado | Primer aviso APROBADO; segundo aviso repetido; un solo folio; una sola venta del pedido en analítica |
| Verificación | Respuesta de /simular; log de payments ('repetido'); inspección de analitica.ventas y orders.pedidos |
| Restauración | No requiere |

### P12 · Anular un pedido pendiente con motivo

| Campo | Contenido |
|---|---|
| Identificación | P12 · CA12 · Flujos: F08 · Requisitos: R03 · Escenario: éxito |
| Criterio de aceptación (CA12) | Anular un pedido pendiente lo deja ANULADO con su motivo y devuelve el stock; un pedido pagado no muestra la opcion de anular |
| Precondiciones | Pedido nuevo de ana en Pendiente de pago (1 Espresso Doble) |
| Procedimiento | Escribir el motivo y presionar Anular pedido |
| Resultado esperado | POST /cancel 200; estado Anulado; stock de Espresso vuelve al valor anterior; historial con el motivo |
| Verificación | Red; logs de orders e inventory-grpc (LiberarStock); inspección de orders.pedidos e inventory.productos |
| Restauración | No requiere |

### P13 · Mis pedidos agrega orders, inventory y payments

| Campo | Contenido |
|---|---|
| Identificación | P13 · CA13 · Flujos: F07 · Requisitos: R16 · Recorrido crítico RC3 · Escenario: éxito |
| Criterio de aceptación (CA13) | La pantalla Mis pedidos muestra, en una consulta GraphQL, el estado (orders), los nombres de producto (inventory) y el pago (payments) de cada pedido propio |
| Precondiciones | Ana con pedidos de P03 a P12 |
| Procedimiento | Abrir Mis pedidos |
| Resultado esperado | POST /graphql 200 sin errors; un pedido por cada pedido de ana en orders.pedidos; estados y pagos iguales a los guardados |
| Verificación | Red (consulta y respuesta); logs de graphql, orders, inventory y payments con el mismo id; inspección de orders.pedidos de USR-003 |
| Restauración | No modifica datos |

### P14 · Pedido ajeno

| Campo | Contenido |
|---|---|
| Identificación | P14 · CA14 · Flujos: F07 · Requisitos: R15 · Recorrido crítico RC3 · Escenario: rechazo |
| Criterio de aceptación (CA14) | Otro cliente no puede ver un pedido ajeno: la pantalla no revela datos y el pedido no cambia |
| Precondiciones | Pedido pagado de ana; sesión de pedro@aromaycafe.test |
| Procedimiento | Pedro abre pedido.php?id=<pedido de ana> y consulta resumenPedido por GraphQL |
| Resultado esperado | GET /orders/{id} 404 con mensaje 'No encontramos ese pedido'; GraphQL resumenPedido = null; el pedido de ana sin cambios |
| Verificación | Red (404 y respuesta GraphQL); log de orders; inspección del pedido de ana |
| Restauración | No modifica datos |

### P15 · Mis pedidos con inventory detenido

| Campo | Contenido |
|---|---|
| Identificación | P15 · CA15 · Flujos: F07 · Requisitos: R16, R17 · Recorrido crítico RC3 · Escenario: fallo y recuperación |
| Criterio de aceptación (CA15) | Si inventory falla, Mis pedidos muestra lo que pudo armar y avisa que la información esta incompleta; al volver inventory se ve completa |
| Precondiciones | Ana con pedidos; inventory detenido |
| Procedimiento | Abrir Mis pedidos; iniciar inventory; recargar |
| Resultado esperado | Respuesta GraphQL con errors 'Servicio inventory no disponible'; aviso 'Información incompleta' y 'Producto (dato no disponible)'; después, sin errors |
| Verificación | Red (respuesta con errors); log de graphql |
| Restauración | docker compose start inventory |

### P16 · Permisos de campos y límites de GraphQL

| Campo | Contenido |
|---|---|
| Identificación | P16 · CA16 · Flujos: F07 · Requisitos: R15, R16 · Recorrido crítico RC3 · Escenario: rechazo y límite |
| Criterio de aceptación (CA16) | Un cliente no obtiene datos personales (cliente) ni reportes, y una consulta que excede el límite se rechaza |
| Precondiciones | Sesión de ana |
| Procedimiento | Desde la sesión enviar: consulta con el campo cliente; reporteVentas; consulta con 6 alias; consulta de más de 2000 caracteres |
| Resultado esperado | cliente = null con error de autorización; reporteVentas con error; la consulta de 6 alias se rechaza (límite 5) y la de más de 2000 caracteres responde 422 |
| Verificación | Respuestas GraphQL |
| Restauración | No modifica datos |

### P17 · Editar mi ficha

| Campo | Contenido |
|---|---|
| Identificación | P17 · CA17 · Flujos: F04 · Requisitos: R05 · Recorrido crítico RC4 · Escenario: éxito |
| Criterio de aceptación (CA17) | Los cambios de la ficha quedan guardados en clients y se ven al recargar y en una sesión nueva |
| Precondiciones | Sesión de ana |
| Procedimiento | En Mi cuenta cambiar teléfono y comuna; Guardar cambios; recargar |
| Resultado esperado | PUT /clients/me 200; aviso 'Tus datos quedaron guardados'; valores nuevos al recargar y en otra sesión |
| Verificación | Red; log de clients ('actualiza clients.clientes'); inspección de clients.clientes USR-003 |
| Restauración | No requiere |

### P18 · RUN inválido en la ficha

| Campo | Contenido |
|---|---|
| Identificación | P18 · CA18 · Flujos: F04 · Requisitos: R05 · Recorrido crítico RC4 · Escenario: rechazo |
| Criterio de aceptación (CA18) | Un RUN con dígito verificador incorrecto se rechaza con un mensaje claro y la ficha no cambia |
| Precondiciones | Sesión de ana |
| Procedimiento | Escribir el RUN 12.345.678-9 y guardar |
| Resultado esperado | PUT /clients/me 422; mensaje 'El RUN no es válido'; ficha sin cambios |
| Verificación | Red (422); inspección de clients.clientes antes y después |
| Restauración | No requiere |

### P19 · Sesión expirada

| Campo | Contenido |
|---|---|
| Identificación | P19 · CA19 · Flujos: F03, F04 · Requisitos: R15 · Recorrido crítico RC4 · Escenario: rechazo |
| Criterio de aceptación (CA19) | Con la sesión vencida en el servidor, la página protegida lleva a iniciar sesión con un aviso y no muestra datos |
| Precondiciones | Sesión de ana; su sesión vencida en auth (vencer_sesion.py) |
| Procedimiento | Abrir Mi cuenta |
| Resultado esperado | GET /clients/me 401; redirige a login.php?expirada=1 con aviso; la sesión se borra de auth.sesiones |
| Verificación | Red (401); log de auth ('sesión expirada'); inspección de auth.sesiones |
| Restauración | Iniciar sesión de nuevo |

### P20 · Página protegida sin sesión

| Campo | Contenido |
|---|---|
| Identificación | P20 · CA20 · Flujos: F04 · Requisitos: R15 · Recorrido crítico RC4 · Escenario: rechazo |
| Criterio de aceptación (CA20) | Sin sesión, Mi cuenta lleva a iniciar sesión y la API responde 401 sin llamar al backend |
| Precondiciones | Visitante sin sesión |
| Procedimiento | Abrir cuenta.php; llamar GET /clients/me sin token |
| Resultado esperado | Redirige a login.php; la API responde 401 'Bearer token requerido' |
| Verificación | Red; log del gateway ('sin token') |
| Restauración | No modifica datos |

### P21 · Login fallido, login y cierre de sesión

| Campo | Contenido |
|---|---|
| Identificación | P21 · CA21 · Flujos: F03 · Requisitos: R12, R15 · Recorrido crítico RC4 · Escenario: rechazo y éxito |
| Criterio de aceptación (CA21) | Una clave incorrecta se rechaza; al cerrar sesión el token deja de servir en el servidor |
| Precondiciones | Visitante |
| Procedimiento | Login con clave incorrecta; login correcto; Cerrar sesión; usar el token anterior |
| Resultado esperado | 401 'Correo o contraseña incorrectos'; 200 y 'Hola, Ana'; después del logout el token anterior recibe 401 |
| Verificación | Red; logs de auth (login rechazado, login correcto, logout) |
| Restauración | No requiere |

### P22 · Registro con verificación de correo

| Campo | Contenido |
|---|---|
| Identificación | P22 · CA22 · Flujos: F02 · Requisitos: R05, R11 · Escenario: éxito y rechazo |
| Criterio de aceptación (CA22) | Un cliente nuevo no puede entrar hasta verificar su correo con el código; con el código correcto puede iniciar sesión |
| Precondiciones | Correo ficticio nuevo |
| Procedimiento | Registrarse; intentar entrar; leer el código en la bandeja simulada; verificar; iniciar sesión |
| Resultado esperado | POST /auth/register 201; login 403 antes de verificar; verify-email 200; login 200 |
| Verificación | Red; logs de auth, clients y notificaciones; inspección de auth.usuarios (correo_verificado) y notificaciones.correos |
| Restauración | No requiere |

### P23 · Inventario del dueño: oferta, alta y baja

| Campo | Contenido |
|---|---|
| Identificación | P23 · CA23 · Flujos: F09 · Requisitos: R07, R10 · Escenario: éxito |
| Criterio de aceptación (CA23) | Los cambios del dueño quedan en inventory y la carta los refleja |
| Precondiciones | Sesión de dueno@aromaycafe.test |
| Procedimiento | Oferta 2900 al Latte; agregar un producto; darlo de baja; revisar la carta |
| Resultado esperado | PUT 200, POST 201, DELETE 204; la carta muestra la oferta, y el producto dado de baja no aparece |
| Verificación | Red; log de inventory; inspección de inventory.productos |
| Restauración | Quitar la oferta del Latte |

### P24 · Rol sin permiso

| Campo | Contenido |
|---|---|
| Identificación | P24 · CA24 · Flujos: F09, F10 · Requisitos: R12, R15 · Escenario: rechazo |
| Criterio de aceptación (CA24) | Un cliente que entra a Inventario o Despacho escribiendo la dirección recibe 403 del backend y no ve datos |
| Precondiciones | Sesión de ana |
| Procedimiento | Abrir inventario.php y despacho.php |
| Resultado esperado | GET /admin/products 403 y GET /admin/dispatch-orders 403; aviso 'No tienes permiso' |
| Verificación | Red (403); log del gateway ('no tiene permiso') |
| Restauración | No modifica datos |

### P25 · Despacho avanza el pedido pagado

| Campo | Contenido |
|---|---|
| Identificación | P25 · CA25 · Flujos: F10 · Requisitos: R02, R13 · Escenario: éxito |
| Criterio de aceptación (CA25) | El encargado ve los pedidos pagados en orden de pago y los avanza solo por transiciones válidas hasta Entregado |
| Precondiciones | Pedido pagado (P09) de tipo retiro; sesión de despacho@aromaycafe.test |
| Procedimiento | Marcar en preparación, listo y entregado |
| Resultado esperado | Tres PUT /status 200; el pedido sale de la lista al quedar Entregado; historial en orders |
| Verificación | Red; log de orders; inspección de orders.pedidos (historial) |
| Restauración | No requiere |

### P26 · Ventas de la caja web

| Campo | Contenido |
|---|---|
| Identificación | P26 · CA26 · Flujos: F11 · Requisitos: R04 · Escenario: éxito |
| Criterio de aceptación (CA26) | El cajero ve la venta del pedido pagado con su folio y total en la caja CAJA-WEB-01 |
| Precondiciones | Pedido pagado (P09); sesión de cajero@aromaycafe.test |
| Procedimiento | Abrir Ventas |
| Resultado esperado | GET /admin/sales 200; fila con el folio y el total del pedido de P09 |
| Verificación | Red; inspección de orders.pedidos (folio, caja) |
| Restauración | No modifica datos |

### P27 · Reporte de ventas actualizado

| Campo | Contenido |
|---|---|
| Identificación | P27 · CA27 · Flujos: F12 · Requisitos: R09 · Escenario: éxito |
| Criterio de aceptación (CA27) | El reporte del dueño suma cada pedido pagado al momento del pago |
| Precondiciones | Sesión de dueño; al menos un pedido pagado |
| Procedimiento | Abrir Reportes; pagar un pedido nuevo con ana; Actualizar |
| Resultado esperado | GET /admin/reports/sales 200; pedidos pagados aumenta en 1 y el total en el monto del pedido |
| Verificación | Red; logs de analítica; inspección de analitica.ventas |
| Restauración | No requiere |

### P28 · Analítica detenida y recuperación

| Campo | Contenido |
|---|---|
| Identificación | P28 · CA28 · Flujos: F12 · Requisitos: R09, R17 · Escenario: fallo y recuperación |
| Criterio de aceptación (CA28) | Si analítica no responde, el pago igual se confirma y el reporte informa el error; al volver analítica, la venta se suma (reintento cada 30 s) |
| Precondiciones | analítica detenida; pedido pendiente de ana |
| Procedimiento | Pagar el pedido; abrir Reportes; iniciar analítica; esperar hasta 70 s; Actualizar |
| Resultado esperado | Pago aprobado; Reportes muestra un error mientras analítica esta detenida; después de iniciarla, el reporte incluye la venta |
| Verificación | Red; log de orders (reintento) y analítica; inspección de analitica.ventas |
| Restauración | docker compose start analítica |

### P29 · Administración de usuarios y clientes

| Campo | Contenido |
|---|---|
| Identificación | P29 · CA29 · Flujos: F13 · Requisitos: R06, R10, R12 · Escenario: éxito y rechazo |
| Criterio de aceptación (CA29) | El admin crea funcionarios, cambia perfiles (no el suyo) y registra clientes en el local |
| Precondiciones | Sesión de admin@aromaycafe.test |
| Procedimiento | Crear un cajero; cambiarlo a despacho; intentar cambiar el propio perfil; registrar un cliente en el local |
| Resultado esperado | POST /admin/users 201; PUT /role 200; PUT del propio perfil 409; POST /admin/clients 201 |
| Verificación | Red; inspección de auth.usuarios |
| Restauración | No requiere |

### P30 · Formulario de contacto

| Campo | Contenido |
|---|---|
| Identificación | P30 · CA30 · Flujos: F14 · Requisitos: R14 · Escenario: éxito |
| Criterio de aceptación (CA30) | El mensaje enviado queda guardado y el admin lo ve en Administración |
| Precondiciones | Visitante |
| Procedimiento | Enviar el formulario de contacto; el admin abre Administración |
| Resultado esperado | POST /contact 201 y aviso de gracias; el mensaje aparece en la tabla del admin |
| Verificación | Red; log de clients; inspección de clients.contacto |
| Restauración | No requiere |

### P31 · Servicio llamado sin el secreto del gateway

| Campo | Contenido |
|---|---|
| Identificación | P31 · CA31 · Flujos: — · Requisitos: R15 · Escenario: control de backend |
| Criterio de aceptación (CA31) | Un servicio privado rechaza una llamada que no trae el secreto de Vault, aunque venga desde la red interna |
| Precondiciones | Sistema en Docker |
| Procedimiento | docker compose exec clients python llamada_sin_secreto.py |
| Resultado esperado | 403 sin secreto y 403 con secreto falso; dos lineas 'llamada RECHAZADA' en inventory |
| Verificación | Salida del script; log de inventory |
| Restauración | No modifica datos |

### P32 · Páginas sin desborde horizontal

| Campo | Contenido |
|---|---|
| Identificación | P32 · CA32 · Flujos: F01, F03, F04, F05, F06, F07 · Requisitos: R18 · Escenario: responsivo |
| Criterio de aceptación (CA32) | Las páginas principales se usan sin desborde horizontal en el viewport de la campaña |
| Precondiciones | Sesión de ana |
| Procedimiento | Abrir index, catalogo, carrito, login, cuenta, mis-pedidos y pedido |
| Resultado esperado | En cada página el ancho del documento no supera el del viewport |
| Verificación | Medicion del DOM y capturas |
| Restauración | No modifica datos |

## Cambios del protocolo

| Versión | Fecha | Cambio | Motivo | Pruebas que se repiten |
|---|---|---|---|---|
| 1.0 | 2026-11-28 | Versión inicial | — | — |
| 1.1 | 2026-11-28 | P16: la consulta de profundidad 6 se reemplaza por una consulta de más de 2000 caracteres | El esquema llega como máximo a profundidad 4 (misPedidos > lineas > producto > nombre), así que no se puede escribir una consulta válida que pase el límite de profundidad 5; el límite de tamaño (2000 caracteres) sí se puede probar. Se detectó al implementar la suite, antes de la primera ejecución. Además se corrigen tildes en títulos (sin cambio de criterios) | P16 (aún no ejecutada) |
| 1.1 | 2026-11-28 | Aclaración (después de ejecutar, sin cambio de criterios): el viewport móvil del perfil Pixel 7 es 412×839 (la pantalla es 412×915); la v1.0 decía 412×915 | Corregir la descripción para que coincida con lo registrado en las ejecuciones C2 y C4 | Ninguna |
