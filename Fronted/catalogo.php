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

    <div class="product-card-lg" data-category="cafe">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M28 44 h56 v34 a28 28 0 0 1 -56 0 Z" fill="#FFFFFF" stroke="#3E2723" stroke-width="4"/><path d="M84 52 q20 -2 20 14 t-20 14" fill="none" stroke="#3E2723" stroke-width="6" stroke-linecap="round"/><ellipse cx="56" cy="44" rx="28" ry="8" fill="#4E342E"/><ellipse cx="56" cy="104" rx="40" ry="7" fill="#D7CCC8"/></svg>
      </div>
      <h4>Espresso Doble</h4>
      <div class="price-row"><span class="price-now">$2.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="espresso-doble" data-name="Espresso Doble" data-price="2500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="cafe">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M26 38 h60 v40 a30 30 0 0 1 -60 0 Z" fill="#FFFFFF" stroke="#3E2723" stroke-width="4"/><path d="M86 48 q20 -2 20 15 t-20 15" fill="none" stroke="#3E2723" stroke-width="6" stroke-linecap="round"/><ellipse cx="56" cy="38" rx="30" ry="9" fill="#C89F80"/><path d="M56 26 q10 12 0 24 q-10 -12 0 -24" fill="#FFF6F0"/><ellipse cx="56" cy="106" rx="42" ry="7" fill="#D7CCC8"/></svg>
      </div>
      <h4>Latte Art</h4>
      <div class="price-row"><span class="price-now">$3.200</span></div>
      <button class="btn-add" data-add-to-cart data-id="latte-art" data-name="Latte Art" data-price="3200">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="cafe">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M30 40 h54 v36 a27 27 0 0 1 -54 0 Z" fill="#FFFFFF" stroke="#3E2723" stroke-width="4"/><ellipse cx="57" cy="40" rx="27" ry="8" fill="#8D6E63"/><g fill="#FFFFFF"><circle cx="46" cy="38" r="5"/><circle cx="58" cy="35" r="6"/><circle cx="70" cy="39" r="4.5"/></g><path d="M84 50 q18 -2 18 13 t-18 13" fill="none" stroke="#3E2723" stroke-width="6" stroke-linecap="round"/></svg>
      </div>
      <h4>Cappuccino</h4>
      <div class="price-row"><span class="price-now">$3.000</span></div>
      <button class="btn-add" data-add-to-cart data-id="cappuccino" data-name="Cappuccino" data-price="3000">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="frio">
      <div class="art">
        <svg viewBox="0 0 120 120"><rect x="38" y="18" width="44" height="84" rx="8" fill="#F7F1EE" stroke="#3E2723" stroke-width="4"/><rect x="42" y="46" width="36" height="52" rx="6" fill="#5D4037"/><g fill="#D7CCC8" opacity="0.9"><rect x="48" y="52" width="12" height="12" rx="3"/><rect x="62" y="68" width="12" height="12" rx="3"/></g><rect x="56" y="6" width="8" height="18" rx="4" fill="#FF813E"/></svg>
      </div>
      <h4>Cold Brew</h4>
      <div class="price-row"><span class="price-now">$3.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="cold-brew" data-name="Cold Brew" data-price="3500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="frio">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M34 26 h52 l-8 70 a8 8 0 0 1 -8 7 h-20 a8 8 0 0 1 -8 -7 Z" fill="#F7F1EE" stroke="#3E2723" stroke-width="4"/><path d="M38 52 h44 l-6 44 h-32 Z" fill="#A1887F"/><ellipse cx="60" cy="26" rx="26" ry="7" fill="#FFF6F0" stroke="#3E2723" stroke-width="3"/><path d="M60 24 v-16" stroke="#FF813E" stroke-width="5" stroke-linecap="round"/></svg>
      </div>
      <h4>Frappé de Mocha</h4>
      <div class="price-row"><span class="price-now">$3.900</span></div>
      <button class="btn-add" data-add-to-cart data-id="frappe-mocha" data-name="Frappé de Mocha" data-price="3900">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M20 78 q16 -36 44 -30 q-8 14 -3 28 q16 -20 40 -7 q-16 8 -21 22 q-26 14 -52 0 q-12 -6 -8 -13 Z" fill="#E8A55C" stroke="#3E2723" stroke-width="4" stroke-linejoin="round"/><path d="M44 72 q12 14 10 36" fill="none" stroke="#C97F35" stroke-width="3"/><path d="M70 68 q8 18 4 38" fill="none" stroke="#C97F35" stroke-width="3"/></svg>
      </div>
      <h4>Croissant de Mantequilla</h4>
      <div class="price-row"><span class="price-now">$2.800</span></div>
      <button class="btn-add" data-add-to-cart data-id="croissant" data-name="Croissant de Mantequilla" data-price="2800">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M22 84 h76 v-26 h-76 Z" fill="#FFF3E0" stroke="#3E2723" stroke-width="4"/><path d="M22 58 q38 -18 76 0" fill="#F6C8C8" stroke="#3E2723" stroke-width="4"/><g fill="#C2185B"><circle cx="40" cy="52" r="6"/><circle cx="60" cy="47" r="6.5"/><circle cx="80" cy="53" r="6"/></g><path d="M22 84 h76 l-6 14 h-64 Z" fill="#D7A86E" stroke="#3E2723" stroke-width="4"/></svg>
      </div>
      <h4>Tarta de Frambuesa</h4>
      <div class="price-row"><span class="price-now">$4.500</span></div>
      <button class="btn-add" data-add-to-cart data-id="tarta-frambuesa" data-name="Tarta de Frambuesa" data-price="4500">Agregar al pedido</button>
    </div>

    <div class="product-card-lg" data-category="reposteria">
      <div class="art">
        <svg viewBox="0 0 120 120"><path d="M30 92 L60 26 L90 92 Z" fill="#FFF8E1" stroke="#3E2723" stroke-width="4" stroke-linejoin="round"/><path d="M40 70 L60 26 L80 70 Z" fill="#FFD166"/><path d="M30 92 h60 l-4 10 h-52 Z" fill="#C89F63" stroke="#3E2723" stroke-width="3"/><g fill="#8D6E63"><circle cx="54" cy="62" r="2.5"/><circle cx="66" cy="58" r="2.5"/></g></svg>
      </div>
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