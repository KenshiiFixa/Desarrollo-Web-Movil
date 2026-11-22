<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aroma &amp; Café - Mi cuenta</title>
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

<div class="auth-layout">
  <h1>Mi cuenta</h1>
  <p class="auth-sub" id="cuenta-correo"></p>
  <p class="aviso" id="cuenta-aviso" role="status">Cargando tus datos…</p>
  <form id="cuenta-form" class="auth-form" novalidate hidden>
    <label>Nombre completo * <input type="text" name="nombre" minlength="2" maxlength="80" required></label>
    <div class="auth-grid">
      <label>RUN <input type="text" name="run" maxlength="14"></label>
      <label>Teléfono <input type="tel" name="telefono" maxlength="20"></label>
    </div>
    <label>Dirección <input type="text" name="direccion" maxlength="150"></label>
    <div class="auth-grid">
      <label>Comuna <input type="text" name="comuna" maxlength="60"></label>
      <label>Provincia <input type="text" name="provincia" maxlength="60"></label>
    </div>
    <div class="auth-grid">
      <label>Región <input type="text" name="region" maxlength="60"></label>
      <label>Fecha de nacimiento <input type="date" name="fecha_nacimiento"></label>
    </div>
    <label>Sexo
      <select name="sexo">
        <option value="">Prefiero no decirlo</option>
        <option value="femenino">Femenino</option>
        <option value="masculino">Masculino</option>
        <option value="otro">Otro</option>
      </select>
    </label>
    <button type="submit" class="btn-primary">Guardar cambios</button>
  </form>
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