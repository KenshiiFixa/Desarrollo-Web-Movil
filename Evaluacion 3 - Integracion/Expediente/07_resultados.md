# 7. Resultados, indicadores y conclusiones

Versión evaluada: incremento I7, del 2026-11-28 (protocolo v1.1). Campañas: C1 (Escritorio, ejecución 1), C2 (Móvil, ejecución 1), C3 (Escritorio, ejecución 2), C4 (Móvil, ejecución 2).

## Conteos

| | Cantidad |
|---|---|
| Pruebas distintas planificadas | 32 |
| Ejecuciones (pruebas × campañas) | 128 |
| Ejecuciones aprobadas / fallidas / bloqueadas / no ejecutadas | 128 / 0 / 0 / 0 |
| Pruebas distintas aprobadas en las 4 campañas | 32 |
| Pruebas distintas con alguna falla (intermitentes o fallidas) | 0 |
| Pruebas distintas bloqueadas / no ejecutadas | 0 / 0 |

Criterio de consolidación (definido en el protocolo antes de ejecutar): una prueba distinta cuenta como aprobada solo si se aprueba en las cuatro campañas.

## Indicadores

| Indicador | Cálculo | Resultado | Cuidado de interpretación |
|---|---|---|---|
| Cobertura del diseño | requisitos con criterios y pruebas / requisitos en alcance = 19 / 19 | **100.0 %** | Mide planificación, no logro |
| Ejecución del plan | pruebas distintas con resultado aprobado o fallido / planificadas = 32 / 32 | **100.0 %** | Bloqueadas: 0; no ejecutadas: 0 |
| Aprobación observada | pruebas distintas aprobadas / pruebas distintas ejecutadas = 32 / 32 | **100.0 %** | Repeticiones: 128 de 128 ejecuciones aprobadas |
| Logro demostrado | requisitos demostrados / requisitos en alcance = 14 / 19 | **73.7 %** | 5 requisitos parcialmente demostrados no se cuentan (R06, R08, R11, R17, R18) |

Los porcentajes describen esta versión en este entorno; no son una probabilidad de éxito en producción.

## Evolución respecto de la línea base

| Flujo | Línea base (frontend de la Solemne 2) | Versión evaluada |
|---|---|---|
| F01 Consultar la carta | Productos escritos a mano en el HTML (sin API) | Integrado; 3 de 3 pruebas aprobadas en las 4 campañas |
| F02 Registro con verificación de correo | Botón Registrarse sin destino | Integrado; 1 de 1 pruebas aprobadas en las 4 campañas |
| F03 Iniciar y cerrar sesión | Botón Iniciar sesión sin destino | Integrado; 3 de 3 pruebas aprobadas en las 4 campañas |
| F04 Mi cuenta (ver y editar ficha) | No existía | Integrado; 5 de 5 pruebas aprobadas en las 4 campañas |
| F05 Crear pedido desde el carrito | Pagar solo vaciaba el carrito local | Integrado; 7 de 7 pruebas aprobadas en las 4 campañas |
| F06 Pagar pedido y obtener boleta | No existía | Integrado; 4 de 4 pruebas aprobadas en las 4 campañas |
| F07 Mis pedidos (GraphQL) y detalle | No existía | Integrado; 5 de 5 pruebas aprobadas en las 4 campañas |
| F08 Anular pedido | No existía | Integrado; 1 de 1 pruebas aprobadas en las 4 campañas |
| F09 Inventario del dueño | No existía | Integrado; 3 de 3 pruebas aprobadas en las 4 campañas |
| F10 Órdenes de despacho | No existía | Integrado; 2 de 2 pruebas aprobadas en las 4 campañas |
| F11 Ventas de la caja web | No existía | Integrado; 1 de 1 pruebas aprobadas en las 4 campañas |
| F12 Reporte de ventas | No existía | Integrado; 2 de 2 pruebas aprobadas en las 4 campañas |
| F13 Administración de usuarios y clientes | No existía | Integrado; 1 de 1 pruebas aprobadas en las 4 campañas |
| F14 Contacto | Mostraba éxito sin guardar nada | Integrado; 1 de 1 pruebas aprobadas en las 4 campañas |

## Matriz de conclusiones

Clasificación: **demostrado** en el entorno evaluado, **parcial** o **no demostrado**.

