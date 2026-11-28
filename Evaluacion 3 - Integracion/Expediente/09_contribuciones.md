# 9. Contribuciones

Aportes de cada integrante por área de trabajo, con el material del repositorio que los respalda.

| Área | Ian Arroyo | Alejandro Martínez | Respaldo |
|---|---|---|---|
| Línea base y alcance (Etapa 1) | Ficha del entorno, cuentas por rol y restauración | Medición del estado inicial del frontend, inventario de flujos, criticidad y selección de recorridos críticos | `01_linea_base.md`, `02_inventario_flujos.md`, `docs/evidencias/LB` |
| Criterios y protocolo (Etapa 2) | Fichas de las pruebas técnicas (idempotencia, gRPC, GraphQL, fallos controlados) | Criterios de aceptación de los flujos y fichas de las pruebas de interfaz, permisos y paneles | `03_protocolo_pruebas.md`, `pruebas/protocolo_datos.py` |
| Integración (Etapa 3) | Carta y CORS (I1), despliegue en Docker (I2), pedido, pago e idempotencia (I4) | Login, registro, mi cuenta, inventario y contacto (I3), paneles por rol y registro de clientes en el local (I5–I6) | `04_bitacora.md`, `Frontend/`, `Backend/` |
| Ejecución y evidencias (Etapa 4) | Suite de integración y campañas C1–C4 | Línea base (LB01–LB05), revisión de las evidencias y del registro de ejecuciones | `pruebas/suite_integracion.js`, `pruebas/linea_base.js`, `05_ejecuciones.md`, `evidencias.md` |
| Corrección y revalidación (Etapa 5) | INC-02, INC-03, INC-08, INC-09, INC-10, INC-11 | INC-01, INC-04, INC-05, INC-06, INC-07, INC-12 | `06_incidencias.md` |
| Análisis y conclusiones (Etapa 6) | Conteos e indicadores | Matriz de conclusiones, amenazas a la validez y acciones pendientes | `07_resultados.md`, `trazabilidad.csv` |
| Arquitectura y contratos | Contratos que usa el frontend | Modelo C4 y diagramas exportados | `08_contratos.md`, `10_diagramas.md`, `docs/arquitectura/AromaCafe.dsl` |
| Informe y defensa | Redacción de resultados, incidencias e indicadores del informe | Redacción de caso, alcance, línea base y conclusiones del informe | `Informe.md` |

## Revisión del protocolo entre integrantes

| Versión | Escrito por | Revisado por | Observaciones |
|---|---|---|---|
| 1.0 | Ian Arroyo y Alejandro Martínez | Alejandro Martínez (pruebas técnicas) e Ian Arroyo (pruebas de interfaz) | Cada integrante revisó las fichas escritas por el otro |
| 1.1 | Ian Arroyo | Alejandro Martínez | Cambio de P16 (consulta de más de 2000 caracteres en vez de profundidad 6) |
