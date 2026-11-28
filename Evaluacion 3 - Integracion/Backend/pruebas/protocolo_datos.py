"""Fuente unica del protocolo de pruebas (version 1.0): requisitos, flujos, criterios y fichas de prueba.
Genera pruebas/protocolo.json, que lee la suite (suite_integracion.js) y el generador de documentos."""
import json
import os

VERSION = "1.1"

# Cambios del protocolo despues de la version 1.0: (version, fecha, cambio, motivo, pruebas que se repiten)
CAMBIOS = [
    ("1.0", "2026-11-28", "Versión inicial", "—", "—"),
    ("1.1", "2026-11-28", "P16: la consulta de profundidad 6 se reemplaza por una consulta de más de 2000 caracteres",
     "El esquema llega como máximo a profundidad 4 (misPedidos > lineas > producto > nombre), así que no se puede escribir "
     "una consulta válida que pase el límite de profundidad 5; el límite de tamaño (2000 caracteres) sí se puede probar. "
     "Se detectó al implementar la suite, antes de la primera ejecución. Además se corrigen tildes en títulos (sin cambio de criterios)",
     "P16 (aún no ejecutada)"),
    ("1.1", "2026-11-28", "Aclaración (después de ejecutar, sin cambio de criterios): el viewport móvil del perfil Pixel 7 es 412×839 (la pantalla es 412×915); la v1.0 decía 412×915",
     "Corregir la descripción para que coincida con lo registrado en las ejecuciones C2 y C4", "Ninguna"),
]

REQUISITOS = {
    "R01": "Armar un pedido con los productos disponibles de la carta (RF1)",
    "R02": "El pedido se prepara solo cuando el pago esta confirmado (RF2)",
    "R03": "Anular una compra indicando el motivo (RF3)",
    "R04": "Vender solo a clientes registrados; ventas web en la caja del cajero virtual (RF4)",
    "R05": "Registro y ficha del cliente con RUN, direccion, comuna, telefono y otros datos (RF5)",
    "R06": "El administrador registra clientes en el local (RF6)",
    "R07": "Consultar y actualizar disponibilidad, precio y oferta de los productos (RF7)",
    "R08": "Boleta digital por cada venta, enviada al correo del cliente (RF8)",
    "R09": "Reporte de ventas para el dueno (RF9)",
    "R10": "Mantenedores de productos, usuarios y clientes (RF10)",
    "R11": "Validar el correo con un codigo enviado por la API de mensajeria (RF11)",
    "R12": "Autenticacion y acceso segun el perfil asignado por el administrador (RF12)",
    "R13": "Ordenes de despacho en el orden en que se pagan (RF13)",
    "R14": "Formulario de contacto publico (pantalla Contacto)",
    "R15": "Acceso protegido: sin sesion, sesion expirada, rol sin permiso y recurso ajeno se rechazan sin modificar datos",
    "R16": "Agregacion GraphQL de orders, inventory y payments en una pantalla real, con permisos y limites",
    "R17": "Ante una dependencia privada caida o lenta, mensaje comprensible y recuperacion coherente",
    "R18": "Frontend responsivo: las acciones funcionan en escritorio y movil contra el mismo backend",
    "R19": "Una operacion critica reintentada no produce efectos duplicados (pedido y aviso de pago)",
}

