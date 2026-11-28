# Informe – Evaluación 3: integración frontend–backend y validación basada en evidencias

| | |
|---|---|
| Caso | N° 4 – Cafetería "Aroma & Café" (basado en el Caso 19) |
| Integrantes | Ian Arroyo · Alejandro Martínez (NRC 8479) |
| Versión evaluada | Incremento I7, del 2026-11-28; protocolo de pruebas v1.1 |
| Resultado principal | 32 pruebas distintas × 4 campañas = **128 ejecuciones, 128 aprobadas**; 14 de 19 requisitos demostrados y 5 parcialmente demostrados |

## Índice

1. [Caso y alcance](#1-caso-y-alcance)
2. [Línea base](#2-línea-base)
3. [Criterios y protocolos](#3-criterios-y-protocolos)
4. [Estrategia incremental](#4-estrategia-incremental)
5. [Resultados](#5-resultados)
6. [Incidencias y correcciones](#6-incidencias-y-correcciones)
7. [Indicadores](#7-indicadores)
8. [Conclusiones](#8-conclusiones)
9. [Limitaciones y amenazas a la validez](#9-limitaciones-y-amenazas-a-la-validez)
10. [Componentes condicionales: analítica y gRPC](#10-componentes-condicionales-analítica-y-grpc)
11. [Cómo reproducir](#11-cómo-reproducir)
12. [Expediente](#12-expediente)

## 1. Caso y alcance

Aroma & Café vende en línea café y repostería, con retiro en el local o despacho gratis dentro de 3 km. En la Unidad 2 construimos el backend
seguro y en la Unidad 1 el frontend responsivo. En esta unidad **conectamos el frontend al backend real** y validamos de forma sistemática qué
flujos funcionan de punta a punta, en qué condiciones y con qué evidencias.

El alcance son **19 requisitos**: RF1–RF13 del caso (R01–R13) y 6 transversales (contacto, acceso protegido, GraphQL, tolerancia a fallos, diseño
responsivo e idempotencia). Abarcan **14 flujos** y 6 perfiles (visitante, cliente, dueño, administrador, encargado de despacho y cajero).

Se eligieron **4 recorridos críticos** para la validación profunda:

| Recorrido | Qué cubre | Servicios |
|---|---|---|
| RC1 Comprar: carta → carrito → pedido | Lectura y cambio persistente | inventory, orders (gRPC) |
| RC2 Pagar y obtener la boleta | Cambio persistente con dinero | payments, orders, notificaciones, analítica |
| RC3 Mis pedidos con GraphQL y pedido ajeno | Lectura agregada y acceso protegido | graphql, orders, inventory, payments |
| RC4 Mi cuenta y sesión | Acceso protegido y datos personales | auth, clients |

Detalle en [inventario de flujos](Expediente/02_inventario_flujos.md).

## 2. Línea base

El frontend inicial (Solemne 2, commit `c51e899` del 2026-11-09) **no llamaba al backend**. Lo medimos con `pruebas/linea_base.js`, sin hacer cambios:
- la carta estaba escrita a mano en el HTML;
- los botones de sesión tenían `href="#"`;
- "Pagar pedido" solo borraba el carrito del navegador;
- el contacto mostraba un "gracias" sin guardar nada;
- no existían las pantallas de cuenta, pedidos ni paneles.

El backend estaba completo pero sin consumidor y solo corría en local. Ficha del entorno, cuentas por rol, restauración y clasificación de las
dependencias en [línea base](Expediente/01_linea_base.md).

## 3. Criterios y protocolos

Cada prueba tiene un criterio de aceptación observable, precondiciones, procedimiento, resultado esperado, verificación y restauración
([protocolo](Expediente/03_protocolo_pruebas.md)). Los criterios se escribieron y se fijaron **antes** de ejecutar (protocolo v1.0, 2026-11-28).

Cada recorrido crítico tiene al menos un escenario exitoso, uno de rechazo o fallo y uno de límite o recuperación. La verificación no depende de la
pantalla que ejecutó la acción: se inspecciona MongoDB dentro del contenedor de cada servicio (`inspeccionar.py`) o se vuelve a leer en una sesión
nueva. Cada solicitud del frontend se vincula con los logs de cada servicio mediante su `X-Request-ID`.

El protocolo tuvo un cambio (v1.1, antes de la primera ejecución). P16 pedía una consulta GraphQL de profundidad 6, pero el esquema llega como
máximo a 4, así que se reemplazó por una consulta de más de 2.000 caracteres.

No se fijaron objetivos de rendimiento, así que **no se sacan conclusiones de rendimiento**.

## 4. Estrategia incremental

Primero se integró un flujo de solo lectura (la carta), después el despliegue en Docker, la autenticación y las operaciones protegidas, y por último
los cambios de estado críticos (pedido y pago), GraphQL y los paneles. Antes de cada incremento se repitieron las pruebas ya existentes. Cada
incremento, con su fecha y las diferencias de contrato que encontró (DC01–DC09), está en la [bitácora](Expediente/04_bitacora.md).

Cambios de arquitectura:
- todo el sistema en contenedores, con solo el frontend y el gateway publicados en 127.0.0.1;
- CORS limitado al frontend;
- idempotencia en la creación de pedidos;
- logs por paso con id de correlación en todos los servicios.

Los contratos que usa la interfaz están en [contratos](Expediente/08_contratos.md) y los diagramas en [diagramas](Expediente/10_diagramas.md).

## 5. Resultados

La suite `pruebas/suite_integracion.js` ejecutó las 32 pruebas desde el frontend (Chromium con Playwright) contra el sistema completo en Docker,
en 4 campañas independientes. Cada campaña partió de la base vacía:

| Campaña | Viewport | Resultado |
|---|---|---|
| C1 | Escritorio 1366×768 | 32/32 aprobadas |
| C2 | Móvil emulado Pixel 7 (412×839) | 32/32 aprobadas |
| C3 | Escritorio 1366×768 | 32/32 aprobadas |
| C4 | Móvil emulado Pixel 7 (412×839) | 32/32 aprobadas |

Cada ejecución (RUN) guarda la red con los `X-Request-ID`, las capturas, los logs de cada contenedor con esos ids y la inspección de MongoDB, con
claves y tokens enmascarados ([registro de ejecuciones](Expediente/05_ejecuciones.md), [índice de evidencias](Expediente/evidencias.md)).

Además, la regresión del backend de la Unidad 2 (42 pruebas en modo local) pasó 42/42 sobre la misma versión.

Ejemplo de cadena probatoria, P03 en C1 (crear un pedido):
1. **E-C1-P03-01** muestra el pedido creado en la pantalla.
2. **red.json** registra `POST /orders` con respuesta 201 y su `X-Request-ID`.
3. **logs.txt** muestra con ese mismo id:
   - el gateway validando con Auth;
   - orders guardando el pedido;
   - inventory recibiendo `ReservarStock` por gRPC.
4. **persistencia.json** confirma en `orders.pedidos` el pedido de USR-003 por $9.200, y en `inventory.productos` el stock que bajó de 40 a 38 y de 40 a 39.
5. Una sesión nueva ve el mismo estado.

## 6. Incidencias y correcciones

Se registraron **12 incidencias**, todas cerradas, con su origen, su causa (confirmada o hipótesis), su corrección y su nueva validación
([incidencias](Expediente/06_incidencias.md)). Algunos ejemplos:

- **INC-08.** Un doble envío creaba dos pedidos. Se agregó una clave de idempotencia y P07 lo comprueba ahora en las 4 campañas.
- **INC-10.** El ensayo 1 de la suite mostró que Reportes no permitía reintentar después de una falla. Se agregó "Reintentar" en 7 pantallas; el ensayo 2 y las 4 campañas lo validan.
- **INC-11.** En el mismo ensayo, una falla de P19 resultó ser un defecto de la **prueba**, no del sistema: la respuesta 401 sí estaba en `red.json`.
- **INC-05.** La portada quedaba vacía en Windows con las animaciones desactivadas. Lo reportó el equipo y venía del frontend original.

Los ensayos se conservan en `docs/evidencias/historial/` y no se suman a los resultados finales.

## 7. Indicadores

| Indicador | Resultado | Interpretación |
|---|---|---|
| Cobertura del diseño | 19 / 19 = **100 %** | Todos los requisitos tienen criterio y prueba (mide planificación) |
| Ejecución del plan | 32 / 32 = **100 %** | 0 bloqueadas y 0 no ejecutadas |
| Aprobación observada | 32 / 32 = **100 %** | 128 de 128 ejecuciones aprobadas; una prueba cuenta solo si se aprueba en las 4 campañas |
| Logro demostrado | 14 / 19 = **73,7 %** | R06, R08, R11, R17 y R18 solo están parcialmente demostrados y no se cuentan |

Detalle, evolución respecto de la línea base y matriz de conclusiones en [resultados](Expediente/07_resultados.md); matriz de trazabilidad editable
en [trazabilidad.csv](Expediente/trazabilidad.csv).

## 8. Conclusiones

**Por recorrido crítico:**
- **RC1 Comprar.** La carta muestra exactamente los productos activos de inventory. Un cliente crea un pedido con los precios del servidor, el
  stock se descuenta una sola vez y el pedido se ve igual al recargar y en otra sesión, en las 4 campañas. Se rechazan sin efectos el pedido sin
  sesión, fuera del radio y sin stock. Con inventory caído o lento, la interfaz informa y se recupera. No se probó concurrencia masiva.
- **RC2 Pagar.** Con el pago aprobado, el pedido queda PAGADO con boleta y folio, el pago queda APROBADO con el monto del servidor, y la boleta y la
  venta llegan a notificaciones y analítica. Un pago rechazado no cambia el pedido y un aviso repetido no duplica nada. **El proveedor es un doble
  de prueba**: se concluye sobre el contrato simulado, no sobre un proveedor real.
- **RC3 Mis pedidos.** La pantalla junta orders, inventory y payments en una consulta GraphQL y coincide con lo guardado. Un pedido ajeno no se
  muestra (404 en REST, `null` en GraphQL) y no cambia. Si inventory falla, la pantalla avisa que la información está incompleta. Los campos
  restringidos y las consultas excesivas se rechazan.
- **RC4 Mi cuenta y sesión.** La ficha se guarda en clients y persiste en otra sesión; un RUN inválido no cambia nada. Una sesión vencida o un token
  cerrado se rechazan en el servidor.

**Otros flujos:** registro con verificación, inventario del dueño, despacho, ventas, reportes, administración y contacto operan desde la interfaz
contra los servicios reales, con una prueba cada uno en las 4 campañas (ver la matriz de conclusiones).

**Conclusión global:** en el entorno evaluado (Docker en un equipo, datos ficticios, versión del 2026-11-28), los 14 flujos del caso funcionan de punta
a punta desde el frontend hasta los servicios reales, con persistencia, permisos, agregación GraphQL, gRPC y analítica verificables, en
escritorio y en móvil emulado.

Esto **no** permite afirmar que el sistema sea "totalmente seguro" ni que esté "listo para producción". Las pruebas cubren casos concretos, el
pago y el correo son simulados, y no se midieron rendimiento ni disponibilidad.

**Acciones pendientes:**

| Pendiente | Requisito | Riesgo que cubre |
|---|---|---|
| Probar en un celular físico y en otro navegador | R18 | Diferencias reales de dispositivo y navegador |
| Agregar pruebas de caída de auth, orders, payments y clients desde la interfaz | R17 | Comportamiento ante fallas no probadas |
| Probar el correo con un proveedor sandbox | R08, R11 | Envío real de correos |
| Completar el login del cliente registrado en el local | R06 | Flujo completo del registro en el local |
| Automatizar los controles que hoy son manuales: INC-02, INC-05, INC-07 e INC-12 | Varios | Que esos casos queden en la regresión |

## 9. Limitaciones y amenazas a la validez

| Amenaza | Detalle | Efecto sobre las conclusiones |
|---|---|---|
| Datos pequeños y sintéticos | 8 productos, 6 cuentas y pocos pedidos por campaña | No se concluye sobre volumen |
| Emulación móvil | Perfil Pixel 7 de Playwright; un solo motor (Chromium) | R18 queda parcial |
| Dobles de prueba | Proveedor de pagos y correo simulados | R08 y R11 quedan parciales; R02 se concluye sobre el contrato simulado |
| Entorno local | Todo en un equipo con Docker; Vault en modo desarrollo | No se concluye sobre red real ni disponibilidad |
| Observador que implementó el flujo | El mismo equipo escribió el código y las pruebas | Mitigado con criterios fijados antes y verificación en la base de datos, no solo en la pantalla |
| Entorno de ejecución de las campañas | Las campañas C1–C4 se ejecutaron en Linux con Docker (zona horaria UTC); no se repitieron en Windows | Los resultados corresponden a ese entorno; el procedimiento para repetirlas está en [cómo reproducir](#11-cómo-reproducir) |
| Límite del gateway subido durante las campañas | El límite general pasó de 120 a 600 solicitudes por minuto, porque el navegador de prueba sale de una sola IP; el de login no cambió | El límite general no se probó dentro de las campañas (sí en la Unidad 2) |
| Certificado aceptado por la prueba | El navegador automático usa `ignoreHTTPSErrors`; una persona lo acepta una vez | No cambia la validación de TLS entre servicios |

## 10. Componentes condicionales: analítica y gRPC

Se mantienen las decisiones de la Unidad 2:
- **Analítica** está separada de los servicios transaccionales y no recibe datos personales.
- **gRPC** se usa entre orders e inventory para reservar y devolver stock, con TLS y un plazo de 3 s.

Las dos se validaron desde el recorrido funcional:
- **Analítica:** el reporte del dueño suma cada pedido pagado al momento (P27). Si analítica está caída, el pago igual se confirma, orders reintenta y la venta llega al volver: entre 14 y 21 s después de iniciarla en las 4 campañas (P28).
- **gRPC:** la reserva y la devolución de stock se ven en P03 y P12. Con inventory en pausa, el pedido se rechaza después del plazo (entre 3,34 y 3,37 s) y se crea al reintentar (P08).

## 11. Cómo reproducir

```bash
cd "Evaluacion 3 - Integracion/Backend"
cp .env.example .env                       # cambiar los valores
docker compose up -d --build
cd pruebas
npm install
npx playwright install chromium
TEST_PASSWORD=<SEED_PASSWORD> node suite_integracion.js C1     # C1..C4; cada una deja la base en cero
python generar_documentos.py               # vuelve a generar ejecuciones, evidencias, resultados y trazabilidad
```

En PowerShell: `$env:TEST_PASSWORD="..."; node suite_integracion.js C1`.

La línea base se repite con `node linea_base.js "<carpeta Solemne 2/Frontend>"`.

El protocolo manual de interfaz responsiva es el mismo de la suite: las fichas de [protocolo](Expediente/03_protocolo_pruebas.md), en un
navegador de escritorio y en un celular.

## 12. Expediente

| Documento | Contenido |
|---|---|
| [01 Línea base](Expediente/01_linea_base.md) | Estado inicial, componentes reales y simulados, ficha del entorno, inicio y restauración |
| [02 Inventario de flujos](Expediente/02_inventario_flujos.md) | Requisitos, flujos con riesgo y recorridos críticos |
| [03 Protocolo](Expediente/03_protocolo_pruebas.md) | Criterios de aceptación y fichas de prueba (v1.1) |
| [04 Bitácora](Expediente/04_bitacora.md) | Incrementos por fecha, diferencias de contrato y subidas al repositorio |
| [05 Ejecuciones](Expediente/05_ejecuciones.md) | Registro de las 128 ejecuciones |
| [06 Incidencias](Expediente/06_incidencias.md) | Incidencias, causas, correcciones y revalidación |
| [07 Resultados](Expediente/07_resultados.md) | Conteos, indicadores, evolución y matriz de conclusiones |
| [08 Contratos](Expediente/08_contratos.md) | Rutas que usa el frontend y cambios de contrato |
| [09 Contribuciones](Expediente/09_contribuciones.md) | Aportes de cada integrante |
| [10 Diagramas](Expediente/10_diagramas.md) | Vistas C4 y recorrido de una solicitud |
| [Evidencias](Expediente/evidencias.md) | Índice de evidencias con sus rutas |
| [Trazabilidad](Expediente/trazabilidad.csv) | Matriz editable: requisito → flujo → pantalla → rol → servicio → criterio → prueba → ejecución → evidencia → conclusión |
