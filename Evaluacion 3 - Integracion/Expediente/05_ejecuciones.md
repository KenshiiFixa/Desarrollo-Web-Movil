# 5. Registro de ejecuciones

Generado desde `Backend/docs/evidencias/<campaña>/resultados.json`. Cada fila es una ejecución (RUN) de una prueba en una campaña. Las campañas parten de la base vacía. Los ensayos previos a la versión evaluada están en `docs/evidencias/historial/` y no se suman a estos resultados.

## Campañas

| Campaña | Nombre | Commit evaluado | Inicio | Fin | Zona horaria | Ejecutor | Navegador | Viewport | Docker | Estado inicial | Configuración declarada | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Escritorio, ejecución 1 | `61efbab` | 2026-11-28T17:35:02+00:00 | 2026-11-28T17:38:39+00:00 | UTC | Ian Arroyo (ejecución automatizada) | Chromium 153.0.8010.12 (Playwright 1.63.0) | 1366x768 | 29.9.2 | base vacía (docker compose down -v / up -d) | Límite general del gateway: 600 solicitudes por minuto (login: 10 por minuto, sin cambios) | 32 aprobada |
| C2 | Móvil, ejecución 1 | `61efbab` (+ solo las evidencias de las campañas anteriores, sin cambios de código) | 2026-11-28T17:39:07+00:00 | 2026-11-28T17:42:50+00:00 | UTC | Ian Arroyo (ejecución automatizada) | Chromium 153.0.8010.12 (Playwright 1.63.0) | Pixel 7 emulado (412x839) | 29.9.2 | base vacía (docker compose down -v / up -d) | Límite general del gateway: 600 solicitudes por minuto (login: 10 por minuto, sin cambios) | 32 aprobada |
| C3 | Escritorio, ejecución 2 | `61efbab` (+ solo las evidencias de las campañas anteriores, sin cambios de código) | 2026-11-28T17:43:33+00:00 | 2026-11-28T17:47:15+00:00 | UTC | Ian Arroyo (ejecución automatizada) | Chromium 153.0.8010.12 (Playwright 1.63.0) | 1366x768 | 29.9.2 | base vacía (docker compose down -v / up -d) | Límite general del gateway: 600 solicitudes por minuto (login: 10 por minuto, sin cambios) | 32 aprobada |
| C4 | Móvil, ejecución 2 | `61efbab` (+ solo las evidencias de las campañas anteriores, sin cambios de código) | 2026-11-28T17:47:44+00:00 | 2026-11-28T17:51:26+00:00 | UTC | Ian Arroyo (ejecución automatizada) | Chromium 153.0.8010.12 (Playwright 1.63.0) | Pixel 7 emulado (412x839) | 29.9.2 | base vacía (docker compose down -v / up -d) | Límite general del gateway: 600 solicitudes por minuto (login: 10 por minuto, sin cambios) | 32 aprobada |

La emulación móvil (C2 y C4) usa el perfil Pixel 7 de Playwright (viewport 412×839, pantalla 412×915, táctil). No equivale a probar un dispositivo físico.

## Ejecuciones