FLUJOS = [
    # id, nombre, rol, pantalla, servicios y protocolos, datos afectados, criticidad, justificacion, estado inicial, requisitos, dependencia externa
    ("F01", "Consultar la carta", "Visitante", "catalogo.php, index.php", "Gateway → inventory (HTTPS)", "Lectura de inventory.productos",
     "Alta", "Es la entrada de toda compra; un precio o stock errado afecta al cliente y al negocio",
     "Productos escritos a mano en el HTML (sin API)", ["R01", "R07"], "Ninguna"),
    ("F02", "Registro con verificacion de correo", "Visitante", "registro.php", "Gateway → auth → clients y notificaciones (HTTPS)",
     "auth.usuarios, clients.clientes, notificaciones.correos", "Media", "Sin verificacion no hay venta a clientes registrados",
     "Boton Registrarse sin destino", ["R05", "R11"], "Correo: doble de prueba (bandeja simulada)"),
    ("F03", "Iniciar y cerrar sesion", "Todos", "login.php, encabezado", "Gateway → auth (+ clients para el nombre)",
     "auth.sesiones", "Alta", "Controla el acceso a todo lo protegido", "Boton Iniciar sesion sin destino", ["R12", "R15"], "Ninguna"),
    ("F04", "Mi cuenta (ver y editar ficha)", "Cliente", "cuenta.php", "Gateway → auth (introspect) → clients",
     "clients.clientes", "Alta", "Datos personales: una escritura indebida expone o corrompe datos del cliente",
     "No existia", ["R05", "R15"], "Ninguna"),
    ("F05", "Crear pedido desde el carrito", "Cliente", "carrito.php, pedido.php", "Gateway → orders → inventory (gRPC con TLS)",
     "orders.pedidos, inventory.productos (stock), inventory.reservas", "Critica",
     "Cambia stock y crea la venta; un error duplica pedidos o vende sin stock", "Pagar solo vaciaba el carrito local",
     ["R01", "R04", "R19"], "Ninguna"),
    ("F06", "Pagar pedido y obtener boleta", "Cliente", "pedido.php", "Gateway → payments → proveedor (doble) → webhook firmado → orders → notificaciones y analitica",
     "payments.pagos, payments.avisos, orders.pedidos, notificaciones.correos, analitica.ventas", "Critica",
     "Dinero y comprobante: cobrar dos veces o confirmar sin pago son fallos graves", "No existia",
     ["R02", "R08", "R19"], "Proveedor de pagos: doble de prueba (proveedor_pagos)"),
    ("F07", "Mis pedidos (GraphQL) y detalle", "Cliente", "mis-pedidos.php, pedido.php", "Gateway → graphql → orders, inventory y payments",
     "Lectura de orders, inventory y payments", "Critica", "Muestra datos propios; un fallo expone pedidos ajenos o presenta datos incompletos como completos",
     "No existia", ["R15", "R16", "R17"], "Ninguna"),
    ("F08", "Anular pedido", "Cliente", "pedido.php", "Gateway → orders → inventory (gRPC LiberarStock)",
     "orders.pedidos, inventory.productos", "Media", "Debe devolver el stock y conservar el motivo", "No existia", ["R03"], "Ninguna"),
    ("F09", "Inventario del dueno", "Dueno, admin", "inventario.php", "Gateway → inventory", "inventory.productos", "Alta",
     "Precios y stock que ve todo cliente", "No existia", ["R07", "R10"], "Ninguna"),
    ("F10", "Ordenes de despacho", "Encargado de despacho, admin", "despacho.php", "Gateway → orders (+ clients para datos de entrega)",
     "orders.pedidos (estado e historial)", "Media", "Entregas fuera de orden o pedidos sin pagar en cocina", "No existia", ["R02", "R13"], "Ninguna"),
    ("F11", "Ventas de la caja web", "Cajero, admin", "ventas.php", "Gateway → orders", "Lectura de orders.pedidos", "Baja",
     "Consulta contable, sin cambios", "No existia", ["R04"], "Ninguna"),
    ("F12", "Reporte de ventas", "Dueno, admin", "reportes.php", "Gateway → analitica (alimentada por orders)", "Lectura de analitica.ventas",
     "Media", "Decisiones del negocio con datos frescos", "No existia", ["R09"], "Ninguna"),
    ("F13", "Administracion de usuarios y clientes", "Admin", "admin.php", "Gateway → auth y clients",
     "auth.usuarios, auth.sesiones, clients.clientes, clients.contacto", "Alta", "Asignar perfiles define quien accede a que",
     "No existia", ["R06", "R10", "R12"], "Ninguna"),
    ("F14", "Contacto", "Visitante", "Contacto.php", "Gateway → clients", "clients.contacto", "Baja",
     "Mensajes de clientes; no afecta ventas", "Mostraba exito sin guardar nada", ["R14"], "Ninguna"),
]

