<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Carta</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <link href="Index.css" rel="stylesheet">
</head>
<body>

<header class="topbar">
  <a class="logo" href="Index.php">Aroma &amp; Café <span>Santiago</span></a>
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
    <li><a href="Index.php">Inicio</a></li>
    <li class="active"><a href="catalogo.php">Carta</a></li>
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

<div class="page-layout">
  <div class="page-title">
    <h1>Carta online</h1>
    <p>Todo lo que preparamos en el local, listo para retirar o despachar.</p>
  </div>

  <aside class="filters">
    <h3>Filtros</h3>
    <form id="filter-form">
      <fieldset class="filter-group">
        <legend>Categoría</legend>
        <label class="filter-option">
          <input type="checkbox" value="cafe"> Café caliente
        </label>
        <label class="filter-option">
          <input type="checkbox" value="frio"> Bebidas frías
        </label>
        <label class="filter-option">
          <input type="checkbox" value="reposteria"> Repostería
        </label>
      </fieldset>
      <button type="submit" class="btn-filter">Aplicar filtros</button>
      <a href="#" class="filter-reset">Limpiar filtros</a>
    </form>
  </aside>

  <section class="product-grid">

    <style>
      .product-card-lg img {
        width: 116px; 
        height: 116px; 
        object-fit: contain; /* Evita que la imagen se recorte */
        margin: 0 auto 14px; 
        display: block;
        filter: drop-shadow(0px 8px 10px rgba(62,39,35,0.15)); /* Sombra para dar volumen al producto flotante */
      }
    </style>

    <div class="product-card-lg" data-category="cafe">
      <img src="espresso.png" alt="Espresso Doble">
      <h4>Espresso Doble</h4>
      <div class="price-row"><span class="price-now">$2.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="espresso-doble" data-name="Espresso Doble" data-price="2500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="cafe">
      <img src="latte.png" alt="Latte Art">
      <h4>Latte Art</h4>
      <div class="price-row"><span class="price-now">$3.200</span></div>
      <button class="btn-add" data-add-to-cart data-id="latte-art" data-name="Latte Art" data-price="3200">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="cafe">
      <img src="cappuccino.png" alt="Cappuccino">
      <h4>Cappuccino</h4>
      <div class="price-row"><span class="price-now">$3.000</span></div>
      <button class="btn-add" data-add-to-cart data-id="cappuccino" data-name="Cappuccino" data-price="3000">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="frio">
      <img src="cold-brew.png" alt="Cold Brew">
      <h4>Cold Brew</h4>
      <div class="price-row"><span class="price-now">$3.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="cold-brew" data-name="Cold Brew" data-price="3500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="frio">
      <img src="frappe-mocha.png" alt="Frappé de Mocha">
      <h4>Frappé de Mocha</h4>
      <div class="price-row"><span class="price-now">$3.900</span></div>
      <button class="btn-add" data-add-to-cart data-id="frappe-mocha" data-name="Frappé de Mocha" data-price="3900">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <img src="croissant.png" alt="Croissant de Mantequilla">
      <h4>Croissant de Mantequilla</h4>
      <div class="price-row"><span class="price-now">$2.800</span></div>
      <button class="btn-add" data-add-to-cart data-id="croissant" data-name="Croissant de Mantequilla" data-price="2800">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <img src="tarta-frambuesa.png" alt="Tarta de Frambuesa">
      <h4>Tarta de Frambuesa</h4>
      <div class="price-row"><span class="price-now">$4.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="tarta-frambuesa" data-name="Tarta de Frambuesa" data-price="4500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <img src="cheesecake-maracuya.png" alt="Cheesecake de Maracuyá">
      <h4>Cheesecake de Maracuyá</h4>
      <div class="price-row"><span class="price-now">$4.800</span></div>
      <button class="btn-add" data-add-to-cart data-id="cheesecake-maracuya" data-name="Cheesecake de Maracuyá" data-price="4800">Agregar al pedido</button>
    </div>

    <p class="empty-state" id="empty-state">No hay productos que coincidan con los filtros seleccionados.</p>

  </section>
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

<script src="App.js"></script>
</body>
</html>