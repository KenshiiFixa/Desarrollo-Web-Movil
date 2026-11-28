<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Reportes</title>
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

<div class="inv-layout">
  <h1>Reporte de ventas</h1>
  <p class="auth-sub">Datos del servicio de analítica, que recibe cada pedido pagado (sin datos personales).</p>
  <p class="aviso mostrar" id="rep-aviso" role="status">Cargando el reporte…</p>
  <div id="rep-contenido" hidden>
    <div class="resumen-cifras">
      <div><span>Pedidos pagados</span><strong id="rep-pedidos"></strong></div>
      <div><span>Total vendido</span><strong id="rep-total"></strong></div>
      <div><span>Ticket promedio</span><strong id="rep-ticket"></strong></div>
    </div>
    <p class="nota-total" id="rep-hora"></p>
    <h2>Productos más vendidos</h2>
    <div class="inv-tabla-wrap">
      <table class="inv-tabla">
        <thead><tr><th>Producto</th><th>Cantidad</th><th>Total</th></tr></thead>
        <tbody id="rep-productos"></tbody>
      </table>
    </div>
    <h2>Ventas por día</h2>
    <div class="inv-tabla-wrap">
      <table class="inv-tabla">
        <thead><tr><th>Día</th><th>Pedidos</th><th>Total</th></tr></thead>
        <tbody id="rep-dias"></tbody>
      </table>
    </div>
    <button type="button" class="btn-chico" id="rep-actualizar">Actualizar</button>
  </div>
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