CRITICOS = {
    "RC1": ("Comprar: carta → carrito → pedido", ["F01", "F05"], "Lectura y cambio persistente de estado; inventory y orders (gRPC)"),
    "RC2": ("Pagar el pedido y obtener boleta", ["F06"], "Cambio persistente con dinero; payments, orders, notificaciones y analitica"),
    "RC3": ("Mis pedidos con GraphQL y acceso a pedido ajeno", ["F07"], "Lectura agregada y acceso protegido; orders, inventory y payments"),
    "RC4": ("Mi cuenta y sesion", ["F03", "F04"], "Acceso protegido y cambio persistente de datos personales; clients y auth"),
}

# Cada prueba: id, recorrido critico (o None), flujos, requisitos, tipo de escenario, titulo, criterio de aceptacion,
# precondiciones, procedimiento, resultado esperado, verificacion, restauracion
PRUEBAS = [
 ("P01", "RC1", ["F01"], ["R01", "R07"], "exito", "La carta se arma con los productos de la API",
  "La carta muestra exactamente los productos activos que entrega GET /products, con sus nombres y precios (oferta si existe)",
  "Base limpia; visitante sin sesion", "Abrir catalogo.php y esperar las tarjetas",
  "GET https://127.0.0.1:8000/api/v1/products responde 200 con origen localhost:8080 y CORS; tarjetas = productos de la respuesta; precios iguales",
  "Red (solicitud, respuesta y X-Request-ID); log del gateway e inventory con el mismo id; conteo en inventory.productos (activo=true)",
  "No modifica datos"),
 ("P02", "RC1", ["F01"], ["R17"], "fallo y recuperacion", "Carta con inventory detenido y recuperacion",
  "Si inventory no responde, la carta no inventa productos: muestra un error comprensible con Reintentar; al volver inventory, Reintentar carga la carta",
  "Base limpia; contenedor inventory detenido (docker compose stop inventory)", "Abrir catalogo.php; iniciar inventory; presionar Reintentar",
  "Con inventory detenido: respuesta 502, 0 tarjetas y mensaje 'No pudimos cargar la carta'. Despues de iniciarlo: 200 y todas las tarjetas",
  "Red (502 y luego 200); log del gateway ('inventory no responde -> 502')", "docker compose start inventory"),
 ("P03", "RC1", ["F05"], ["R01", "R04"], "exito", "Crear un pedido de retiro desde el carrito",
  "El pedido queda guardado con los precios del servidor, descuenta el stock una vez y se ve igual al recargar y en otra sesion",
  "Base limpia; cliente ana@aromaycafe.test; stock inicial 40 de cada producto",
  "Agregar 2 Latte Art y 1 Croissant; iniciar sesion; Confirmar pedido con Retiro en el local",
  "POST /orders 201; pedido.php muestra Pendiente de pago y total $9.200; stock Latte 38 y Croissant 39",
  "Red (POST /orders y X-Request-ID); logs de orders e inventory-grpc (ReservarStock); inspeccion de orders.pedidos y inventory.productos; lectura en una sesion nueva",
  "Base limpia en la siguiente campana"),
 ("P04", "RC1", ["F05"], ["R04", "R15"], "rechazo", "Confirmar pedido sin sesion",
  "Sin sesion no se crea pedido: la pagina lleva a iniciar sesion y vuelve al carrito",
  "Visitante sin sesion con productos en el carrito", "Presionar Confirmar pedido",
  "Redirige a login.php?volver=carrito.php; no se envia POST /orders; orders.pedidos sin cambios",
  "Red (sin POST /orders); conteo de orders.pedidos antes y despues", "No modifica datos"),
 ("P05", "RC1", ["F05"], ["R01"], "rechazo", "Despacho fuera del radio de 3 km",
  "Un despacho a una comuna fuera del radio se rechaza con un mensaje claro y sin crear pedido ni descontar stock",
  "Cliente ana con productos en el carrito", "Elegir Despacho a domicilio, comuna Providencia, Confirmar pedido",
  "POST /orders 422; mensaje 'fuera del radio de despacho'; sin pedido nuevo; stock igual",
  "Red (422); conteo de orders.pedidos e inventory.productos antes y despues", "No modifica datos"),
 ("P06", "RC1", ["F05", "F09"], ["R01", "R07"], "limite", "Pedido con mas cantidad que el stock",
  "Si la cantidad supera el stock, el pedido se rechaza completo (todo o nada) y el stock no cambia",
  "Duena deja el stock de Cappuccino en 1 desde Inventario", "Cliente ana agrega 2 Cappuccino y confirma",
  "POST /orders 409; mensaje 'No hay stock suficiente'; Cappuccino sigue con stock 1; sin pedido nuevo",
  "Red (PUT del inventario y POST 409); log de inventory-grpc; inspeccion de inventory.productos", "Duena vuelve el stock a 40"),
 ("P07", "RC1", ["F05"], ["R19"], "limite", "Reintento del mismo pedido (doble envio)",
  "Dos envios con la misma clave de idempotencia crean un solo pedido y descuentan el stock una sola vez",
  "Cliente ana con sesion", "Desde la sesion del navegador enviar dos veces el mismo POST /orders (mismo cuerpo y clave)",
  "Primera respuesta 201 y segunda 200 con repetido=true y el mismo id; un solo documento con esa clave; stock descontado una vez",
  "Respuestas; log de orders ('pedido repetido'); inspeccion de orders.pedidos por clave e inventory.productos", "No requiere"),
 ("P08", "RC1", ["F05"], ["R17"], "fallo y recuperacion", "Crear pedido con inventory demorado (gRPC)",
  "Si inventory no responde dentro del plazo de gRPC (3 s), no se crea el pedido y se informa; al reintentar con inventory activo, se crea",
  "Cliente ana con productos en el carrito; inventory en pausa (docker compose pause inventory)",
  "Confirmar pedido; reanudar inventory; Confirmar pedido otra vez",
  "Primer intento: 502 y mensaje de servicio no disponible, sin pedido; segundo intento: 201 y pedido creado",
  "Red (502 y 201); tiempo de respuesta del primer intento; log de orders; conteo de orders.pedidos", "docker compose unpause inventory"),
 ("P09", "RC2", ["F06"], ["R02", "R04", "R08"], "exito", "Pagar con el proveedor simulado y obtener la boleta",
  "Con el pago aprobado por el proveedor, el pedido queda PAGADO con boleta y folio, el pago APROBADO con el monto del servidor, y se registran el correo de boleta y la venta en analitica",
  "Pedido de ana en Pendiente de pago", "Pagar; Pagar con tarjeta de prueba",
  "POST /payments 201 con el monto del pedido; POST /simular 202; pedido Pagado; boleta con folio, neto, IVA y total",
  "Red; logs de payments, orders, notificaciones y analitica; inspeccion de payments.pagos, orders.pedidos, notificaciones.correos y analitica.ventas; lectura en sesion nueva",
  "Base limpia en la siguiente campana"),
 ("P10", "RC2", ["F06"], ["R02"], "rechazo y recuperacion", "Pago rechazado por el proveedor y nuevo intento",
  "Un pago rechazado no cambia el pedido (sigue pendiente) y se puede pagar de nuevo",
  "Pedido de ana en Pendiente de pago", "Pagar; Simular pago rechazado; Pagar; Pagar con tarjeta de prueba",
  "Primer pago RECHAZADO y pedido Pendiente de pago; segundo pago APROBADO y pedido Pagado",
  "Red; log de payments; inspeccion de payments.pagos (uno RECHAZADO y uno APROBADO) y orders.pedidos", "No requiere"),
 ("P11", "RC2", ["F06"], ["R19"], "limite", "Aviso de pago repetido por el proveedor",
  "Si el proveedor envia dos veces el mismo aviso, se procesa una vez: un folio, una venta en analitica",
  "Pedido de ana en Pendiente de pago con pago iniciado", "Simular el pago aprobado con repetir_aviso=2 desde la sesion del navegador",
  "Primer aviso APROBADO; segundo aviso repetido; un solo folio; una sola venta del pedido en analitica",
  "Respuesta de /simular; log de payments ('repetido'); inspeccion de analitica.ventas y orders.pedidos", "No requiere"),
 ("P12", None, ["F08"], ["R03"], "exito", "Anular un pedido pendiente con motivo",
  "Anular un pedido pendiente lo deja ANULADO con su motivo y devuelve el stock; un pedido pagado no muestra la opcion de anular",
  "Pedido nuevo de ana en Pendiente de pago (1 Espresso Doble)", "Escribir el motivo y presionar Anular pedido",
  "POST /cancel 200; estado Anulado; stock de Espresso vuelve al valor anterior; historial con el motivo",
  "Red; logs de orders e inventory-grpc (LiberarStock); inspeccion de orders.pedidos e inventory.productos", "No requiere"),
 ("P13", "RC3", ["F07"], ["R16"], "exito", "Mis pedidos agrega orders, inventory y payments",
  "La pantalla Mis pedidos muestra, en una consulta GraphQL, el estado (orders), los nombres de producto (inventory) y el pago (payments) de cada pedido propio",
  "Ana con pedidos de P03 a P12", "Abrir Mis pedidos",
  "POST /graphql 200 sin errors; un pedido por cada pedido de ana en orders.pedidos; estados y pagos iguales a los guardados",
  "Red (consulta y respuesta); logs de graphql, orders, inventory y payments con el mismo id; inspeccion de orders.pedidos de USR-003",
  "No modifica datos"),
 ("P14", "RC3", ["F07"], ["R15"], "rechazo", "Pedido ajeno",
  "Otro cliente no puede ver un pedido ajeno: la pantalla no revela datos y el pedido no cambia",
  "Pedido pagado de ana; sesion de pedro@aromaycafe.test", "Pedro abre pedido.php?id=<pedido de ana> y consulta resumenPedido por GraphQL",
  "GET /orders/{id} 404 con mensaje 'No encontramos ese pedido'; GraphQL resumenPedido = null; el pedido de ana sin cambios",
  "Red (404 y respuesta GraphQL); log de orders; inspeccion del pedido de ana", "No modifica datos"),
 ("P15", "RC3", ["F07"], ["R16", "R17"], "fallo y recuperacion", "Mis pedidos con inventory detenido",
  "Si inventory falla, Mis pedidos muestra lo que pudo armar y avisa que la informacion esta incompleta; al volver inventory se ve completa",
  "Ana con pedidos; inventory detenido", "Abrir Mis pedidos; iniciar inventory; recargar",
  "Respuesta GraphQL con errors 'Servicio inventory no disponible'; aviso 'Informacion incompleta' y 'Producto (dato no disponible)'; despues, sin errors",
  "Red (respuesta con errors); log de graphql", "docker compose start inventory"),
 ("P16", "RC3", ["F07"], ["R15", "R16"], "rechazo y limite", "Permisos de campos y limites de GraphQL",
  "Un cliente no obtiene datos personales (cliente) ni reportes, y una consulta que excede el limite se rechaza",
  "Sesion de ana", "Desde la sesion enviar: consulta con el campo cliente; reporteVentas; consulta con 6 alias; consulta de mas de 2000 caracteres",
  "cliente = null con error de autorizacion; reporteVentas con error; la consulta de 6 alias se rechaza (limite 5) y la de mas de 2000 caracteres responde 422",
  "Respuestas GraphQL", "No modifica datos"),
 ("P17", "RC4", ["F04"], ["R05"], "exito", "Editar mi ficha",
  "Los cambios de la ficha quedan guardados en clients y se ven al recargar y en una sesion nueva",
  "Sesion de ana", "En Mi cuenta cambiar telefono y comuna; Guardar cambios; recargar",
  "PUT /clients/me 200; aviso 'Tus datos quedaron guardados'; valores nuevos al recargar y en otra sesion",
  "Red; log de clients ('actualiza clients.clientes'); inspeccion de clients.clientes USR-003", "No requiere"),
 ("P18", "RC4", ["F04"], ["R05"], "rechazo", "RUN invalido en la ficha",
  "Un RUN con digito verificador incorrecto se rechaza con un mensaje claro y la ficha no cambia",
  "Sesion de ana", "Escribir el RUN 12.345.678-9 y guardar", "PUT /clients/me 422; mensaje 'El RUN no es valido'; ficha sin cambios",
  "Red (422); inspeccion de clients.clientes antes y despues", "No requiere"),
 ("P19", "RC4", ["F03", "F04"], ["R15"], "rechazo", "Sesion expirada",
  "Con la sesion vencida en el servidor, la pagina protegida lleva a iniciar sesion con un aviso y no muestra datos",
  "Sesion de ana; su sesion vencida en auth (vencer_sesion.py)", "Abrir Mi cuenta",
  "GET /clients/me 401; redirige a login.php?expirada=1 con aviso; la sesion se borra de auth.sesiones",
  "Red (401); log de auth ('sesion expirada'); inspeccion de auth.sesiones", "Iniciar sesion de nuevo"),
 ("P20", "RC4", ["F04"], ["R15"], "rechazo", "Pagina protegida sin sesion",
  "Sin sesion, Mi cuenta lleva a iniciar sesion y la API responde 401 sin llamar al backend",
  "Visitante sin sesion", "Abrir cuenta.php; llamar GET /clients/me sin token",
  "Redirige a login.php; la API responde 401 'Bearer token requerido'", "Red; log del gateway ('sin token')", "No modifica datos"),
 ("P21", "RC4", ["F03"], ["R12", "R15"], "rechazo y exito", "Login fallido, login y cierre de sesion",
  "Una clave incorrecta se rechaza; al cerrar sesion el token deja de servir en el servidor",
  "Visitante", "Login con clave incorrecta; login correcto; Cerrar sesion; usar el token anterior",
  "401 'Correo o contrasena incorrectos'; 200 y 'Hola, Ana'; despues del logout el token anterior recibe 401",
  "Red; logs de auth (login rechazado, login correcto, logout)", "No requiere"),
 ("P22", None, ["F02"], ["R05", "R11"], "exito y rechazo", "Registro con verificacion de correo",
  "Un cliente nuevo no puede entrar hasta verificar su correo con el codigo; con el codigo correcto puede iniciar sesion",
  "Correo ficticio nuevo", "Registrarse; intentar entrar; leer el codigo en la bandeja simulada; verificar; iniciar sesion",
  "POST /auth/register 201; login 403 antes de verificar; verify-email 200; login 200",
  "Red; logs de auth, clients y notificaciones; inspeccion de auth.usuarios (correo_verificado) y notificaciones.correos", "No requiere"),
 ("P23", None, ["F09"], ["R07", "R10"], "exito", "Inventario del dueno: oferta, alta y baja",
  "Los cambios del dueno quedan en inventory y la carta los refleja",
  "Sesion de dueno@aromaycafe.test", "Oferta 2900 al Latte; agregar un producto; darlo de baja; revisar la carta",
  "PUT 200, POST 201, DELETE 204; la carta muestra la oferta, y el producto dado de baja no aparece",
  "Red; log de inventory; inspeccion de inventory.productos", "Quitar la oferta del Latte"),
 ("P24", None, ["F09", "F10"], ["R12", "R15"], "rechazo", "Rol sin permiso",
  "Un cliente que entra a Inventario o Despacho escribiendo la direccion recibe 403 del backend y no ve datos",
  "Sesion de ana", "Abrir inventario.php y despacho.php",
  "GET /admin/products 403 y GET /admin/dispatch-orders 403; aviso 'No tienes permiso'",
  "Red (403); log del gateway ('no tiene permiso')", "No modifica datos"),
 ("P25", None, ["F10"], ["R02", "R13"], "exito", "Despacho avanza el pedido pagado",
  "El encargado ve los pedidos pagados en orden de pago y los avanza solo por transiciones validas hasta Entregado",
  "Pedido pagado (P09) de tipo retiro; sesion de despacho@aromaycafe.test", "Marcar en preparacion, listo y entregado",
  "Tres PUT /status 200; el pedido sale de la lista al quedar Entregado; historial en orders",
  "Red; log de orders; inspeccion de orders.pedidos (historial)", "No requiere"),
 ("P26", None, ["F11"], ["R04"], "exito", "Ventas de la caja web",
  "El cajero ve la venta del pedido pagado con su folio y total en la caja CAJA-WEB-01",
  "Pedido pagado (P09); sesion de cajero@aromaycafe.test", "Abrir Ventas",
  "GET /admin/sales 200; fila con el folio y el total del pedido de P09", "Red; inspeccion de orders.pedidos (folio, caja)", "No modifica datos"),
 ("P27", None, ["F12"], ["R09"], "exito", "Reporte de ventas actualizado",
  "El reporte del dueno suma cada pedido pagado al momento del pago",
  "Sesion de dueno; al menos un pedido pagado", "Abrir Reportes; pagar un pedido nuevo con ana; Actualizar",
  "GET /admin/reports/sales 200; pedidos pagados aumenta en 1 y el total en el monto del pedido",
  "Red; logs de analitica; inspeccion de analitica.ventas", "No requiere"),
 ("P28", None, ["F12"], ["R09", "R17"], "fallo y recuperacion", "Analitica detenida y recuperacion",
  "Si analitica no responde, el pago igual se confirma y el reporte informa el error; al volver analitica, la venta se suma (reintento cada 30 s)",
  "analitica detenida; pedido pendiente de ana", "Pagar el pedido; abrir Reportes; iniciar analitica; esperar hasta 70 s; Actualizar",
  "Pago aprobado; Reportes muestra un error mientras analitica esta detenida; despues de iniciarla, el reporte incluye la venta",
  "Red; log de orders (reintento) y analitica; inspeccion de analitica.ventas", "docker compose start analitica"),
 ("P29", None, ["F13"], ["R06", "R10", "R12"], "exito y rechazo", "Administracion de usuarios y clientes",
  "El admin crea funcionarios, cambia perfiles (no el suyo) y registra clientes en el local",
  "Sesion de admin@aromaycafe.test", "Crear un cajero; cambiarlo a despacho; intentar cambiar el propio perfil; registrar un cliente en el local",
  "POST /admin/users 201; PUT /role 200; PUT del propio perfil 409; POST /admin/clients 201",
  "Red; inspeccion de auth.usuarios", "No requiere"),
 ("P30", None, ["F14"], ["R14"], "exito", "Formulario de contacto",
  "El mensaje enviado queda guardado y el admin lo ve en Administracion",
  "Visitante", "Enviar el formulario de contacto; el admin abre Administracion",
  "POST /contact 201 y aviso de gracias; el mensaje aparece en la tabla del admin",
  "Red; log de clients; inspeccion de clients.contacto", "No requiere"),
 ("P31", None, [], ["R15"], "control de backend", "Servicio llamado sin el secreto del gateway",
  "Un servicio privado rechaza una llamada que no trae el secreto de Vault, aunque venga desde la red interna",
  "Sistema en Docker", "docker compose exec clients python llamada_sin_secreto.py",
  "403 sin secreto y 403 con secreto falso; dos lineas 'llamada RECHAZADA' en inventory",
  "Salida del script; log de inventory", "No modifica datos"),
 ("P32", None, ["F01", "F03", "F04", "F05", "F06", "F07"], ["R18"], "responsivo", "Paginas sin desborde horizontal",
  "Las paginas principales se usan sin desborde horizontal en el viewport de la campana",
  "Sesion de ana", "Abrir index, catalogo, carrito, login, cuenta, mis-pedidos y pedido",
  "En cada pagina el ancho del documento no supera el del viewport", "Medicion del DOM y capturas", "No modifica datos"),
]

