// Linea base (Etapa 1): registra con evidencia el estado del frontend INICIAL, antes de la integracion.
// Sirve la carpeta del frontend de la Solemne 2 con PHP en Docker (puerto 8081) y comprueba, desde Chromium,
// si cada pantalla usa el backend o datos locales.
//
// Uso (desde Backend/pruebas, con Docker abierto):
//   node linea_base.js "<ruta a la carpeta Solemne 2/Frontend del repositorio Desarrollo-Web-Movil>"
// Evidencias en docs/evidencias/LB/.
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium } = require('playwright');

const CARPETA = path.resolve(process.argv[2] || '');
if (!fs.existsSync(path.join(CARPETA, 'catalogo.php'))) {
  console.error('Uso: node linea_base.js "<carpeta del frontend inicial>"');
  process.exit(2);
}
const SALIDA = path.join(__dirname, '..', 'docs', 'evidencias', 'LB');
const URL = 'http://localhost:8081/';
fs.rmSync(SALIDA, { recursive: true, force: true });
fs.mkdirSync(SALIDA, { recursive: true });

const docker = (...a) => spawnSync('docker', a, { encoding: 'utf8' });
docker('rm', '-f', 'linea-base-frontend');
const r = docker('run', '-d', '--name', 'linea-base-frontend', '-p', '127.0.0.1:8081:8080', '-v', `${CARPETA}:/app:ro`,
  'php:8.3-cli-alpine', 'php', '-S', '0.0.0.0:8080', '-t', '/app');
if (r.status !== 0) { console.error(r.stderr); process.exit(2); }

(async () => {
  const resultados = [];
  const navegador = await chromium.launch();
  const ctx = await navegador.newContext({ viewport: { width: 1366, height: 768 } });
  const backend = [];
  ctx.on('request', req => { if (/:8000|\/api\//.test(req.url())) backend.push(req.method() + ' ' + req.url()); });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept());
  await new Promise(res => setTimeout(res, 1500));
  const prueba = async (id, descripcion, fn) => {
    backend.length = 0;
    let observado;
    try { observado = await fn(); } catch (e) { observado = 'error: ' + e.message.split('\n')[0]; }
    await page.screenshot({ path: path.join(SALIDA, `${id}.jpg`), type: 'jpeg', quality: 60 });
    resultados.push({ id, descripcion, observado, solicitudes_al_backend: [...backend], evidencia: `LB/${id}.jpg` });
    console.log(id, descripcion, '→', observado, '| solicitudes al backend:', backend.length);
  };

  await prueba('LB01', 'Carta: origen de los productos', async () => {
    await page.goto(URL + 'catalogo.php');
    const n = await page.locator('.product-card-lg').count();
    const enHtml = (fs.readFileSync(path.join(CARPETA, 'catalogo.php'), 'utf8').match(/class="product-card-lg"/g) || []).length;
    return `${n} tarjetas, escritas en el HTML de catalogo.php (${enHtml} tarjetas class="product-card-lg" en el archivo)`;
  });
  await prueba('LB02', 'Botones Iniciar sesión y Registrarse', async () => {
    const hrefs = await page.locator('.auth-actions a').evaluateAll(as => as.map(a => `${a.textContent.trim()} → href="${a.getAttribute('href')}"`));
    return hrefs.join('; ');
  });
  await prueba('LB03', 'Carrito: Pagar pedido', async () => {
    await page.locator('[data-add-to-cart]').first().click();
    await page.goto(URL + 'carrito.php');
    const antes = await page.evaluate(() => localStorage.getItem('aroma_cart'));
    await page.click('#btn-pay');
    await page.waitForTimeout(800);
    const despues = await page.evaluate(() => localStorage.getItem('aroma_cart'));
    return `carrito antes: ${antes ? JSON.parse(antes).length + ' producto(s)' : 'vacío'}; después: ${despues ? 'con datos' : 'borrado del navegador'}; aviso: "${(await page.textContent('.toast')) || ''}"`;
  });
  await prueba('LB04', 'Contacto: enviar mensaje', async () => {
    await page.goto(URL + 'Contacto.php');
    const campos = await page.locator('#contact-form input, #contact-form textarea').all();
    for (const c of campos) await c.fill(((await c.getAttribute('type')) === 'email') ? 'a@b.cl' : 'Mensaje de prueba');
    await page.click('#contact-form button[type=submit]');
    await page.waitForTimeout(500);
    return `aviso: "${await page.textContent('#form-note')}"`;
  });
  await prueba('LB05', 'Pantallas de pedidos, cuenta y paneles', async () => {
    const paginas = ['login.php', 'registro.php', 'cuenta.php', 'pedido.php', 'mis-pedidos.php', 'inventario.php', 'despacho.php', 'admin.php'];
    const estados = [];
    for (const p of paginas) estados.push(`${p}: ${(await page.goto(URL + p)).status()}`);
    return estados.join(', ');
  });
  await navegador.close();
  docker('rm', '-f', 'linea-base-frontend');
  fs.writeFileSync(path.join(SALIDA, 'resultados.json'), JSON.stringify({
    fecha: new Date().toISOString(), frontend: CARPETA.split(path.sep).slice(-2).join('/'), navegador: 'Chromium (Playwright)',
    viewport: '1366x768', resultados }, null, 1));
})();