| Requisito | Afirmación | Criterios | Ejecuciones y evidencias | Resultado | Límite de validez | Riesgo pendiente / próxima acción |
|---|---|---|---|---|---|---|
| R01 Armar un pedido con los productos disponibles de la carta (RF1) | Un cliente arma un pedido con productos de la carta; el pedido y el stock quedan guardados | CA01, CA03, CA05, CA06 | P01×4, P03×4, P05×4, P06×4 → [registro](05_ejecuciones.md) | **demostrado** | Datos ficticios; un solo local | — |
| R02 El pedido se prepara solo cuando el pago esta confirmado (RF2) | El pedido pasa a PAGADO solo con el aviso firmado del proveedor y solo entonces aparece en despacho | CA09, CA10, CA25 | P09×4, P10×4, P25×4 → [registro](05_ejecuciones.md) | **demostrado** | Proveedor real no probado: doble de prueba | — |
| R03 Anular una compra indicando el motivo (RF3) | Anular un pedido pendiente exige motivo, lo deja ANULADO y devuelve el stock | CA12 | P12×4 → [registro](05_ejecuciones.md) | **demostrado** | No se probó anular desde la cuenta del admin | — |
| R04 Vender solo a clientes registrados; ventas web en la caja del cajero virtual (RF4) | Sin sesión no se compra; la venta pagada queda en la caja CAJA-WEB-01 | CA03, CA04, CA09, CA26 | P03×4, P04×4, P09×4, P26×4 → [registro](05_ejecuciones.md) | **demostrado** | — | — |
| R05 Registro y ficha del cliente con RUN, dirección, comuna, teléfono y otros datos (RF5) | El registro guarda los datos del cliente y la ficha se edita y valida (RUN) | CA17, CA18, CA22 | P17×4, P18×4, P22×4 → [registro](05_ejecuciones.md) | **demostrado** | Solo se probó un RUN inválido y algunos campos | — |
| R06 El administrador registra clientes en el local (RF6) | El admin registra un cliente en el local (cuenta creada sin verificar) | CA29 | P29×4 → [registro](05_ejecuciones.md) | **parcial** | No se probó que ese cliente verifique su correo e inicie sesión | Agregar a la suite la verificación y el login del cliente registrado en el local |
| R07 Consultar y actualizar disponibilidad, precio y oferta de los productos (RF7) | El dueño cambia oferta y stock, agrega y da de baja productos, y la carta lo refleja | CA01, CA06, CA23 | P01×4, P06×4, P23×4 → [registro](05_ejecuciones.md) | **demostrado** | — | — |
| R08 Boleta digital por cada venta, enviada al correo del cliente (RF8) | Cada venta genera su boleta y un correo de boleta en la bandeja simulada | CA09 | P09×4 → [registro](05_ejecuciones.md) | **parcial** | Correo simulado: no se probó el envío real | Conectar un proveedor de correo en sandbox y verificar la recepción |
| R09 Reporte de ventas para el dueño (RF9) | El reporte del dueño suma cada pedido pagado al momento | CA27, CA28 | P27×4, P28×4 → [registro](05_ejecuciones.md) | **demostrado** | Pocos datos (ventas de una campaña) | — |
| R10 Mantenedores de productos, usuarios y clientes (RF10) | Mantenedores de productos y usuarios operan desde la interfaz | CA23, CA29 | P23×4, P29×4 → [registro](05_ejecuciones.md) | **demostrado** | Edición de clientes por el admin no probada en la interfaz | — |
| R11 Validar el correo con un código enviado por la API de mensajeria (RF11) | Sin el código no se inicia sesión; con el código correcto sí | CA22 | P22×4 → [registro](05_ejecuciones.md) | **parcial** | API de mensajería simulada (doble de prueba) | Igual que R08 |
| R12 Autenticacion y acceso según el perfil asignado por el administrador (RF12) | Login, logout y acceso por perfil; el admin cambia perfiles salvo el propio | CA21, CA24, CA29 | P21×4, P24×4, P29×4 → [registro](05_ejecuciones.md) | **demostrado** | No se probó que el usuario con perfil cambiado deba volver a iniciar sesión | — |
| R13 Órdenes de despacho en el orden en que se pagan (RF13) | Despacho ve los pedidos pagados y los avanza solo por transiciones válidas | CA25 | P25×4 → [registro](05_ejecuciones.md) | **demostrado** | Solo un pedido de retiro por campaña | — |
| R14 Formulario de contacto publico (pantalla Contacto) | El mensaje de contacto se guarda y el admin lo ve | CA30 | P30×4 → [registro](05_ejecuciones.md) | **demostrado** | — | — |
| R15 Acceso protegido: sin sesión, sesión expirada, rol sin permiso y recurso ajeno se rechazan sin modificar datos | Sin sesión, sesión expirada, rol sin permiso, pedido ajeno y servicio sin secreto se rechazan sin modificar datos | CA04, CA14, CA16, CA19, CA20, CA21, CA24, CA31 | P04×4, P14×4, P16×4, P19×4, P20×4, P21×4, P24×4, P31×4 → [registro](05_ejecuciones.md) | **demostrado** | Casos probados; no es una auditoría completa de seguridad | — |
| R16 Agregación GraphQL de orders, inventory y payments en una pantalla real, con permisos y límites | Mis pedidos junta orders, inventory y payments en una consulta, con permisos y límites | CA13, CA15, CA16 | P13×4, P15×4, P16×4 → [registro](05_ejecuciones.md) | **demostrado** | Límite de profundidad no ejecutable con este esquema (ver protocolo 1.1) | — |
| R17 Ante una dependencia privada caida o lenta, mensaje comprensible y recuperación coherente | Con inventory detenido o lento y con analítica detenida, la interfaz informa y se recupera | CA02, CA08, CA15, CA28 | P02×4, P08×4, P15×4, P28×4 → [registro](05_ejecuciones.md) | **parcial** | No se probaron caídas de auth, orders, payments ni clients desde la interfaz | Agregar pruebas de caída de auth, orders, payments y clients desde la interfaz |
| R18 Frontend responsivo: las acciones funcionan en escritorio y móvil contra el mismo backend | Las 32 pruebas pasan en escritorio y en móvil emulado, sin desborde horizontal | CA32 | P32×4 → [registro](05_ejecuciones.md) | **parcial** | Emulación móvil, sin dispositivo físico; un solo navegador (Chromium) | Repetir los recorridos críticos en un celular físico y en otro navegador |
| R19 Una operación crítica reintentada no produce efectos duplicados (pedido y aviso de pago) | Un pedido reenviado y un aviso de pago repetido no duplican efectos | CA07, CA11 | P07×4, P11×4 → [registro](05_ejecuciones.md) | **demostrado** | Dos envíos simultáneos; no se probó concurrencia masiva | — |
