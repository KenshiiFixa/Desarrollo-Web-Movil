<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Locales</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <link href="Index.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
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
    <li><a href="catalogo.php">Carta</a></li>
    <li class="active"><a href="Locales.php">Locales</a></li>
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

<div class="locales-layout">
  <div>
    <h1 style="margin-bottom:22px;">Nuestros locales</h1>

    <div class="locale-card" data-lat="-33.4235" data-lng="-70.6120" data-nombre="Local Providencia Norte">
      <h4>Local Providencia Norte</h4>
      <div class="meta">
        Av. Nueva Providencia 2000, Providencia<br>
        +56 9 1234 5678<br>
        Lun a vie, 8:00 a 20:00 · Sáb y dom, 9:00 a 16:00
      </div>
    </div>

    <div class="locale-card" data-lat="-33.4422" data-lng="-70.6268" data-nombre="Local Barrio Italia">
      <h4>Local Barrio Italia</h4>
      <div class="meta">
        Av. Italia 1200, Providencia<br>
        +56 9 8765 4321<br>
        Lun a sáb, 9:00 a 21:00
      </div>
    </div>

    <div class="locale-card" data-lat="-33.3857" data-lng="-70.6158" data-nombre="Local Ciudad Empresarial">
      <h4>Local Ciudad Empresarial</h4>
      <div class="meta">
        Av. Santa Clara 400, Ciudad Empresarial, Huechuraba<br>
        +56 9 5555 1122<br>
        Lun a vie, 7:30 a 19:00 · Sáb, 10:00 a 14:00
      </div>
    </div>
  </div>

  <div id="map"></div>
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
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    var mapEl = document.getElementById('map');
    if (!mapEl || typeof L === 'undefined') return;

    // Mapa centrado entre Providencia y Huechuraba
    var map = L.map('map').setView([-33.4150, -70.6150], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);

    var cards = document.querySelectorAll('.locale-card');
    var markers = {};

    cards.forEach(function (card) {
      var lat = parseFloat(card.getAttribute('data-lat'));
      var lng = parseFloat(card.getAttribute('data-lng'));
      var nombre = card.getAttribute('data-nombre');
      var marker = L.marker([lat, lng]).addTo(map).bindPopup(nombre);
      markers[nombre] = marker;

      card.addEventListener('click', function () {
        cards.forEach(function (c) { c.classList.remove('is-active'); });
        card.classList.add('is-active');
        map.flyTo([lat, lng], 15, { duration: 0.6 });
        marker.openPopup();
      });

      marker.on('click', function () {
        cards.forEach(function (c) { c.classList.remove('is-active'); });
        card.classList.add('is-active');
      });
    });
  });
</script>
</body>
</html>