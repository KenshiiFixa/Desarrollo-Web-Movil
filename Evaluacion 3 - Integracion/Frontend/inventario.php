<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Inventario</title>
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
  <h1>Inventario</h1>
  <p class="auth-sub">Productos, precios, ofertas y stock. Solo para el dueño y el administrador.</p>
  <p class="aviso" id="inv-aviso" role="status">Cargando el inventario…</p>

  <div class="inv-tabla-wrap" id="inv-tabla-wrap" hidden>
    <table class="inv-tabla">
      <thead>
        <tr><th>Producto</th><th>Categoría</th><th>Precio</th><th>Oferta</th><th>Stock</th><th>Estado</th><th></th></tr>
      </thead>
      <tbody id="inv-filas"></tbody>
    </table>
  </div>

  <details class="inv-nuevo" id="inv-nuevo" hidden>
    <summary>Agregar producto</summary>
    <form id="inv-nuevo-form" class="auth-form" novalidate>
      <div class="auth-grid">
        <label>Código (id) * <input type="text" name="id" placeholder="mocaccino" pattern="[a-z0-9-]{2,40}" maxlength="40" required></label>
        <label>Nombre * <input type="text" name="nombre" minlength="2" maxlength="80" required></label>
      </div>
      <label>Descripción <input type="text" name="descripcion" maxlength="300"></label>
      <div class="auth-grid">
        <label>Categoría *
          <select name="categoria">
            <option value="cafe">Café caliente</option>
            <option value="frio">Bebidas frías</option>
            <option value="reposteria">Repostería</option>
          </select>
        </label>
        <label>Imagen (archivo) <input type="text" name="imagen" placeholder="latte.png" maxlength="80"></label>
      </div>
      <div class="auth-grid">
        <label>Precio * <input type="number" name="precio" min="1" max="1000000" required></label>
        <label>Stock * <input type="number" name="stock" min="0" max="100000" required></label>
      </div>
      <label>Precio de oferta (opcional) <input type="number" name="precio_oferta" min="1"></label>
      <button type="submit" class="btn-primary">Agregar producto</button>
    </form>
  </details>
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