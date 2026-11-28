// Suite de integracion de la Evaluacion 3: ejecuta las pruebas de pruebas/protocolo.json desde el frontend
// (Chromium con Playwright) contra el sistema completo en Docker y guarda las evidencias de cada ejecucion.
//
// Uso, desde la carpeta Backend/pruebas (con Docker abierto y el .env de Backend creado):
//   npm install && npx playwright install chromium
//   TEST_PASSWORD=<SEED_PASSWORD del .env> node suite_integracion.js C1        (C1 a C4, ver protocolo.json)
//   PowerShell: $env:TEST_PASSWORD="..."; node suite_integracion.js C1
// Opciones: --sin-reinicio (no vuelve la base a cero) y una lista de pruebas (ej. P01 P03) para correr solo esas.
//
// Cada campana parte de la base vacia (docker compose down -v / up -d). Las evidencias quedan en
// docs/evidencias/<campana>/<prueba>/ y el resumen en docs/evidencias/<campana>/resultados.json.
// El navegador de la prueba acepta el certificado de la CA local sin instalarlo (ignoreHTTPSErrors).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium, devices } = require('playwright');

const AQUI = __dirname;
const BACKEND = path.resolve(AQUI, '..');
const RAIZ = path.resolve(BACKEND, '..');
const PROTOCOLO = JSON.parse(fs.readFileSync(path.join(AQUI, 'protocolo.json'), 'utf8'));
const CAMPANA = process.argv[2];
const CONF = PROTOCOLO.campanas[CAMPANA];
const SOLO = process.argv.slice(3).filter(a => /^P\d+$/.test(a));
const SIN_REINICIO = process.argv.includes('--sin-reinicio');
const CLAVE = process.env.TEST_PASSWORD;
const FRONT = 'http://localhost:8080/';
const API = 'https://127.0.0.1:8000/api/v1';
const SALIDA = path.join(BACKEND, 'docs', 'evidencias', CAMPANA || 'X');
// Todas las solicitudes del navegador de prueba salen de una sola IP: se sube el limite general del gateway
// durante la campana (el de login, 10 por minuto, no cambia). Queda registrado en los metadatos.
const LIMITE_GENERAL = '600';
const SERVICIOS = ['gateway', 'auth', 'inventory', 'orders', 'clients', 'payments', 'graphql', 'analitica',
  'notificaciones', 'proveedor'];

if (!CONF || !CLAVE) {
  console.error('Uso: TEST_PASSWORD=<SEED_PASSWORD> node suite_integracion.js C1|C2|C3|C4 [P01 ...] [--sin-reinicio]');
  process.exit(2);
}

class Bloqueada extends Error {}

// ---------------------------------------------------------------- Docker y comandos
function ejecutar(programa, args, opciones = {}) {
  const r = spawnSync(programa, args, { cwd: BACKEND, encoding: 'utf8', env: { ...process.env, LIMITE_POR_MINUTO: LIMITE_GENERAL },
    maxBuffer: 64 * 1024 * 1024, ...opciones });
  if (r.status !== 0 && !opciones.permitirError) {
    throw new Bloqueada(`${programa} ${args.join(' ')} fallo: ${(r.stderr || r.stdout || '').trim().slice(-300)}`);
  }
  return (r.stdout || '') + (opciones.conError ? (r.stderr || '') : '');
}
const dc = (...args) => ejecutar('docker', ['compose', ...args]);
const dormir = ms => new Promise(r => setTimeout(r, ms));

async function esperarSanos(servicios, segundos = 120) {
  for (let i = 0; i < segundos; i++) {
    const estados = {};
    const salida = dc('ps', '-a', '--format', 'json').trim();
    const lista = salida.startsWith('[') ? JSON.parse(salida) : salida.split('\n').filter(Boolean).map(l => JSON.parse(l));
    for (const c of lista) estados[c.Service] = c;
    if (servicios.every(s => estados[s] && estados[s].Health === 'healthy')) return;
    await dormir(1000);
  }
  throw new Bloqueada('Los servicios no quedaron healthy a tiempo: ' + servicios.join(', '));
}

async function reiniciarSistema() {
  console.log('Base a cero: docker compose down -v / up -d ...');
  dc('down', '-v');
  dc('up', '-d');
  await esperarSanos(SERVICIOS, 180);
}

function inspeccionar(servicio, coleccion, filtro = {}, campos) {
  const args = ['compose', 'exec', '-T', servicio, 'python', 'inspeccionar.py', coleccion, JSON.stringify(filtro)];
  if (campos) args.push(campos);
  return JSON.parse(ejecutar('docker', args));
}

