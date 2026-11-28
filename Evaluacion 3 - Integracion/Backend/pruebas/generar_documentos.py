"""Genera los documentos del expediente (carpeta Expediente/) a partir de protocolo.json y, cuando existen,
de los resultados de las ejecuciones (docs/evidencias/<campana>/resultados.json).

Uso:  python pruebas/generar_documentos.py
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(AQUI)
RAIZ = os.path.dirname(BACKEND)
EXPEDIENTE = os.path.join(RAIZ, "Expediente")
PROTOCOLO = json.load(open(os.path.join(AQUI, "protocolo.json"), encoding="utf-8"))


def escribir(nombre, lineas):
    os.makedirs(EXPEDIENTE, exist_ok=True)
    with open(os.path.join(EXPEDIENTE, nombre), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas).rstrip() + "\n")
    print("generado Expediente/" + nombre)


def celda(texto):
    return str(texto).replace("|", "\\|").replace("\n", " ")


def inventario_flujos():
    req = PROTOCOLO["requisitos"]
    pruebas_por_flujo = {}
    for p in PROTOCOLO["pruebas"]:
        for f in p["flujos"]:
            pruebas_por_flujo.setdefault(f, []).append(p)
    L = ["# 2. Inventario de flujos, requisitos y recorridos críticos", "",
         f"Generado desde `Backend/pruebas/protocolo.json` (protocolo v{PROTOCOLO['version']}).", "",
         "## Requisitos en alcance", "",
         "Se mantienen los requisitos de la Unidad 2 (RF1–RF13 → R01–R13) y se agregan requisitos transversales (R14–R19).", "",
         "| ID | Requisito |", "|---|---|"]
    L += [f"| {k} | {celda(v)} |" for k, v in req.items()]
    L += ["", "## Inventario de flujos", "",
          "Criticidad según el efecto de un fallo sobre usuarios, datos y negocio. Responsables: equipo (Ian Arroyo y Alejandro Martínez).", "",
          "| ID | Flujo | Rol | Pantalla | Servicios y protocolos | Datos afectados | Criticidad y justificación | Estado inicial (línea base) | Requisitos | Dependencia externa | Criterios |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in PROTOCOLO["flujos"]:
        cas = ", ".join(p["ca"] for p in pruebas_por_flujo.get(f["id"], []))
        L.append(f"| {f['id']} | {celda(f['nombre'])} | {celda(f['rol'])} | {celda(f['pantalla'])} | {celda(f['servicios'])} | "
                 f"{celda(f['datos'])} | **{f['criticidad']}**: {celda(f['justificacion'])} | {celda(f['estado_inicial'])} | "
                 f"{', '.join(f['requisitos'])} | {celda(f['dependencia'])} | {cas} |")
    L += ["", "## Recorridos críticos (validación profunda)", "",
          "Cubren lectura, cambio persistente de estado y acceso protegido, e incluyen inventory, orders, clients y payments. "
          "Los demás flujos siguen en alcance con al menos una prueba cada uno.", "",
          "| ID | Recorrido | Flujos | Qué cubre | Pruebas (éxito / rechazo o fallo / límite o recuperación) |", "|---|---|---|---|---|"]
    for k, c in PROTOCOLO["criticos"].items():
        ps = [p for p in PROTOCOLO["pruebas"] if p["recorrido"] == k]
        L.append(f"| {k} | {celda(c['nombre'])} | {', '.join(c['flujos'])} | {celda(c['cubre'])} | "
                 + "; ".join(f"{p['id']} ({p['escenario']})" for p in ps) + " |")
    escribir("02_inventario_flujos.md", L)


def protocolo():
    L = ["# 3. Criterios de aceptación y protocolo de pruebas", "",
         f"**Versión del protocolo: {PROTOCOLO['version']}.** Se definió y se subió al repositorio **antes** de la primera ejecución; "
         "los cambios posteriores quedan en la sección *Cambios del protocolo* con su motivo y las pruebas que se repitieron.", "",
         "## Reglas comunes", "",
         "- **Entorno:** sistema completo en Docker (`docker compose up -d` en `Backend/`), frontend en `http://localhost:8080`, "
         "gateway en `https://127.0.0.1:8000`. Versión: la del incremento I7 (2026-11-28).",
         "- **Estado inicial controlado:** cada campaña parte de la base vacía (`docker compose down -v` y `docker compose up -d`); "
         "los servicios crean los datos ficticios de prueba (8 productos con stock 40 y 6 cuentas, una por perfil).",
         "- **Cuentas:** `ana@` y `pedro@` (cliente), `dueno@`, `admin@`, `despacho@` y `cajero@` (`@aromaycafe.test`), clave = `SEED_PASSWORD` del `.env`.",
         "- **Campañas:** C1 y C3 en escritorio (1366×768); C2 y C4 en móvil emulado (perfil Pixel 7 de Playwright: viewport 412×839, pantalla 412×915, táctil). Cada prueba se ejecuta en las cuatro.",
         "- **Ejecución:** cada prueba se inicia desde el frontend en Chromium (Playwright), salvo P31, que es un control de backend. "
         "Las solicitudes directas desde la sesión del navegador (P07, P11, P16) se usan solo donde la interfaz no permite provocar el caso "
         "(doble envío, aviso repetido del proveedor, consultas GraphQL fuera de la pantalla).",
         "- **Verificación independiente de la pantalla:** inspección de MongoDB con `inspeccionar.py` (dentro del contenedor del servicio, "
         "con su propio usuario) o lectura posterior en una sesión nueva.",
         "- **Vinculación:** cada solicitud del frontend lleva el `X-Request-ID` que crea el gateway; con él se extraen los logs de cada servicio.",
         "- **Estados:** *aprobada* (lo observado cumple el criterio), *fallida* (no lo cumple), *bloqueada* (no se pudo ejecutar por una causa "
         "externa a la prueba) y *no ejecutada*. Un rechazo previsto que el sistema aplica correctamente cuenta como aprobado.",
         "- **Repeticiones e intermitencia:** una prueba distinta se considera aprobada en la versión final solo si se aprueba en las cuatro "
         "campañas; si falla en alguna, se informa como intermitente y no se cuenta como aprobada.",
         "- **Rendimiento:** no se fijan objetivos de tiempo ni de carga en esta evaluación; solo se registra la duración de cada prueba como dato. "
         "Por eso el informe no saca conclusiones de rendimiento (la prueba de carga es de la Unidad 2).",
         "- **Protección:** las evidencias enmascaran contraseñas, tokens y cabeceras `Authorization`.", "",
         "## Fichas de prueba", ""]
    for p in PROTOCOLO["pruebas"]:
        L += [f"### {p['id']} · {p['titulo']}", "",
              "| Campo | Contenido |", "|---|---|",
              f"| Identificación | {p['id']} · {p['ca']} · Flujos: {', '.join(p['flujos']) or '—'} · Requisitos: {', '.join(p['requisitos'])}"
              + (f" · Recorrido crítico {p['recorrido']}" if p['recorrido'] else "") + f" · Escenario: {p['escenario']} |",
              f"| Criterio de aceptación ({p['ca']}) | {celda(p['criterio'])} |",
              f"| Precondiciones | {celda(p['precondiciones'])} |",
              f"| Procedimiento | {celda(p['procedimiento'])} |",
              f"| Resultado esperado | {celda(p['esperado'])} |",
              f"| Verificación | {celda(p['verificacion'])} |",
              f"| Restauración | {celda(p['restauracion'])} |", ""]
    L += ["## Cambios del protocolo", "", "| Versión | Fecha | Cambio | Motivo | Pruebas que se repiten |", "|---|---|---|---|---|"]
    L += [f"| {c['version']} | {c['fecha']} | {celda(c['cambio'])} | {celda(c['motivo'])} | {celda(c['repetir'])} |"
          for c in PROTOCOLO["cambios"]]
    escribir("03_protocolo_pruebas.md", L)


# ---------------------------------------------------------------- Resultados de las campanas
EVIDENCIAS = os.path.join(BACKEND, "docs", "evidencias")
CAMPANAS = ["C1", "C2", "C3", "C4"]


def cargar_resultados():
    datos = {}
    for c in CAMPANAS:
        ruta = os.path.join(EVIDENCIAS, c, "resultados.json")
        if os.path.exists(ruta):
            datos[c] = json.load(open(ruta, encoding="utf-8"))
            # Nombre de la campana con tildes para los documentos
            m = datos[c]["meta"]
            m["nombre"] = m["nombre"].replace("ejecucion", "ejecución").replace("Movil", "Móvil")
    return datos


def enlace(ruta):
    return f"../Backend/docs/evidencias/{ruta}"


def ejecuciones(datos):
    L = ["# 5. Registro de ejecuciones", "",
         "Generado desde `Backend/docs/evidencias/<campaña>/resultados.json`. Cada fila es una ejecución (RUN) de una prueba en una campaña. "
         "Las campañas parten de la base vacía. Los ensayos previos a la versión evaluada están en `docs/evidencias/historial/` "
         "y no se suman a estos resultados.", "",
         "## Campañas", "",
         "| Campaña | Nombre | Inicio | Fin | Zona horaria | Ejecutor | Navegador | Viewport | Docker | Estado inicial | Configuración declarada | Resultado |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, d in datos.items():
        m = d["meta"]
        L.append(f"| {c} | {m['nombre']} | {m['inicio']} | {m['fin']} | {m['zona_horaria']} | {m['ejecutor']} | "
                 f"{m['navegador']} | {m['viewport']} | {m['docker']} | {m['estado_inicial']} | Límite general del gateway: {m['limite_general_gateway']} | "
                 + ", ".join(f"{v} {k}" for k, v in d["conteo"].items()) + " |")
    L += ["", "La emulación móvil (C2 y C4) usa el perfil Pixel 7 de Playwright (viewport 412×839, pantalla 412×915, táctil). "
          "No equivale a probar un dispositivo físico.", "", "## Ejecuciones", "",
          "| RUN | Prueba | CA | Estado | Inicio | Duración | Evidencias | Vinculación (extracto) | Notas |", "|---|---|---|---|---|---|---|---|---|"]
    for c, d in datos.items():
        for r in d["resultados"]:
            evs = " ".join(f"[{e['id'].split('-')[-1]}]({enlace(e['ruta'])})" for e in r["evidencias"])
            vin = "; ".join(v for v in r["vinculacion"] if v.startswith("pedido") or v.startswith("clave"))[:120] or (r["vinculacion"][0] if r["vinculacion"] else "")
            L.append(f"| {r['run']} | {r['id']} {celda(r['titulo'])} | {r['ca']} | **{r['estado']}** | {r['inicio'][11:19]} | {r['duracion_ms'] / 1000:.1f} s | {evs} | "
                     f"{celda(vin)} | {celda('; '.join(r['notas']))} |")
    L += ["", "## Detalle de una ejecución: esperado y observado", "",
          "El detalle completo de cada ejecución (cada comprobación con su resultado observado) está en el `resultados.json` de la campaña. "
          "Ejemplo de C1:", ""]
    if "C1" in datos:
        for r in datos["C1"]["resultados"][:32]:
            L += [f"<details><summary>{r['run']} · {celda(r['titulo'])} · {r['estado']}</summary>", "",
                  f"**Esperado:** {celda(r['esperado'])}", "", "| Comprobación | Resultado | Observado |", "|---|---|---|"]
            L += [f"| {celda(o['descripcion'])} | {'✔' if o['ok'] else '✘'} | {celda(o['detalle'])[:200]} |" for o in r["observado"]]
            L += ["", "</details>", ""]
    escribir("05_ejecuciones.md", L)


def indice_evidencias(datos):
    L = ["# Índice de evidencias", "",
         "Identificador `E-<campaña>-<prueba>-<n>`. Las rutas son relativas a esta carpeta. Las contraseñas, tokens y cabeceras `Authorization` "
         "están enmascarados; el cuerpo de los correos (que contiene el código de verificación) no se guarda.", "",
         "| Evidencia | Ejecución | Tipo | Descripción |", "|---|---|---|---|"]
    for c, d in datos.items():
        for r in d["resultados"]:
            for e in r["evidencias"]:
                L.append(f"| [{e['id']}]({enlace(e['ruta'])}) | {r['run']} | {e['tipo']} | {celda(e['descripcion'])} |")
    L += ["", "## Otras evidencias", "",
          "| Evidencia | Qué es |", "|---|---|",
          f"| [Línea base (LB01–LB05)]({enlace('LB/resultados.json')}) | Estado del frontend inicial (Solemne 2, commit `c51e899`): capturas y resultado |",
          f"| [Ensayo 1]({enlace('historial/ensayo-1/resultados.json')}) | Primera corrida de la suite (antes de la versión evaluada); origen de INC-10 e INC-11 |",
          f"| [Ensayo 2]({enlace('historial/ensayo-2/resultados.json')}) | Nueva validación de P15, P19 y P28 después de las correcciones |",
          f"| [Regresión del backend]({enlace('prueba_seguridad.txt')}), [flujos]({enlace('prueba_flujos.txt')}), [fallos]({enlace('prueba_fallos.txt')}) | Scripts de la Unidad 2 en modo local (42 pruebas) |",
          f"| [Avance 1]({enlace('historial/avance-1/prueba_frontend.txt')}) | Prueba del frontend del avance 1 (versión anterior) |"]
    escribir("evidencias.md", L)


# Clasificacion de cada requisito, decidida con las evidencias de las cuatro campanas
CONCLUSIONES = {
 "R01": ("demostrado", "Un cliente arma un pedido con productos de la carta; el pedido y el stock quedan guardados", "Datos ficticios; un solo local"),
 "R02": ("demostrado", "El pedido pasa a PAGADO solo con el aviso firmado del proveedor y solo entonces aparece en despacho", "Proveedor real no probado: doble de prueba"),
 "R03": ("demostrado", "Anular un pedido pendiente exige motivo, lo deja ANULADO y devuelve el stock", "No se probó anular desde la cuenta del admin"),
 "R04": ("demostrado", "Sin sesión no se compra; la venta pagada queda en la caja CAJA-WEB-01", "—"),
 "R05": ("demostrado", "El registro guarda los datos del cliente y la ficha se edita y valida (RUN)", "Solo se probó un RUN inválido y algunos campos"),
 "R06": ("parcial", "El admin registra un cliente en el local (cuenta creada sin verificar)", "No se probó que ese cliente verifique su correo e inicie sesión"),
 "R07": ("demostrado", "El dueño cambia oferta y stock, agrega y da de baja productos, y la carta lo refleja", "—"),
 "R08": ("parcial", "Cada venta genera su boleta y un correo de boleta en la bandeja simulada", "Correo simulado: no se probó el envío real"),
 "R09": ("demostrado", "El reporte del dueño suma cada pedido pagado al momento", "Pocos datos (ventas de una campaña)"),
 "R10": ("demostrado", "Mantenedores de productos y usuarios operan desde la interfaz", "Edición de clientes por el admin no probada en la interfaz"),
 "R11": ("parcial", "Sin el código no se inicia sesión; con el código correcto sí", "API de mensajería simulada (doble de prueba)"),
 "R12": ("demostrado", "Login, logout y acceso por perfil; el admin cambia perfiles salvo el propio", "No se probó que el usuario con perfil cambiado deba volver a iniciar sesión"),
 "R13": ("demostrado", "Despacho ve los pedidos pagados y los avanza solo por transiciones válidas", "Solo un pedido de retiro por campaña"),
 "R14": ("demostrado", "El mensaje de contacto se guarda y el admin lo ve", "—"),
 "R15": ("demostrado", "Sin sesión, sesión expirada, rol sin permiso, pedido ajeno y servicio sin secreto se rechazan sin modificar datos", "Casos probados; no es una auditoría completa de seguridad"),
 "R16": ("demostrado", "Mis pedidos junta orders, inventory y payments en una consulta, con permisos y límites", "Límite de profundidad no ejecutable con este esquema (ver protocolo 1.1)"),
 "R17": ("parcial", "Con inventory detenido o lento y con analítica detenida, la interfaz informa y se recupera", "No se probaron caídas de auth, orders, payments ni clients desde la interfaz"),
 "R18": ("parcial", "Las 32 pruebas pasan en escritorio y en móvil emulado, sin desborde horizontal", "Emulación móvil, sin dispositivo físico; un solo navegador (Chromium)"),
 "R19": ("demostrado", "Un pedido reenviado y un aviso de pago repetido no duplican efectos", "Dos envíos simultáneos; no se probó concurrencia masiva"),
}
PENDIENTES = {
 "R06": "Agregar a la suite la verificación y el login del cliente registrado en el local",
 "R08": "Conectar un proveedor de correo en sandbox y verificar la recepción",
 "R11": "Igual que R08",
 "R17": "Agregar pruebas de caída de auth, orders, payments y clients desde la interfaz",
 "R18": "Repetir los recorridos críticos en un celular físico y en otro navegador",
}


def resultados(datos):
    pruebas = PROTOCOLO["pruebas"]
    req = PROTOCOLO["requisitos"]
    estados = {p["id"]: [d_c for d_c in (next((r["estado"] for r in datos[c]["resultados"] if r["id"] == p["id"]), "no ejecutada") for c in datos)] for p in pruebas}
    distintas = len(pruebas)
    aprob_todas = [i for i, e in estados.items() if e and all(x == "aprobada" for x in e) and len(e) == len(datos)]
    fallidas = [i for i, e in estados.items() if "fallida" in e]
    bloqueadas = [i for i, e in estados.items() if "bloqueada" in e and "fallida" not in e]
    no_ejec = [i for i, e in estados.items() if not e or all(x == "no ejecutada" for x in e)]
    ejecutadas = distintas - len(no_ejec) - len(bloqueadas)
    rep = [x for e in estados.values() for x in e]
    con_criterio = {r for p in pruebas for r in p["requisitos"]}
    demostrados = [r for r, c in CONCLUSIONES.items() if c[0] == "demostrado"]
    parciales = [r for r, c in CONCLUSIONES.items() if c[0] == "parcial"]
    pct = lambda a, b: f"{100 * a / b:.1f} %" if b else "no calculable"
    L = ["# 7. Resultados, indicadores y conclusiones", "",
         f"Versión evaluada: incremento I7, del {next(iter(datos.values()))['meta']['inicio'][:10]} (protocolo v{PROTOCOLO['version']}). "
         f"Campañas: {', '.join(f'{c} ({d['meta']['nombre']})' for c, d in datos.items())}.", "",
         "## Conteos", "",
         "| | Cantidad |", "|---|---|",
         f"| Pruebas distintas planificadas | {distintas} |",
         f"| Ejecuciones (pruebas × campañas) | {len(rep)} |",
         f"| Ejecuciones aprobadas / fallidas / bloqueadas / no ejecutadas | {rep.count('aprobada')} / {rep.count('fallida')} / {rep.count('bloqueada')} / {rep.count('no ejecutada')} |",
         f"| Pruebas distintas aprobadas en las {len(datos)} campañas | {len(aprob_todas)} |",
         f"| Pruebas distintas con alguna falla (intermitentes o fallidas) | {len(fallidas)}{(' (' + ', '.join(fallidas) + ')') if fallidas else ''} |",
         f"| Pruebas distintas bloqueadas / no ejecutadas | {len(bloqueadas)} / {len(no_ejec)} |", "",
         "Criterio de consolidación (definido en el protocolo antes de ejecutar): una prueba distinta cuenta como aprobada solo si se aprueba en las cuatro campañas.", "",
         "## Indicadores", "",
         "| Indicador | Cálculo | Resultado | Cuidado de interpretación |", "|---|---|---|---|",
         f"| Cobertura del diseño | requisitos con criterios y pruebas / requisitos en alcance = {len(con_criterio & set(req))} / {len(req)} | **{pct(len(con_criterio & set(req)), len(req))}** | Mide planificación, no logro |",
         f"| Ejecución del plan | pruebas distintas con resultado aprobado o fallido / planificadas = {ejecutadas} / {distintas} | **{pct(ejecutadas, distintas)}** | Bloqueadas: {len(bloqueadas)}; no ejecutadas: {len(no_ejec)} |",
         f"| Aprobación observada | pruebas distintas aprobadas / pruebas distintas ejecutadas = {len(aprob_todas)} / {ejecutadas} | **{pct(len(aprob_todas), ejecutadas)}** | Repeticiones: {rep.count('aprobada')} de {len(rep)} ejecuciones aprobadas |",
         f"| Logro demostrado | requisitos demostrados / requisitos en alcance = {len(demostrados)} / {len(req)} | **{pct(len(demostrados), len(req))}** | {len(parciales)} requisitos parcialmente demostrados no se cuentan ({', '.join(parciales)}) |", "",
         "Los porcentajes describen esta versión en este entorno; no son una probabilidad de éxito en producción.", "",
         "## Evolución respecto de la línea base", "",
         "| Flujo | Línea base (frontend de la Solemne 2) | Versión evaluada |", "|---|---|---|"]
    for f in PROTOCOLO["flujos"]:
        ps = [p for p in pruebas if f["id"] in p["flujos"]]
        ok = sum(1 for p in ps if p["id"] in aprob_todas)
        L.append(f"| {f['id']} {celda(f['nombre'])} | {celda(f['estado_inicial'])} | Integrado; {ok} de {len(ps)} pruebas aprobadas en las 4 campañas |")
    L += ["", "## Matriz de conclusiones", "",
          "Clasificación: **demostrado** en el entorno evaluado, **parcial** o **no demostrado**.", "",
          "| Requisito | Afirmación | Criterios | Ejecuciones y evidencias | Resultado | Límite de validez | Riesgo pendiente / próxima acción |",
          "|---|---|---|---|---|---|---|"]
    for r, texto in req.items():
        ps = [p for p in pruebas if r in p["requisitos"]]
        clas, afirma, limite = CONCLUSIONES[r]
        runs = ", ".join(f"{p['id']}×{len(datos)}" for p in ps)
        L.append(f"| {r} {celda(texto)} | {celda(afirma)} | {', '.join(p['ca'] for p in ps)} | {runs} → [registro](05_ejecuciones.md) | **{clas}** | {celda(limite)} | {celda(PENDIENTES.get(r, '—'))} |")
    escribir("07_resultados.md", L)


def trazabilidad(datos):
    import csv
    flujos = {f["id"]: f for f in PROTOCOLO["flujos"]}
    ruta = os.path.join(EXPEDIENTE, "trazabilidad.csv")
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Requisito", "Flujo", "Pantalla", "Rol", "Servicio o integración", "Criterio", "Prueba", "Escenario",
                    "Ejecuciones", "Estados", "Evidencias", "Conclusión del requisito"])
        for r in PROTOCOLO["requisitos"]:
            for p in [p for p in PROTOCOLO["pruebas"] if r in p["requisitos"]]:
                fls = [flujos[x] for x in p["flujos"]] or [{"id": "—", "pantalla": "— (control de backend)", "rol": "—", "servicios": "clients → inventory"}]
                runs, est, evs = [], [], []
                for c, d in datos.items():
                    rr = next((x for x in d["resultados"] if x["id"] == p["id"]), None)
                    if rr:
                        runs.append(rr["run"]); est.append(rr["estado"]); evs += [e["id"] for e in rr["evidencias"]]
                w.writerow([r, " / ".join(x["id"] for x in fls), " / ".join(x["pantalla"] for x in fls), " / ".join(x["rol"] for x in fls),
                            " / ".join(x["servicios"] for x in fls), f"{p['ca']}: {p['criterio']}", f"{p['id']} {p['titulo']}", p["escenario"],
                            " ".join(runs), " ".join(est), " ".join(evs), CONCLUSIONES[r][0]])
    print("generado Expediente/trazabilidad.csv")


if __name__ == "__main__":
    inventario_flujos()
    protocolo()
    datos = cargar_resultados()
    if datos:
        ejecuciones(datos)
        indice_evidencias(datos)
        resultados(datos)
        trazabilidad(datos)
