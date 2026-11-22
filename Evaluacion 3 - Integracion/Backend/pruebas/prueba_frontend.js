// Prueba del frontend en Chromium (Playwright) contra el sistema en Docker, en escritorio y en celular (Pixel 7):
// login, registro con codigo, mi cuenta, inventario, cerrar sesion, sesion vencida y contacto.
//
// Uso (con 'docker compose up -d' corriendo):
//   cd pruebas && npm install && npx playwright install chromium
//   TEST_PASSWORD=<SEED_PASSWORD del .env> npm test          (PowerShell: $env:TEST_PASSWORD="..."; npm test)
//
// El navegador de la prueba acepta el certificado de la CA local sin instalarlo (ignoreHTTPSErrors).
// Crea un usuario y un producto nuevos y cambia la oferta y el stock del Latte.
const fs = require('fs');
const path = require('path');
const { chromium, devices } = require('playwright');
const { execSync } = require('child_process');
const BACK = path.resolve(__dirname, '..');
const OUT = path.join(BACK, 'docs', 'evidencias', 'capturas');
const CLAVE = process.env.TEST_PASSWORD;
if (!CLAVE) { console.error('Falta la variable TEST_PASSWORD (la SEED_PASSWORD del .env)'); process.exit(1); }
fs.mkdirSync(OUT, { recursive: true });
const URL = 'http://localhost:8080/';
const ID_NUEVO = 'mocaccino-' + Date.now().toString(36);
const lineas = [];
let ok = 0, fallas = 0;
function check(nombre, cond, extra) {
  const linea = cond ? `  [OK]    ${nombre}` : `  [FALLA] ${nombre} ${extra || ''}`;
  if (cond) ok++; else fallas++;
  console.log(linea); lineas.push(linea);
}
async function login(page, email, clave) {
  await page.goto(URL + 'login.php');
  await page.fill('input[name=email]', email); await page.fill('input[name=password]', clave);
  await page.click('#login-form button[type=submit]');
}
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  const errores = []; page.on('pageerror', e => errores.push(e.message));
  page.on('dialog', d => d.accept());

  // 1. login con clave mala
  await login(page, 'ana@aromaycafe.test', 'clave-mala-123');
  await page.waitForSelector('#login-aviso.mostrar');
  check('login con clave incorrecta muestra error', (await page.textContent('#login-aviso')).includes('incorrectos'));
  // 2. login correcto
  await login(page, 'ana@aromaycafe.test', CLAVE);
  await page.waitForURL('**/catalogo.php');
  await page.waitForSelector('.auth-actions .saludo');
  check('login correcto: saludo con el nombre', (await page.textContent('.auth-actions .saludo')) === 'Hola, Ana', await page.textContent('.auth-actions'));
  check('cliente no ve el enlace Inventario', (await page.locator('.auth-actions a[href="inventario.php"]').count()) === 0);
  await page.screenshot({ path: OUT + '/1-carta-con-sesion.png' });
  // 3. mi cuenta
  await page.click('.auth-actions .saludo');
  await page.waitForSelector('#cuenta-form:not([hidden])');
  check('mi cuenta carga el perfil (clients)', (await page.inputValue('input[name=nombre]')) === 'Ana Pérez');
  await page.fill('input[name=telefono]', '+56 9 8765 4321'); await page.fill('input[name=comuna]', 'Maipú');
  await page.click('#cuenta-form button[type=submit]');
  await page.waitForSelector('#cuenta-aviso.ok');
  await page.reload(); await page.waitForSelector('#cuenta-form:not([hidden])');
  check('mi cuenta guarda los cambios (persisten al recargar)', (await page.inputValue('input[name=comuna]')) === 'Maipú');
  await page.fill('input[name=run]', '12.345.678-9'); await page.click('#cuenta-form button[type=submit]');
  await page.waitForSelector('#cuenta-aviso.error');
  check('RUN invalido muestra error', (await page.textContent('#cuenta-aviso')).includes('RUN'));
  await page.screenshot({ path: OUT + '/2-mi-cuenta.png' });
  // 4. cliente escribe inventario.php a mano
  await page.goto(URL + 'inventario.php'); await page.waitForSelector('#inv-aviso.error');
  check('cliente en inventario.php: backend responde 403 y se muestra sin permiso', (await page.textContent('#inv-aviso')).includes('No tienes permiso'));
  // 5. logout e invalidacion del token
  const tokenAna = await page.evaluate(() => JSON.parse(sessionStorage.getItem('aroma_sesion')).token);
  await page.click('.auth-actions button.btn-register'); await page.waitForURL('**/login.php?salio=1');
  check('cerrar sesion vuelve al login', (await page.textContent('#login-aviso')).includes('Cerraste'));
  const r = await page.evaluate(async t => (await fetch('https://127.0.0.1:8000/api/v1/clients/me', { headers: { Authorization: 'Bearer ' + t } })).status, tokenAna);
  check('despues del logout el token viejo ya no sirve (401)', r === 401, r);
  // 6. sesion vencida / token invalido
  await page.evaluate(() => sessionStorage.setItem('aroma_sesion', JSON.stringify({ token: 'token-vencido-1234567890', rol: 'cliente', email: 'x', nombre: 'X', expira: Date.now() + 60000 })));
  await page.goto(URL + 'cuenta.php'); await page.waitForURL('**/login.php?expirada=1**');
  check('token vencido: manda a iniciar sesion de nuevo', (await page.textContent('#login-aviso')).includes('expiró'));
  // 7. registro + verificacion
  const correo = 'prueba' + Date.now() + '@correo.cl';
  await page.goto(URL + 'registro.php');
  check('registro: al entrar solo se ve el paso 1', await page.isVisible('#registro-form') && !(await page.isVisible('#verificar-form')));
  await page.fill('#registro-form input[name=nombre]', 'Camila Rojas'); await page.fill('#registro-form input[name=email]', correo);
  await page.fill('#registro-form input[name=password]', 'clave-segura-1'); await page.fill('#registro-form input[name=password2]', 'otra-clave-22');
  await page.click('#registro-form button[type=submit]');
  check('registro: contrasenas distintas', (await page.textContent('#registro-aviso')).includes('no coinciden'));
  await page.fill('#registro-form input[name=password2]', 'clave-segura-1');
  await page.fill('#registro-form input[name=run]', '11.111.111-1'); await page.fill('#registro-form input[name=comuna]', 'Maipú');
  await page.click('#registro-form button[type=submit]');
  await page.waitForSelector('#verificar-form:not([hidden])');
  check('registro: pasa al paso 2 y el paso 1 se oculta', !(await page.isVisible('#registro-form')));
  await page.screenshot({ path: OUT + '/3-registro-codigo.png' });
  // login sin verificar
  const p2 = await ctx.newPage();
  await login(p2, correo, 'clave-segura-1'); await p2.waitForSelector('#login-aviso.mostrar');
  check('login sin verificar el correo: 403 con enlace a verificar', (await p2.textContent('#login-aviso')).includes('verificar'));
  await p2.close();
  await page.fill('#verificar-form input[name=codigo]', '000000'); await page.click('#verificar-form button[type=submit]');
  await page.waitForSelector('#registro-aviso.error');
  check('codigo incorrecto: error', (await page.textContent('#registro-aviso')).includes('código'));
  const bandeja = execSync(`docker compose exec -T notificaciones python bandeja.py ${correo}`, { cwd: BACK }).toString();
  const codigo = bandeja.match(/es (\d{6})/)[1];
  await page.fill('#verificar-form input[name=codigo]', codigo); await page.click('#verificar-form button[type=submit]');
  await page.waitForSelector('#registro-aviso.ok >> text=verificado');
  check('codigo correcto: correo verificado', true);
  await page.click('#registro-aviso a'); await page.waitForURL('**/login.php?email=**');
  await page.fill('input[name=password]', 'clave-segura-1'); await page.click('#login-form button[type=submit]');
  await page.waitForURL('**/catalogo.php'); await page.waitForSelector('.auth-actions .saludo');
  check('usuario nuevo inicia sesion', (await page.textContent('.auth-actions .saludo')) === 'Hola, Camila');
  await page.click('.auth-actions button.btn-register'); await page.waitForURL('**/login.php?salio=1');
  // 8. duena: inventario
  await login(page, 'dueno@aromaycafe.test', CLAVE);
  await page.waitForURL('**/inventario.php'); await page.waitForSelector('#inv-tabla-wrap:not([hidden])');
  check('saludo con ñ', (await page.textContent('.auth-actions .saludo')) === 'Hola, Dueña');
  const total = await page.locator('#inv-filas tr').count();
  check('duena entra directo a inventario con la tabla de productos', total >= 8, total);
  check('duena ve el enlace Inventario', (await page.locator('.auth-actions a[href="inventario.php"]').count()) === 1);
  const filaLatte = page.locator('#inv-filas tr', { hasText: 'Latte Art' });
  await filaLatte.locator('input').nth(1).fill('2900'); await filaLatte.locator('input').nth(2).fill('15');
  await filaLatte.locator('button', { hasText: 'Guardar' }).click();
  await page.waitForSelector('#inv-aviso.ok');
  await page.waitForFunction(() => [...document.querySelectorAll('#inv-filas tr')].some(tr => tr.textContent.includes('Latte') && tr.querySelectorAll('input')[2].value === '15'));
  check('modifica oferta y stock (persiste)', true);
  await filaLatte.locator('input').nth(1).fill('5000'); await filaLatte.locator('button', { hasText: 'Guardar' }).click();
  await page.waitForSelector('#inv-aviso.error');
  check('oferta mayor que el precio: error del backend', (await page.textContent('#inv-aviso')).includes('oferta'));
  await page.click('#inv-nuevo summary');
  await page.fill('#inv-nuevo-form input[name=id]', ID_NUEVO); await page.fill('#inv-nuevo-form input[name=nombre]', 'Mocaccino');
  await page.fill('#inv-nuevo-form input[name=descripcion]', 'Espresso, chocolate y leche.'); await page.fill('#inv-nuevo-form input[name=imagen]', 'latte.png');
  await page.fill('#inv-nuevo-form input[name=precio]', '3600'); await page.fill('#inv-nuevo-form input[name=stock]', '20');
  await page.click('#inv-nuevo-form button[type=submit]');
  await page.waitForFunction(n => document.querySelectorAll('#inv-filas tr').length === n + 1, total);
  check('agrega producto nuevo', true);
  await page.screenshot({ path: OUT + '/4-inventario.png', fullPage: true });
  await page.locator('#inv-filas tr', { hasText: 'Cold Brew' }).locator('button', { hasText: 'Dar de baja' }).click();
  await page.waitForFunction(() => [...document.querySelectorAll('#inv-filas tr')].some(tr => tr.textContent.includes('Cold Brew') && tr.textContent.includes('De baja')));
  check('da de baja un producto', true);
  await page.goto(URL + 'catalogo.php'); await page.waitForSelector('.product-card-lg');
  const nombres = await page.locator('.product-card-lg h4').allTextContents();
  check('la carta refleja el inventario (Mocaccino si, Cold Brew no)', nombres.includes('Mocaccino') && !nombres.includes('Cold Brew'), nombres.join(','));
  const latte = await page.locator('.product-card-lg', { hasText: 'Latte Art' }).locator('.price-row').textContent();
  check('la carta muestra la oferta nueva del Latte', latte.includes('2.900') && latte.includes('3.200'), latte);
  // Reactivar para dejar los datos como estaban
  await page.goto(URL + 'inventario.php'); await page.waitForSelector('#inv-tabla-wrap:not([hidden])');
  await page.locator('#inv-filas tr', { hasText: 'Cold Brew' }).locator('button', { hasText: 'Reactivar' }).click();
  await page.waitForFunction(() => [...document.querySelectorAll('#inv-filas tr')].some(tr => tr.textContent.includes('Cold Brew') && tr.textContent.includes('Activo')));
  check('reactiva el producto', true);
  // 9. contacto
  await page.goto(URL + 'Contacto.php');
  await page.fill('input[name=email]', 'visita@correo.cl'); await page.fill('input[name=nombre]', 'Visita');
  await page.selectOption('select[name=motivo]', 'sugerencia'); await page.fill('textarea[name=mensaje]', 'Me encanta el cold brew');
  await page.click('#contact-form button[type=submit]'); await page.waitForSelector('#form-note.show');
  check('formulario de contacto guardado', (await page.textContent('#form-note')).includes('Gracias'));
  check('sin errores de JavaScript', errores.length === 0, errores.join(' | '));
  await ctx.close();
  // 10. celular
  const movil = await b.newContext({ ...devices['Pixel 7'], ignoreHTTPSErrors: true });
  const m = await movil.newPage();
  await login(m, 'dueno@aromaycafe.test', CLAVE); await m.waitForURL('**/inventario.php'); await m.waitForSelector('#inv-tabla-wrap:not([hidden])');
  const ancho = await m.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
  check('celular: la pagina no tiene scroll horizontal (la tabla se desplaza dentro de su caja)', ancho);
  await m.screenshot({ path: OUT + '/5-celular-inventario.png' });
  await m.goto(URL + 'registro.php'); await m.screenshot({ path: OUT + '/6-celular-registro.png', fullPage: true });
  await b.close();
  const resumen = `Resultado: ${ok} de ${ok + fallas} pruebas OK`;
  console.log('\n' + resumen);
  const titulo = `Prueba del frontend en Chromium (escritorio y Pixel 7) contra Docker (${new Date().toLocaleString('es-CL')})`;
  fs.writeFileSync(path.join(BACK, 'docs', 'evidencias', 'prueba_frontend.txt'), [titulo, '', ...lineas, '', resumen, ''].join('\n'));
  process.exit(fallas ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
