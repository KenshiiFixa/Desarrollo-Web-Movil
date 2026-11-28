<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Pedido</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <link href="index.css" rel="stylesheet">
</head>
<body>

<header class="topbar">
  <a class="logo" href="index.php">Aroma &amp; Café <span>Maipú</span></a>
  <div class="search">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" placeholder="Buscar espresso, latte, tartas…">
  </div>
  <div class="auth-actions">
    <a href="login.php" class="btn-login">Iniciar sesión</a>
    <a href="registro.php" class="btn-register">Registrarse</a>
  </div>
</header>

<nav class="mainnav">
  <ul>
    <li><a href="index.php">Inicio</a></li>
    <li><a href="catalogo.php">Carta</a></li>
    <li><a href="Locales.php">Locales</a></li>
    <li><a href="Contacto.php">Contacto</a></li>
    <li class="nav-right">
      <a href="carrito.php">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
        <span>Pedido</span>
        <span class="cart-count"></span>
      </a>
    </li>
  </ul>
</nav>

<div class="pedido-layout">
  <h1>Pedido <span id="ped-id"></span></h1>
  <p class="aviso mostrar" id="ped-aviso" role="status">Cargando el pedido…</p>

  <section id="ped-detalle" class="ped-bloque" hidden>
    <div class="ped-cabecera">
      <span class="chip" id="ped-estado"></span>
      <span id="ped-entrega"></span>
      <span id="ped-fecha"></span>
    </div>
    <div class="inv-tabla-wrap">
      <table class="inv-tabla ped-tabla">
        <thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Subtotal</th></tr></thead>
        <tbody id="ped-lineas"></tbody>
      </table>
    </div>
    <p class="ped-total">Total: <strong id="ped-total"></strong></p>
  </section>

  <section id="ped-pago" class="ped-bloque" hidden>
    <h2>Pago</h2>
    <p class="auth-sub">El monto lo calcula el servidor; el navegador no lo envía.</p>
    <button type="button" class="btn-primary" id="btn-iniciar-pago">Pagar</button>
    <div id="pasarela" class="pasarela" hidden>
      <span class="etiqueta-simulada">Pasarela de pago simulada · proveedor de prueba</span>
      <p>Monto a cobrar: <strong id="pas-monto"></strong></p>
      <div class="pasarela-botones">
        <button type="button" class="btn-primary" id="btn-aprobar">Pagar con tarjeta de prueba</button>
        <button type="button" class="btn-chico peligro" id="btn-rechazar">Simular pago rechazado</button>
      </div>
    </div>
  </section>

  <section id="ped-anular" class="ped-bloque" hidden>
    <h2>Anular pedido</h2>
    <form id="anular-form" class="auth-form" novalidate>
      <label>Motivo <input type="text" name="motivo" minlength="5" maxlength="200" placeholder="Me equivoqué de producto"></label>
      <button type="submit" class="btn-chico peligro">Anular pedido</button>
    </form>
  </section>

  <section id="ped-boleta" class="ped-bloque boleta" hidden>
    <h2>Boleta <span id="bol-folio"></span></h2>
    <p class="auth-sub" id="bol-fecha"></p>
    <div class="inv-tabla-wrap">
      <table class="inv-tabla ped-tabla">
        <thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Total</th></tr></thead>
        <tbody id="bol-detalle"></tbody>
      </table>
    </div>
    <div class="boleta-totales">
      <span>Neto</span><strong id="bol-neto"></strong>
      <span>IVA (19 %)</span><strong id="bol-iva"></strong>
      <span>Total</span><strong id="bol-total"></strong>
    </div>
  </section>

  <p class="auth-alt"><a href="mis-pedidos.php">Ver mis pedidos</a></p>
</div>

<footer>
  <div>
    <h3>Aroma &amp; Café</h3>
    <p class="desc">Café de especialidad y repostería casera desde 2015. Pide online, retira en el local o recibe en tu casa.</p>
  </div>
  <div>
    <h3>Contacto</h3>
    <ul>
      <li><a href="Contacto.php">contacto@aromaycafe.cl</a></li>
      <li><a href="Contacto.php">+56 9 1234 5678</a></li>
      <li><a href="Locales.php">Nuestros locales</a></li>
    </ul>
  </div>
  <div>
    <h3>Nosotros</h3>
    <ul>
      <li><a href="#">Nuestro tostado</a></li>
      <li><a href="#">Productores</a></li>
      <li><a href="#">Trabaja con nosotros</a></li>
    </ul>
  </div>
  <div class="foot-bottom">© 2026 Aroma &amp; Café. Todos los derechos reservados.</div>
</footer>

<script src="app.js"></script>
</body>
</html>