function fechaLocal(d = new Date()) {
  const o = -d.getTimezoneOffset();
  const p = n => String(Math.floor(Math.abs(n))).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}` +
    `${o >= 0 ? '+' : '-'}${p(o / 60)}:${p(o % 60)}`;
}

// ---------------------------------------------------------------- Evidencias
function enmascarar(texto) {
  if (!texto) return texto;
  return texto
    .replace(/("(?:password|access_token|token|codigo|password2)"\s*:\s*")[^"]*"/g, '$1***"')
    .slice(0, 4000);
}

function nuevaPrueba(def) {
  const dir = path.join(SALIDA, def.id);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  return { def, dir, run: `RUN-${CAMPANA}-${def.id}`, red: [], checks: [], evidencias: [], inspecciones: [],
    patronesLog: [], vinculos: new Set(), inicio: new Date(), notas: [] };
}

function evidencia(t, tipo, archivo, descripcion) {
  const id = `E-${CAMPANA}-${t.def.id}-${String(t.evidencias.length + 1).padStart(2, '0')}`;
  t.evidencias.push({ id, tipo, ruta: path.relative(path.join(BACKEND, 'docs', 'evidencias'), path.join(t.dir, archivo)).split(path.sep).join('/'), descripcion });
}

async function captura(t, page, nombre, descripcion) {
  const archivo = `${String(t.evidencias.length + 1).padStart(2, '0')}-${nombre}.jpg`;
  await page.screenshot({ path: path.join(t.dir, archivo), type: 'jpeg', quality: 60 });
  evidencia(t, 'captura', archivo, descripcion);
}

function check(t, descripcion, ok, detalle) {
  t.checks.push({ descripcion, ok: Boolean(ok), detalle: detalle === undefined ? '' : String(detalle) });
}

function inspeccion(t, descripcion, servicio, coleccion, filtro, campos) {
  const r = inspeccionar(servicio, coleccion, filtro, campos);
  t.inspecciones.push({ descripcion, hora: fechaLocal(), ...r });
  return r;
}

function respuestas(t, metodo, fragmento) {
  return t.red.filter(r => r.metodo === metodo && r.url.includes(fragmento));
}

function cerrarPrueba(t, estado) {
  const fin = new Date();
  fs.writeFileSync(path.join(t.dir, 'red.json'), JSON.stringify(t.red, null, 1));
  evidencia(t, 'red', 'red.json', 'Solicitudes y respuestas del navegador al gateway (con X-Request-ID; claves y tokens enmascarados)');
  if (t.inspecciones.length) {
    fs.writeFileSync(path.join(t.dir, 'persistencia.json'), JSON.stringify(t.inspecciones, null, 1));
    evidencia(t, 'persistencia', 'persistencia.json', 'Inspección de MongoDB dentro del contenedor de cada servicio');
  }
  const ids = new Set(t.red.map(r => r.request_id).filter(Boolean));
  const desde = new Date(t.inicio.getTime() - 2000).toISOString();
  const lineas = dc('logs', '--no-color', '--since', desde, ...SERVICIOS).split('\n')
    .filter(l => [...ids].some(id => l.includes('req=' + id)) || t.patronesLog.some(p => l.includes(p)));
  if (lineas.length) {
    fs.writeFileSync(path.join(t.dir, 'logs.txt'), lineas.join('\n') + '\n');
    evidencia(t, 'logs', 'logs.txt', 'Logs de los contenedores con los X-Request-ID de esta ejecución');
  }
  ids.forEach(id => t.vinculos.add('X-Request-ID ' + id));
  return {
    id: t.def.id, ca: t.def.ca, titulo: t.def.titulo, recorrido: t.def.recorrido, flujos: t.def.flujos,
    requisitos: t.def.requisitos, escenario: t.def.escenario, run: t.run, campana: CAMPANA,
    inicio: fechaLocal(t.inicio), fin: fechaLocal(fin), duracion_ms: fin - t.inicio, estado,
    esperado: t.def.esperado, observado: t.checks, notas: t.notas, evidencias: t.evidencias,
    vinculacion: [...t.vinculos].slice(0, 30),
  };
}

// ---------------------------------------------------------------- Navegador
let navegador;
const sesiones = {};

async function nuevoContexto(t) {
  const opciones = CONF.dispositivo ? { ...devices[CONF.dispositivo] } : { viewport: CONF.viewport };
  const ctx = await navegador.newContext({ ...opciones, ignoreHTTPSErrors: true, locale: 'es-CL', timezoneId: 'America/Santiago' });
  ctx.setDefaultTimeout(20000);
  ctx.on('response', async resp => {
    const url = resp.url();
    if (!url.startsWith('https://127.0.0.1:8000')) return;
    const req = resp.request();
    if (req.method() === 'OPTIONS') return;
    let cuerpo = '';
    try { cuerpo = await resp.text(); } catch (e) { cuerpo = ''; }
    const cab = await req.allHeaders().catch(() => ({}));
    t.red.push({ hora: fechaLocal(), metodo: req.method(), url: url.replace('https://127.0.0.1:8000', ''), estado: resp.status(),
      request_id: resp.headers()['x-request-id'] || null, origin: cab.origin || null,
      authorization: cab.authorization ? 'Bearer ***' : null,
      cors: resp.headers()['access-control-allow-origin'] || null,
      solicitud: enmascarar(req.postData() || ''), respuesta: enmascarar(cuerpo) });
  });
  return ctx;
}

async function iniciarSesion(page, email, clave = CLAVE) {
  for (let intento = 0; intento < 3; intento++) {
    await page.goto(FRONT + 'login.php');
    await page.fill('input[name=email]', email);
    await page.fill('input[name=password]', clave);
    await page.click('#login-form button[type=submit]');
    const r = await Promise.race([
      page.waitForURL(u => !u.toString().includes('login.php'), { timeout: 15000 }).then(() => 'ok'),
      page.waitForSelector('#login-aviso.error', { timeout: 15000 }).then(() => 'error'),
    ]);
    if (r === 'ok') {
      sesiones[email] = await page.evaluate(() => sessionStorage.getItem('aroma_sesion'));
      return;
    }
    const aviso = await page.textContent('#login-aviso');
    if (!aviso.includes('Demasiados intentos')) throw new Error('Login fallido: ' + aviso);
    console.log('   (limite de 10 logins por minuto: se espera 61 s)');
    await dormir(61000);
  }
  throw new Bloqueada('No se pudo iniciar sesion por el limite de intentos');
}

// Pagina con la sesion de un usuario. Reutiliza la sesion ya iniciada (sessionStorage) para no pasar el
// limite de 10 logins por minuto; con nueva=true inicia sesion de nuevo desde login.php.
async function paginaCon(t, email, nueva = false) {
  const ctx = await nuevoContexto(t);
  if (email && sesiones[email] && !nueva) {
    await ctx.addInitScript(s => { if (location.origin === 'http://localhost:8080') sessionStorage.setItem('aroma_sesion', s); }, sesiones[email]);
  }
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept());
  if (email && (!sesiones[email] || nueva)) await iniciarSesion(page, email);
  return page;
}

async function agregarAlCarrito(page, productos) {
  await page.goto(FRONT + 'catalogo.php');
  await page.waitForSelector('.product-card-lg');
  for (const [id, cantidad] of productos) {
    for (let i = 0; i < cantidad; i++) await page.click(`[data-id="${id}"]`);
  }
}

async function confirmarPedido(page) {
  await page.goto(FRONT + 'carrito.php');
  await page.waitForSelector('.cart-item');
  await page.click('#btn-pay');
}

function desdePagina(page, metodo, ruta, cuerpo, conToken = true) {
  return page.evaluate(async ({ api, metodo, ruta, cuerpo, conToken }) => {
    const s = JSON.parse(sessionStorage.getItem('aroma_sesion') || 'null');
    const cab = { 'Content-Type': 'application/json' };
    if (conToken && s) cab.Authorization = 'Bearer ' + s.token;
    const r = await fetch(api + ruta, { method: metodo, headers: cab, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
    const texto = await r.text();
    let datos = null;
    try { datos = JSON.parse(texto); } catch (e) { datos = texto; }
    return { status: r.status, datos };
  }, { api: API, metodo, ruta, cuerpo, conToken });
}

const stock = id => inspeccionar('inventory', 'productos', { _id: id }, 'stock').resultado[0].stock;
const totalPedidos = () => inspeccionar('orders', 'pedidos', {}, '_id').total;
const ANA = 'ana@aromaycafe.test';
const estado = {};   // datos que una prueba deja para las siguientes (ids de pedidos)

// ---------------------------------------------------------------- Pruebas
const PRUEBAS = {
  async P01(t) {
    const page = await paginaCon(t, null);
    await page.goto(FRONT + 'catalogo.php');
    await page.waitForSelector('.product-card-lg');
    const nombres = await page.locator('.product-card-lg h4').allTextContents();
    const r = respuestas(t, 'GET', '/api/v1/products')[0];
    check(t, 'GET /products responde 200', r && r.estado === 200, r && r.estado);
    check(t, 'CORS: access-control-allow-origin = origen del frontend', r && r.cors === 'http://localhost:8080' && r.origin === 'http://localhost:8080', r && `${r.origin} -> ${r.cors}`);
    const api = JSON.parse(r.respuesta);
    check(t, 'Las tarjetas son los productos de la respuesta', JSON.stringify(nombres) === JSON.stringify(api.map(p => p.nombre)), nombres.join(', '));
    const precios = await page.locator('.product-card-lg .price-now').allTextContents();
    const esperados = api.map(p => '$' + (p.precio_oferta || p.precio).toLocaleString('es-CL'));
    check(t, 'Precios de las tarjetas = precio vigente de la API', JSON.stringify(precios) === JSON.stringify(esperados), precios.join(' '));
    const db = inspeccion(t, 'Productos activos en inventory', 'inventory', 'productos', { activo: true }, 'nombre,precio,precio_oferta,stock');
    check(t, 'Cantidad de tarjetas = productos activos en inventory.productos', db.total === nombres.length, `${nombres.length} tarjetas / ${db.total} en la base`);
    await captura(t, page, 'carta', 'Carta armada con los productos de la API');
  },

  async P02(t) {
    dc('stop', 'inventory');
    t.patronesLog.push('inventory no responde');
    const page = await paginaCon(t, null);
    try {
      await page.goto(FRONT + 'catalogo.php');
      await page.waitForSelector('#catalog-status button');
      const texto = await page.textContent('#catalog-status');
      check(t, 'Con inventory detenido: mensaje de error y 0 tarjetas', texto.includes('No pudimos cargar la carta') && await page.locator('.product-card-lg').count() === 0, texto);
      const r = respuestas(t, 'GET', '/api/v1/products')[0];
      check(t, 'El gateway responde 502 (backend no disponible)', r && r.estado === 502, r && r.estado);
      await captura(t, page, 'inventory-detenido', 'Carta con inventory detenido');
    } finally {
      dc('start', 'inventory');
      await esperarSanos(['inventory']);
    }
    await page.click('#catalog-status button');
    await page.waitForSelector('.product-card-lg');
    check(t, 'Al volver inventory, Reintentar carga la carta', await page.locator('.product-card-lg').count() >= 8, await page.locator('.product-card-lg').count());
    const r2 = respuestas(t, 'GET', '/api/v1/products').pop();
    check(t, 'La nueva solicitud responde 200', r2 && r2.estado === 200, r2 && r2.estado);
    await captura(t, page, 'recuperado', 'Carta después de iniciar inventory y presionar Reintentar');
  },

  async P03(t) {
    const antes = { latte: stock('latte-art'), croissant: stock('croissant') };
    const page = await paginaCon(t, null);
    await agregarAlCarrito(page, [['latte-art', 2], ['croissant', 1]]);
    await confirmarPedido(page);
    await page.waitForURL('**/login.php**');
    await page.fill('input[name=email]', ANA);
    await page.fill('input[name=password]', CLAVE);
    await page.click('#login-form button[type=submit]');
    await page.waitForURL('**/carrito.php');
    sesiones[ANA] = await page.evaluate(() => sessionStorage.getItem('aroma_sesion'));
    await page.click('#btn-pay');
    await page.waitForURL('**/pedido.php?id=**');
    await page.waitForSelector('#ped-detalle:not([hidden])');
    const id = new globalThis.URL(page.url()).searchParams.get('id');
    estado.P03 = id;
    t.vinculos.add('pedido ' + id);
    const post = respuestas(t, 'POST', '/api/v1/orders')[0];
    check(t, 'POST /orders responde 201', post && post.estado === 201, post && post.estado);
    check(t, 'La pantalla muestra Pendiente de pago y total $9.200 (precios del servidor)',
      (await page.textContent('#ped-estado')) === 'Pendiente de pago' && (await page.textContent('#ped-total')) === '$9.200',
      `${await page.textContent('#ped-estado')} ${await page.textContent('#ped-total')}`);
    await captura(t, page, 'pedido-creado', 'Pedido creado');
    const doc = inspeccion(t, 'Pedido en orders.pedidos', 'orders', 'pedidos', { _id: id }, 'user_id,estado,total,lineas,tipo_entrega').resultado[0];
    check(t, 'orders.pedidos: pedido de USR-003, PENDIENTE_PAGO, total 9200, retiro', doc && doc.user_id === 'USR-003' && doc.estado === 'PENDIENTE_PAGO' && doc.total === 9200 && doc.tipo_entrega === 'retiro', JSON.stringify(doc));
    const despues = { latte: stock('latte-art'), croissant: stock('croissant') };
    inspeccion(t, 'Stock después del pedido', 'inventory', 'productos', { _id: { $in: ['latte-art', 'croissant'] } }, 'stock');
    check(t, 'Stock descontado una vez (Latte -2, Croissant -1)', despues.latte === antes.latte - 2 && despues.croissant === antes.croissant - 1, `${JSON.stringify(antes)} -> ${JSON.stringify(despues)}`);
    await page.reload();
    await page.waitForSelector('#ped-detalle:not([hidden])');
    check(t, 'Al recargar se ve el mismo pedido', (await page.textContent('#ped-total')) === '$9.200');
    const otra = await paginaCon(t, ANA, true);
    await otra.goto(FRONT + 'pedido.php?id=' + id);
    await otra.waitForSelector('#ped-detalle:not([hidden])');
    check(t, 'En una sesión nueva se ve el mismo estado y total', (await otra.textContent('#ped-estado')) === 'Pendiente de pago' && (await otra.textContent('#ped-total')) === '$9.200');
    await captura(t, otra, 'sesion-nueva', 'El pedido visto desde una sesión nueva');
  },

  async P04(t) {
    const antes = totalPedidos();
    const page = await paginaCon(t, null);
    await agregarAlCarrito(page, [['espresso-doble', 1]]);
    await confirmarPedido(page);
    await page.waitForURL('**/login.php**');
    check(t, 'Redirige a login.php con volver=carrito.php', page.url().includes('volver=carrito.php'), page.url());
    check(t, 'No se envió POST /orders', respuestas(t, 'POST', '/api/v1/orders').length === 0);
    const despues = inspeccion(t, 'Total de pedidos', 'orders', 'pedidos', {}, '_id').total;
    check(t, 'orders.pedidos sin cambios', despues === antes, `${antes} -> ${despues}`);
    await captura(t, page, 'login', 'Sin sesión, la confirmación lleva a iniciar sesión');
  },

  async P05(t) {
    const antes = { pedidos: totalPedidos(), stock: stock('espresso-doble') };
    const page = await paginaCon(t, ANA);
    await agregarAlCarrito(page, [['espresso-doble', 1]]);
    await page.goto(FRONT + 'carrito.php');
    await page.check('input[value=delivery]');
    await page.fill('input[name=direccion]', 'Av. Providencia 1234');
    await page.fill('input[name=comuna]', 'Providencia');
    await page.click('#btn-pay');
    await page.waitForSelector('#pedido-aviso.error');
    const aviso = await page.textContent('#pedido-aviso');
    check(t, 'Mensaje: fuera del radio de despacho', aviso.includes('fuera del radio'), aviso);
    const post = respuestas(t, 'POST', '/api/v1/orders')[0];
    check(t, 'POST /orders responde 422', post && post.estado === 422, post && post.estado);
    const despues = { pedidos: inspeccion(t, 'Total de pedidos', 'orders', 'pedidos', {}, '_id').total, stock: stock('espresso-doble') };
    check(t, 'Sin pedido nuevo y stock igual', despues.pedidos === antes.pedidos && despues.stock === antes.stock, `${JSON.stringify(antes)} -> ${JSON.stringify(despues)}`);
    await captura(t, page, 'fuera-radio', 'Despacho fuera del radio rechazado');
    await page.evaluate(() => localStorage.removeItem('aroma_cart'));
  },

  async P06(t) {
    const dueno = await paginaCon(t, 'dueno@aromaycafe.test');
    async function fijarStock(valor) {
      await dueno.goto(FRONT + 'inventario.php');
      await dueno.waitForSelector('#inv-tabla-wrap:not([hidden])');
      const fila = dueno.locator('#inv-filas tr', { hasText: 'Cappuccino' });
      await fila.locator('input').nth(2).fill(String(valor));
      await fila.locator('button', { hasText: 'Guardar' }).click();
      await dueno.waitForSelector('#inv-aviso.ok');
    }
    await fijarStock(1);
    const antes = { pedidos: totalPedidos(), stock: stock('cappuccino') };
    check(t, 'Precondición: stock de Cappuccino en 1', antes.stock === 1, antes.stock);
    const page = await paginaCon(t, ANA);
    try {
      await agregarAlCarrito(page, [['cappuccino', 2]]);
      await confirmarPedido(page);
      await page.waitForSelector('#pedido-aviso.error');
      const aviso = await page.textContent('#pedido-aviso');
      check(t, 'Mensaje: no hay stock suficiente', aviso.includes('No hay stock suficiente'), aviso);
      const post = respuestas(t, 'POST', '/api/v1/orders')[0];
      check(t, 'POST /orders responde 409', post && post.estado === 409, post && post.estado);
      await captura(t, page, 'sin-stock', 'Pedido rechazado por stock insuficiente');
      inspeccion(t, 'Stock de Cappuccino', 'inventory', 'productos', { _id: 'cappuccino' }, 'stock');
      const despues = { pedidos: totalPedidos(), stock: stock('cappuccino') };
      check(t, 'Stock sigue en 1 y no hay pedido nuevo (todo o nada)', despues.stock === 1 && despues.pedidos === antes.pedidos, JSON.stringify(despues));
      await page.evaluate(() => localStorage.removeItem('aroma_cart'));
    } finally {
      await fijarStock(40);
    }
    check(t, 'Restauración: stock de Cappuccino en 40', stock('cappuccino') === 40);
  },

  async P07(t) {
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'index.php');
    const antes = stock('tarta-frambuesa');
    const clave = `PRUEBA-${CAMPANA}-${Date.now()}`;
    const resultados = await page.evaluate(async ({ api, clave }) => {
      const s = JSON.parse(sessionStorage.getItem('aroma_sesion'));
      const cuerpo = JSON.stringify({ items: [{ product_id: 'tarta-frambuesa', cantidad: 1 }], tipo_entrega: 'retiro', clave });
      const pedir = () => fetch(api + '/orders', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + s.token }, body: cuerpo })
        .then(async r => ({ status: r.status, datos: await r.json() }));
      return Promise.all([pedir(), pedir()]);
    }, { api: API, clave });
    const estados = resultados.map(r => r.status).sort();
    check(t, 'Las dos respuestas son 201 y 200', JSON.stringify(estados) === '[200,201]', estados.join(', '));
    check(t, 'Mismo id de pedido y una marcada como repetida', resultados[0].datos.id === resultados[1].datos.id && resultados.some(r => r.datos.repetido === true),
      resultados.map(r => `${r.datos.id}${r.datos.repetido ? ' (repetido)' : ''}`).join(' / '));
    estado.P07 = resultados[0].datos.id;
    t.vinculos.add('pedido ' + estado.P07);
    t.vinculos.add('clave ' + clave);
    t.patronesLog.push('pedido repetido');
    const docs = inspeccion(t, 'Pedidos con esa clave', 'orders', 'pedidos', { clave }, '_id,estado,total');
    check(t, 'Un solo documento con esa clave en orders.pedidos', docs.total === 1, docs.total);
    const despues = stock('tarta-frambuesa');
    inspeccion(t, 'Stock de Tarta de Frambuesa', 'inventory', 'productos', { _id: 'tarta-frambuesa' }, 'stock');
    check(t, 'Stock descontado una sola vez', despues === antes - 1, `${antes} -> ${despues}`);
  },

  async P08(t) {
    const page = await paginaCon(t, ANA);
    await agregarAlCarrito(page, [['croissant', 1]]);
    const antes = totalPedidos();
    dc('pause', 'inventory');
    let ms;
    try {
      await page.goto(FRONT + 'carrito.php');
      await page.waitForSelector('.cart-item');
      const t0 = Date.now();
      await page.click('#btn-pay');
      await page.waitForSelector('#pedido-aviso.error');
      ms = Date.now() - t0;
      const aviso = await page.textContent('#pedido-aviso');
      check(t, 'Mensaje de servicio no disponible', aviso.includes('no está disponible'), aviso);
      const post = respuestas(t, 'POST', '/api/v1/orders')[0];
      check(t, 'POST /orders responde 502 tras el plazo de gRPC', post && post.estado === 502 && ms >= 2500, `${post && post.estado} en ${ms} ms`);
      check(t, 'No se creó pedido', totalPedidos() === antes);
      await captura(t, page, 'inventory-en-pausa', 'Pedido con inventory sin responder');
    } finally {
      dc('unpause', 'inventory');
    }
    await dormir(1500);
    await page.click('#btn-pay');
    await page.waitForURL('**/pedido.php?id=**');
    const id = new globalThis.URL(page.url()).searchParams.get('id');
    estado.P08 = id;
    t.vinculos.add('pedido ' + id);
    const posts = respuestas(t, 'POST', '/api/v1/orders');
    check(t, 'Al reintentar con inventory activo: 201 y pedido creado', posts.length >= 2 && posts[posts.length - 1].estado === 201, posts.map(p => p.estado).join(', '));
    inspeccion(t, 'Pedido creado al reintentar', 'orders', 'pedidos', { _id: id }, 'estado,total');
    t.notas.push(`El primer intento tardó ${ms} ms (plazo de gRPC: 3 s)`);
    await captura(t, page, 'recuperado', 'Pedido creado al reintentar');
  },

  async P09(t) {
    if (!estado.P03) throw new Bloqueada('Depende de P03, que no dejó un pedido');
    const id = estado.P03;
    t.vinculos.add('pedido ' + id);
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'pedido.php?id=' + id);
    await page.waitForSelector('#ped-pago:not([hidden])');
    await page.click('#btn-iniciar-pago');
    await page.waitForSelector('#pasarela:not([hidden])');
    const pago = respuestas(t, 'POST', '/api/v1/payments')[0];
    check(t, 'POST /payments 201 con el monto del pedido (9200)', pago && pago.estado === 201 && JSON.parse(pago.respuesta).monto === 9200, pago && pago.respuesta);
    check(t, 'La pasarela muestra $9.200', (await page.textContent('#pas-monto')) === '$9.200');
    await captura(t, page, 'pasarela', 'Pasarela de pago simulada');
    await page.click('#btn-aprobar');
    await page.waitForSelector('#ped-boleta:not([hidden])');
    const sim = respuestas(t, 'POST', '/simular')[0];
    check(t, 'POST /simular responde 202', sim && sim.estado === 202, sim && sim.estado);
    const folio = await page.textContent('#bol-folio');
    estado.folioP09 = folio;
    check(t, 'Pedido Pagado y boleta con folio y total $9.200', (await page.textContent('#ped-estado')) === 'Pagado' && /^B-\d{6}$/.test(folio) && (await page.textContent('#bol-total')) === '$9.200', folio);
    await captura(t, page, 'boleta', 'Pedido pagado con su boleta');
    t.patronesLog.push(id);
    const pagos = inspeccion(t, 'Pagos del pedido', 'payments', 'pagos', { order_id: id }, 'estado,monto');
    check(t, 'payments.pagos: APROBADO por 9200', pagos.resultado.some(p => p.estado === 'APROBADO' && p.monto === 9200), JSON.stringify(pagos.resultado));
    const ped = inspeccion(t, 'Pedido', 'orders', 'pedidos', { _id: id }, 'estado,folio,caja').resultado[0];
    check(t, 'orders.pedidos: PAGADO con el mismo folio en CAJA-WEB-01', ped.estado === 'PAGADO' && ped.folio === folio && ped.caja === 'CAJA-WEB-01', JSON.stringify(ped));
    await dormir(1000);
    const correo = inspeccion(t, 'Correo de boleta', 'notificaciones', 'correos', { _id: id }, 'tipo,asunto,estado');
    check(t, 'notificaciones.correos: boleta enviada (simulada)', correo.total === 1 && correo.resultado[0].tipo === 'boleta', JSON.stringify(correo.resultado));
    const venta = inspeccion(t, 'Venta en analítica', 'analitica', 'ventas', { _id: id }, 'total,tipo_entrega');
    check(t, 'analitica.ventas: venta registrada sin datos personales', venta.total === 1 && venta.resultado[0].total === 9200 && !('user_id' in venta.resultado[0]), JSON.stringify(venta.resultado));
    const otra = await paginaCon(t, ANA, true);
    await otra.goto(FRONT + 'pedido.php?id=' + id);
    await otra.waitForSelector('#ped-boleta:not([hidden])');
    check(t, 'En una sesión nueva: Pagado con la misma boleta', (await otra.textContent('#ped-estado')) === 'Pagado' && (await otra.textContent('#bol-folio')) === folio);
  },

  async P10(t) {
    if (!estado.P08) throw new Bloqueada('Depende de P08, que no dejó un pedido pendiente');
    const id = estado.P08;
    t.vinculos.add('pedido ' + id);
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'pedido.php?id=' + id);
    await page.waitForSelector('#ped-pago:not([hidden])');
    await page.click('#btn-iniciar-pago');
    await page.waitForSelector('#pasarela:not([hidden])');
    await page.click('#btn-rechazar');
    await page.waitForSelector('#ped-aviso.error');
    const aviso = await page.textContent('#ped-aviso');
    check(t, 'Mensaje de pago rechazado y pedido Pendiente de pago', aviso.includes('rechazó') && (await page.textContent('#ped-estado')) === 'Pendiente de pago', aviso);
    await captura(t, page, 'rechazado', 'Pago rechazado por el proveedor');
    const p1 = inspeccion(t, 'Pagos tras el rechazo', 'payments', 'pagos', { order_id: id }, 'estado,monto');
    check(t, 'payments.pagos: un pago RECHAZADO', p1.resultado.length === 1 && p1.resultado[0].estado === 'RECHAZADO', JSON.stringify(p1.resultado));
    check(t, 'orders.pedidos sigue PENDIENTE_PAGO', inspeccion(t, 'Pedido tras el rechazo', 'orders', 'pedidos', { _id: id }, 'estado').resultado[0].estado === 'PENDIENTE_PAGO');
    await page.click('#btn-iniciar-pago');
    await page.waitForSelector('#pasarela:not([hidden])');
    await page.click('#btn-aprobar');
    await page.waitForSelector('#ped-boleta:not([hidden])');
    check(t, 'El segundo intento aprueba el pago: Pagado', (await page.textContent('#ped-estado')) === 'Pagado');
    const p2 = inspeccion(t, 'Pagos tras el segundo intento', 'payments', 'pagos', { order_id: id }, 'estado,monto');
    check(t, 'payments.pagos: uno RECHAZADO y uno APROBADO', p2.resultado.map(p => p.estado).sort().join(',') === 'APROBADO,RECHAZADO', JSON.stringify(p2.resultado));
    await captura(t, page, 'aprobado', 'Pago aprobado en el segundo intento');
  },

  async P11(t) {
    const page = await paginaCon(t, ANA);
    await agregarAlCarrito(page, [['espresso-doble', 1]]);
    await confirmarPedido(page);
    await page.waitForURL('**/pedido.php?id=**');
    const id = new globalThis.URL(page.url()).searchParams.get('id');
    t.vinculos.add('pedido ' + id);
    await page.waitForSelector('#ped-pago:not([hidden])');
    await page.click('#btn-iniciar-pago');
    await page.waitForSelector('#pasarela:not([hidden])');
    const pagoId = JSON.parse(respuestas(t, 'POST', '/api/v1/payments')[0].respuesta).id;
    const r = await desdePagina(page, 'POST', `/payments/${pagoId}/simular`, { resultado: 'aprobado', repetir_aviso: 2 });
    const avisos = r.datos.avisos || [];
    check(t, 'POST /simular 202 con dos avisos enviados', r.status === 202 && avisos.length === 2, JSON.stringify(r.datos));
    check(t, 'Primer aviso APROBADO y segundo marcado como repetido', avisos[0] && avisos[0].respuesta.estado === 'APROBADO' && avisos[1] && avisos[1].respuesta.repetido === true, JSON.stringify(avisos));
    t.patronesLog.push('repetido');
    await dormir(1000);
    const venta = inspeccion(t, 'Ventas del pedido en analítica', 'analitica', 'ventas', { _id: id }, 'total');
    check(t, 'Una sola venta del pedido en analitica.ventas', venta.total === 1, venta.total);
    const ped = inspeccion(t, 'Pedido', 'orders', 'pedidos', { _id: id }, 'estado,folio').resultado[0];
    check(t, 'Pedido PAGADO con un solo folio', ped.estado === 'PAGADO' && /^B-\d{6}$/.test(ped.folio), JSON.stringify(ped));
    await page.reload();
    await page.waitForSelector('#ped-boleta:not([hidden])');
    await captura(t, page, 'pagado-una-vez', 'Pedido pagado una vez pese al aviso repetido');
  },

  async P12(t) {
    const page = await paginaCon(t, ANA);
    const antes = stock('espresso-doble');
    await agregarAlCarrito(page, [['espresso-doble', 1]]);
    await confirmarPedido(page);
    await page.waitForURL('**/pedido.php?id=**');
    const id = new globalThis.URL(page.url()).searchParams.get('id');
    t.vinculos.add('pedido ' + id);
    await page.waitForSelector('#ped-anular:not([hidden])');
    check(t, 'Al crear el pedido se reserva 1 Espresso', stock('espresso-doble') === antes - 1);
    await page.fill('input[name=motivo]', 'Me equivoque de producto');
    await page.click('#anular-form button');
    await page.waitForSelector('#ped-aviso.ok >> text=anulado');
    check(t, 'Estado Anulado', (await page.textContent('#ped-estado')) === 'Anulado');
    const c = respuestas(t, 'POST', '/cancel')[0];
    check(t, 'POST /cancel responde 200', c && c.estado === 200, c && c.estado);
    await captura(t, page, 'anulado', 'Pedido anulado');
    await dormir(500);
    inspeccion(t, 'Stock de Espresso', 'inventory', 'productos', { _id: 'espresso-doble' }, 'stock');
    check(t, 'El stock vuelve al valor anterior', stock('espresso-doble') === antes, `${antes} -> ${stock('espresso-doble')}`);
    const ped = inspeccion(t, 'Pedido anulado', 'orders', 'pedidos', { _id: id }, 'estado,motivo_anulacion,historial').resultado[0];
    check(t, 'orders.pedidos: ANULADO con el motivo en el historial', ped.estado === 'ANULADO' && ped.historial.some(h => h.estado === 'ANULADO' && h.motivo), JSON.stringify(ped.historial));
    if (estado.P03) {
      await page.goto(FRONT + 'pedido.php?id=' + estado.P03);
      await page.waitForSelector('#ped-detalle:not([hidden])');
      check(t, 'Un pedido pagado no muestra la opción de anular', await page.isHidden('#ped-anular'));
    }
  },

  async P13(t) {
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'mis-pedidos.php');
    await page.waitForSelector('.mp-pedido');
    const r = respuestas(t, 'POST', '/api/v1/graphql')[0];
    const datos = JSON.parse(r.respuesta);
    check(t, 'POST /graphql 200 sin errors', r.estado === 200 && !datos.errors, r.estado);
    const db = inspeccion(t, 'Pedidos de USR-003', 'orders', 'pedidos', { user_id: 'USR-003' }, 'estado,total');
    const tarjetas = await page.locator('.mp-pedido').count();
    check(t, 'Un pedido en pantalla por cada pedido de ana en orders.pedidos', tarjetas === db.total, `${tarjetas} / ${db.total}`);
    const porId = Object.fromEntries(db.resultado.map(d => [d._id, d.estado]));
    check(t, 'Estados de GraphQL = estados guardados en orders', datos.data.misPedidos.every(p => porId[p.id] === p.estado));
    const conNombres = datos.data.misPedidos.every(p => p.lineas.every(l => l.producto && l.producto.nombre));
    check(t, 'Todos los productos traen nombre (inventory)', conNombres);
    const pagos = inspeccion(t, 'Pagos de ana', 'payments', 'pagos', { user_id: 'USR-003' }, 'order_id,estado');
    check(t, 'Los pedidos con pago muestran el pago (payments)', datos.data.misPedidos.filter(p => p.pago).every(p => pagos.resultado.some(x => x.order_id === p.id)), pagos.total);
    await captura(t, page, 'mis-pedidos', 'Mis pedidos agregado por GraphQL');
  },

  async P14(t) {
    if (!estado.P03) throw new Bloqueada('Depende de P03, que no dejó un pedido');
    const id = estado.P03;
    t.vinculos.add('pedido ' + id);
    const antes = inspeccionar('orders', 'pedidos', { _id: id }, 'estado,user_id,total').resultado[0];
    const page = await paginaCon(t, 'pedro@aromaycafe.test');
    await page.goto(FRONT + 'pedido.php?id=' + id);
    await page.waitForSelector('#ped-aviso.error');
    check(t, 'Mensaje "No encontramos ese pedido" y sin detalle', (await page.textContent('#ped-aviso')).includes('No encontramos') && await page.isHidden('#ped-detalle'));
    const g = respuestas(t, 'GET', '/api/v1/orders/' + id)[0];
    check(t, 'GET /orders/{id} responde 404', g && g.estado === 404, g && g.estado);
    await captura(t, page, 'pedido-ajeno', 'Pedro intenta ver el pedido de Ana');
    const q = await desdePagina(page, 'POST', '/graphql', { query: 'query($id: String!) { resumenPedido(id: $id) { id estado total } }', variables: { id } });
    check(t, 'GraphQL resumenPedido del pedido ajeno = null', q.status === 200 && q.datos.data.resumenPedido === null, JSON.stringify(q.datos));
    const despues = inspeccion(t, 'Pedido de ana', 'orders', 'pedidos', { _id: id }, 'estado,user_id,total').resultado[0];
    check(t, 'El pedido de ana no cambió', JSON.stringify(antes) === JSON.stringify(despues), JSON.stringify(despues));
  },

  async P15(t) {
    const page = await paginaCon(t, ANA);
    dc('stop', 'inventory');
    t.patronesLog.push('no disponible');
    try {
      await page.goto(FRONT + 'mis-pedidos.php');
      await page.waitForSelector('.mp-pedido');
      await page.waitForSelector('#mp-aviso.error');
      const aviso = await page.textContent('#mp-aviso');
      check(t, 'Aviso de información incompleta', aviso.includes('Información incompleta'), aviso);
      check(t, 'Productos marcados como dato no disponible', await page.locator('.mp-productos .incompleto').count() > 0);
      const r = JSON.parse(respuestas(t, 'POST', '/api/v1/graphql')[0].respuesta);
      check(t, 'La respuesta GraphQL trae errors de inventory y data parcial', (r.errors || []).some(e => e.message.includes('inventory')) && Array.isArray(r.data.misPedidos), JSON.stringify(r.errors));
      await captura(t, page, 'incompleto', 'Mis pedidos con inventory detenido');
    } finally {
      dc('start', 'inventory');
      await esperarSanos(['inventory']);
    }
    await page.reload();
    await page.waitForSelector('.mp-pedido');
    await dormir(500);
    check(t, 'Con inventory de vuelta: sin aviso y sin productos incompletos', !(await page.isVisible('#mp-aviso.error')) && await page.locator('.mp-productos .incompleto').count() === 0);
    await captura(t, page, 'completo', 'Mis pedidos completo otra vez');
  },

  async P16(t) {
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'index.php');
    const id = estado.P03 || 'ORD-00000000';
    const q1 = await desdePagina(page, 'POST', '/graphql', { query: 'query($id: String!) { resumenPedido(id: $id) { id cliente { nombre telefono } } }', variables: { id } });
    check(t, 'Campo cliente: null con error de autorización', q1.status === 200 && q1.datos.data.resumenPedido && q1.datos.data.resumenPedido.cliente === null && (q1.datos.errors || []).some(e => e.message.includes('No autorizado')), JSON.stringify(q1.datos));
    const q2 = await desdePagina(page, 'POST', '/graphql', { query: '{ reporteVentas { pedidos totalVendido } }' });
    check(t, 'reporteVentas para un cliente: error', (q2.datos.errors || []).some(e => e.message.includes('Solo el dueno')), JSON.stringify(q2.datos));
    const alias = ['a', 'b', 'c', 'd', 'e', 'f'].map(a => `${a}: misPedidos { id }`).join(' ');
    const q3 = await desdePagina(page, 'POST', '/graphql', { query: `{ ${alias} }` });
    check(t, 'Consulta con 6 alias rechazada (límite 5)', q3.datos.data === null && (q3.datos.errors || []).length > 0, JSON.stringify(q3.datos).slice(0, 200));
    const q4 = await desdePagina(page, 'POST', '/graphql', { query: '{ misPedidos { id } }' + ' '.repeat(2100) });
    check(t, 'Consulta de más de 2000 caracteres: 422', q4.status === 422, q4.status);
  },

  async P17(t) {
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'cuenta.php');
    await page.waitForSelector('#cuenta-form:not([hidden])');
    const telefono = '+56 9 5555 ' + String(Date.now()).slice(-4);
    await page.fill('input[name=telefono]', telefono);
    await page.fill('input[name=comuna]', 'Maipú');
    await page.click('#cuenta-form button[type=submit]');
    await page.waitForSelector('#cuenta-aviso.ok');
    const put = respuestas(t, 'PUT', '/api/v1/clients/me')[0];
    check(t, 'PUT /clients/me responde 200', put && put.estado === 200, put && put.estado);
    await page.reload();
    await page.waitForSelector('#cuenta-form:not([hidden])');
    check(t, 'Al recargar se ven los valores nuevos', (await page.inputValue('input[name=telefono]')) === telefono && (await page.inputValue('input[name=comuna]')) === 'Maipú');
    await captura(t, page, 'ficha', 'Ficha guardada');
    const doc = inspeccion(t, 'Ficha de USR-003', 'clients', 'clientes', { _id: 'USR-003' }, 'telefono,comuna,run').resultado[0];
    check(t, 'clients.clientes guarda teléfono y comuna', doc.telefono === telefono && doc.comuna === 'Maipú', JSON.stringify(doc));
    const otra = await paginaCon(t, ANA, true);
    await otra.goto(FRONT + 'cuenta.php');
    await otra.waitForSelector('#cuenta-form:not([hidden])');
    check(t, 'En una sesión nueva se ven los mismos datos', (await otra.inputValue('input[name=telefono]')) === telefono);
  },

  async P18(t) {
    const antes = inspeccionar('clients', 'clientes', { _id: 'USR-003' }, 'run,telefono,comuna').resultado[0];
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'cuenta.php');
    await page.waitForSelector('#cuenta-form:not([hidden])');
    await page.fill('input[name=run]', '12.345.678-9');
    await page.click('#cuenta-form button[type=submit]');
    await page.waitForSelector('#cuenta-aviso.error');
    const aviso = await page.textContent('#cuenta-aviso');
    check(t, 'Mensaje: el RUN no es válido', aviso.includes('RUN no es válido'), aviso);
    const put = respuestas(t, 'PUT', '/api/v1/clients/me')[0];
    check(t, 'PUT /clients/me responde 422', put && put.estado === 422, put && put.estado);
    const despues = inspeccion(t, 'Ficha de USR-003', 'clients', 'clientes', { _id: 'USR-003' }, 'run,telefono,comuna').resultado[0];
    check(t, 'La ficha no cambió', JSON.stringify(antes) === JSON.stringify(despues), JSON.stringify(despues));
    await captura(t, page, 'run-invalido', 'RUN inválido rechazado');
  },

  async P19(t) {
    const page = await paginaCon(t, ANA, true);
    const salida = ejecutar('docker', ['compose', 'exec', '-T', 'auth', 'python', 'vencer_sesion.py', ANA]);
    t.notas.push(salida.trim());
    const antes = inspeccion(t, 'Sesiones de USR-003 antes', 'auth', 'sesiones', { user_id: 'USR-003' }, 'expires_at').total;
    await page.goto(FRONT + 'cuenta.php');
    await page.waitForURL('**/login.php?expirada=1**');
    const aviso = await page.textContent('#login-aviso');
    check(t, 'Redirige a login.php?expirada=1 con aviso', aviso.includes('expiró'), aviso);
    const g = respuestas(t, 'GET', '/api/v1/clients/me').pop();   // la ultima: la del acceso con la sesion vencida
    check(t, 'GET /clients/me (con la sesión vencida) responde 401', g && g.estado === 401, g && g.estado);
    t.patronesLog.push('sesion expirada');
    const despues = inspeccion(t, 'Sesiones de USR-003 después', 'auth', 'sesiones', { user_id: 'USR-003' }, 'expires_at').total;
    check(t, 'La sesión vencida se borró de auth.sesiones', despues === antes - 1, `${antes} -> ${despues}`);
    await captura(t, page, 'sesion-expirada', 'Sesión expirada: vuelve a iniciar sesión');
    delete sesiones[ANA];
  },

  async P20(t) {
    const page = await paginaCon(t, null);
    await page.goto(FRONT + 'cuenta.php');
    await page.waitForURL('**/login.php**');
    check(t, 'Sin sesión, Mi cuenta lleva a login.php', page.url().includes('volver=cuenta.php'), page.url());
    const r = await desdePagina(page, 'GET', '/clients/me', null, false);
    check(t, 'GET /clients/me sin token: 401 "Bearer token requerido"', r.status === 401 && r.datos.detail === 'Bearer token requerido', JSON.stringify(r));
    t.patronesLog.push('sin token');
    await captura(t, page, 'sin-sesion', 'Página protegida sin sesión');
  },

  async P21(t) {
    const page = await paginaCon(t, null);
    await page.goto(FRONT + 'login.php');
    await page.fill('input[name=email]', ANA);
    await page.fill('input[name=password]', 'clave-incorrecta-1');
    await page.click('#login-form button[type=submit]');
    await page.waitForSelector('#login-aviso.error');
    check(t, 'Clave incorrecta: "Correo o contraseña incorrectos"', (await page.textContent('#login-aviso')).includes('incorrectos'));
    check(t, 'POST /auth/login responde 401', respuestas(t, 'POST', '/auth/login')[0].estado === 401);
    await iniciarSesion(page, ANA);
    check(t, 'Login correcto: "Hola, Ana"', (await page.textContent('.auth-actions .saludo')) === 'Hola, Ana');
    const token = await page.evaluate(() => JSON.parse(sessionStorage.getItem('aroma_sesion')).token);
    await page.click('.auth-actions button.btn-register');
    await page.waitForURL('**/login.php?salio=1');
    const r = await page.evaluate(async ({ api, token }) => (await fetch(api + '/clients/me', { headers: { Authorization: 'Bearer ' + token } })).status, { api: API, token });
    check(t, 'Después de cerrar sesión, el token anterior recibe 401', r === 401, r);
    t.patronesLog.push('logout');
    await captura(t, page, 'cerro-sesion', 'Sesión cerrada');
    delete sesiones[ANA];
  },

  async P22(t) {
    const correo = `camila.${CAMPANA.toLowerCase()}.${Date.now()}@correo.cl`;
    t.vinculos.add('correo ' + correo);
    const page = await paginaCon(t, null);
    await page.goto(FRONT + 'registro.php');
    await page.fill('#registro-form input[name=nombre]', 'Camila Rojas');
    await page.fill('#registro-form input[name=email]', correo);
    await page.fill('#registro-form input[name=password]', 'clave-segura-1');
    await page.fill('#registro-form input[name=password2]', 'clave-segura-1');
    await page.fill('#registro-form input[name=run]', '11.111.111-1');
    await page.fill('#registro-form input[name=comuna]', 'Maipú');
    await page.click('#registro-form button[type=submit]');
    await page.waitForSelector('#verificar-form:not([hidden])');
    check(t, 'POST /auth/register responde 201', respuestas(t, 'POST', '/auth/register')[0].estado === 201);
    await captura(t, page, 'paso-2', 'Registro: paso 2 (código)');
    const otra = await (await nuevoContexto(t)).newPage();
    await otra.goto(FRONT + 'login.php');
    await otra.fill('input[name=email]', correo);
    await otra.fill('input[name=password]', 'clave-segura-1');
    await otra.click('#login-form button[type=submit]');
    await otra.waitForSelector('#login-aviso.error');
    check(t, 'Antes de verificar: login 403 con aviso para verificar', (await otra.textContent('#login-aviso')).includes('verificar') && respuestas(t, 'POST', '/auth/login').some(r => r.estado === 403));
    const bandeja = ejecutar('docker', ['compose', 'exec', '-T', 'notificaciones', 'python', 'bandeja.py', correo]);
    const codigo = (bandeja.match(/es (\d{6})/) || [])[1];
    check(t, 'El código llegó a la bandeja simulada', Boolean(codigo));
    await page.fill('#verificar-form input[name=codigo]', codigo || '000000');
    await page.click('#verificar-form button[type=submit]');
    await page.waitForSelector('#registro-aviso.ok >> text=verificado');
    check(t, 'POST /auth/verify-email responde 200', respuestas(t, 'POST', '/verify-email').some(r => r.estado === 200));
    await iniciarSesion(otra, correo, 'clave-segura-1');
    check(t, 'Después de verificar: "Hola, Camila"', (await otra.textContent('.auth-actions .saludo')) === 'Hola, Camila');
    const u = inspeccion(t, 'Usuario nuevo', 'auth', 'usuarios', { email: correo }, 'email,rol,correo_verificado').resultado[0];
    check(t, 'auth.usuarios: rol cliente y correo verificado', u && u.rol === 'cliente' && u.correo_verificado === true, JSON.stringify(u));
    inspeccion(t, 'Correo de verificación (cuerpo oculto)', 'notificaciones', 'correos', { para: correo }, 'tipo,asunto,estado,cuerpo');
    await captura(t, otra, 'sesion-nueva', 'La cuenta verificada inicia sesión');
  },

  async P23(t) {
    const page = await paginaCon(t, 'dueno@aromaycafe.test');
    await page.goto(FRONT + 'inventario.php');
    await page.waitForSelector('#inv-tabla-wrap:not([hidden])');
    const latte = page.locator('#inv-filas tr', { hasText: 'Latte Art' });
    await latte.locator('input').nth(1).fill('2900');
    await latte.locator('button', { hasText: 'Guardar' }).click();
    await page.waitForSelector('#inv-aviso.ok >> text=Latte');
    const idNuevo = `prueba-${CAMPANA.toLowerCase()}`;
    await page.click('#inv-nuevo summary');
    await page.fill('#inv-nuevo-form input[name=id]', idNuevo);
    await page.fill('#inv-nuevo-form input[name=nombre]', 'Mocaccino de prueba');
    await page.fill('#inv-nuevo-form input[name=imagen]', 'latte.png');
    await page.fill('#inv-nuevo-form input[name=precio]', '3600');
    await page.fill('#inv-nuevo-form input[name=stock]', '5');
    await page.click('#inv-nuevo-form button[type=submit]');
    await page.waitForSelector('#inv-aviso.ok >> text=Mocaccino');
    await page.locator('#inv-filas tr', { hasText: 'Mocaccino de prueba' }).locator('button', { hasText: 'Dar de baja' }).click();
    await page.waitForSelector('#inv-aviso.ok >> text=baja');
    check(t, 'PUT 200, POST 201 y DELETE 204', respuestas(t, 'PUT', '/admin/products/latte-art')[0].estado === 200 &&
      respuestas(t, 'POST', '/admin/products')[0].estado === 201 && respuestas(t, 'DELETE', '/admin/products/' + idNuevo)[0].estado === 204);
    await captura(t, page, 'inventario', 'Inventario después de los cambios');
    const carta = await paginaCon(t, null);
    await carta.goto(FRONT + 'catalogo.php');
    await carta.waitForSelector('.product-card-lg');
    const nombres = await carta.locator('.product-card-lg h4').allTextContents();
    const precioLatte = await carta.locator('.product-card-lg', { hasText: 'Latte Art' }).locator('.price-row').textContent();
    check(t, 'La carta muestra la oferta del Latte ($2.900 y $3.200 tachado)', precioLatte.includes('2.900') && precioLatte.includes('3.200'), precioLatte);
    check(t, 'El producto dado de baja no aparece en la carta', !nombres.includes('Mocaccino de prueba'));
    await captura(t, carta, 'carta', 'La carta refleja los cambios');
    const docs = inspeccion(t, 'Productos modificados', 'inventory', 'productos', { _id: { $in: ['latte-art', idNuevo] } }, 'nombre,precio,precio_oferta,activo');
    check(t, 'inventory.productos: Latte con oferta 2900 y el nuevo con activo=false',
      docs.resultado.some(d => d._id === 'latte-art' && d.precio_oferta === 2900) && docs.resultado.some(d => d._id === idNuevo && d.activo === false));
    await latte.locator('input').nth(1).fill('');
    await latte.locator('button', { hasText: 'Guardar' }).click();
    await page.waitForSelector('#inv-aviso.ok >> text=Latte');
    check(t, 'Restauración: el Latte sin oferta', inspeccionar('inventory', 'productos', { _id: 'latte-art' }, 'precio_oferta').resultado[0].precio_oferta === null);
  },

  async P24(t) {
    const page = await paginaCon(t, ANA);
    await page.goto(FRONT + 'inventario.php');
    await page.waitForSelector('#inv-aviso.error');
    check(t, 'Inventario: "No tienes permiso"', (await page.textContent('#inv-aviso')).includes('No tienes permiso'));
    await captura(t, page, 'inventario-403', 'Cliente en Inventario');
    await page.goto(FRONT + 'despacho.php');
    await page.waitForSelector('#des-aviso.error');
    check(t, 'Despacho: "No tienes permiso"', (await page.textContent('#des-aviso')).includes('No tienes permiso'));
    check(t, 'GET /admin/products y /admin/dispatch-orders responden 403',
      respuestas(t, 'GET', '/admin/products')[0].estado === 403 && respuestas(t, 'GET', '/admin/dispatch-orders')[0].estado === 403);
    await captura(t, page, 'despacho-403', 'Cliente en Despacho');
  },

  async P25(t) {
    if (!estado.P03) throw new Bloqueada('Depende de P09 (pedido pagado de P03)');
    const id = estado.P03;
    t.vinculos.add('pedido ' + id);
    const page = await paginaCon(t, 'despacho@aromaycafe.test');
    await page.goto(FRONT + 'despacho.php');
    await page.waitForSelector('#des-lista .mp-pedido');
    const ordenes = await page.locator('#des-lista .mp-pedido strong').allTextContents();
    check(t, 'El pedido pagado aparece en la lista', ordenes.includes(id), ordenes.join(', '));
    const tarjeta = () => page.locator('#des-lista .mp-pedido', { hasText: id });
    for (const [boton, texto] of [['en preparación', 'En preparación'], ['listo', 'Listo']]) {
      await tarjeta().locator('button', { hasText: 'Marcar ' + boton }).click();
      await page.waitForSelector(`#des-aviso.ok >> text=${texto}`);
    }
    check(t, 'En Listo (retiro) no se ofrece "en camino"', await tarjeta().locator('button', { hasText: 'Marcar en camino' }).count() === 0);
    await captura(t, page, 'listo', 'Pedido listo para retiro');
    await tarjeta().locator('button', { hasText: 'Marcar entregado' }).click();
    await page.waitForSelector('#des-aviso.ok >> text=Entregado');
    check(t, 'Tres PUT /status 200', respuestas(t, 'PUT', '/status').filter(r => r.estado === 200).length === 3);
    check(t, 'Al quedar Entregado sale de la lista', await page.locator('#des-lista .mp-pedido', { hasText: id }).count() === 0);
    const ped = inspeccion(t, 'Historial del pedido', 'orders', 'pedidos', { _id: id }, 'estado,historial').resultado[0];
    check(t, 'orders.pedidos: ENTREGADO con el historial completo', ped.estado === 'ENTREGADO' &&
      ped.historial.map(h => h.estado).join('>') === 'PENDIENTE_PAGO>PAGADO>EN_PREPARACION>LISTO>ENTREGADO', ped.historial.map(h => h.estado).join(' > '));
  },

  async P26(t) {
    if (!estado.folioP09) throw new Bloqueada('Depende de P09 (folio de la boleta)');
    const page = await paginaCon(t, 'cajero@aromaycafe.test');
    await page.goto(FRONT + 'ventas.php');
    await page.waitForSelector('#ven-resumen:not([hidden])');
    const fila = page.locator('#ven-filas tr', { hasText: estado.folioP09 });
    check(t, 'Fila con el folio de P09 y total $9.200', await fila.count() === 1 && (await fila.textContent()).includes('$9.200'), await fila.count() ? await fila.textContent() : 'sin fila');
    check(t, 'GET /admin/sales responde 200', respuestas(t, 'GET', '/admin/sales')[0].estado === 200);
    inspeccion(t, 'Pedidos en la caja web', 'orders', 'pedidos', { caja: 'CAJA-WEB-01' }, 'folio,total,caja');
    await captura(t, page, 'ventas', 'Ventas de la caja web');
  },

  async P27(t) {
    const dueno = await paginaCon(t, 'dueno@aromaycafe.test');
    await dueno.goto(FRONT + 'reportes.php');
    await dueno.waitForSelector('#rep-contenido:not([hidden])');
    const antes = { pedidos: Number(await dueno.textContent('#rep-pedidos')), total: await dueno.textContent('#rep-total') };
    const ana = await paginaCon(t, ANA);
    await agregarAlCarrito(ana, [['cold-brew', 1]]);
    await confirmarPedido(ana);
    await ana.waitForURL('**/pedido.php?id=**');
    const id = new globalThis.URL(ana.url()).searchParams.get('id');
    t.vinculos.add('pedido ' + id);
    await ana.click('#btn-iniciar-pago');
    await ana.click('#btn-aprobar');
    await ana.waitForSelector('#ped-boleta:not([hidden])');
    await dormir(1000);
    await dueno.click('#rep-actualizar');
    await dueno.waitForFunction(n => Number(document.querySelector('#rep-pedidos').textContent) === n, antes.pedidos + 1, { timeout: 10000 }).catch(() => {});
    const despues = { pedidos: Number(await dueno.textContent('#rep-pedidos')), total: await dueno.textContent('#rep-total') };
    check(t, 'Pedidos pagados aumenta en 1 al actualizar', despues.pedidos === antes.pedidos + 1, `${antes.pedidos} -> ${despues.pedidos}`);
    const montos = [antes.total, despues.total].map(s => Number(s.replace(/\D/g, '')));
    check(t, 'Total vendido aumenta en $3.500 (Cold Brew)', montos[1] - montos[0] === 3500, `${antes.total} -> ${despues.total}`);
    inspeccion(t, 'Venta en analítica', 'analitica', 'ventas', { _id: id }, 'total');
    await captura(t, dueno, 'reporte', 'Reporte actualizado');
  },

  async P28(t) {
    const antes = inspeccionar('analitica', 'ventas', {}, '_id').total;
    dc('stop', 'analitica');
    let id;
    const dueno = await paginaCon(t, 'dueno@aromaycafe.test');
    try {
      const ana = await paginaCon(t, ANA);
      await agregarAlCarrito(ana, [['cappuccino', 1]]);
      await confirmarPedido(ana);
      await ana.waitForURL('**/pedido.php?id=**');
      id = new globalThis.URL(ana.url()).searchParams.get('id');
      t.vinculos.add('pedido ' + id);
      t.patronesLog.push(id);
      await ana.click('#btn-iniciar-pago');
      await ana.click('#btn-aprobar');
      await ana.waitForSelector('#ped-boleta:not([hidden])');
      check(t, 'Con analítica detenida el pago se confirma (Pagado)', (await ana.textContent('#ped-estado')) === 'Pagado');
      await dueno.goto(FRONT + 'reportes.php');
      await dueno.waitForSelector('#rep-aviso.error');
      check(t, 'Reportes informa el error mientras analítica está detenida', (await dueno.textContent('#rep-aviso')).includes('no está disponible'), await dueno.textContent('#rep-aviso'));
      await captura(t, dueno, 'analitica-detenida', 'Reportes con analítica detenida');
      const ped = inspeccion(t, 'Pedido con aviso pendiente', 'orders', 'pedidos', { _id: id }, 'estado,avisos_enviados').resultado[0];
      check(t, 'orders guarda el aviso como pendiente', ped.estado === 'PAGADO' && ped.avisos_enviados === false, JSON.stringify(ped));
    } finally {
      dc('start', 'analitica');
      await esperarSanos(['analitica']);
    }
    const t0 = Date.now();
    let total = antes;
    while (Date.now() - t0 < 90000) {
      total = inspeccionar('analitica', 'ventas', {}, '_id').total;
      if (total === antes + 1) break;
      await dormir(5000);
    }
    const segundos = Math.round((Date.now() - t0) / 1000);
    check(t, 'Al volver analítica, la venta se registra (reintento de orders)', total === antes + 1, `${antes} -> ${total} en ${segundos} s`);
    t.notas.push(`La venta llegó a analítica ${segundos} s después de iniciarla (orders reintenta cada 30 s)`);
    inspeccion(t, 'Venta registrada después de la recuperación', 'analitica', 'ventas', { _id: id }, 'total');
    // Sin recargar la pagina: el aviso de error ofrece Reintentar
    await dueno.click('#rep-aviso .btn-reintentar');
    await dueno.waitForSelector('#rep-contenido:not([hidden])');
    await dormir(800);
    check(t, 'Reintentar en Reportes muestra el reporte con la venta', Number(await dueno.textContent('#rep-pedidos')) === total, await dueno.textContent('#rep-pedidos'));
    await captura(t, dueno, 'recuperado', 'Reporte después de la recuperación');
  },

  async P29(t) {
    const page = await paginaCon(t, 'admin@aromaycafe.test');
    await page.goto(FRONT + 'admin.php');
    await page.waitForSelector('#adm-usuarios tr');
    const sufijo = `${CAMPANA.toLowerCase()}.${Date.now()}`;
    const cajero = `cajero.${sufijo}@aromaycafe.test`;
    await page.locator('details', { hasText: 'Crear cuenta de funcionario' }).locator('summary').click();
    await page.fill('#adm-funcionario input[name=email]', cajero);
    await page.fill('#adm-funcionario input[name=password]', 'clave-cajero-1');
    await page.selectOption('#adm-funcionario select[name=rol]', 'cajero');
    await page.click('#adm-funcionario button[type=submit]');
    await page.waitForSelector('#adm-aviso.ok >> text=Cuenta creada');
    const fila = page.locator('#adm-usuarios tr', { hasText: cajero });
    await fila.locator('select').selectOption('despacho');
    await fila.locator('button').click();
    await page.waitForSelector('#adm-aviso.ok >> text=Encargado de despacho');
    const propia = page.locator('#adm-usuarios tr', { hasText: 'admin@aromaycafe.test' });
    await propia.locator('select').selectOption('cliente');
    await propia.locator('button').click();
    await page.waitForSelector('#adm-aviso.error');
    check(t, 'Cambiar el propio perfil: "No puedes cambiar tu propio perfil"', (await page.textContent('#adm-aviso')).includes('propio perfil'));
    const cliente = `luis.${sufijo}@correo.cl`;
    await page.locator('details', { hasText: 'Registrar cliente en el local' }).locator('summary').click();
    await page.fill('#adm-cliente input[name=nombre]', 'Luis Soto');
    await page.fill('#adm-cliente input[name=email]', cliente);
    await page.fill('#adm-cliente input[name=password]', 'clave-luis-12');
    await page.click('#adm-cliente button[type=submit]');
    await page.waitForSelector('#adm-aviso.ok >> text=Cliente registrado');
    check(t, 'POST /admin/users 201, PUT /role 200, PUT propio 409 y POST /admin/clients 201',
      respuestas(t, 'POST', '/admin/users')[0].estado === 201 && respuestas(t, 'PUT', '/role').map(r => r.estado).join(',') === '200,409' &&
      respuestas(t, 'POST', '/admin/clients')[0].estado === 201, respuestas(t, 'PUT', '/role').map(r => r.estado).join(','));
    await captura(t, page, 'administracion', 'Administración de usuarios');
    const us = inspeccion(t, 'Usuarios creados', 'auth', 'usuarios', { email: { $in: [cajero, cliente, 'admin@aromaycafe.test'] } }, 'email,rol,correo_verificado');
    const por = Object.fromEntries(us.resultado.map(u => [u.email, u]));
    check(t, 'auth.usuarios: funcionario con perfil despacho, admin sin cambio y cliente sin verificar',
      por[cajero] && por[cajero].rol === 'despacho' && por['admin@aromaycafe.test'].rol === 'admin' && por[cliente] && por[cliente].rol === 'cliente' && por[cliente].correo_verificado === false,
      JSON.stringify(us.resultado));
  },

  async P30(t) {
    const nombre = `Visita ${CAMPANA} ${Date.now() % 100000}`;
    const page = await paginaCon(t, null);
    await page.goto(FRONT + 'Contacto.php');
    await page.fill('input[name=email]', 'visita@correo.cl');
    await page.fill('input[name=nombre]', nombre);
    await page.selectOption('select[name=motivo]', 'sugerencia');
    await page.fill('textarea[name=mensaje]', 'Me gustaria que tuvieran leche de avena');
    await page.click('#contact-form button[type=submit]');
    await page.waitForSelector('#form-note.show');
    check(t, 'Aviso de gracias y POST /contact 201', (await page.textContent('#form-note')).includes('Gracias') && respuestas(t, 'POST', '/contact')[0].estado === 201);
    await captura(t, page, 'contacto', 'Mensaje de contacto enviado');
    const admin = await paginaCon(t, 'admin@aromaycafe.test');
    await admin.goto(FRONT + 'admin.php');
    await admin.waitForSelector('#adm-contacto tr');
    check(t, 'El admin ve el mensaje en Administración', await admin.locator('#adm-contacto tr', { hasText: nombre }).count() === 1);
    const db = inspeccion(t, 'Mensaje guardado', 'clients', 'contacto', { nombre }, 'nombre,motivo,creado_en');
    check(t, 'clients.contacto: mensaje guardado', db.total === 1);
  },

  async P31(t) {
    const salida = ejecutar('docker', ['compose', 'exec', '-T', 'clients', 'python', 'llamada_sin_secreto.py']);
    fs.writeFileSync(path.join(t.dir, 'salida.txt'), salida);
    evidencia(t, 'salida', 'salida.txt', 'Salida de llamada_sin_secreto.py');
    check(t, 'Sin secreto y con secreto falso: 403', (salida.match(/403 Forbidden/g) || []).length === 2, salida.trim());
    t.patronesLog.push('RECHAZADA');
  },

  async P32(t) {
    const page = await paginaCon(t, ANA);
    const paginas = ['index.php', 'catalogo.php', 'carrito.php', 'cuenta.php', 'mis-pedidos.php', 'Contacto.php'];
    if (estado.P03) paginas.push('pedido.php?id=' + estado.P03);
    const viewport = page.viewportSize();
    t.notas.push(`Viewport ${viewport.width}x${viewport.height}${CONF.dispositivo ? ' (' + CONF.dispositivo + ', emulado)' : ''}`);
    for (const p of paginas) {
      await page.goto(FRONT + p);
      await page.waitForLoadState('networkidle');
      const medida = await page.evaluate(() => ({ documento: document.documentElement.scrollWidth, ventana: window.innerWidth }));
      check(t, `${p}: sin desborde horizontal`, medida.documento <= medida.ventana, `${medida.documento} <= ${medida.ventana}`);
    }
    await page.goto(FRONT + 'mis-pedidos.php');
    await page.waitForSelector('.mp-pedido');
    await captura(t, page, 'mis-pedidos', 'Mis pedidos en este viewport');
  },
};