| RUN | Prueba | CA | Estado | Inicio | Duración | Evidencias | Vinculación (extracto) | Notas |
|---|---|---|---|---|---|---|---|---|
| RUN-C1-P01 | P01 La carta se arma con los productos de la API | CA01 | **aprobada** | 17:35:02 | 2.2 s | [01](../Backend/docs/evidencias/C1/P01/01-carta.jpg) [02](../Backend/docs/evidencias/C1/P01/red.json) [03](../Backend/docs/evidencias/C1/P01/persistencia.json) [04](../Backend/docs/evidencias/C1/P01/logs.txt) | X-Request-ID 3f97be4d9b9c |  |
| RUN-C1-P02 | P02 Carta con inventory detenido y recuperación | CA02 | **aprobada** | 17:35:04 | 19.1 s | [01](../Backend/docs/evidencias/C1/P02/01-inventory-detenido.jpg) [02](../Backend/docs/evidencias/C1/P02/02-recuperado.jpg) [03](../Backend/docs/evidencias/C1/P02/red.json) [04](../Backend/docs/evidencias/C1/P02/logs.txt) | X-Request-ID 8c4a1f5e62f2 |  |
| RUN-C1-P03 | P03 Crear un pedido de retiro desde el carrito | CA03 | **aprobada** | 17:35:23 | 11.2 s | [01](../Backend/docs/evidencias/C1/P03/01-pedido-creado.jpg) [02](../Backend/docs/evidencias/C1/P03/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C1/P03/red.json) [04](../Backend/docs/evidencias/C1/P03/persistencia.json) [05](../Backend/docs/evidencias/C1/P03/logs.txt) | pedido ORD-30400C33 |  |
| RUN-C1-P04 | P04 Confirmar pedido sin sesión | CA04 | **aprobada** | 17:35:35 | 4.0 s | [01](../Backend/docs/evidencias/C1/P04/01-login.jpg) [02](../Backend/docs/evidencias/C1/P04/red.json) [03](../Backend/docs/evidencias/C1/P04/persistencia.json) [04](../Backend/docs/evidencias/C1/P04/logs.txt) | X-Request-ID 4c95b1145b79 |  |
| RUN-C1-P05 | P05 Despacho fuera del radio de 3 km | CA05 | **aprobada** | 17:35:39 | 6.8 s | [01](../Backend/docs/evidencias/C1/P05/01-fuera-radio.jpg) [02](../Backend/docs/evidencias/C1/P05/red.json) [03](../Backend/docs/evidencias/C1/P05/persistencia.json) [04](../Backend/docs/evidencias/C1/P05/logs.txt) | X-Request-ID 34ffc8f92ae6 |  |
| RUN-C1-P06 | P06 Pedido con más cantidad que el stock | CA06 | **aprobada** | 17:35:46 | 10.9 s | [01](../Backend/docs/evidencias/C1/P06/01-sin-stock.jpg) [02](../Backend/docs/evidencias/C1/P06/red.json) [03](../Backend/docs/evidencias/C1/P06/persistencia.json) [04](../Backend/docs/evidencias/C1/P06/logs.txt) | X-Request-ID 35e57b6119b5 |  |
| RUN-C1-P07 | P07 Reintento del mismo pedido (doble envío) | CA07 | **aprobada** | 17:35:57 | 6.0 s | [01](../Backend/docs/evidencias/C1/P07/red.json) [02](../Backend/docs/evidencias/C1/P07/persistencia.json) [03](../Backend/docs/evidencias/C1/P07/logs.txt) | pedido ORD-8DF554B6; clave PRUEBA-C1-1795887359153 |  |
| RUN-C1-P08 | P08 Crear pedido con inventory demorado (gRPC) | CA08 | **aprobada** | 17:36:03 | 10.4 s | [01](../Backend/docs/evidencias/C1/P08/01-inventory-en-pausa.jpg) [02](../Backend/docs/evidencias/C1/P08/02-recuperado.jpg) [03](../Backend/docs/evidencias/C1/P08/red.json) [04](../Backend/docs/evidencias/C1/P08/persistencia.json) [05](../Backend/docs/evidencias/C1/P08/logs.txt) | pedido ORD-E4206731 | El primer intento tardó 3339 ms (plazo de gRPC: 3 s) |
| RUN-C1-P09 | P09 Pagar con el proveedor simulado y obtener la boleta | CA09 | **aprobada** | 17:36:14 | 8.6 s | [01](../Backend/docs/evidencias/C1/P09/01-pasarela.jpg) [02](../Backend/docs/evidencias/C1/P09/02-boleta.jpg) [03](../Backend/docs/evidencias/C1/P09/red.json) [04](../Backend/docs/evidencias/C1/P09/persistencia.json) [05](../Backend/docs/evidencias/C1/P09/logs.txt) | pedido ORD-30400C33 |  |
| RUN-C1-P10 | P10 Pago rechazado por el proveedor y nuevo intento | CA10 | **aprobada** | 17:36:22 | 5.1 s | [01](../Backend/docs/evidencias/C1/P10/01-rechazado.jpg) [02](../Backend/docs/evidencias/C1/P10/02-aprobado.jpg) [03](../Backend/docs/evidencias/C1/P10/red.json) [04](../Backend/docs/evidencias/C1/P10/persistencia.json) [05](../Backend/docs/evidencias/C1/P10/logs.txt) | pedido ORD-E4206731 |  |
| RUN-C1-P11 | P11 Aviso de pago repetido por el proveedor | CA11 | **aprobada** | 17:36:28 | 5.0 s | [01](../Backend/docs/evidencias/C1/P11/01-pagado-una-vez.jpg) [02](../Backend/docs/evidencias/C1/P11/red.json) [03](../Backend/docs/evidencias/C1/P11/persistencia.json) [04](../Backend/docs/evidencias/C1/P11/logs.txt) | pedido ORD-EF73EAC1 |  |
| RUN-C1-P12 | P12 Anular un pedido pendiente con motivo | CA12 | **aprobada** | 17:36:33 | 11.1 s | [01](../Backend/docs/evidencias/C1/P12/01-anulado.jpg) [02](../Backend/docs/evidencias/C1/P12/red.json) [03](../Backend/docs/evidencias/C1/P12/persistencia.json) [04](../Backend/docs/evidencias/C1/P12/logs.txt) | pedido ORD-DCCAFAAB |  |
| RUN-C1-P13 | P13 Mis pedidos agrega orders, inventory y payments | CA13 | **aprobada** | 17:36:44 | 3.3 s | [01](../Backend/docs/evidencias/C1/P13/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C1/P13/red.json) [03](../Backend/docs/evidencias/C1/P13/persistencia.json) [04](../Backend/docs/evidencias/C1/P13/logs.txt) | X-Request-ID b2114575ad72 |  |
| RUN-C1-P14 | P14 Pedido ajeno | CA14 | **aprobada** | 17:36:48 | 3.5 s | [01](../Backend/docs/evidencias/C1/P14/01-pedido-ajeno.jpg) [02](../Backend/docs/evidencias/C1/P14/red.json) [03](../Backend/docs/evidencias/C1/P14/persistencia.json) [04](../Backend/docs/evidencias/C1/P14/logs.txt) | pedido ORD-30400C33 |  |
| RUN-C1-P15 | P15 Mis pedidos con inventory detenido | CA15 | **aprobada** | 17:36:51 | 19.7 s | [01](../Backend/docs/evidencias/C1/P15/01-incompleto.jpg) [02](../Backend/docs/evidencias/C1/P15/02-completo.jpg) [03](../Backend/docs/evidencias/C1/P15/red.json) [04](../Backend/docs/evidencias/C1/P15/logs.txt) | X-Request-ID 96021b8da368 |  |
| RUN-C1-P16 | P16 Permisos de campos y límites de GraphQL | CA16 | **aprobada** | 17:37:11 | 0.5 s | [01](../Backend/docs/evidencias/C1/P16/red.json) [02](../Backend/docs/evidencias/C1/P16/logs.txt) | X-Request-ID ef237449f753 |  |
| RUN-C1-P17 | P17 Editar mi ficha | CA17 | **aprobada** | 17:37:12 | 2.8 s | [01](../Backend/docs/evidencias/C1/P17/01-ficha.jpg) [02](../Backend/docs/evidencias/C1/P17/red.json) [03](../Backend/docs/evidencias/C1/P17/persistencia.json) [04](../Backend/docs/evidencias/C1/P17/logs.txt) | X-Request-ID a1b205225179 |  |
| RUN-C1-P18 | P18 RUN inválido en la ficha | CA18 | **aprobada** | 17:37:15 | 3.5 s | [01](../Backend/docs/evidencias/C1/P18/01-run-invalido.jpg) [02](../Backend/docs/evidencias/C1/P18/red.json) [03](../Backend/docs/evidencias/C1/P18/persistencia.json) [04](../Backend/docs/evidencias/C1/P18/logs.txt) | X-Request-ID 94d17d55cd71 |  |
| RUN-C1-P19 | P19 Sesión expirada | CA19 | **aprobada** | 17:37:19 | 5.0 s | [01](../Backend/docs/evidencias/C1/P19/01-sesion-expirada.jpg) [02](../Backend/docs/evidencias/C1/P19/red.json) [03](../Backend/docs/evidencias/C1/P19/persistencia.json) [04](../Backend/docs/evidencias/C1/P19/logs.txt) | X-Request-ID e4bac8a8e540 | Sesiones vencidas de USR-003: 5 |
| RUN-C1-P20 | P20 Página protegida sin sesión | CA20 | **aprobada** | 17:37:24 | 0.4 s | [01](../Backend/docs/evidencias/C1/P20/01-sin-sesion.jpg) [02](../Backend/docs/evidencias/C1/P20/red.json) [03](../Backend/docs/evidencias/C1/P20/logs.txt) | X-Request-ID 204f58465614 |  |
| RUN-C1-P21 | P21 Login fallido, login y cierre de sesión | CA21 | **aprobada** | 17:37:24 | 1.0 s | [01](../Backend/docs/evidencias/C1/P21/01-cerro-sesion.jpg) [02](../Backend/docs/evidencias/C1/P21/red.json) [03](../Backend/docs/evidencias/C1/P21/logs.txt) | X-Request-ID 072cc5146a58 |  |
| RUN-C1-P22 | P22 Registro con verificación de correo | CA22 | **aprobada** | 17:37:26 | 6.6 s | [01](../Backend/docs/evidencias/C1/P22/01-paso-2.jpg) [02](../Backend/docs/evidencias/C1/P22/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C1/P22/red.json) [04](../Backend/docs/evidencias/C1/P22/persistencia.json) [05](../Backend/docs/evidencias/C1/P22/logs.txt) | correo camila.c1.1795887446112@correo.cl |  |
| RUN-C1-P23 | P23 Inventario del dueño: oferta, alta y baja | CA23 | **aprobada** | 17:37:32 | 4.1 s | [01](../Backend/docs/evidencias/C1/P23/01-inventario.jpg) [02](../Backend/docs/evidencias/C1/P23/02-carta.jpg) [03](../Backend/docs/evidencias/C1/P23/red.json) [04](../Backend/docs/evidencias/C1/P23/persistencia.json) [05](../Backend/docs/evidencias/C1/P23/logs.txt) | X-Request-ID ba0ee9e20379 |  |
| RUN-C1-P24 | P24 Rol sin permiso | CA24 | **aprobada** | 17:37:37 | 1.1 s | [01](../Backend/docs/evidencias/C1/P24/01-inventario-403.jpg) [02](../Backend/docs/evidencias/C1/P24/02-despacho-403.jpg) [03](../Backend/docs/evidencias/C1/P24/red.json) [04](../Backend/docs/evidencias/C1/P24/logs.txt) | X-Request-ID 8b056f65b475 |  |
| RUN-C1-P25 | P25 Despacho avanza el pedido pagado | CA25 | **aprobada** | 17:37:38 | 2.5 s | [01](../Backend/docs/evidencias/C1/P25/01-listo.jpg) [02](../Backend/docs/evidencias/C1/P25/red.json) [03](../Backend/docs/evidencias/C1/P25/persistencia.json) [04](../Backend/docs/evidencias/C1/P25/logs.txt) | pedido ORD-30400C33 |  |
| RUN-C1-P26 | P26 Ventas de la caja web | CA26 | **aprobada** | 17:37:41 | 2.2 s | [01](../Backend/docs/evidencias/C1/P26/01-ventas.jpg) [02](../Backend/docs/evidencias/C1/P26/red.json) [03](../Backend/docs/evidencias/C1/P26/persistencia.json) [04](../Backend/docs/evidencias/C1/P26/logs.txt) | X-Request-ID 68f5e0b3c1b6 |  |
| RUN-C1-P27 | P27 Reporte de ventas actualizado | CA27 | **aprobada** | 17:37:43 | 4.9 s | [01](../Backend/docs/evidencias/C1/P27/01-reporte.jpg) [02](../Backend/docs/evidencias/C1/P27/red.json) [03](../Backend/docs/evidencias/C1/P27/persistencia.json) [04](../Backend/docs/evidencias/C1/P27/logs.txt) | pedido ORD-B90E4D58 |  |
| RUN-C1-P28 | P28 Analítica detenida y recuperación | CA28 | **aprobada** | 17:37:48 | 40.0 s | [01](../Backend/docs/evidencias/C1/P28/01-analitica-detenida.jpg) [02](../Backend/docs/evidencias/C1/P28/02-recuperado.jpg) [03](../Backend/docs/evidencias/C1/P28/red.json) [04](../Backend/docs/evidencias/C1/P28/persistencia.json) [05](../Backend/docs/evidencias/C1/P28/logs.txt) | pedido ORD-42B1484B | La venta llegó a analítica 14 s después de iniciarla (orders reintenta cada 30 s) |
| RUN-C1-P29 | P29 Administración de usuarios y clientes | CA29 | **aprobada** | 17:38:28 | 3.2 s | [01](../Backend/docs/evidencias/C1/P29/01-administracion.jpg) [02](../Backend/docs/evidencias/C1/P29/red.json) [03](../Backend/docs/evidencias/C1/P29/persistencia.json) [04](../Backend/docs/evidencias/C1/P29/logs.txt) | X-Request-ID eaf67e24aea7 |  |
| RUN-C1-P30 | P30 Formulario de contacto | CA30 | **aprobada** | 17:38:32 | 2.4 s | [01](../Backend/docs/evidencias/C1/P30/01-contacto.jpg) [02](../Backend/docs/evidencias/C1/P30/red.json) [03](../Backend/docs/evidencias/C1/P30/persistencia.json) [04](../Backend/docs/evidencias/C1/P30/logs.txt) | X-Request-ID 8c8e6d9bfd1e |  |
| RUN-C1-P31 | P31 Servicio llamado sin el secreto del gateway | CA31 | **aprobada** | 17:38:34 | 0.2 s | [01](../Backend/docs/evidencias/C1/P31/salida.txt) [02](../Backend/docs/evidencias/C1/P31/red.json) [03](../Backend/docs/evidencias/C1/P31/logs.txt) |  |  |
| RUN-C1-P32 | P32 Páginas sin desborde horizontal | CA32 | **aprobada** | 17:38:35 | 4.4 s | [01](../Backend/docs/evidencias/C1/P32/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C1/P32/red.json) [03](../Backend/docs/evidencias/C1/P32/logs.txt) | X-Request-ID 19bdcd98cfc8 | Viewport 1366x768 |
| RUN-C2-P01 | P01 La carta se arma con los productos de la API | CA01 | **aprobada** | 17:39:07 | 2.4 s | [01](../Backend/docs/evidencias/C2/P01/01-carta.jpg) [02](../Backend/docs/evidencias/C2/P01/red.json) [03](../Backend/docs/evidencias/C2/P01/persistencia.json) [04](../Backend/docs/evidencias/C2/P01/logs.txt) | X-Request-ID bfe8670d18ca |  |
| RUN-C2-P02 | P02 Carta con inventory detenido y recuperación | CA02 | **aprobada** | 17:39:10 | 19.0 s | [01](../Backend/docs/evidencias/C2/P02/01-inventory-detenido.jpg) [02](../Backend/docs/evidencias/C2/P02/02-recuperado.jpg) [03](../Backend/docs/evidencias/C2/P02/red.json) [04](../Backend/docs/evidencias/C2/P02/logs.txt) | X-Request-ID 2db184f02926 |  |
| RUN-C2-P03 | P03 Crear un pedido de retiro desde el carrito | CA03 | **aprobada** | 17:39:29 | 10.8 s | [01](../Backend/docs/evidencias/C2/P03/01-pedido-creado.jpg) [02](../Backend/docs/evidencias/C2/P03/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C2/P03/red.json) [04](../Backend/docs/evidencias/C2/P03/persistencia.json) [05](../Backend/docs/evidencias/C2/P03/logs.txt) | pedido ORD-85DB18DC |  |
| RUN-C2-P04 | P04 Confirmar pedido sin sesión | CA04 | **aprobada** | 17:39:40 | 3.7 s | [01](../Backend/docs/evidencias/C2/P04/01-login.jpg) [02](../Backend/docs/evidencias/C2/P04/red.json) [03](../Backend/docs/evidencias/C2/P04/persistencia.json) [04](../Backend/docs/evidencias/C2/P04/logs.txt) | X-Request-ID dbebe4ee7f5c |  |
| RUN-C2-P05 | P05 Despacho fuera del radio de 3 km | CA05 | **aprobada** | 17:39:44 | 6.6 s | [01](../Backend/docs/evidencias/C2/P05/01-fuera-radio.jpg) [02](../Backend/docs/evidencias/C2/P05/red.json) [03](../Backend/docs/evidencias/C2/P05/persistencia.json) [04](../Backend/docs/evidencias/C2/P05/logs.txt) | X-Request-ID 6201bf15dd08 |  |
| RUN-C2-P06 | P06 Pedido con más cantidad que el stock | CA06 | **aprobada** | 17:39:51 | 10.4 s | [01](../Backend/docs/evidencias/C2/P06/01-sin-stock.jpg) [02](../Backend/docs/evidencias/C2/P06/red.json) [03](../Backend/docs/evidencias/C2/P06/persistencia.json) [04](../Backend/docs/evidencias/C2/P06/logs.txt) | X-Request-ID c8fac162673c |  |
| RUN-C2-P07 | P07 Reintento del mismo pedido (doble envío) | CA07 | **aprobada** | 17:40:01 | 6.1 s | [01](../Backend/docs/evidencias/C2/P07/red.json) [02](../Backend/docs/evidencias/C2/P07/persistencia.json) [03](../Backend/docs/evidencias/C2/P07/logs.txt) | pedido ORD-FEEC9246; clave PRUEBA-C2-1795887603548 |  |
| RUN-C2-P08 | P08 Crear pedido con inventory demorado (gRPC) | CA08 | **aprobada** | 17:40:08 | 10.5 s | [01](../Backend/docs/evidencias/C2/P08/01-inventory-en-pausa.jpg) [02](../Backend/docs/evidencias/C2/P08/02-recuperado.jpg) [03](../Backend/docs/evidencias/C2/P08/red.json) [04](../Backend/docs/evidencias/C2/P08/persistencia.json) [05](../Backend/docs/evidencias/C2/P08/logs.txt) | pedido ORD-697C1C21 | El primer intento tardó 3361 ms (plazo de gRPC: 3 s) |
| RUN-C2-P09 | P09 Pagar con el proveedor simulado y obtener la boleta | CA09 | **aprobada** | 17:40:18 | 8.6 s | [01](../Backend/docs/evidencias/C2/P09/01-pasarela.jpg) [02](../Backend/docs/evidencias/C2/P09/02-boleta.jpg) [03](../Backend/docs/evidencias/C2/P09/red.json) [04](../Backend/docs/evidencias/C2/P09/persistencia.json) [05](../Backend/docs/evidencias/C2/P09/logs.txt) | pedido ORD-85DB18DC |  |
| RUN-C2-P10 | P10 Pago rechazado por el proveedor y nuevo intento | CA10 | **aprobada** | 17:40:27 | 5.3 s | [01](../Backend/docs/evidencias/C2/P10/01-rechazado.jpg) [02](../Backend/docs/evidencias/C2/P10/02-aprobado.jpg) [03](../Backend/docs/evidencias/C2/P10/red.json) [04](../Backend/docs/evidencias/C2/P10/persistencia.json) [05](../Backend/docs/evidencias/C2/P10/logs.txt) | pedido ORD-697C1C21 |  |
| RUN-C2-P11 | P11 Aviso de pago repetido por el proveedor | CA11 | **aprobada** | 17:40:33 | 5.2 s | [01](../Backend/docs/evidencias/C2/P11/01-pagado-una-vez.jpg) [02](../Backend/docs/evidencias/C2/P11/red.json) [03](../Backend/docs/evidencias/C2/P11/persistencia.json) [04](../Backend/docs/evidencias/C2/P11/logs.txt) | pedido ORD-488151CA |  |
| RUN-C2-P12 | P12 Anular un pedido pendiente con motivo | CA12 | **aprobada** | 17:40:38 | 10.4 s | [01](../Backend/docs/evidencias/C2/P12/01-anulado.jpg) [02](../Backend/docs/evidencias/C2/P12/red.json) [03](../Backend/docs/evidencias/C2/P12/persistencia.json) [04](../Backend/docs/evidencias/C2/P12/logs.txt) | pedido ORD-E79C9D72 |  |
| RUN-C2-P13 | P13 Mis pedidos agrega orders, inventory y payments | CA13 | **aprobada** | 17:40:48 | 3.3 s | [01](../Backend/docs/evidencias/C2/P13/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C2/P13/red.json) [03](../Backend/docs/evidencias/C2/P13/persistencia.json) [04](../Backend/docs/evidencias/C2/P13/logs.txt) | X-Request-ID 246cb7f44a96 |  |
| RUN-C2-P14 | P14 Pedido ajeno | CA14 | **aprobada** | 17:40:52 | 3.6 s | [01](../Backend/docs/evidencias/C2/P14/01-pedido-ajeno.jpg) [02](../Backend/docs/evidencias/C2/P14/red.json) [03](../Backend/docs/evidencias/C2/P14/persistencia.json) [04](../Backend/docs/evidencias/C2/P14/logs.txt) | pedido ORD-85DB18DC |  |
| RUN-C2-P15 | P15 Mis pedidos con inventory detenido | CA15 | **aprobada** | 17:40:56 | 19.9 s | [01](../Backend/docs/evidencias/C2/P15/01-incompleto.jpg) [02](../Backend/docs/evidencias/C2/P15/02-completo.jpg) [03](../Backend/docs/evidencias/C2/P15/red.json) [04](../Backend/docs/evidencias/C2/P15/logs.txt) | X-Request-ID 4d754d121a72 |  |
| RUN-C2-P16 | P16 Permisos de campos y límites de GraphQL | CA16 | **aprobada** | 17:41:16 | 0.5 s | [01](../Backend/docs/evidencias/C2/P16/red.json) [02](../Backend/docs/evidencias/C2/P16/logs.txt) | X-Request-ID a65867ec2994 |  |
| RUN-C2-P17 | P17 Editar mi ficha | CA17 | **aprobada** | 17:41:17 | 3.0 s | [01](../Backend/docs/evidencias/C2/P17/01-ficha.jpg) [02](../Backend/docs/evidencias/C2/P17/red.json) [03](../Backend/docs/evidencias/C2/P17/persistencia.json) [04](../Backend/docs/evidencias/C2/P17/logs.txt) | X-Request-ID a5cac3cb6b9e |  |
| RUN-C2-P18 | P18 RUN inválido en la ficha | CA18 | **aprobada** | 17:41:20 | 3.3 s | [01](../Backend/docs/evidencias/C2/P18/01-run-invalido.jpg) [02](../Backend/docs/evidencias/C2/P18/red.json) [03](../Backend/docs/evidencias/C2/P18/persistencia.json) [04](../Backend/docs/evidencias/C2/P18/logs.txt) | X-Request-ID ec371092bf0a |  |
| RUN-C2-P19 | P19 Sesión expirada | CA19 | **aprobada** | 17:41:23 | 4.9 s | [01](../Backend/docs/evidencias/C2/P19/01-sesion-expirada.jpg) [02](../Backend/docs/evidencias/C2/P19/red.json) [03](../Backend/docs/evidencias/C2/P19/persistencia.json) [04](../Backend/docs/evidencias/C2/P19/logs.txt) | X-Request-ID 24554cbfd131 | Sesiones vencidas de USR-003: 5 |
| RUN-C2-P20 | P20 Página protegida sin sesión | CA20 | **aprobada** | 17:41:28 | 0.4 s | [01](../Backend/docs/evidencias/C2/P20/01-sin-sesion.jpg) [02](../Backend/docs/evidencias/C2/P20/red.json) [03](../Backend/docs/evidencias/C2/P20/logs.txt) | X-Request-ID f814b87f30d3 |  |
| RUN-C2-P21 | P21 Login fallido, login y cierre de sesión | CA21 | **aprobada** | 17:41:29 | 1.3 s | [01](../Backend/docs/evidencias/C2/P21/01-cerro-sesion.jpg) [02](../Backend/docs/evidencias/C2/P21/red.json) [03](../Backend/docs/evidencias/C2/P21/logs.txt) | X-Request-ID 96d84badf1a7 |  |
| RUN-C2-P22 | P22 Registro con verificación de correo | CA22 | **aprobada** | 17:41:30 | 6.4 s | [01](../Backend/docs/evidencias/C2/P22/01-paso-2.jpg) [02](../Backend/docs/evidencias/C2/P22/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C2/P22/red.json) [04](../Backend/docs/evidencias/C2/P22/persistencia.json) [05](../Backend/docs/evidencias/C2/P22/logs.txt) | correo camila.c2.1795887690971@correo.cl |  |
| RUN-C2-P23 | P23 Inventario del dueño: oferta, alta y baja | CA23 | **aprobada** | 17:41:37 | 8.1 s | [01](../Backend/docs/evidencias/C2/P23/01-inventario.jpg) [02](../Backend/docs/evidencias/C2/P23/02-carta.jpg) [03](../Backend/docs/evidencias/C2/P23/red.json) [04](../Backend/docs/evidencias/C2/P23/persistencia.json) [05](../Backend/docs/evidencias/C2/P23/logs.txt) | X-Request-ID a14f1c8f2a38 |  |
| RUN-C2-P24 | P24 Rol sin permiso | CA24 | **aprobada** | 17:41:45 | 1.2 s | [01](../Backend/docs/evidencias/C2/P24/01-inventario-403.jpg) [02](../Backend/docs/evidencias/C2/P24/02-despacho-403.jpg) [03](../Backend/docs/evidencias/C2/P24/red.json) [04](../Backend/docs/evidencias/C2/P24/logs.txt) | X-Request-ID 33264e890e15 |  |
| RUN-C2-P25 | P25 Despacho avanza el pedido pagado | CA25 | **aprobada** | 17:41:47 | 2.5 s | [01](../Backend/docs/evidencias/C2/P25/01-listo.jpg) [02](../Backend/docs/evidencias/C2/P25/red.json) [03](../Backend/docs/evidencias/C2/P25/persistencia.json) [04](../Backend/docs/evidencias/C2/P25/logs.txt) | pedido ORD-85DB18DC |  |
| RUN-C2-P26 | P26 Ventas de la caja web | CA26 | **aprobada** | 17:41:49 | 2.5 s | [01](../Backend/docs/evidencias/C2/P26/01-ventas.jpg) [02](../Backend/docs/evidencias/C2/P26/red.json) [03](../Backend/docs/evidencias/C2/P26/persistencia.json) [04](../Backend/docs/evidencias/C2/P26/logs.txt) | X-Request-ID 16fce5ef3270 |  |
| RUN-C2-P27 | P27 Reporte de ventas actualizado | CA27 | **aprobada** | 17:41:52 | 6.2 s | [01](../Backend/docs/evidencias/C2/P27/01-reporte.jpg) [02](../Backend/docs/evidencias/C2/P27/red.json) [03](../Backend/docs/evidencias/C2/P27/persistencia.json) [04](../Backend/docs/evidencias/C2/P27/logs.txt) | pedido ORD-C7D5DD46 |  |
| RUN-C2-P28 | P28 Analítica detenida y recuperación | CA28 | **aprobada** | 17:41:58 | 40.3 s | [01](../Backend/docs/evidencias/C2/P28/01-analitica-detenida.jpg) [02](../Backend/docs/evidencias/C2/P28/02-recuperado.jpg) [03](../Backend/docs/evidencias/C2/P28/red.json) [04](../Backend/docs/evidencias/C2/P28/persistencia.json) [05](../Backend/docs/evidencias/C2/P28/logs.txt) | pedido ORD-8676B646 | La venta llegó a analítica 14 s después de iniciarla (orders reintenta cada 30 s) |
| RUN-C2-P29 | P29 Administración de usuarios y clientes | CA29 | **aprobada** | 17:42:39 | 3.2 s | [01](../Backend/docs/evidencias/C2/P29/01-administracion.jpg) [02](../Backend/docs/evidencias/C2/P29/red.json) [03](../Backend/docs/evidencias/C2/P29/persistencia.json) [04](../Backend/docs/evidencias/C2/P29/logs.txt) | X-Request-ID ae614b53474d |  |
| RUN-C2-P30 | P30 Formulario de contacto | CA30 | **aprobada** | 17:42:42 | 2.2 s | [01](../Backend/docs/evidencias/C2/P30/01-contacto.jpg) [02](../Backend/docs/evidencias/C2/P30/red.json) [03](../Backend/docs/evidencias/C2/P30/persistencia.json) [04](../Backend/docs/evidencias/C2/P30/logs.txt) | X-Request-ID 45d88143f445 |  |
| RUN-C2-P31 | P31 Servicio llamado sin el secreto del gateway | CA31 | **aprobada** | 17:42:45 | 0.2 s | [01](../Backend/docs/evidencias/C2/P31/salida.txt) [02](../Backend/docs/evidencias/C2/P31/red.json) [03](../Backend/docs/evidencias/C2/P31/logs.txt) |  |  |
| RUN-C2-P32 | P32 Páginas sin desborde horizontal | CA32 | **aprobada** | 17:42:45 | 4.3 s | [01](../Backend/docs/evidencias/C2/P32/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C2/P32/red.json) [03](../Backend/docs/evidencias/C2/P32/logs.txt) | X-Request-ID c7582124e2ba | Viewport 412x839 (Pixel 7, emulado) |
| RUN-C3-P01 | P01 La carta se arma con los productos de la API | CA01 | **aprobada** | 17:43:34 | 2.4 s | [01](../Backend/docs/evidencias/C3/P01/01-carta.jpg) [02](../Backend/docs/evidencias/C3/P01/red.json) [03](../Backend/docs/evidencias/C3/P01/persistencia.json) [04](../Backend/docs/evidencias/C3/P01/logs.txt) | X-Request-ID 15348c992974 |  |
| RUN-C3-P02 | P02 Carta con inventory detenido y recuperación | CA02 | **aprobada** | 17:43:36 | 19.2 s | [01](../Backend/docs/evidencias/C3/P02/01-inventory-detenido.jpg) [02](../Backend/docs/evidencias/C3/P02/02-recuperado.jpg) [03](../Backend/docs/evidencias/C3/P02/red.json) [04](../Backend/docs/evidencias/C3/P02/logs.txt) | X-Request-ID 4050773b9b5f |  |
| RUN-C3-P03 | P03 Crear un pedido de retiro desde el carrito | CA03 | **aprobada** | 17:43:56 | 10.5 s | [01](../Backend/docs/evidencias/C3/P03/01-pedido-creado.jpg) [02](../Backend/docs/evidencias/C3/P03/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C3/P03/red.json) [04](../Backend/docs/evidencias/C3/P03/persistencia.json) [05](../Backend/docs/evidencias/C3/P03/logs.txt) | pedido ORD-752AD31F |  |
| RUN-C3-P04 | P04 Confirmar pedido sin sesión | CA04 | **aprobada** | 17:44:06 | 3.6 s | [01](../Backend/docs/evidencias/C3/P04/01-login.jpg) [02](../Backend/docs/evidencias/C3/P04/red.json) [03](../Backend/docs/evidencias/C3/P04/persistencia.json) [04](../Backend/docs/evidencias/C3/P04/logs.txt) | X-Request-ID 2677ca9fe5c8 |  |
| RUN-C3-P05 | P05 Despacho fuera del radio de 3 km | CA05 | **aprobada** | 17:44:10 | 6.7 s | [01](../Backend/docs/evidencias/C3/P05/01-fuera-radio.jpg) [02](../Backend/docs/evidencias/C3/P05/red.json) [03](../Backend/docs/evidencias/C3/P05/persistencia.json) [04](../Backend/docs/evidencias/C3/P05/logs.txt) | X-Request-ID dae2ee7bed93 |  |
| RUN-C3-P06 | P06 Pedido con más cantidad que el stock | CA06 | **aprobada** | 17:44:17 | 10.1 s | [01](../Backend/docs/evidencias/C3/P06/01-sin-stock.jpg) [02](../Backend/docs/evidencias/C3/P06/red.json) [03](../Backend/docs/evidencias/C3/P06/persistencia.json) [04](../Backend/docs/evidencias/C3/P06/logs.txt) | X-Request-ID 91f333704985 |  |
| RUN-C3-P07 | P07 Reintento del mismo pedido (doble envío) | CA07 | **aprobada** | 17:44:27 | 5.9 s | [01](../Backend/docs/evidencias/C3/P07/red.json) [02](../Backend/docs/evidencias/C3/P07/persistencia.json) [03](../Backend/docs/evidencias/C3/P07/logs.txt) | pedido ORD-899665FB; clave PRUEBA-C3-1795887869437 |  |
| RUN-C3-P08 | P08 Crear pedido con inventory demorado (gRPC) | CA08 | **aprobada** | 17:44:33 | 10.3 s | [01](../Backend/docs/evidencias/C3/P08/01-inventory-en-pausa.jpg) [02](../Backend/docs/evidencias/C3/P08/02-recuperado.jpg) [03](../Backend/docs/evidencias/C3/P08/red.json) [04](../Backend/docs/evidencias/C3/P08/persistencia.json) [05](../Backend/docs/evidencias/C3/P08/logs.txt) | pedido ORD-724B33B7 | El primer intento tardó 3365 ms (plazo de gRPC: 3 s) |
| RUN-C3-P09 | P09 Pagar con el proveedor simulado y obtener la boleta | CA09 | **aprobada** | 17:44:44 | 8.4 s | [01](../Backend/docs/evidencias/C3/P09/01-pasarela.jpg) [02](../Backend/docs/evidencias/C3/P09/02-boleta.jpg) [03](../Backend/docs/evidencias/C3/P09/red.json) [04](../Backend/docs/evidencias/C3/P09/persistencia.json) [05](../Backend/docs/evidencias/C3/P09/logs.txt) | pedido ORD-752AD31F |  |
| RUN-C3-P10 | P10 Pago rechazado por el proveedor y nuevo intento | CA10 | **aprobada** | 17:44:52 | 5.1 s | [01](../Backend/docs/evidencias/C3/P10/01-rechazado.jpg) [02](../Backend/docs/evidencias/C3/P10/02-aprobado.jpg) [03](../Backend/docs/evidencias/C3/P10/red.json) [04](../Backend/docs/evidencias/C3/P10/persistencia.json) [05](../Backend/docs/evidencias/C3/P10/logs.txt) | pedido ORD-724B33B7 |  |
| RUN-C3-P11 | P11 Aviso de pago repetido por el proveedor | CA11 | **aprobada** | 17:44:58 | 5.1 s | [01](../Backend/docs/evidencias/C3/P11/01-pagado-una-vez.jpg) [02](../Backend/docs/evidencias/C3/P11/red.json) [03](../Backend/docs/evidencias/C3/P11/persistencia.json) [04](../Backend/docs/evidencias/C3/P11/logs.txt) | pedido ORD-0C911072 |  |
| RUN-C3-P12 | P12 Anular un pedido pendiente con motivo | CA12 | **aprobada** | 17:45:03 | 11.0 s | [01](../Backend/docs/evidencias/C3/P12/01-anulado.jpg) [02](../Backend/docs/evidencias/C3/P12/red.json) [03](../Backend/docs/evidencias/C3/P12/persistencia.json) [04](../Backend/docs/evidencias/C3/P12/logs.txt) | pedido ORD-D42CA98C |  |
| RUN-C3-P13 | P13 Mis pedidos agrega orders, inventory y payments | CA13 | **aprobada** | 17:45:14 | 3.4 s | [01](../Backend/docs/evidencias/C3/P13/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C3/P13/red.json) [03](../Backend/docs/evidencias/C3/P13/persistencia.json) [04](../Backend/docs/evidencias/C3/P13/logs.txt) | X-Request-ID 860b17aeac8a |  |
| RUN-C3-P14 | P14 Pedido ajeno | CA14 | **aprobada** | 17:45:18 | 3.5 s | [01](../Backend/docs/evidencias/C3/P14/01-pedido-ajeno.jpg) [02](../Backend/docs/evidencias/C3/P14/red.json) [03](../Backend/docs/evidencias/C3/P14/persistencia.json) [04](../Backend/docs/evidencias/C3/P14/logs.txt) | pedido ORD-752AD31F |  |
| RUN-C3-P15 | P15 Mis pedidos con inventory detenido | CA15 | **aprobada** | 17:45:21 | 19.7 s | [01](../Backend/docs/evidencias/C3/P15/01-incompleto.jpg) [02](../Backend/docs/evidencias/C3/P15/02-completo.jpg) [03](../Backend/docs/evidencias/C3/P15/red.json) [04](../Backend/docs/evidencias/C3/P15/logs.txt) | X-Request-ID a10d3e9539c4 |  |
| RUN-C3-P16 | P16 Permisos de campos y límites de GraphQL | CA16 | **aprobada** | 17:45:41 | 0.4 s | [01](../Backend/docs/evidencias/C3/P16/red.json) [02](../Backend/docs/evidencias/C3/P16/logs.txt) | X-Request-ID af49a0d4af36 |  |
| RUN-C3-P17 | P17 Editar mi ficha | CA17 | **aprobada** | 17:45:42 | 3.2 s | [01](../Backend/docs/evidencias/C3/P17/01-ficha.jpg) [02](../Backend/docs/evidencias/C3/P17/red.json) [03](../Backend/docs/evidencias/C3/P17/persistencia.json) [04](../Backend/docs/evidencias/C3/P17/logs.txt) | X-Request-ID 13826be73add |  |
| RUN-C3-P18 | P18 RUN inválido en la ficha | CA18 | **aprobada** | 17:45:45 | 3.2 s | [01](../Backend/docs/evidencias/C3/P18/01-run-invalido.jpg) [02](../Backend/docs/evidencias/C3/P18/red.json) [03](../Backend/docs/evidencias/C3/P18/persistencia.json) [04](../Backend/docs/evidencias/C3/P18/logs.txt) | X-Request-ID af9cd2cd0151 |  |
| RUN-C3-P19 | P19 Sesión expirada | CA19 | **aprobada** | 17:45:49 | 4.9 s | [01](../Backend/docs/evidencias/C3/P19/01-sesion-expirada.jpg) [02](../Backend/docs/evidencias/C3/P19/red.json) [03](../Backend/docs/evidencias/C3/P19/persistencia.json) [04](../Backend/docs/evidencias/C3/P19/logs.txt) | X-Request-ID 97d3dddd26be | Sesiones vencidas de USR-003: 5 |
| RUN-C3-P20 | P20 Página protegida sin sesión | CA20 | **aprobada** | 17:45:54 | 0.4 s | [01](../Backend/docs/evidencias/C3/P20/01-sin-sesion.jpg) [02](../Backend/docs/evidencias/C3/P20/red.json) [03](../Backend/docs/evidencias/C3/P20/logs.txt) | X-Request-ID 9929204f57a2 |  |
| RUN-C3-P21 | P21 Login fallido, login y cierre de sesión | CA21 | **aprobada** | 17:45:55 | 1.1 s | [01](../Backend/docs/evidencias/C3/P21/01-cerro-sesion.jpg) [02](../Backend/docs/evidencias/C3/P21/red.json) [03](../Backend/docs/evidencias/C3/P21/logs.txt) | X-Request-ID ff0c5637076c |  |
| RUN-C3-P22 | P22 Registro con verificación de correo | CA22 | **aprobada** | 17:45:56 | 6.7 s | [01](../Backend/docs/evidencias/C3/P22/01-paso-2.jpg) [02](../Backend/docs/evidencias/C3/P22/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C3/P22/red.json) [04](../Backend/docs/evidencias/C3/P22/persistencia.json) [05](../Backend/docs/evidencias/C3/P22/logs.txt) | correo camila.c3.1795887956315@correo.cl |  |
| RUN-C3-P23 | P23 Inventario del dueño: oferta, alta y baja | CA23 | **aprobada** | 17:46:03 | 4.0 s | [01](../Backend/docs/evidencias/C3/P23/01-inventario.jpg) [02](../Backend/docs/evidencias/C3/P23/02-carta.jpg) [03](../Backend/docs/evidencias/C3/P23/red.json) [04](../Backend/docs/evidencias/C3/P23/persistencia.json) [05](../Backend/docs/evidencias/C3/P23/logs.txt) | X-Request-ID 4efa878fc7ac |  |
| RUN-C3-P24 | P24 Rol sin permiso | CA24 | **aprobada** | 17:46:07 | 0.8 s | [01](../Backend/docs/evidencias/C3/P24/01-inventario-403.jpg) [02](../Backend/docs/evidencias/C3/P24/02-despacho-403.jpg) [03](../Backend/docs/evidencias/C3/P24/red.json) [04](../Backend/docs/evidencias/C3/P24/logs.txt) | X-Request-ID 2e3e1d6e3652 |  |
| RUN-C3-P25 | P25 Despacho avanza el pedido pagado | CA25 | **aprobada** | 17:46:08 | 2.4 s | [01](../Backend/docs/evidencias/C3/P25/01-listo.jpg) [02](../Backend/docs/evidencias/C3/P25/red.json) [03](../Backend/docs/evidencias/C3/P25/persistencia.json) [04](../Backend/docs/evidencias/C3/P25/logs.txt) | pedido ORD-752AD31F |  |
| RUN-C3-P26 | P26 Ventas de la caja web | CA26 | **aprobada** | 17:46:10 | 2.1 s | [01](../Backend/docs/evidencias/C3/P26/01-ventas.jpg) [02](../Backend/docs/evidencias/C3/P26/red.json) [03](../Backend/docs/evidencias/C3/P26/persistencia.json) [04](../Backend/docs/evidencias/C3/P26/logs.txt) | X-Request-ID b88df893b762 |  |
| RUN-C3-P27 | P27 Reporte de ventas actualizado | CA27 | **aprobada** | 17:46:13 | 4.7 s | [01](../Backend/docs/evidencias/C3/P27/01-reporte.jpg) [02](../Backend/docs/evidencias/C3/P27/red.json) [03](../Backend/docs/evidencias/C3/P27/persistencia.json) [04](../Backend/docs/evidencias/C3/P27/logs.txt) | pedido ORD-E87AB715 |  |
| RUN-C3-P28 | P28 Analítica detenida y recuperación | CA28 | **aprobada** | 17:46:18 | 46.3 s | [01](../Backend/docs/evidencias/C3/P28/01-analitica-detenida.jpg) [02](../Backend/docs/evidencias/C3/P28/02-recuperado.jpg) [03](../Backend/docs/evidencias/C3/P28/red.json) [04](../Backend/docs/evidencias/C3/P28/persistencia.json) [05](../Backend/docs/evidencias/C3/P28/logs.txt) | pedido ORD-B29ED291 | La venta llegó a analítica 21 s después de iniciarla (orders reintenta cada 30 s) |
| RUN-C3-P29 | P29 Administración de usuarios y clientes | CA29 | **aprobada** | 17:47:04 | 3.4 s | [01](../Backend/docs/evidencias/C3/P29/01-administracion.jpg) [02](../Backend/docs/evidencias/C3/P29/red.json) [03](../Backend/docs/evidencias/C3/P29/persistencia.json) [04](../Backend/docs/evidencias/C3/P29/logs.txt) | X-Request-ID ab066dcb8b6b |  |
| RUN-C3-P30 | P30 Formulario de contacto | CA30 | **aprobada** | 17:47:08 | 2.3 s | [01](../Backend/docs/evidencias/C3/P30/01-contacto.jpg) [02](../Backend/docs/evidencias/C3/P30/red.json) [03](../Backend/docs/evidencias/C3/P30/persistencia.json) [04](../Backend/docs/evidencias/C3/P30/logs.txt) | X-Request-ID 50c507678b4b |  |
| RUN-C3-P31 | P31 Servicio llamado sin el secreto del gateway | CA31 | **aprobada** | 17:47:10 | 0.3 s | [01](../Backend/docs/evidencias/C3/P31/salida.txt) [02](../Backend/docs/evidencias/C3/P31/red.json) [03](../Backend/docs/evidencias/C3/P31/logs.txt) |  |  |
| RUN-C3-P32 | P32 Páginas sin desborde horizontal | CA32 | **aprobada** | 17:47:11 | 4.4 s | [01](../Backend/docs/evidencias/C3/P32/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C3/P32/red.json) [03](../Backend/docs/evidencias/C3/P32/logs.txt) | X-Request-ID f4e4abc11026 | Viewport 1366x768 |
| RUN-C4-P01 | P01 La carta se arma con los productos de la API | CA01 | **aprobada** | 17:47:44 | 2.6 s | [01](../Backend/docs/evidencias/C4/P01/01-carta.jpg) [02](../Backend/docs/evidencias/C4/P01/red.json) [03](../Backend/docs/evidencias/C4/P01/persistencia.json) [04](../Backend/docs/evidencias/C4/P01/logs.txt) | X-Request-ID 58b2559dfefd |  |
| RUN-C4-P02 | P02 Carta con inventory detenido y recuperación | CA02 | **aprobada** | 17:47:47 | 19.2 s | [01](../Backend/docs/evidencias/C4/P02/01-inventory-detenido.jpg) [02](../Backend/docs/evidencias/C4/P02/02-recuperado.jpg) [03](../Backend/docs/evidencias/C4/P02/red.json) [04](../Backend/docs/evidencias/C4/P02/logs.txt) | X-Request-ID 5aff3d1012da |  |
| RUN-C4-P03 | P03 Crear un pedido de retiro desde el carrito | CA03 | **aprobada** | 17:48:06 | 11.2 s | [01](../Backend/docs/evidencias/C4/P03/01-pedido-creado.jpg) [02](../Backend/docs/evidencias/C4/P03/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C4/P03/red.json) [04](../Backend/docs/evidencias/C4/P03/persistencia.json) [05](../Backend/docs/evidencias/C4/P03/logs.txt) | pedido ORD-BF9EE529 |  |
| RUN-C4-P04 | P04 Confirmar pedido sin sesión | CA04 | **aprobada** | 17:48:17 | 3.9 s | [01](../Backend/docs/evidencias/C4/P04/01-login.jpg) [02](../Backend/docs/evidencias/C4/P04/red.json) [03](../Backend/docs/evidencias/C4/P04/persistencia.json) [04](../Backend/docs/evidencias/C4/P04/logs.txt) | X-Request-ID 05facd517b6a |  |
| RUN-C4-P05 | P05 Despacho fuera del radio de 3 km | CA05 | **aprobada** | 17:48:22 | 6.5 s | [01](../Backend/docs/evidencias/C4/P05/01-fuera-radio.jpg) [02](../Backend/docs/evidencias/C4/P05/red.json) [03](../Backend/docs/evidencias/C4/P05/persistencia.json) [04](../Backend/docs/evidencias/C4/P05/logs.txt) | X-Request-ID 77713dbe9b33 |  |
| RUN-C4-P06 | P06 Pedido con más cantidad que el stock | CA06 | **aprobada** | 17:48:28 | 10.5 s | [01](../Backend/docs/evidencias/C4/P06/01-sin-stock.jpg) [02](../Backend/docs/evidencias/C4/P06/red.json) [03](../Backend/docs/evidencias/C4/P06/persistencia.json) [04](../Backend/docs/evidencias/C4/P06/logs.txt) | X-Request-ID 9405c3d3a24e |  |
| RUN-C4-P07 | P07 Reintento del mismo pedido (doble envío) | CA07 | **aprobada** | 17:48:39 | 6.1 s | [01](../Backend/docs/evidencias/C4/P07/red.json) [02](../Backend/docs/evidencias/C4/P07/persistencia.json) [03](../Backend/docs/evidencias/C4/P07/logs.txt) | pedido ORD-0DC89B8F; clave PRUEBA-C4-1795888121263 |  |
| RUN-C4-P08 | P08 Crear pedido con inventory demorado (gRPC) | CA08 | **aprobada** | 17:48:45 | 10.4 s | [01](../Backend/docs/evidencias/C4/P08/01-inventory-en-pausa.jpg) [02](../Backend/docs/evidencias/C4/P08/02-recuperado.jpg) [03](../Backend/docs/evidencias/C4/P08/red.json) [04](../Backend/docs/evidencias/C4/P08/persistencia.json) [05](../Backend/docs/evidencias/C4/P08/logs.txt) | pedido ORD-AA552546 | El primer intento tardó 3354 ms (plazo de gRPC: 3 s) |
| RUN-C4-P09 | P09 Pagar con el proveedor simulado y obtener la boleta | CA09 | **aprobada** | 17:48:56 | 8.7 s | [01](../Backend/docs/evidencias/C4/P09/01-pasarela.jpg) [02](../Backend/docs/evidencias/C4/P09/02-boleta.jpg) [03](../Backend/docs/evidencias/C4/P09/red.json) [04](../Backend/docs/evidencias/C4/P09/persistencia.json) [05](../Backend/docs/evidencias/C4/P09/logs.txt) | pedido ORD-BF9EE529 |  |
| RUN-C4-P10 | P10 Pago rechazado por el proveedor y nuevo intento | CA10 | **aprobada** | 17:49:05 | 5.1 s | [01](../Backend/docs/evidencias/C4/P10/01-rechazado.jpg) [02](../Backend/docs/evidencias/C4/P10/02-aprobado.jpg) [03](../Backend/docs/evidencias/C4/P10/red.json) [04](../Backend/docs/evidencias/C4/P10/persistencia.json) [05](../Backend/docs/evidencias/C4/P10/logs.txt) | pedido ORD-AA552546 |  |
| RUN-C4-P11 | P11 Aviso de pago repetido por el proveedor | CA11 | **aprobada** | 17:49:10 | 5.2 s | [01](../Backend/docs/evidencias/C4/P11/01-pagado-una-vez.jpg) [02](../Backend/docs/evidencias/C4/P11/red.json) [03](../Backend/docs/evidencias/C4/P11/persistencia.json) [04](../Backend/docs/evidencias/C4/P11/logs.txt) | pedido ORD-2A5B3F55 |  |
| RUN-C4-P12 | P12 Anular un pedido pendiente con motivo | CA12 | **aprobada** | 17:49:15 | 10.4 s | [01](../Backend/docs/evidencias/C4/P12/01-anulado.jpg) [02](../Backend/docs/evidencias/C4/P12/red.json) [03](../Backend/docs/evidencias/C4/P12/persistencia.json) [04](../Backend/docs/evidencias/C4/P12/logs.txt) | pedido ORD-EE4EB7FA |  |
| RUN-C4-P13 | P13 Mis pedidos agrega orders, inventory y payments | CA13 | **aprobada** | 17:49:26 | 3.2 s | [01](../Backend/docs/evidencias/C4/P13/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C4/P13/red.json) [03](../Backend/docs/evidencias/C4/P13/persistencia.json) [04](../Backend/docs/evidencias/C4/P13/logs.txt) | X-Request-ID 1ce7d3005644 |  |
| RUN-C4-P14 | P14 Pedido ajeno | CA14 | **aprobada** | 17:49:29 | 3.6 s | [01](../Backend/docs/evidencias/C4/P14/01-pedido-ajeno.jpg) [02](../Backend/docs/evidencias/C4/P14/red.json) [03](../Backend/docs/evidencias/C4/P14/persistencia.json) [04](../Backend/docs/evidencias/C4/P14/logs.txt) | pedido ORD-BF9EE529 |  |
| RUN-C4-P15 | P15 Mis pedidos con inventory detenido | CA15 | **aprobada** | 17:49:33 | 19.7 s | [01](../Backend/docs/evidencias/C4/P15/01-incompleto.jpg) [02](../Backend/docs/evidencias/C4/P15/02-completo.jpg) [03](../Backend/docs/evidencias/C4/P15/red.json) [04](../Backend/docs/evidencias/C4/P15/logs.txt) | X-Request-ID d2a70d4b9e18 |  |
| RUN-C4-P16 | P16 Permisos de campos y límites de GraphQL | CA16 | **aprobada** | 17:49:53 | 0.5 s | [01](../Backend/docs/evidencias/C4/P16/red.json) [02](../Backend/docs/evidencias/C4/P16/logs.txt) | X-Request-ID 843bc1bb19c3 |  |
| RUN-C4-P17 | P17 Editar mi ficha | CA17 | **aprobada** | 17:49:54 | 2.8 s | [01](../Backend/docs/evidencias/C4/P17/01-ficha.jpg) [02](../Backend/docs/evidencias/C4/P17/red.json) [03](../Backend/docs/evidencias/C4/P17/persistencia.json) [04](../Backend/docs/evidencias/C4/P17/logs.txt) | X-Request-ID dd01a28f0f4c |  |
| RUN-C4-P18 | P18 RUN inválido en la ficha | CA18 | **aprobada** | 17:49:57 | 3.4 s | [01](../Backend/docs/evidencias/C4/P18/01-run-invalido.jpg) [02](../Backend/docs/evidencias/C4/P18/red.json) [03](../Backend/docs/evidencias/C4/P18/persistencia.json) [04](../Backend/docs/evidencias/C4/P18/logs.txt) | X-Request-ID 1a98ff1b2c48 |  |
| RUN-C4-P19 | P19 Sesión expirada | CA19 | **aprobada** | 17:50:00 | 5.0 s | [01](../Backend/docs/evidencias/C4/P19/01-sesion-expirada.jpg) [02](../Backend/docs/evidencias/C4/P19/red.json) [03](../Backend/docs/evidencias/C4/P19/persistencia.json) [04](../Backend/docs/evidencias/C4/P19/logs.txt) | X-Request-ID c3ccec695538 | Sesiones vencidas de USR-003: 5 |
| RUN-C4-P20 | P20 Página protegida sin sesión | CA20 | **aprobada** | 17:50:05 | 0.5 s | [01](../Backend/docs/evidencias/C4/P20/01-sin-sesion.jpg) [02](../Backend/docs/evidencias/C4/P20/red.json) [03](../Backend/docs/evidencias/C4/P20/logs.txt) | X-Request-ID a2dbc24d949f |  |
| RUN-C4-P21 | P21 Login fallido, login y cierre de sesión | CA21 | **aprobada** | 17:50:06 | 1.1 s | [01](../Backend/docs/evidencias/C4/P21/01-cerro-sesion.jpg) [02](../Backend/docs/evidencias/C4/P21/red.json) [03](../Backend/docs/evidencias/C4/P21/logs.txt) | X-Request-ID 71c9d784c1e7 |  |
| RUN-C4-P22 | P22 Registro con verificación de correo | CA22 | **aprobada** | 17:50:07 | 6.4 s | [01](../Backend/docs/evidencias/C4/P22/01-paso-2.jpg) [02](../Backend/docs/evidencias/C4/P22/02-sesion-nueva.jpg) [03](../Backend/docs/evidencias/C4/P22/red.json) [04](../Backend/docs/evidencias/C4/P22/persistencia.json) [05](../Backend/docs/evidencias/C4/P22/logs.txt) | correo camila.c4.1795888207897@correo.cl |  |
| RUN-C4-P23 | P23 Inventario del dueño: oferta, alta y baja | CA23 | **aprobada** | 17:50:14 | 8.2 s | [01](../Backend/docs/evidencias/C4/P23/01-inventario.jpg) [02](../Backend/docs/evidencias/C4/P23/02-carta.jpg) [03](../Backend/docs/evidencias/C4/P23/red.json) [04](../Backend/docs/evidencias/C4/P23/persistencia.json) [05](../Backend/docs/evidencias/C4/P23/logs.txt) | X-Request-ID 72737b2dde76 |  |
| RUN-C4-P24 | P24 Rol sin permiso | CA24 | **aprobada** | 17:50:22 | 0.9 s | [01](../Backend/docs/evidencias/C4/P24/01-inventario-403.jpg) [02](../Backend/docs/evidencias/C4/P24/02-despacho-403.jpg) [03](../Backend/docs/evidencias/C4/P24/red.json) [04](../Backend/docs/evidencias/C4/P24/logs.txt) | X-Request-ID 6d723e777d5c |  |
| RUN-C4-P25 | P25 Despacho avanza el pedido pagado | CA25 | **aprobada** | 17:50:23 | 2.5 s | [01](../Backend/docs/evidencias/C4/P25/01-listo.jpg) [02](../Backend/docs/evidencias/C4/P25/red.json) [03](../Backend/docs/evidencias/C4/P25/persistencia.json) [04](../Backend/docs/evidencias/C4/P25/logs.txt) | pedido ORD-BF9EE529 |  |
| RUN-C4-P26 | P26 Ventas de la caja web | CA26 | **aprobada** | 17:50:26 | 2.1 s | [01](../Backend/docs/evidencias/C4/P26/01-ventas.jpg) [02](../Backend/docs/evidencias/C4/P26/red.json) [03](../Backend/docs/evidencias/C4/P26/persistencia.json) [04](../Backend/docs/evidencias/C4/P26/logs.txt) | X-Request-ID 3160f2edeb26 |  |
| RUN-C4-P27 | P27 Reporte de ventas actualizado | CA27 | **aprobada** | 17:50:28 | 6.1 s | [01](../Backend/docs/evidencias/C4/P27/01-reporte.jpg) [02](../Backend/docs/evidencias/C4/P27/red.json) [03](../Backend/docs/evidencias/C4/P27/persistencia.json) [04](../Backend/docs/evidencias/C4/P27/logs.txt) | pedido ORD-167D37DB |  |
| RUN-C4-P28 | P28 Analítica detenida y recuperación | CA28 | **aprobada** | 17:50:35 | 40.3 s | [01](../Backend/docs/evidencias/C4/P28/01-analitica-detenida.jpg) [02](../Backend/docs/evidencias/C4/P28/02-recuperado.jpg) [03](../Backend/docs/evidencias/C4/P28/red.json) [04](../Backend/docs/evidencias/C4/P28/persistencia.json) [05](../Backend/docs/evidencias/C4/P28/logs.txt) | pedido ORD-358A2AFD | La venta llegó a analítica 14 s después de iniciarla (orders reintenta cada 30 s) |
| RUN-C4-P29 | P29 Administración de usuarios y clientes | CA29 | **aprobada** | 17:51:15 | 3.2 s | [01](../Backend/docs/evidencias/C4/P29/01-administracion.jpg) [02](../Backend/docs/evidencias/C4/P29/red.json) [03](../Backend/docs/evidencias/C4/P29/persistencia.json) [04](../Backend/docs/evidencias/C4/P29/logs.txt) | X-Request-ID 69da6a07b26d |  |
| RUN-C4-P30 | P30 Formulario de contacto | CA30 | **aprobada** | 17:51:19 | 2.4 s | [01](../Backend/docs/evidencias/C4/P30/01-contacto.jpg) [02](../Backend/docs/evidencias/C4/P30/red.json) [03](../Backend/docs/evidencias/C4/P30/persistencia.json) [04](../Backend/docs/evidencias/C4/P30/logs.txt) | X-Request-ID d4402ab10332 |  |
| RUN-C4-P31 | P31 Servicio llamado sin el secreto del gateway | CA31 | **aprobada** | 17:51:21 | 0.3 s | [01](../Backend/docs/evidencias/C4/P31/salida.txt) [02](../Backend/docs/evidencias/C4/P31/red.json) [03](../Backend/docs/evidencias/C4/P31/logs.txt) |  |  |
| RUN-C4-P32 | P32 Páginas sin desborde horizontal | CA32 | **aprobada** | 17:51:22 | 4.3 s | [01](../Backend/docs/evidencias/C4/P32/01-mis-pedidos.jpg) [02](../Backend/docs/evidencias/C4/P32/red.json) [03](../Backend/docs/evidencias/C4/P32/logs.txt) | X-Request-ID 21f06c6ca467 | Viewport 412x839 (Pixel 7, emulado) |