CAMPANAS = {
    "C1": {"nombre": "Escritorio, ejecucion 1", "viewport": {"width": 1366, "height": 768}, "dispositivo": None},
    "C2": {"nombre": "Movil, ejecucion 1", "viewport": None, "dispositivo": "Pixel 7"},
    "C3": {"nombre": "Escritorio, ejecucion 2", "viewport": {"width": 1366, "height": 768}, "dispositivo": None},
    "C4": {"nombre": "Movil, ejecucion 2", "viewport": None, "dispositivo": "Pixel 7"},
}

# Tildes para los textos (los datos se escriben sin tildes para no tocar identificadores como analitica.ventas)
PALABRAS = {
    "sesion": "sesión", "Sesion": "Sesión", "Pagina": "Página", "Paginas": "Páginas", "envio": "envío",
    "Analitica": "Analítica", "sesiones": "sesiones", "pagina": "página", "paginas": "páginas", "dueno": "dueño", "Dueno": "Dueño",
    "Duena": "Dueña", "duena": "dueña", "analitica": "analítica", "informacion": "información", "Informacion": "Información",
    "codigo": "código", "invalido": "inválido", "invalida": "inválida", "valido": "válido", "validas": "válidas",
    "contrasena": "contraseña", "transicion": "transición", "transiciones": "transiciones", "verificacion": "verificación",
    "autenticacion": "autenticación", "autorizacion": "autorización", "Administracion": "Administración",
    "administracion": "administración", "recuperacion": "recuperación", "preparacion": "preparación",
    "anulacion": "anulación", "despues": "después", "movil": "móvil", "ejecucion": "ejecución", "campana": "campaña",
    "operacion": "operación", "Critica": "Crítica", "critica": "crítica", "telefono": "teléfono", "direccion": "dirección",
    "digito": "dígito", "limite": "límite", "limites": "límites", "mas": "más", "Ordenes": "Órdenes", "ordenes": "órdenes",
    "Agregacion": "Agregación", "agregacion": "agregación", "medicion": "medición", "inspeccion": "inspección",
    "Inspeccion": "Inspección", "demas": "demás", "Boton": "Botón", "boton": "botón", "segun": "según", "estan": "están",
    "dia": "día", "existia": "existía", "Mostraba": "Mostraba", "exito": "éxito", "ficha": "ficha", "unica": "única",
    "Ademas": "Además", "ademas": "además", "Ingles": "Inglés", "region": "región", "electronico": "electrónico",
    "validacion": "validación", "Validacion": "Validación", "conexion": "conexión", "Revisa": "Revisa",
    "decision": "decisión", "decisiones": "decisiones", "plazo": "plazo", "comprension": "comprensión",
    "deberia": "debería", "carta": "carta", "articulo": "artículo", "quedo": "quedó", "envia": "envía",
    "envian": "envían", "solo": "solo", "despacho": "despacho", "rapido": "rápido", "ultimo": "último",
}
import re as _re
_PATRON = _re.compile(r"(?<![\w.@_=/-])(" + "|".join(sorted(PALABRAS, key=len, reverse=True)) + r")(?![\w.@_=/-])")


