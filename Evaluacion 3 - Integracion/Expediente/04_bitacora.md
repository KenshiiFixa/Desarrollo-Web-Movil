# 4. Bitácora de integración

Estrategia: primero un flujo acotado de lectura (la carta), después el despliegue, la autenticación y las operaciones protegidas,
y al final los cambios de estado críticos (pedido y pago), la agregación GraphQL y los paneles. Antes de cada incremento nuevo se repitieron
las pruebas de los flujos ya integrados (regresión). Los commits son del repositorio de trabajo `desarrollo-web-movil---sem-2`; las entregas al
repositorio principal están al final.

| Inc. | Fecha | Commit | Flujo | Diferencia de contrato encontrada | Cambio realizado | Prueba asociada | Estado | Siguiente acción |
|---|---|---|---|---|---|---|---|---|
| I1 | 2026-11-16 | `747d250` | F01 Carta | **DC01** nombres con tilde distintos ("Frappé" en el frontend, "Frappe" en el backend). **DC02** el gateway no enviaba cabeceras CORS: el navegador bloqueaba la respuesta | Nombres con tilde en el backend (UTF-8 de punta a punta); CORS solo para `http://localhost:8080`; la carta se arma con `GET /products` con estados de carga, vacío y error | Prueba de navegador del avance 1 y curl de CORS ([historial](../Backend/docs/evidencias/historial/avance-1/prueba_frontend.txt)); hoy P01 y P02 | Integrado | Desplegar en contenedores |
| I1 | 2026-11-16 | `747d250` | Transversal | **DC03** un token con formato inválido (menos de 10 caracteres) hacía que Auth respondiera 422 y el gateway devolviera 502 | El gateway trata ese 422 como token inválido y responde 401 | Prueba manual con curl ([INC-02](06_incidencias.md)) | Corregido | — |
| I2 | 2026-11-16 | `1bc9cdd` | Todos | El backend solo corría en local | `docker-compose.yml` con un contenedor por componente, Vault con HTTPS, certificado con el nombre de cada contenedor y red privada `internal` | Regresión del backend 22/22, 17/17 y 3/3; flujos principales por API en Docker | Integrado | Autenticación en el frontend |
| I3 | 2026-11-16 | `34bd7c2` | F02, F03, F04, F09, F14 | **DC04** el nombre del usuario no viene en el login, solo el token y el rol. **DC05** los mensajes del backend vienen sin tildes | Después del login se pide `GET /clients/me` para el saludo; tabla de mensajes en el frontend; páginas de login, registro con código, mi cuenta, inventario y contacto | Prueba de navegador del avance 3 (30/30, [historial](../Backend/docs/evidencias/historial/avance-1/prueba_frontend.txt)) | Integrado | Corregir lo visto en las capturas ([INC-04](06_incidencias.md)) |
| I3 | 2026-11-17 | `fe81a08` | Portada y carta | Con las animaciones desactivadas en Windows, la portada quedaba en blanco | El CSS muestra directamente lo que entraba con animación | Revisión en Chromium con `reducedMotion: reduce` ([INC-05](06_incidencias.md)) | Corregido | — |
| I3 | 2026-11-16 | `b2f1df7` | Transversal | — | `llamada_sin_secreto.py` para demostrar el rechazo de una llamada sin el secreto | Hoy P31 | Integrado | — |
| I3 | 2026-11-22 | `7f75865` | — | — | Limpieza de comentarios (sin cambio de comportamiento) | Regresión del backend 42/42 y navegador 30/30 | Sin cambio funcional | — |
| I4 | 2026-11-28 | `7f6ebb9` | F05, F06, F07, F08 | **DC06** el carrito guardaba el precio del navegador; el contrato de `POST /orders` solo acepta productos y cantidades. **DC07** un doble envío creaba dos pedidos. **DC08** GraphQL entrega los campos en camelCase (`tipoEntrega`, `creadoEn`) | El precio final lo muestra la pantalla del pedido con el total del servidor; campo `clave` (idempotencia) en `POST /orders`, que responde 200 y `repetido: true` si se repite; el frontend usa los nombres camelCase de GraphQL | Recorrido completo en el navegador (pedido, rechazo y aprobación del pago, boleta, Mis pedidos, pedido ajeno); hoy P03 a P16 | Integrado | Paneles por rol |
| I4 | 2026-11-28 | `7f6ebb9` | F05 | El carrito armaba sus filas con `innerHTML` usando el nombre del producto (que ahora viene de la API) | Las filas se arman con `textContent` | Revisión de código ([INC-07](06_incidencias.md)) | Corregido | — |
| I5 | 2026-11-28 | `7f6ebb9` | F10, F11, F12, F13 | **DC09** el reporte por día solo existe en REST (`/admin/reports/sales`); GraphQL `reporteVentas` no lo trae | Reportes usa la ruta REST; GraphQL se mantiene en Mis pedidos. Paneles de despacho, ventas, reportes y administración; portada con destacados de la API; cada rol llega a su panel al iniciar sesión | Paneles en el navegador; hoy P24 a P30 | Integrado | Protocolo de pruebas |
| I6 | 2026-11-28 | `17fafb2` | F13 | R06 no tenía pantalla | Formulario "Registrar cliente en el local" en Administración | Hoy P29 | Integrado | Ejecutar el protocolo |
| — | 2026-11-28 | `17fafb2` | — | — | **Protocolo de pruebas v1.0** subido antes de ejecutar | — | — | Implementar la suite |
| I7 | 2026-11-28 | `61efbab` | Todos | Ensayo 1 de la suite: 30/32 ([INC-10](06_incidencias.md) y [INC-11](06_incidencias.md)) | "Reintentar" en todas las cargas fallidas; corrección de la suite; el aviso flotante ya no bloquea clics ([INC-09](06_incidencias.md)); protocolo v1.1 (P16) | Ensayo 2: P15, P19 y P28 aprobadas; regresión del backend 42/42 | **Versión evaluada** | Campañas oficiales |
| — | 2026-11-28 | `d2b3ad2` | Todos | — | Campañas C1–C4 sobre `61efbab` | 128/128 ejecuciones aprobadas ([registro](05_ejecuciones.md)) | Cerrado | Informe |

## Entregas al repositorio principal (`Desarrollo-Web-Movil`)

| Fecha | Commit | Mensaje | Contenido |
|---|---|---|---|
| 2026-11-09 | `c51e899` | Evaluacion 2 - Frontend y Backend | Línea base de esta unidad |
| 2026-11-22 | `b108b20` | Avance 1 | Incrementos I1–I3 |
| 2026-11-22 | `d39d072` | Readme eliminado | Cambio del equipo en el repositorio principal |
| 2026-11-22 | `612e654` | Actualizacion - Avance 1 | Limpieza de comentarios |

## Contratos

Los contratos que usa el frontend, con sus cambios, están en [08_contratos.md](08_contratos.md).