## Detalle de una ejecución: esperado y observado

El detalle completo de cada ejecución (cada comprobación con su resultado observado) está en el `resultados.json` de la campaña. Ejemplo de C1:

<details><summary>RUN-C1-P01 · La carta se arma con los productos de la API · aprobada</summary>

**Esperado:** GET https://127.0.0.1:8000/api/v1/products responde 200 con origen localhost:8080 y CORS; tarjetas = productos de la respuesta; precios iguales

| Comprobación | Resultado | Observado |
|---|---|---|
| GET /products responde 200 | ✔ | 200 |
| CORS: access-control-allow-origin = origen del frontend | ✔ | http://localhost:8080 -> http://localhost:8080 |
| Las tarjetas son los productos de la respuesta | ✔ | Cappuccino, Cheesecake de Maracuyá, Cold Brew, Croissant de Mantequilla, Espresso Doble, Frappé de Mocha, Latte Art, Tarta de Frambuesa |
| Precios de las tarjetas = precio vigente de la API | ✔ | $3.000 $4.800 $3.500 $2.800 $2.500 $3.400 $3.200 $4.500 |
| Cantidad de tarjetas = productos activos en inventory.productos | ✔ | 8 tarjetas / 8 en la base |

</details>

<details><summary>RUN-C1-P02 · Carta con inventory detenido y recuperación · aprobada</summary>