def tildes(texto):
    if isinstance(texto, list):
        return [tildes(t) for t in texto]
    if not isinstance(texto, str):
        return texto
    return _PATRON.sub(lambda m: PALABRAS[m.group(1)], texto)


if __name__ == "__main__":
    claves = ["id", "recorrido", "flujos", "requisitos", "escenario", "titulo", "criterio", "precondiciones",
              "procedimiento", "esperado", "verificacion", "restauracion"]
    pruebas = []
    for i, p in enumerate(PRUEBAS, start=1):
        d = dict(zip(claves, p))
        for campo in ("escenario", "titulo", "criterio", "precondiciones", "procedimiento", "esperado", "verificacion",
                      "restauracion"):
            d[campo] = tildes(d[campo])
        d["ca"] = f"CA{i:02d}"
        pruebas.append(d)
    flujos = []
    for f in FLUJOS:
        d = dict(zip(["id", "nombre", "rol", "pantalla", "servicios", "datos", "criticidad", "justificacion",
                      "estado_inicial", "requisitos", "dependencia"], f))
        for campo in ("nombre", "rol", "criticidad", "justificacion", "estado_inicial", "dependencia"):
            d[campo] = tildes(d[campo])
        flujos.append(d)
    salida = {"version": VERSION, "requisitos": {k: tildes(v) for k, v in REQUISITOS.items()}, "flujos": flujos,
              "criticos": {k: {"nombre": tildes(v[0]), "flujos": v[1], "cubre": tildes(v[2])} for k, v in CRITICOS.items()},
              "pruebas": pruebas, "campanas": CAMPANAS,
              "cambios": [dict(zip(["version", "fecha", "cambio", "motivo", "repetir"], [tildes(x) for x in c])) for c in CAMBIOS]}
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protocolo.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print(f"protocolo.json v{VERSION}: {len(pruebas)} pruebas, {len(flujos)} flujos, {len(REQUISITOS)} requisitos")
