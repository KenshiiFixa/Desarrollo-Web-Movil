# 2. Inventario de flujos, requisitos y recorridos críticos

Generado desde `Backend/pruebas/protocolo.json` (protocolo v1.1).

## Requisitos en alcance

Se mantienen los requisitos de la Unidad 2 (RF1–RF13 → R01–R13) y se agregan requisitos transversales (R14–R19).

| ID | Requisito |
|---|---|
| R01 | Armar un pedido con los productos disponibles de la carta (RF1) |
| R02 | El pedido se prepara solo cuando el pago esta confirmado (RF2) |
| R03 | Anular una compra indicando el motivo (RF3) |
| R04 | Vender solo a clientes registrados; ventas web en la caja del cajero virtual (RF4) |
| R05 | Registro y ficha del cliente con RUN, dirección, comuna, teléfono y otros datos (RF5) |
| R06 | El administrador registra clientes en el local (RF6) |
| R07 | Consultar y actualizar disponibilidad, precio y oferta de los productos (RF7) |
| R08 | Boleta digital por cada venta, enviada al correo del cliente (RF8) |
| R09 | Reporte de ventas para el dueño (RF9) |
| R10 | Mantenedores de productos, usuarios y clientes (RF10) |
| R11 | Validar el correo con un código enviado por la API de mensajeria (RF11) |
| R12 | Autenticacion y acceso según el perfil asignado por el administrador (RF12) |
| R13 | Órdenes de despacho en el orden en que se pagan (RF13) |
| R14 | Formulario de contacto publico (pantalla Contacto) |
| R15 | Acceso protegido: sin sesión, sesión expirada, rol sin permiso y recurso ajeno se rechazan sin modificar datos |
| R16 | Agregación GraphQL de orders, inventory y payments en una pantalla real, con permisos y límites |
| R17 | Ante una dependencia privada caida o lenta, mensaje comprensible y recuperación coherente |
| R18 | Frontend responsivo: las acciones funcionan en escritorio y móvil contra el mismo backend |
| R19 | Una operación crítica reintentada no produce efectos duplicados (pedido y aviso de pago) |

## Inventario de flujos

Criticidad según el efecto de un fallo sobre usuarios, datos y negocio. Responsables: equipo (Ian Arroyo y Alejandro Martínez).

