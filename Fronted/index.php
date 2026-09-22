<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Inicio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <link href="Index.css" rel="stylesheet">
</head>
<body>

<header class="topbar">
  <a class="logo" href="Index.php">Aroma &amp; Café <span>Maipú</span></a>
  <div class="search">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" placeholder="Buscar espresso, latte, tartas…">
  </div>
  <div class="auth-actions">
    <a href="#" class="btn-login">Iniciar sesión</a>
    <a href="#" class="btn-register">Registrarse</a>
  </div>
</header>

<nav class="mainnav">
  <ul>
    <li class="active"><a href="Index.php">Inicio</a></li>
    <li><a href="catalogo.php">Carta</a></li>
    <li><a href="Locales.php">Locales</a></li>
    <li><a href="Contacto.php">Contacto</a></li>
    <li class="nav-right">
      <a href="Carrito.php">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
        <span>Pedido</span>
        <span class="cart-count"></span>
      </a>
    </li>
  </ul>
</nav>

<main>
  <section class="hero">
    <div class="hero-art">
      <!-- Imagen real de café insertada con enlace directo y borde estilo boceto -->
      <img src="cafe_index.png" alt="Café de especialidad y repostería" style="width: 100%; max-width: 580px; height: auto; display: block; margin: 0 auto;">
    </div>

    <div class="hero-copy">
      <div class="eyebrow-line">Tostado de la semana</div>
      <h1>El café se toma recién hecho, no recalentado.</h1>
      <p>Preparamos cada taza al momento en que pagas tu pedido online, con granos de especialidad tostados acá mismo en Maipú.</p>
      <div class="hero-actions">
        <a href="catalogo.php" class="btn-primary">Ver la carta completa</a>
        <a href="Locales.php" class="btn-ghost">Dónde estamos</a>
      </div>
    </div>
  </section>

 
  <aside class="featured">
    <h2>Los más pedidos</h2>
    <div class="product-list">

      <div class="product-card">
        <div class="product-thumb">
          <img src="espresso.png" alt="Espresso Doble" style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0px 4px 4px rgba(62,39,35,0.2));">
        </div>
        <div class="product-info">
          <div class="name">Espresso Doble</div>
          <div class="meta">Taza · 60 ml</div>
        </div>
        <div class="product-price">$2.500</div>
      </div>

      <div class="product-card">
        <div class="product-thumb">
          <img src="latte.png" alt="Latte Art" style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0px 4px 4px rgba(62,39,35,0.2));">
        </div>
        <div class="product-info">
          <div class="name">Latte Art</div>
          <div class="meta">Taza · 240 ml</div>
        </div>
        <div class="product-price">$3.200</div>
      </div>

      <div class="product-card">
        <div class="product-thumb">
          <img src="cold-brew.png" alt="Cold Brew" style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0px 4px 4px rgba(62,39,35,0.2));">
        </div>
        <div class="product-info">
          <div class="name">Cold Brew</div>
          <div class="meta">Vaso · 350 ml</div>
        </div>
        <div class="product-price">$3.500</div>
      </div>

    </div>
    <a href="catalogo.php" class="see-all">Ver toda la carta</a>
  </aside>

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

<script src="App.js"></script>
</body>
</html>