// ---------------------------------------------------------------- Ejecucion
(async () => {
  fs.mkdirSync(SALIDA, { recursive: true });
  const git = (...a) => spawnSync('git', a, { cwd: RAIZ, encoding: 'utf8' }).stdout.trim();
  if (!SIN_REINICIO) await reiniciarSistema();
  navegador = await chromium.launch();
  const meta = {
    campana: CAMPANA, nombre: CONF.nombre, protocolo: PROTOCOLO.version,
    commit: git('rev-parse', '--short', 'HEAD'), cambios_sin_commit: git('status', '--porcelain', '--', '.') !== '',
    inicio: fechaLocal(), zona_horaria: Intl.DateTimeFormat().resolvedOptions().timeZone,
    ejecutor: process.env.EJECUTOR || os.userInfo().username, sistema: `${os.type()} ${os.release()}`,
    navegador: `Chromium ${navegador.version()} (Playwright ${require('playwright/package.json').version})`,
    viewport: CONF.dispositivo ? `${CONF.dispositivo} emulado (${devices[CONF.dispositivo].viewport.width}x${devices[CONF.dispositivo].viewport.height})` : `${CONF.viewport.width}x${CONF.viewport.height}`,
    docker: ejecutar('docker', ['version', '--format', '{{.Server.Version}}']).trim(),
    estado_inicial: SIN_REINICIO ? 'sin reinicio (base existente)' : 'base vacía (docker compose down -v / up -d)',
    limite_general_gateway: `${LIMITE_GENERAL} solicitudes por minuto (login: 10 por minuto, sin cambios)`,
  };
  console.log(`Campaña ${CAMPANA} (${meta.nombre}) · commit ${meta.commit}${meta.cambios_sin_commit ? ' + cambios sin commit' : ''} · ${meta.viewport}`);
  const resultados = [];
  for (const def of PROTOCOLO.pruebas) {
    if (SOLO.length && !SOLO.includes(def.id)) continue;
    const t = nuevaPrueba(def);
    let estadoFinal;
    try {
      await PRUEBAS[def.id](t);
      estadoFinal = t.checks.length && t.checks.every(c => c.ok) ? 'aprobada' : 'fallida';
    } catch (error) {
      if (error instanceof Bloqueada) {
        estadoFinal = 'bloqueada';
        t.notas.push('Bloqueada: ' + error.message);
      } else {
        estadoFinal = 'fallida';
        check(t, 'La prueba terminó sin errores', false, error.message.split('\n')[0]);
      }
    }
    for (const c of navegador.contexts()) await c.close();
    let r;
    try { r = cerrarPrueba(t, estadoFinal); } catch (e) { r = { id: def.id, run: t.run, estado: 'bloqueada', notas: [e.message] }; }
    resultados.push(r);
    const fallos = r.observado ? r.observado.filter(c => !c.ok).map(c => c.descripcion + ': ' + c.detalle) : r.notas;
    console.log(`${r.estado.padEnd(10)} ${r.run} ${def.titulo}${fallos.length && r.estado !== 'aprobada' ? '\n           ' + fallos.join('\n           ') : ''}`);
  }
  await navegador.close();
  meta.fin = fechaLocal();
  const conteo = resultados.reduce((c, r) => ({ ...c, [r.estado]: (c[r.estado] || 0) + 1 }), {});
  fs.writeFileSync(path.join(SALIDA, 'resultados.json'), JSON.stringify({ meta, conteo, resultados }, null, 1));
  console.log('\nResultado:', JSON.stringify(conteo), '→', path.relative(BACKEND, path.join(SALIDA, 'resultados.json')));
  process.exit(conteo.fallida || conteo.bloqueada ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