| ID | Flujo | Rol | Pantalla | Servicios y protocolos | Datos afectados | Criticidad y justificación | Estado inicial (línea base) | Requisitos | Dependencia externa | Criterios |
|---|---|---|---|---|---|---|---|---|---|---|
| F01 | Consultar la carta | Visitante | catalogo.php, index.php | Gateway → inventory (HTTPS) | Lectura de inventory.productos | **Alta**: Es la entrada de toda compra; un precio o stock errado afecta al cliente y al negocio | Productos escritos a mano en el HTML (sin API) | R01, R07 | Ninguna | CA01, CA02, CA32 |
| F02 | Registro con verificación de correo | Visitante | registro.php | Gateway → auth → clients y notificaciones (HTTPS) | auth.usuarios, clients.clientes, notificaciones.correos | **Media**: Sin verificación no hay venta a clientes registrados | Botón Registrarse sin destino | R05, R11 | Correo: doble de prueba (bandeja simulada) | CA22 |
| F03 | Iniciar y cerrar sesión | Todos | login.php, encabezado | Gateway → auth (+ clients para el nombre) | auth.sesiones | **Alta**: Controla el acceso a todo lo protegido | Botón Iniciar sesión sin destino | R12, R15 | Ninguna | CA19, CA21, CA32 |
| F04 | Mi cuenta (ver y editar ficha) | Cliente | cuenta.php | Gateway → auth (introspect) → clients | clients.clientes | **Alta**: Datos personales: una escritura indebida expone o corrompe datos del cliente | No existía | R05, R15 | Ninguna | CA17, CA18, CA19, CA20, CA32 |
| F05 | Crear pedido desde el carrito | Cliente | carrito.php, pedido.php | Gateway → orders → inventory (gRPC con TLS) | orders.pedidos, inventory.productos (stock), inventory.reservas | **Crítica**: Cambia stock y crea la venta; un error duplica pedidos o vende sin stock | Pagar solo vaciaba el carrito local | R01, R04, R19 | Ninguna | CA03, CA04, CA05, CA06, CA07, CA08, CA32 |
| F06 | Pagar pedido y obtener boleta | Cliente | pedido.php | Gateway → payments → proveedor (doble) → webhook firmado → orders → notificaciones y analitica | payments.pagos, payments.avisos, orders.pedidos, notificaciones.correos, analitica.ventas | **Crítica**: Dinero y comprobante: cobrar dos veces o confirmar sin pago son fallos graves | No existía | R02, R08, R19 | Proveedor de pagos: doble de prueba (proveedor_pagos) | CA09, CA10, CA11, CA32 |
| F07 | Mis pedidos (GraphQL) y detalle | Cliente | mis-pedidos.php, pedido.php | Gateway → graphql → orders, inventory y payments | Lectura de orders, inventory y payments | **Crítica**: Muestra datos propios; un fallo expone pedidos ajenos o presenta datos incompletos como completos | No existía | R15, R16, R17 | Ninguna | CA13, CA14, CA15, CA16, CA32 |
| F08 | Anular pedido | Cliente | pedido.php | Gateway → orders → inventory (gRPC LiberarStock) | orders.pedidos, inventory.productos | **Media**: Debe devolver el stock y conservar el motivo | No existía | R03 | Ninguna | CA12 |
| F09 | Inventario del dueño | Dueño, admin | inventario.php | Gateway → inventory | inventory.productos | **Alta**: Precios y stock que ve todo cliente | No existía | R07, R10 | Ninguna | CA06, CA23, CA24 |
| F10 | Órdenes de despacho | Encargado de despacho, admin | despacho.php | Gateway → orders (+ clients para datos de entrega) | orders.pedidos (estado e historial) | **Media**: Entregas fuera de orden o pedidos sin pagar en cocina | No existía | R02, R13 | Ninguna | CA24, CA25 |
| F11 | Ventas de la caja web | Cajero, admin | ventas.php | Gateway → orders | Lectura de orders.pedidos | **Baja**: Consulta contable, sin cambios | No existía | R04 | Ninguna | CA26 |
| F12 | Reporte de ventas | Dueño, admin | reportes.php | Gateway → analitica (alimentada por orders) | Lectura de analitica.ventas | **Media**: Decisiones del negocio con datos frescos | No existía | R09 | Ninguna | CA27, CA28 |
| F13 | Administración de usuarios y clientes | Admin | admin.php | Gateway → auth y clients | auth.usuarios, auth.sesiones, clients.clientes, clients.contacto | **Alta**: Asignar perfiles define quien accede a que | No existía | R06, R10, R12 | Ninguna | CA29 |
| F14 | Contacto | Visitante | Contacto.php | Gateway → clients | clients.contacto | **Baja**: Mensajes de clientes; no afecta ventas | Mostraba éxito sin guardar nada | R14 | Ninguna | CA30 |

## Recorridos críticos (validación profunda)

Cubren lectura, cambio persistente de estado y acceso protegido, e incluyen inventory, orders, clients y payments. Los demás flujos siguen en alcance con al menos una prueba cada uno.

| ID | Recorrido | Flujos | Qué cubre | Pruebas (éxito / rechazo o fallo / límite o recuperación) |
|---|---|---|---|---|
| RC1 | Comprar: carta → carrito → pedido | F01, F05 | Lectura y cambio persistente de estado; inventory y orders (gRPC) | P01 (éxito); P02 (fallo y recuperación); P03 (éxito); P04 (rechazo); P05 (rechazo); P06 (límite); P07 (límite); P08 (fallo y recuperación) |
| RC2 | Pagar el pedido y obtener boleta | F06 | Cambio persistente con dinero; payments, orders, notificaciones y analítica | P09 (éxito); P10 (rechazo y recuperación); P11 (límite) |
| RC3 | Mis pedidos con GraphQL y acceso a pedido ajeno | F07 | Lectura agregada y acceso protegido; orders, inventory y payments | P13 (éxito); P14 (rechazo); P15 (fallo y recuperación); P16 (rechazo y límite) |
| RC4 | Mi cuenta y sesión | F03, F04 | Acceso protegido y cambio persistente de datos personales; clients y auth | P17 (éxito); P18 (rechazo); P19 (rechazo); P20 (rechazo); P21 (rechazo y éxito) |