**Esperado:** Con inventory detenido: respuesta 502, 0 tarjetas y mensaje 'No pudimos cargar la carta'. Despues de iniciarlo: 200 y todas las tarjetas

| Comprobación | Resultado | Observado |
|---|---|---|
| Con inventory detenido: mensaje de error y 0 tarjetas | ✔ | No pudimos cargar la carta. Revisa que el backend esté encendido. Reintentar |
| El gateway responde 502 (backend no disponible) | ✔ | 502 |
| Al volver inventory, Reintentar carga la carta | ✔ | 8 |
| La nueva solicitud responde 200 | ✔ | 200 |

</details>

<details><summary>RUN-C1-P03 · Crear un pedido de retiro desde el carrito · aprobada</summary>

**Esperado:** POST /orders 201; pedido.php muestra Pendiente de pago y total $9.200; stock Latte 38 y Croissant 39

| Comprobación | Resultado | Observado |
|---|---|---|
| POST /orders responde 201 | ✔ | 201 |
| La pantalla muestra Pendiente de pago y total $9.200 (precios del servidor) | ✔ | Pendiente de pago $9.200 |
| orders.pedidos: pedido de USR-003, PENDIENTE_PAGO, total 9200, retiro | ✔ | {"_id":"ORD-30400C33","user_id":"USR-003","estado":"PENDIENTE_PAGO","tipo_entrega":"retiro","lineas":[{"product_id":"latte-art","nombre":"Latte Art","precio":3200,"cantidad":2},{"product_id":"croissan |
| Stock descontado una vez (Latte -2, Croissant -1) | ✔ | {"latte":40,"croissant":40} -> {"latte":38,"croissant":39} |
| Al recargar se ve el mismo pedido | ✔ |  |
| En una sesión nueva se ve el mismo estado y total | ✔ |  |

</details>

<details><summary>RUN-C1-P04 · Confirmar pedido sin sesión · aprobada</summary>

**Esperado:** Redirige a login.php?volver=carrito.php; no se envía POST /orders; orders.pedidos sin cambios

| Comprobación | Resultado | Observado |
|---|---|---|
| Redirige a login.php con volver=carrito.php | ✔ | http://localhost:8080/login.php?volver=carrito.php |
| No se envió POST /orders | ✔ |  |
| orders.pedidos sin cambios | ✔ | 1 -> 1 |

</details>

<details><summary>RUN-C1-P05 · Despacho fuera del radio de 3 km · aprobada</summary>

**Esperado:** POST /orders 422; mensaje 'fuera del radio de despacho'; sin pedido nuevo; stock igual

| Comprobación | Resultado | Observado |
|---|---|---|
| Mensaje: fuera del radio de despacho | ✔ | Esa dirección está fuera del radio de despacho (3 km del local). Puedes elegir retiro en el local. |
| POST /orders responde 422 | ✔ | 422 |
| Sin pedido nuevo y stock igual | ✔ | {"pedidos":1,"stock":40} -> {"pedidos":1,"stock":40} |

</details>

<details><summary>RUN-C1-P06 · Pedido con más cantidad que el stock · aprobada</summary>

**Esperado:** POST /orders 409; mensaje 'No hay stock suficiente'; Cappuccino sigue con stock 1; sin pedido nuevo

| Comprobación | Resultado | Observado |
|---|---|---|
| Precondición: stock de Cappuccino en 1 | ✔ | 1 |
| Mensaje: no hay stock suficiente | ✔ | No hay stock suficiente de uno de los productos. Revisa las cantidades. |
| POST /orders responde 409 | ✔ | 409 |
| Stock sigue en 1 y no hay pedido nuevo (todo o nada) | ✔ | {"pedidos":1,"stock":1} |
| Restauración: stock de Cappuccino en 40 | ✔ |  |

</details>

<details><summary>RUN-C1-P07 · Reintento del mismo pedido (doble envío) · aprobada</summary>

**Esperado:** Primera respuesta 201 y segunda 200 con repetido=true y el mismo id; un solo documento con esa clave; stock descontado una vez

| Comprobación | Resultado | Observado |
|---|---|---|
| Las dos respuestas son 201 y 200 | ✔ | 200, 201 |
| Mismo id de pedido y una marcada como repetida | ✔ | ORD-8DF554B6 / ORD-8DF554B6 (repetido) |
| Un solo documento con esa clave en orders.pedidos | ✔ | 1 |
| Stock descontado una sola vez | ✔ | 40 -> 39 |

</details>

<details><summary>RUN-C1-P08 · Crear pedido con inventory demorado (gRPC) · aprobada</summary>

**Esperado:** Primer intento: 502 y mensaje de servicio no disponible, sin pedido; segundo intento: 201 y pedido creado

| Comprobación | Resultado | Observado |
|---|---|---|
| Mensaje de servicio no disponible | ✔ | Un servicio del sistema no está disponible. Intenta de nuevo en unos segundos. |
| POST /orders responde 502 tras el plazo de gRPC | ✔ | 502 en 3339 ms |
| No se creó pedido | ✔ |  |
| Al reintentar con inventory activo: 201 y pedido creado | ✔ | 502, 201 |

</details>

<details><summary>RUN-C1-P09 · Pagar con el proveedor simulado y obtener la boleta · aprobada</summary>

**Esperado:** POST /payments 201 con el monto del pedido; POST /simular 202; pedido Pagado; boleta con folio, neto, IVA y total

| Comprobación | Resultado | Observado |
|---|---|---|
| POST /payments 201 con el monto del pedido (9200) | ✔ | {"id":"PAY-755E024F","order_id":"ORD-30400C33","estado":"PENDIENTE","monto":9200,"url_pago":"https://sandbox.pagos.example/pagar/chk_9ad2e182b9d6540d"} |
| La pasarela muestra $9.200 | ✔ |  |
| POST /simular responde 202 | ✔ | 202 |
| Pedido Pagado y boleta con folio y total $9.200 | ✔ | B-000001 |
| payments.pagos: APROBADO por 9200 | ✔ | [{"_id":"PAY-755E024F","monto":9200,"estado":"APROBADO"}] |
| orders.pedidos: PAGADO con el mismo folio en CAJA-WEB-01 | ✔ | {"_id":"ORD-30400C33","estado":"PAGADO","folio":"B-000001","caja":"CAJA-WEB-01"} |
| notificaciones.correos: boleta enviada (simulada) | ✔ | [{"_id":"ORD-30400C33","tipo":"boleta","asunto":"Aroma & Cafe - Boleta B-000001","estado":"ENVIADO_SIMULADO"}] |
| analitica.ventas: venta registrada sin datos personales | ✔ | [{"_id":"ORD-30400C33","total":9200,"tipo_entrega":"retiro"}] |
| En una sesión nueva: Pagado con la misma boleta | ✔ |  |

</details>

<details><summary>RUN-C1-P10 · Pago rechazado por el proveedor y nuevo intento · aprobada</summary>

**Esperado:** Primer pago RECHAZADO y pedido Pendiente de pago; segundo pago APROBADO y pedido Pagado

| Comprobación | Resultado | Observado |
|---|---|---|
| Mensaje de pago rechazado y pedido Pendiente de pago | ✔ | El proveedor rechazó el pago. El pedido sigue pendiente; puedes intentarlo de nuevo. |
| payments.pagos: un pago RECHAZADO | ✔ | [{"_id":"PAY-C1F3F3DE","monto":2800,"estado":"RECHAZADO"}] |
| orders.pedidos sigue PENDIENTE_PAGO | ✔ |  |
| El segundo intento aprueba el pago: Pagado | ✔ |  |
| payments.pagos: uno RECHAZADO y uno APROBADO | ✔ | [{"_id":"PAY-C1F3F3DE","monto":2800,"estado":"RECHAZADO"},{"_id":"PAY-51345C47","monto":2800,"estado":"APROBADO"}] |

</details>

<details><summary>RUN-C1-P11 · Aviso de pago repetido por el proveedor · aprobada</summary>

**Esperado:** Primer aviso APROBADO; segundo aviso repetido; un solo folio; una sola venta del pedido en analítica

| Comprobación | Resultado | Observado |
|---|---|---|
| POST /simular 202 con dos avisos enviados | ✔ | {"avisos":[{"status":200,"respuesta":{"ok":true,"estado":"APROBADO"}},{"status":200,"respuesta":{"ok":true,"repetido":true}}]} |
| Primer aviso APROBADO y segundo marcado como repetido | ✔ | [{"status":200,"respuesta":{"ok":true,"estado":"APROBADO"}},{"status":200,"respuesta":{"ok":true,"repetido":true}}] |
| Una sola venta del pedido en analitica.ventas | ✔ | 1 |
| Pedido PAGADO con un solo folio | ✔ | {"_id":"ORD-EF73EAC1","estado":"PAGADO","folio":"B-000003"} |

</details>

<details><summary>RUN-C1-P12 · Anular un pedido pendiente con motivo · aprobada</summary>

**Esperado:** POST /cancel 200; estado Anulado; stock de Espresso vuelve al valor anterior; historial con el motivo

| Comprobación | Resultado | Observado |
|---|---|---|
| Al crear el pedido se reserva 1 Espresso | ✔ |  |
| Estado Anulado | ✔ |  |
| POST /cancel responde 200 | ✔ | 200 |
| El stock vuelve al valor anterior | ✔ | 39 -> 39 |
| orders.pedidos: ANULADO con el motivo en el historial | ✔ | [{"estado":"PENDIENTE_PAGO","por":"USR-003","en":"2026-11-28T17:36:35+00:00"},{"estado":"ANULADO","por":"USR-003","motivo":"Me equivoque de producto","en":"2026-11-28T17:36:38+00:00"}] |
| Un pedido pagado no muestra la opción de anular | ✔ |  |

</details>

<details><summary>RUN-C1-P13 · Mis pedidos agrega orders, inventory y payments · aprobada</summary>

**Esperado:** POST /graphql 200 sin errors; un pedido por cada pedido de ana en orders.pedidos; estados y pagos iguales a los guardados

| Comprobación | Resultado | Observado |
|---|---|---|
| POST /graphql 200 sin errors | ✔ | 200 |
| Un pedido en pantalla por cada pedido de ana en orders.pedidos | ✔ | 5 / 5 |
| Estados de GraphQL = estados guardados en orders | ✔ |  |
| Todos los productos traen nombre (inventory) | ✔ |  |
| Los pedidos con pago muestran el pago (payments) | ✔ | 4 |

</details>

<details><summary>RUN-C1-P14 · Pedido ajeno · aprobada</summary>

**Esperado:** GET /orders/{id} 404 con mensaje 'No encontramos ese pedido'; GraphQL resumenPedido = null; el pedido de ana sin cambios

| Comprobación | Resultado | Observado |
|---|---|---|
| Mensaje "No encontramos ese pedido" y sin detalle | ✔ |  |
| GET /orders/{id} responde 404 | ✔ | 404 |
| GraphQL resumenPedido del pedido ajeno = null | ✔ | {"data":{"resumenPedido":null}} |
| El pedido de ana no cambió | ✔ | {"_id":"ORD-30400C33","user_id":"USR-003","estado":"PAGADO","total":9200} |

</details>

<details><summary>RUN-C1-P15 · Mis pedidos con inventory detenido · aprobada</summary>

**Esperado:** Respuesta GraphQL con errors 'Servicio inventory no disponible'; aviso 'Información incompleta' y 'Producto (dato no disponible)'; después, sin errors

| Comprobación | Resultado | Observado |
|---|---|---|
| Aviso de información incompleta | ✔ | Información incompleta: Servicio inventory no disponible: la respuesta esta incompleta Reintentar |
| Productos marcados como dato no disponible | ✔ |  |
| La respuesta GraphQL trae errors de inventory y data parcial | ✔ | [{"message":"Servicio inventory no disponible: la respuesta esta incompleta","path":null}] |
| Con inventory de vuelta: sin aviso y sin productos incompletos | ✔ |  |

</details>

<details><summary>RUN-C1-P16 · Permisos de campos y límites de GraphQL · aprobada</summary>

**Esperado:** cliente = null con error de autorización; reporteVentas con error; la consulta de 6 alias se rechaza (límite 5) y la de más de 2000 caracteres responde 422

| Comprobación | Resultado | Observado |
|---|---|---|
| Campo cliente: null con error de autorización | ✔ | {"data":{"resumenPedido":{"id":"ORD-30400C33","cliente":null}},"errors":[{"message":"No autorizado para ver datos del cliente","path":["resumenPedido","cliente"]}]} |
| reporteVentas para un cliente: error | ✔ | {"data":null,"errors":[{"message":"Solo el dueno o el administrador pueden ver reportes","path":["reporteVentas"]}]} |
| Consulta con 6 alias rechazada (límite 5) | ✔ | {"data":null,"errors":[{"message":"6 aliases found. Allowed: 5","path":null}]} |
| Consulta de más de 2000 caracteres: 422 | ✔ | 422 |

</details>

<details><summary>RUN-C1-P17 · Editar mi ficha · aprobada</summary>

**Esperado:** PUT /clients/me 200; aviso 'Tus datos quedaron guardados'; valores nuevos al recargar y en otra sesión

| Comprobación | Resultado | Observado |
|---|---|---|
| PUT /clients/me responde 200 | ✔ | 200 |
| Al recargar se ven los valores nuevos | ✔ |  |
| clients.clientes guarda teléfono y comuna | ✔ | {"_id":"USR-003","telefono":"+56 9 5555 2794","run":null,"comuna":"Maipú"} |
| En una sesión nueva se ven los mismos datos | ✔ |  |

</details>

<details><summary>RUN-C1-P18 · RUN inválido en la ficha · aprobada</summary>

**Esperado:** PUT /clients/me 422; mensaje 'El RUN no es válido'; ficha sin cambios

| Comprobación | Resultado | Observado |
|---|---|---|
| Mensaje: el RUN no es válido | ✔ | El RUN no es válido (revisa el dígito verificador). |
| PUT /clients/me responde 422 | ✔ | 422 |
| La ficha no cambió | ✔ | {"_id":"USR-003","telefono":"+56 9 5555 2794","run":null,"comuna":"Maipú"} |

</details>

<details><summary>RUN-C1-P19 · Sesión expirada · aprobada</summary>

**Esperado:** GET /clients/me 401; redirige a login.php?expirada=1 con aviso; la sesión se borra de auth.sesiones

| Comprobación | Resultado | Observado |
|---|---|---|
| Redirige a login.php?expirada=1 con aviso | ✔ | Tu sesión expiró o ya no es válida. Inicia sesión de nuevo. |
| GET /clients/me (con la sesión vencida) responde 401 | ✔ | 401 |
| La sesión vencida se borró de auth.sesiones | ✔ | 5 -> 4 |

</details>

<details><summary>RUN-C1-P20 · Página protegida sin sesión · aprobada</summary>

**Esperado:** Redirige a login.php; la API responde 401 'Bearer token requerido'

| Comprobación | Resultado | Observado |
|---|---|---|
| Sin sesión, Mi cuenta lleva a login.php | ✔ | http://localhost:8080/login.php?volver=cuenta.php |
| GET /clients/me sin token: 401 "Bearer token requerido" | ✔ | {"status":401,"datos":{"detail":"Bearer token requerido"}} |

</details>

<details><summary>RUN-C1-P21 · Login fallido, login y cierre de sesión · aprobada</summary>

**Esperado:** 401 'Correo o contraseña incorrectos'; 200 y 'Hola, Ana'; después del logout el token anterior recibe 401

| Comprobación | Resultado | Observado |
|---|---|---|
| Clave incorrecta: "Correo o contraseña incorrectos" | ✔ |  |
| POST /auth/login responde 401 | ✔ |  |
| Login correcto: "Hola, Ana" | ✔ |  |
| Después de cerrar sesión, el token anterior recibe 401 | ✔ | 401 |

</details>

<details><summary>RUN-C1-P22 · Registro con verificación de correo · aprobada</summary>

**Esperado:** POST /auth/register 201; login 403 antes de verificar; verify-email 200; login 200

| Comprobación | Resultado | Observado |
|---|---|---|
| POST /auth/register responde 201 | ✔ |  |
| Antes de verificar: login 403 con aviso para verificar | ✔ |  |
| El código llegó a la bandeja simulada | ✔ |  |
| POST /auth/verify-email responde 200 | ✔ |  |
| Después de verificar: "Hola, Camila" | ✔ |  |
| auth.usuarios: rol cliente y correo verificado | ✔ | {"_id":"USR-0D202022","email":"camila.c1.1795887446112@correo.cl","rol":"cliente","correo_verificado":true} |

</details>

<details><summary>RUN-C1-P23 · Inventario del dueño: oferta, alta y baja · aprobada</summary>

**Esperado:** PUT 200, POST 201, DELETE 204; la carta muestra la oferta, y el producto dado de baja no aparece

| Comprobación | Resultado | Observado |
|---|---|---|
| PUT 200, POST 201 y DELETE 204 | ✔ |  |
| La carta muestra la oferta del Latte ($2.900 y $3.200 tachado) | ✔ | $2.900$3.200 |
| El producto dado de baja no aparece en la carta | ✔ |  |
| inventory.productos: Latte con oferta 2900 y el nuevo con activo=false | ✔ |  |
| Restauración: el Latte sin oferta | ✔ |  |

</details>

<details><summary>RUN-C1-P24 · Rol sin permiso · aprobada</summary>

**Esperado:** GET /admin/products 403 y GET /admin/dispatch-orders 403; aviso 'No tienes permiso'

| Comprobación | Resultado | Observado |
|---|---|---|
| Inventario: "No tienes permiso" | ✔ |  |
| Despacho: "No tienes permiso" | ✔ |  |
| GET /admin/products y /admin/dispatch-orders responden 403 | ✔ |  |

</details>

<details><summary>RUN-C1-P25 · Despacho avanza el pedido pagado · aprobada</summary>

**Esperado:** Tres PUT /status 200; el pedido sale de la lista al quedar Entregado; historial en orders

| Comprobación | Resultado | Observado |
|---|---|---|
| El pedido pagado aparece en la lista | ✔ | ORD-30400C33, ORD-E4206731, ORD-EF73EAC1 |
| En Listo (retiro) no se ofrece "en camino" | ✔ |  |
| Tres PUT /status 200 | ✔ |  |
| Al quedar Entregado sale de la lista | ✔ |  |
| orders.pedidos: ENTREGADO con el historial completo | ✔ | PENDIENTE_PAGO > PAGADO > EN_PREPARACION > LISTO > ENTREGADO |

</details>

<details><summary>RUN-C1-P26 · Ventas de la caja web · aprobada</summary>

**Esperado:** GET /admin/sales 200; fila con el folio y el total del pedido de P09

| Comprobación | Resultado | Observado |
|---|---|---|
| Fila con el folio de P09 y total $9.200 | ✔ | B-000001ORD-30400C3328-11-26, 2:36 p. m.$9.200Entregado |
| GET /admin/sales responde 200 | ✔ |  |

</details>

<details><summary>RUN-C1-P27 · Reporte de ventas actualizado · aprobada</summary>

**Esperado:** GET /admin/reports/sales 200; pedidos pagados aumenta en 1 y el total en el monto del pedido

| Comprobación | Resultado | Observado |
|---|---|---|
| Pedidos pagados aumenta en 1 al actualizar | ✔ | 3 -> 4 |
| Total vendido aumenta en $3.500 (Cold Brew) | ✔ | $14.500 -> $18.000 |

</details>

<details><summary>RUN-C1-P28 · Analítica detenida y recuperación · aprobada</summary>

**Esperado:** Pago aprobado; Reportes muestra un error mientras analítica esta detenida; después de iniciarla, el reporte incluye la venta

| Comprobación | Resultado | Observado |
|---|---|---|
| Con analítica detenida el pago se confirma (Pagado) | ✔ |  |
| Reportes informa el error mientras analítica está detenida | ✔ | Un servicio del sistema no está disponible. Intenta de nuevo en unos segundos. Reintentar |
| orders guarda el aviso como pendiente | ✔ | {"_id":"ORD-42B1484B","estado":"PAGADO","avisos_enviados":false} |
| Al volver analítica, la venta se registra (reintento de orders) | ✔ | 4 -> 5 en 14 s |
| Reintentar en Reportes muestra el reporte con la venta | ✔ | 5 |

</details>

<details><summary>RUN-C1-P29 · Administración de usuarios y clientes · aprobada</summary>

**Esperado:** POST /admin/users 201; PUT /role 200; PUT del propio perfil 409; POST /admin/clients 201

| Comprobación | Resultado | Observado |
|---|---|---|
| Cambiar el propio perfil: "No puedes cambiar tu propio perfil" | ✔ |  |
| POST /admin/users 201, PUT /role 200, PUT propio 409 y POST /admin/clients 201 | ✔ | 200,409 |
| auth.usuarios: funcionario con perfil despacho, admin sin cambio y cliente sin verificar | ✔ | [{"_id":"USR-001","email":"admin@aromaycafe.test","rol":"admin","correo_verificado":true},{"_id":"USR-199E111C","email":"cajero.c1.1795887509951@aromaycafe.test","rol":"despacho","correo_verificado":t |

</details>

<details><summary>RUN-C1-P30 · Formulario de contacto · aprobada</summary>

**Esperado:** POST /contact 201 y aviso de gracias; el mensaje aparece en la tabla del admin

| Comprobación | Resultado | Observado |
|---|---|---|
| Aviso de gracias y POST /contact 201 | ✔ |  |
| El admin ve el mensaje en Administración | ✔ |  |
| clients.contacto: mensaje guardado | ✔ |  |

</details>

<details><summary>RUN-C1-P31 · Servicio llamado sin el secreto del gateway · aprobada</summary>

**Esperado:** 403 sin secreto y 403 con secreto falso; dos lineas 'llamada RECHAZADA' en inventory

| Comprobación | Resultado | Observado |
|---|---|---|
| Sin secreto y con secreto falso: 403 | ✔ | Sin secreto: inventory respondio 403 Forbidden Haciendose pasar por el gateway con un secreto falso: inventory respondio 403 Forbidden |

</details>

<details><summary>RUN-C1-P32 · Páginas sin desborde horizontal · aprobada</summary>

**Esperado:** En cada página el ancho del documento no supera el del viewport

| Comprobación | Resultado | Observado |
|---|---|---|
| index.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| catalogo.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| carrito.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| cuenta.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| mis-pedidos.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| Contacto.php: sin desborde horizontal | ✔ | 1366 <= 1366 |
| pedido.php?id=ORD-30400C33: sin desborde horizontal | ✔ | 1366 <= 1366 |

</details>
