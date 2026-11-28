(function () {
  var CART_KEY = 'aroma_cart';
  // Direccion del API Gateway (unica entrada al backend)
  var API_URL = 'https://127.0.0.1:8000/api/v1';
  var SESION_KEY = 'aroma_sesion';
  var CLAVE_KEY = 'aroma_clave_pedido';

  // ---------- Sesion ----------
  // El token se guarda en sessionStorage, que se borra al cerrar el navegador.
  function leerSesion() {
    try {
      var s = JSON.parse(sessionStorage.getItem(SESION_KEY));
      return s && s.token ? s : null;
    } catch (e) {
      return null;
    }
  }

  function guardarSesion(s) {
    try { sessionStorage.setItem(SESION_KEY, JSON.stringify(s)); } catch (e) { /* sin almacenamiento */ }
  }

  function borrarSesion() {
    try { sessionStorage.removeItem(SESION_KEY); } catch (e) { /* sin almacenamiento */ }
  }

  function paginaActual() {
    return location.pathname.split('/').pop() || 'index.php';
  }

  function irALogin(motivo) {
    location.href = 'login.php?' + (motivo ? motivo + '=1&' : '') + 'volver=' + encodeURIComponent(paginaActual());
  }

  // Llama al API Gateway. Con conSesion agrega el token y, si la respuesta es 401, cierra la sesion.
  function llamarApi(metodo, ruta, cuerpo, conSesion) {
    var opciones = { method: metodo, headers: { 'Accept': 'application/json' } };
    if (cuerpo !== undefined) {
      opciones.headers['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(cuerpo);
    }
    if (conSesion) {
      var sesion = leerSesion();
      if (!sesion) {
        irALogin();
        return new Promise(function () {});
      }
      opciones.headers['Authorization'] = 'Bearer ' + sesion.token;
    }
    return fetch(API_URL + ruta, opciones).then(function (r) {
      return r.text().then(function (texto) {
        var datos = null;
        try { datos = texto ? JSON.parse(texto) : null; } catch (e) { datos = null; }
        if (conSesion && r.status === 401) {
          borrarSesion();
          irALogin('expirada');
          return new Promise(function () {});
        }
        return { status: r.status, datos: datos };
      });
    });
  }

  // Mensajes del backend (vienen sin tildes) en un texto para el usuario
  var MENSAJES = {
    'Credenciales incorrectas': 'Correo o contraseña incorrectos.',
    'Codigo invalido o vencido': 'El código no es válido o ya venció.',
    'No fue posible registrar con esos datos': 'No fue posible registrar con esos datos. Si ya tienes cuenta, inicia sesión.',
    'Correo invalido': 'El correo no es válido.',
    'RUN invalido': 'El RUN no es válido (revisa el dígito verificador).',
    'Telefono invalido': 'El teléfono no es válido.',
    'Fecha de nacimiento invalida': 'La fecha de nacimiento no es válida.',
    'Permiso insuficiente': 'No tienes permiso para esta sección.',
    'Ya existe un producto con ese id': 'Ya existe un producto con ese código.',
    'Producto no encontrado': 'El producto ya no existe.',
    'Pedido no encontrado': 'No encontramos ese pedido.',
    'Para delivery se requiere direccion y comuna': 'Para el despacho a domicilio escribe la dirección y la comuna.',
    'La direccion esta fuera del radio de despacho (3 km)': 'Esa dirección está fuera del radio de despacho (3 km del local). Puedes elegir retiro en el local.',
    'El pedido ya no se puede anular': 'Este pedido ya no se puede anular.',
    'El pago ya fue procesado': 'Este pago ya fue procesado.',
    'El pedido no esta pendiente de pago': 'Este pedido ya no está pendiente de pago.',
    'El pedido aun no esta pagado': 'El pedido aún no está pagado.',
    'Error en el servicio interno': 'Un servicio del sistema no está disponible. Intenta de nuevo en unos segundos.',
    'Backend no disponible': 'Un servicio del sistema no está disponible. Intenta de nuevo en unos segundos.',
    'Authentication Service no disponible': 'El servicio de sesiones no está disponible. Intenta de nuevo en unos segundos.',
    'No puedes cambiar tu propio perfil': 'No puedes cambiar tu propio perfil.',
    'Ya existe un usuario con ese correo': 'Ya existe un usuario con ese correo.'
  };

  function mensajeError(res) {
    if (res.status === 429) return 'Demasiados intentos. Espera un minuto y vuelve a intentar.';
    var detalle = res.datos && res.datos.detail;
    if (typeof detalle === 'string' && detalle.indexOf('Stock insuficiente') === 0) {
      return 'No hay stock suficiente de uno de los productos. Revisa las cantidades.';
    }
    if (typeof detalle === 'string') return MENSAJES[detalle] || detalle;
    if (res.status === 422) return 'Revisa los datos del formulario.';
    return 'Ocurrió un error (' + res.status + '). Intenta de nuevo.';
  }

  var ERROR_CONEXION = 'No pudimos conectar con el servidor. Revisa que el backend esté encendido.';

  function mostrarAviso(el, texto, tipo, enlace) {
    if (!el) return;
    el.textContent = texto;
    el.className = 'aviso mostrar' + (tipo ? ' ' + tipo : '');
    if (enlace) {
      el.appendChild(document.createTextNode(' '));
      var a = document.createElement('a');
      a.href = enlace.href;
      a.textContent = enlace.texto;
      el.appendChild(a);
    }
  }

  function ocultarAviso(el) {
    if (el) el.className = 'aviso';
  }

  // Error al cargar datos: mensaje con un boton para reintentar sin recargar la pagina
  function errorDeCarga(el, texto, reintentar) {
    mostrarAviso(el, texto, 'error');
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn-chico btn-reintentar';
    b.textContent = 'Reintentar';
    b.addEventListener('click', reintentar);
    el.appendChild(document.createTextNode(' '));
    el.appendChild(b);
  }

  // Lee un formulario: los campos vacios quedan en null (asi el backend los toma como "no informado")
  function leerFormulario(form) {
    var datos = {};
    Array.prototype.forEach.call(form.elements, function (campo) {
      if (!campo.name) return;
      var valor = campo.value.trim();
      datos[campo.name] = valor === '' ? null : valor;
    });
    return datos;
  }

  function bloquear(form, si) {
    var boton = form.querySelector('button[type="submit"]');
    if (boton) boton.disabled = si;
  }

  // Enlaces del encabezado segun el rol de la sesion
  var ENLACES_ROL = {
    cliente: [['mis-pedidos.php', 'Mis pedidos']],
    despacho: [['despacho.php', 'Despacho']],
    cajero: [['ventas.php', 'Ventas']],
    dueno: [['inventario.php', 'Inventario'], ['reportes.php', 'Reportes']],
    admin: [['admin.php', 'Administración']]
  };

  // Encabezado: con sesion muestra "Hola, nombre", los enlaces de su rol y Cerrar sesion
  function pintarEncabezado() {
    var cont = document.querySelector('.auth-actions');
    var sesion = leerSesion();
    if (!cont || !sesion) return;
    if (Date.now() > sesion.expira) {
      borrarSesion();
      showToast('Tu sesión expiró. Inicia sesión de nuevo.');
      return;
    }
    cont.textContent = '';
    var hola = document.createElement('a');
    hola.href = 'cuenta.php';
    hola.className = 'saludo';
    hola.textContent = 'Hola, ' + ((sesion.nombre || sesion.email).split(' ')[0]);
    cont.appendChild(hola);
    (ENLACES_ROL[sesion.rol] || []).forEach(function (enlace) {
      var a = document.createElement('a');
      a.href = enlace[0];
      a.className = 'btn-login';
      a.textContent = enlace[1];
      cont.appendChild(a);
    });
    var salir = document.createElement('button');
    salir.type = 'button';
    salir.className = 'btn-register';
    salir.textContent = 'Cerrar sesión';
    salir.addEventListener('click', cerrarSesion);
    cont.appendChild(salir);
  }

  function cerrarSesion() {
    // Se avisa al backend para que borre la sesion (el token deja de servir aunque alguien lo haya copiado)
    var sesion = leerSesion();
    var fin = function () {
      borrarSesion();
      location.href = 'login.php?salio=1';
    };
    if (!sesion) return fin();
    fetch(API_URL + '/auth/logout', { method: 'POST', headers: { 'Authorization': 'Bearer ' + sesion.token } })
      .then(fin, fin);
  }

  function getCart() {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch (e) {
      return [];
    }
  }

  function saveCart(cart) {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
      sessionStorage.removeItem(CLAVE_KEY);   // carrito distinto = pedido distinto
    } catch (e) { /* sin almacenamiento */ }
    updateCartBadge();
  }

  function updateCartBadge() {
    var cart = getCart();
    var count = cart.reduce(function (sum, item) { return sum + item.qty; }, 0);
    document.querySelectorAll('.cart-count').forEach(function (el) {
      el.textContent = count > 0 ? count : '';
    });
  }

  function showToast(msg) {
    var toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    requestAnimationFrame(function () { toast.classList.add('show'); });
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.classList.remove('show'); }, 2200);
  }

  function addToCart(item) {
    var cart = getCart();
    var existing = cart.filter(function (i) { return i.id === item.id; })[0];
    if (existing) {
      existing.qty += 1;
    } else {
      item.qty = 1;
      cart.push(item);
    }
    saveCart(cart);
    showToast(item.name + ' se agregó a tu pedido');
    renderCart();
  }

  function removeFromCart(id) {
    var cart = getCart().filter(function (i) { return i.id !== id; });
    saveCart(cart);
    renderCart();
  }

  function changeQty(id, delta) {
    var cart = getCart();
    var item = cart.filter(function (i) { return i.id === id; })[0];
    if (!item) return;
    item.qty += delta;
    if (item.qty <= 0) {
      removeFromCart(id);
      return;
    }
    saveCart(cart);
    renderCart();
  }

  function money(n) {
    return '$' + n.toLocaleString('es-CL');
  }

  function renderCart() {
    var list = document.getElementById('cart-list');
    if (!list) return;
    var cart = getCart();
    var emptyMsg = document.getElementById('cart-empty');

    if (cart.length === 0) {
      list.textContent = '';
      if (emptyMsg) emptyMsg.style.display = 'block';
      updateSummary(0);
      return;
    }
    if (emptyMsg) emptyMsg.style.display = 'none';

    // Las filas se arman con textContent: el nombre del producto viene de la API
    list.textContent = '';
    cart.forEach(function (item) {
      var fila = document.createElement('div');
      fila.className = 'cart-item';
      var art = document.createElement('div');
      art.className = 'art';
      if (item.imagen) {
        var img = document.createElement('img');
        img.src = item.imagen;
        img.alt = '';
        art.appendChild(img);
      }
      var info = document.createElement('div');
      info.className = 'info';
      var h4 = document.createElement('h4');
      h4.textContent = item.name;
      var qty = document.createElement('div');
      qty.className = 'qty-control';
      var menos = document.createElement('button');
      menos.type = 'button';
      menos.setAttribute('aria-label', 'Restar');
      menos.textContent = '\u2212';
      menos.addEventListener('click', function () { changeQty(item.id, -1); });
      var cantidad = document.createElement('span');
      cantidad.textContent = item.qty;
      var mas = document.createElement('button');
      mas.type = 'button';
      mas.setAttribute('aria-label', 'Sumar');
      mas.textContent = '+';
      mas.addEventListener('click', function () { changeQty(item.id, 1); });
      qty.appendChild(menos);
      qty.appendChild(cantidad);
      qty.appendChild(mas);
      var quitar = document.createElement('a');
      quitar.href = '#';
      quitar.className = 'remove-item';
      quitar.textContent = 'Quitar';
      quitar.addEventListener('click', function (e) {
        e.preventDefault();
        removeFromCart(item.id);
      });
      info.appendChild(h4);
      info.appendChild(qty);
      info.appendChild(quitar);
      var precio = document.createElement('div');
      precio.className = 'line-price';
      precio.textContent = money(item.price * item.qty);
      fila.appendChild(art);
      fila.appendChild(info);
      fila.appendChild(precio);
      list.appendChild(fila);
    });

    var total = cart.reduce(function (sum, i) { return sum + i.price * i.qty; }, 0);
    updateSummary(total);
  }

  function updateSummary(total) {
    var totalEl = document.getElementById('cart-total');
    var envio = 0;   // el despacho es gratis

    var subtotalEl = document.getElementById('cart-subtotal');
    if (subtotalEl) subtotalEl.textContent = money(total);

    var envioEl = document.getElementById('cart-envio');
    if (envioEl) envioEl.textContent = total === 0 ? '-' : (envio === 0 ? 'Gratis' : money(envio));

    if (totalEl) totalEl.textContent = money(total + envio);

    var payBtn = document.getElementById('btn-pay');
    if (payBtn) payBtn.disabled = total === 0;
  }

  function setupAddButtons(root) {
    (root || document).querySelectorAll('[data-add-to-cart]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        addToCart({
          id: btn.getAttribute('data-id'),
          name: btn.getAttribute('data-name'),
          price: parseInt(btn.getAttribute('data-price'), 10),
          imagen: btn.getAttribute('data-imagen') || ''
        });
      });
    });
  }

  // ---------- Carta desde el API Gateway (GET /api/v1/products) ----------
  // Las tarjetas se arman con textContent para que un texto de la API nunca se ejecute como HTML.
  function crearTarjeta(p) {
    var card = document.createElement('div');
    card.className = 'product-card-lg';
    card.setAttribute('data-category', p.categoria);

    var img = document.createElement('img');
    img.src = p.imagen;
    img.alt = p.nombre;
    card.appendChild(img);

    var h4 = document.createElement('h4');
    h4.textContent = p.nombre;
    card.appendChild(h4);

    var precio = p.precio_oferta || p.precio;   // si hay oferta, se muestra el precio de oferta
    var row = document.createElement('div');
    row.className = 'price-row';
    var now = document.createElement('span');
    now.className = 'price-now';
    now.textContent = money(precio);
    row.appendChild(now);
    if (p.precio_oferta) {
      var old = document.createElement('span');
      old.className = 'price-old';
      old.textContent = money(p.precio);
      row.appendChild(old);
    }
    card.appendChild(row);

    var btn = document.createElement('button');
    btn.className = 'btn-add';
    btn.setAttribute('data-add-to-cart', '');
    btn.setAttribute('data-id', p.id);
    btn.setAttribute('data-name', p.nombre);
    btn.setAttribute('data-price', precio);
    btn.setAttribute('data-imagen', p.imagen || '');
    btn.textContent = p.disponible ? 'Agregar al pedido' : 'Agotado';
    btn.disabled = !p.disponible;
    card.appendChild(btn);
    return card;
  }

  function mostrarEstado(estado, mensaje) {
    estado.textContent = mensaje;
    estado.style.display = 'block';
  }

  function cargarCatalogo() {
    var estado = document.getElementById('catalog-status');
    if (!estado) return;   // solo la pagina de la carta tiene este elemento
    var grid = estado.parentNode;
    grid.querySelectorAll('.product-card-lg').forEach(function (c) { c.remove(); });
    mostrarEstado(estado, 'Cargando la carta…');

    fetch(API_URL + '/products', { headers: { 'Accept': 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error('El servidor respondió ' + r.status);
        return r.json();
      })
      .then(function (productos) {
        if (productos.length === 0) {
          mostrarEstado(estado, 'Por ahora no hay productos disponibles.');
          return;
        }
        estado.style.display = 'none';
        productos.forEach(function (p) { grid.insertBefore(crearTarjeta(p), estado); });
        setupAddButtons(grid);
      })
      .catch(function (error) {
        // Sin conexion con el backend se muestra el error, sin inventar productos.
        console.error('No se pudo cargar la carta:', error);
        mostrarEstado(estado, 'No pudimos cargar la carta. Revisa que el backend esté encendido. ');
        var reintentar = document.createElement('button');
        reintentar.className = 'btn-filter';
        reintentar.textContent = 'Reintentar';
        reintentar.addEventListener('click', cargarCatalogo);
        estado.appendChild(reintentar);
      });
  }

  function setupFilters() {
    var form = document.getElementById('filter-form');
    if (!form) return;
    var emptyState = document.getElementById('empty-state');

    function apply() {
      var active = Array.from(form.querySelectorAll('input[type="checkbox"]:checked')).map(function (c) { return c.value; });
      var visibleCount = 0;
      document.querySelectorAll('.product-card-lg').forEach(function (card) {
        var cat = card.getAttribute('data-category');
        var visible = active.length === 0 || active.indexOf(cat) !== -1;
        card.classList.toggle('is-hidden', !visible);
        if (visible) visibleCount++;
      });
      if (emptyState) emptyState.classList.toggle('show', visibleCount === 0);
    }

    form.addEventListener('submit', function (e) { e.preventDefault(); apply(); });
    form.querySelectorAll('input[type="checkbox"]').forEach(function (c) {
      c.addEventListener('change', apply);
    });
    var resetBtn = form.querySelector('.filter-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', function (e) {
        e.preventDefault();
        form.querySelectorAll('input[type="checkbox"]').forEach(function (c) { c.checked = false; });
        apply();
      });
    }
  }

  function setupSearch() {
    var input = document.querySelector('.search input');
    if (!input) return;
    input.addEventListener('input', function () {
      var texto = input.value.toLowerCase().trim();
      var cards = document.querySelectorAll('.product-card-lg');
      if (cards.length === 0) return;
      cards.forEach(function (card) {
        var nombre = card.querySelector('h4').textContent.toLowerCase();
        card.classList.toggle('is-hidden', texto !== '' && nombre.indexOf(texto) === -1);
      });
    });
  }

  // ---------- Contacto (POST /api/v1/contact, publico) ----------
  function setupContactForm() {
    var form = document.getElementById('contact-form');
    if (!form) return;
    var note = document.getElementById('form-note');
    function nota(texto) {
      if (!note) return;
      note.textContent = texto;
      note.classList.add('show');
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var datos = leerFormulario(form);
      bloquear(form, true);
      llamarApi('POST', '/contact', datos, false)
        .then(function (res) {
          if (res.status === 201) {
            form.reset();
            nota('Gracias, tu mensaje quedó registrado. Te responderemos pronto.');
          } else {
            nota(mensajeError(res));
          }
        })
        .catch(function () { nota(ERROR_CONEXION); })
        .then(function () { bloquear(form, false); });
    });
  }

  // ---------- Iniciar sesion (POST /api/v1/auth/login y GET /api/v1/clients/me) ----------
  function setupLogin() {
    var form = document.getElementById('login-form');
    if (!form) return;
    var aviso = document.getElementById('login-aviso');
    var params = new URLSearchParams(location.search);
    if (params.get('expirada')) mostrarAviso(aviso, 'Tu sesión expiró o ya no es válida. Inicia sesión de nuevo.', 'error');
    if (params.get('salio')) mostrarAviso(aviso, 'Cerraste sesión.', 'ok');
    if (params.get('email')) form.elements.email.value = params.get('email');
    // Solo se vuelve a una pagina de este sitio (evita redirigir a otro dominio)
    var volver = params.get('volver');
    if (!/^[A-Za-z]+\.php$/.test(volver || '') || volver === 'login.php') volver = null;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = form.elements.email.value.trim().toLowerCase();
      var password = form.elements.password.value;
      if (!email || !password) {
        mostrarAviso(aviso, 'Escribe tu correo y tu contraseña.', 'error');
        return;
      }
      bloquear(form, true);
      llamarApi('POST', '/auth/login', { email: email, password: password }, false)
        .then(function (res) {
          if (res.status === 200) {
            var sesion = { token: res.datos.access_token, rol: res.datos.rol, email: email, nombre: '',
                           expira: Date.now() + res.datos.expires_in * 1000 };
            guardarSesion(sesion);
            // Con el token se pide el perfil (servicio clients) para saludar por el nombre
            return llamarApi('GET', '/clients/me', undefined, true).then(function (perfil) {
              if (perfil.status === 200) {
                sesion.nombre = perfil.datos.nombre;
                guardarSesion(sesion);
              }
              var inicio = { despacho: 'despacho.php', cajero: 'ventas.php', dueno: 'inventario.php', admin: 'admin.php' }[sesion.rol] || 'catalogo.php';
              location.href = volver || inicio;
            });
          }
          if (res.status === 403) {
            mostrarAviso(aviso, 'Debes verificar tu correo antes de iniciar sesión.', 'error',
                         { href: 'registro.php?verificar=' + encodeURIComponent(email), texto: 'Verificar ahora' });
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
          form.elements.password.value = '';
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(form, false); });
    });
  }

  // ---------- Registro (POST /api/v1/auth/register) y verificacion del correo (POST /api/v1/auth/verify-email) ----------
  function setupRegistro() {
    var form = document.getElementById('registro-form');
    var formCodigo = document.getElementById('verificar-form');
    if (!form || !formCodigo) return;
    var aviso = document.getElementById('registro-aviso');

    function pasoCodigo(email) {
      form.hidden = true;
      formCodigo.hidden = false;
      formCodigo.elements.email.value = email;
      formCodigo.elements.codigo.focus();
    }

    var verificar = new URLSearchParams(location.search).get('verificar');
    if (verificar) pasoCodigo(verificar);

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var datos = leerFormulario(form);
      if (!datos.nombre || !datos.email || !form.elements.password.value) {
        mostrarAviso(aviso, 'Completa nombre, correo y contraseña.', 'error');
        return;
      }
      if (form.elements.password.value.length < 8) {
        mostrarAviso(aviso, 'La contraseña debe tener al menos 8 caracteres.', 'error');
        return;
      }
      if (form.elements.password.value !== form.elements.password2.value) {
        mostrarAviso(aviso, 'Las contraseñas no coinciden.', 'error');
        return;
      }
      datos.password = form.elements.password.value;   // la contrasena no se recorta
      delete datos.password2;
      datos.email = datos.email.toLowerCase();
      bloquear(form, true);
      llamarApi('POST', '/auth/register', datos, false)
        .then(function (res) {
          if (res.status === 201) {
            mostrarAviso(aviso, 'Cuenta creada. Te enviamos un código a ' + datos.email + ' para activarla.', 'ok');
            pasoCodigo(datos.email);
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(form, false); });
    });

    formCodigo.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = formCodigo.elements.email.value.trim().toLowerCase();
      var codigo = formCodigo.elements.codigo.value.trim();
      if (!/^[0-9]{6}$/.test(codigo)) {
        mostrarAviso(aviso, 'El código tiene 6 dígitos.', 'error');
        return;
      }
      bloquear(formCodigo, true);
      llamarApi('POST', '/auth/verify-email', { email: email, codigo: codigo }, false)
        .then(function (res) {
          if (res.status === 200) {
            formCodigo.hidden = true;
            mostrarAviso(aviso, 'Tu correo quedó verificado.', 'ok',
                         { href: 'login.php?email=' + encodeURIComponent(email), texto: 'Iniciar sesión' });
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(formCodigo, false); });
    });
  }

  // ---------- Mi cuenta (GET y PUT /api/v1/clients/me) ----------
  function setupCuenta() {
    var form = document.getElementById('cuenta-form');
    if (!form) return;
    var aviso = document.getElementById('cuenta-aviso');
    var sesion = leerSesion();
    if (!sesion) { irALogin(); return; }
    document.getElementById('cuenta-correo').textContent = sesion.email;

    function rellenar(perfil) {
      ['nombre', 'run', 'telefono', 'direccion', 'comuna', 'provincia', 'region', 'fecha_nacimiento', 'sexo']
        .forEach(function (c) { form.elements[c].value = perfil[c] || ''; });
    }

    function cargarFicha() {
      mostrarAviso(aviso, 'Cargando tus datos…');
      llamarApi('GET', '/clients/me', undefined, true)
        .then(function (res) {
          if (res.status === 200) {
            rellenar(res.datos);
            ocultarAviso(aviso);
            form.hidden = false;
          } else {
            errorDeCarga(aviso, mensajeError(res), cargarFicha);
          }
        })
        .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, cargarFicha); });
    }
    cargarFicha();

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      bloquear(form, true);
      llamarApi('PUT', '/clients/me', leerFormulario(form), true)
        .then(function (res) {
          if (res.status === 200) {
            rellenar(res.datos);
            var s = leerSesion();
            if (s) { s.nombre = res.datos.nombre; guardarSesion(s); }
            mostrarAviso(aviso, 'Tus datos quedaron guardados.', 'ok');
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(form, false); });
    });
  }

  // ---------- Inventario: dueno y admin (GET, POST, PUT y DELETE /api/v1/admin/products) ----------
  var CATEGORIAS = { cafe: 'Café caliente', frio: 'Bebidas frías', reposteria: 'Repostería' };

  function setupInventario() {
    var filas = document.getElementById('inv-filas');
    if (!filas) return;
    var aviso = document.getElementById('inv-aviso');
    var tabla = document.getElementById('inv-tabla-wrap');
    var nuevo = document.getElementById('inv-nuevo');
    var formNuevo = document.getElementById('inv-nuevo-form');
    if (!leerSesion()) { irALogin(); return; }

    function numero(valor) {
      return valor === '' || valor === null ? null : parseInt(valor, 10);
    }

    function celda(fila, contenido) {
      var td = document.createElement('td');
      if (typeof contenido === 'string') td.textContent = contenido;
      else if (contenido) td.appendChild(contenido);
      fila.appendChild(td);
      return td;
    }

    function entrada(valor, min) {
      var input = document.createElement('input');
      input.type = 'number';
      input.min = min;
      input.value = valor === null || valor === undefined ? '' : valor;
      return input;
    }

    function boton(texto, clase, accion) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn-chico' + (clase ? ' ' + clase : '');
      b.textContent = texto;
      b.addEventListener('click', accion);
      return b;
    }

    function fila(p) {
      var tr = document.createElement('tr');
      if (!p.activo) tr.className = 'inactivo';
      celda(tr, p.nombre);
      celda(tr, CATEGORIAS[p.categoria] || p.categoria);
      var precio = entrada(p.precio, 1);
      var oferta = entrada(p.precio_oferta, 1);
      var stock = entrada(p.stock, 0);
      precio.setAttribute('aria-label', 'Precio de ' + p.nombre);
      oferta.setAttribute('aria-label', 'Oferta de ' + p.nombre);
      stock.setAttribute('aria-label', 'Stock de ' + p.nombre);
      celda(tr, precio);
      celda(tr, oferta);
      celda(tr, stock);
      celda(tr, p.activo ? 'Activo' : 'De baja');
      var acciones = celda(tr, null);
      var caja = document.createElement('div');
      caja.className = 'acciones';
      caja.appendChild(boton(p.activo ? 'Guardar' : 'Reactivar', '', function () {
        var cuerpo = { nombre: p.nombre, descripcion: p.descripcion || '', categoria: p.categoria,
                       imagen: p.imagen || '', precio: numero(precio.value), stock: numero(stock.value),
                       precio_oferta: numero(oferta.value) };
        llamarApi('PUT', '/admin/products/' + encodeURIComponent(p.id), cuerpo, true)
          .then(function (res) {
            if (res.status === 200) {
              mostrarAviso(aviso, 'Se guardó "' + p.nombre + '".', 'ok');
              cargar();
            } else {
              mostrarAviso(aviso, mensajeError(res), 'error');
            }
          })
          .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
      }));
      if (p.activo) {
        caja.appendChild(boton('Dar de baja', 'peligro', function () {
          if (!confirm('¿Dar de baja "' + p.nombre + '"? Deja de aparecer en la carta.')) return;
          llamarApi('DELETE', '/admin/products/' + encodeURIComponent(p.id), undefined, true)
            .then(function (res) {
              if (res.status === 204) {
                mostrarAviso(aviso, '"' + p.nombre + '" quedó dado de baja.', 'ok');
                cargar();
              } else {
                mostrarAviso(aviso, mensajeError(res), 'error');
              }
            })
            .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
        }));
      }
      acciones.appendChild(caja);
      return tr;
    }

    function cargar() {
      llamarApi('GET', '/admin/products', undefined, true)
        .then(function (res) {
          if (res.status === 403) {
            tabla.hidden = true;
            nuevo.hidden = true;
            mostrarAviso(aviso, 'No tienes permiso para ver el inventario. Esta sección es solo para el dueño y el administrador.', 'error');
            return;
          }
          if (res.status !== 200) {
            errorDeCarga(aviso, mensajeError(res), cargar);
            return;
          }
          if (aviso.textContent === 'Cargando el inventario…' || aviso.querySelector('.btn-reintentar')) ocultarAviso(aviso);
          filas.textContent = '';
          res.datos.forEach(function (p) { filas.appendChild(fila(p)); });
          tabla.hidden = false;
          nuevo.hidden = false;
        })
        .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, cargar); });
    }

    formNuevo.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = leerFormulario(formNuevo);
      if (!d.id || !d.nombre || !d.precio || d.stock === null) {
        mostrarAviso(aviso, 'Completa código, nombre, precio y stock.', 'error');
        return;
      }
      var cuerpo = { id: d.id.toLowerCase(), nombre: d.nombre, descripcion: d.descripcion || '', categoria: d.categoria,
                     imagen: d.imagen || '', precio: numero(d.precio), stock: numero(d.stock),
                     precio_oferta: numero(d.precio_oferta) };
      bloquear(formNuevo, true);
      llamarApi('POST', '/admin/products', cuerpo, true)
        .then(function (res) {
          if (res.status === 201) {
            formNuevo.reset();
            mostrarAviso(aviso, 'Se agregó "' + cuerpo.nombre + '".', 'ok');
            cargar();
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(formNuevo, false); });
    });

    cargar();
  }

  // ---------- Confirmar pedido desde el carrito (POST /api/v1/orders) ----------
  function claveDePedido() {
    // Clave de idempotencia: si se reintenta el mismo carrito, orders devuelve el mismo pedido
    try {
      var clave = sessionStorage.getItem(CLAVE_KEY);
      if (!clave) {
        clave = 'PED-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
        sessionStorage.setItem(CLAVE_KEY, clave);
      }
      return clave;
    } catch (e) {
      return null;
    }
  }

  function setupPayButton() {
    var btn = document.getElementById('btn-pay');
    var form = document.getElementById('entrega-form');
    if (!btn || !form) return;
    var aviso = document.getElementById('pedido-aviso');
    var direccion = document.getElementById('entrega-direccion');

    form.addEventListener('change', function () {
      direccion.hidden = form.elements.tipo_entrega.value !== 'delivery';
    });

    btn.addEventListener('click', function () {
      var sesion = leerSesion();
      if (!sesion) {
        irALogin();
        return;
      }
      if (sesion.rol !== 'cliente') {
        mostrarAviso(aviso, 'Solo una cuenta de cliente puede hacer pedidos.', 'error');
        return;
      }
      var cuerpo = {
        items: getCart().map(function (i) { return { product_id: i.id, cantidad: i.qty }; }),
        tipo_entrega: form.elements.tipo_entrega.value,
        clave: claveDePedido()
      };
      if (cuerpo.tipo_entrega === 'delivery') {
        cuerpo.direccion = form.elements.direccion.value.trim() || null;
        cuerpo.comuna = form.elements.comuna.value.trim() || null;
        if (!cuerpo.direccion || !cuerpo.comuna) {
          mostrarAviso(aviso, 'Para el despacho a domicilio escribe la dirección y la comuna.', 'error');
          return;
        }
      }
      btn.disabled = true;
      mostrarAviso(aviso, 'Creando tu pedido…');
      llamarApi('POST', '/orders', cuerpo, true)
        .then(function (res) {
          if (res.status === 201 || res.status === 200) {
            try {
              localStorage.removeItem(CART_KEY);
              sessionStorage.removeItem(CLAVE_KEY);
            } catch (e) { /* sin almacenamiento */ }
            location.href = 'pedido.php?id=' + encodeURIComponent(res.datos.id);
            return;
          }
          mostrarAviso(aviso, mensajeError(res), 'error');
          btn.disabled = false;
        })
        .catch(function () {
          mostrarAviso(aviso, ERROR_CONEXION, 'error');
          btn.disabled = false;
        });
    });
  }

  // ---------- Detalle de un pedido, pago y boleta ----------
  var ESTADOS = {
    PENDIENTE_PAGO: 'Pendiente de pago', PAGADO: 'Pagado', EN_PREPARACION: 'En preparación', LISTO: 'Listo',
    EN_CAMINO: 'En camino', ENTREGADO: 'Entregado', ANULADO: 'Anulado'
  };
  var ENTREGAS = { retiro: 'Retiro en el local', delivery: 'Despacho a domicilio' };

  function fecha(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' });
  }

  function chipEstado(el, estado) {
    el.textContent = ESTADOS[estado] || estado;
    el.className = 'chip chip-' + String(estado).toLowerCase();
  }

  function filaTabla(celdas) {
    var tr = document.createElement('tr');
    celdas.forEach(function (texto) {
      var td = document.createElement('td');
      td.textContent = texto;
      tr.appendChild(td);
    });
    return tr;
  }

  function setupPedido() {
    var detalle = document.getElementById('ped-detalle');
    if (!detalle) return;
    var aviso = document.getElementById('ped-aviso');
    var secPago = document.getElementById('ped-pago');
    var secAnular = document.getElementById('ped-anular');
    var secBoleta = document.getElementById('ped-boleta');
    var pasarela = document.getElementById('pasarela');
    var btnPagar = document.getElementById('btn-iniciar-pago');
    var btnAprobar = document.getElementById('btn-aprobar');
    var btnRechazar = document.getElementById('btn-rechazar');
    var formAnular = document.getElementById('anular-form');
    var id = new URLSearchParams(location.search).get('id') || '';
    var pagoId = null;
    if (!leerSesion()) { irALogin(); return; }
    document.getElementById('ped-id').textContent = id;

    function cargarBoleta() {
      llamarApi('GET', '/orders/' + encodeURIComponent(id) + '/receipt', undefined, true).then(function (res) {
        if (res.status !== 200) return;
        var b = res.datos;
        document.getElementById('bol-folio').textContent = b.folio;
        document.getElementById('bol-fecha').textContent = 'Fecha: ' + fecha(b.fecha) + ' · Caja: ' + b.caja;
        var cuerpo = document.getElementById('bol-detalle');
        cuerpo.textContent = '';
        b.detalle.forEach(function (d) {
          cuerpo.appendChild(filaTabla([d.producto, String(d.cantidad), money(d.precio), money(d.total)]));
        });
        document.getElementById('bol-neto').textContent = money(b.neto);
        document.getElementById('bol-iva').textContent = money(b.iva);
        document.getElementById('bol-total').textContent = money(b.total);
        secBoleta.hidden = false;
      });
    }

    function cargar(mensaje) {
      return llamarApi('GET', '/orders/' + encodeURIComponent(id), undefined, true)
        .then(function (res) {
          if (res.status !== 200) {
            detalle.hidden = secPago.hidden = secAnular.hidden = secBoleta.hidden = true;
            if (res.status >= 500) errorDeCarga(aviso, mensajeError(res), function () { cargar(); });
            else mostrarAviso(aviso, mensajeError(res), 'error');
            return;
          }
          var p = res.datos;
          chipEstado(document.getElementById('ped-estado'), p.estado);
          document.getElementById('ped-entrega').textContent = ENTREGAS[p.tipo_entrega] +
            (p.direccion ? ': ' + p.direccion + ', ' + p.comuna : '');
          document.getElementById('ped-fecha').textContent = 'Creado: ' + fecha(p.creado_en);
          var cuerpo = document.getElementById('ped-lineas');
          cuerpo.textContent = '';
          p.lineas.forEach(function (l) {
            cuerpo.appendChild(filaTabla([l.nombre, String(l.cantidad), money(l.precio), money(l.precio * l.cantidad)]));
          });
          document.getElementById('ped-total').textContent = money(p.total);
          detalle.hidden = false;
          var pendiente = p.estado === 'PENDIENTE_PAGO';
          secPago.hidden = !pendiente;
          secAnular.hidden = !pendiente;
          btnPagar.textContent = 'Pagar ' + money(p.total);
          if (!pendiente) pasarela.hidden = true;
          if (p.pagado_en) cargarBoleta();
          if (mensaje) mostrarAviso(aviso, mensaje[0], mensaje[1]);
          else if (p.estado === 'ANULADO') mostrarAviso(aviso, 'Este pedido está anulado; el stock se devolvió.', '');
          else if (pendiente) mostrarAviso(aviso, 'Tu pedido quedó reservado. Págalo para que lo preparemos.', 'ok');
          else ocultarAviso(aviso);
        })
        .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, function () { cargar(); }); });
    }

    btnPagar.addEventListener('click', function () {
      btnPagar.disabled = true;
      llamarApi('POST', '/payments', { order_id: id }, true)
        .then(function (res) {
          if (res.status === 201 || res.status === 200) {
            pagoId = res.datos.id;
            document.getElementById('pas-monto').textContent = money(res.datos.monto);
            pasarela.hidden = false;
            ocultarAviso(aviso);
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { btnPagar.disabled = false; });
    });

    function simular(resultado) {
      if (!pagoId) return;
      btnAprobar.disabled = btnRechazar.disabled = true;
      llamarApi('POST', '/payments/' + encodeURIComponent(pagoId) + '/simular', { resultado: resultado }, true)
        .then(function (res) {
          pasarela.hidden = true;
          pagoId = null;
          if (res.status !== 202) {
            mostrarAviso(aviso, mensajeError(res), 'error');
            return cargar();
          }
          return cargar(resultado === 'aprobado'
            ? ['Pago aprobado. Tu boleta está abajo.', 'ok']
            : ['El proveedor rechazó el pago. El pedido sigue pendiente; puedes intentarlo de nuevo.', 'error']);
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { btnAprobar.disabled = btnRechazar.disabled = false; });
    }
    btnAprobar.addEventListener('click', function () { simular('aprobado'); });
    btnRechazar.addEventListener('click', function () { simular('rechazado'); });

    formAnular.addEventListener('submit', function (e) {
      e.preventDefault();
      var motivo = formAnular.elements.motivo.value.trim();
      if (motivo.length < 5) {
        mostrarAviso(aviso, 'Escribe el motivo de la anulación (al menos 5 caracteres).', 'error');
        return;
      }
      bloquear(formAnular, true);
      llamarApi('POST', '/orders/' + encodeURIComponent(id) + '/cancel', { motivo: motivo }, true)
        .then(function (res) {
          if (res.status === 200) return cargar(['Pedido anulado; el stock se devolvió.', 'ok']);
          mostrarAviso(aviso, mensajeError(res), 'error');
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(formAnular, false); });
    });

    cargar();
  }

  // ---------- Mis pedidos (POST /api/v1/graphql: orders + inventory + payments) ----------
  var CONSULTA_MIS_PEDIDOS = 'query { misPedidos(limite: 20) { id estado tipoEntrega total creadoEn ' +
    'lineas { cantidad precio producto { nombre } } pago { estado monto } } }';

  function setupMisPedidos() {
    var lista = document.getElementById('mp-lista');
    if (!lista) return;
    var aviso = document.getElementById('mp-aviso');
    if (!leerSesion()) { irALogin(); return; }

    function cargar() {
    mostrarAviso(aviso, 'Cargando tus pedidos…');
    llamarApi('POST', '/graphql', { query: CONSULTA_MIS_PEDIDOS }, true)
      .then(function (res) {
        if (res.status !== 200) {
          errorDeCarga(aviso, mensajeError(res), cargar);
          return;
        }
        var errores = res.datos.errors || [];
        var pedidos = res.datos.data ? res.datos.data.misPedidos : null;
        if (!pedidos) {
          errorDeCarga(aviso, errores.length ? errores[0].message : 'No se pudieron cargar tus pedidos.', cargar);
          return;
        }
        // Si inventory o payments fallaron, se avisa que la informacion esta incompleta
        if (errores.length) {
          errorDeCarga(aviso, 'Información incompleta: ' + errores.map(function (e) { return e.message; }).join(' · '), cargar);
        } else if (pedidos.length === 0) {
          mostrarAviso(aviso, 'Todavía no tienes pedidos.', '', { href: 'catalogo.php', texto: 'Ver la carta' });
        } else {
          ocultarAviso(aviso);
        }
        lista.textContent = '';
        pedidos.forEach(function (p) {
          var tarjeta = document.createElement('article');
          tarjeta.className = 'mp-pedido';
          var cab = document.createElement('div');
          cab.className = 'mp-cab';
          var titulo = document.createElement('a');
          titulo.href = 'pedido.php?id=' + encodeURIComponent(p.id);
          titulo.className = 'mp-id';
          titulo.textContent = p.id;
          var chip = document.createElement('span');
          chipEstado(chip, p.estado);
          cab.appendChild(titulo);
          cab.appendChild(chip);
          var meta = document.createElement('p');
          meta.className = 'mp-meta';
          meta.textContent = fecha(p.creadoEn) + ' · ' + ENTREGAS[p.tipoEntrega] + ' · Total ' + money(p.total);
          var productos = document.createElement('ul');
          productos.className = 'mp-productos';
          p.lineas.forEach(function (l) {
            var li = document.createElement('li');
            li.textContent = l.cantidad + ' × ' + (l.producto ? l.producto.nombre : 'Producto (dato no disponible)');
            if (!l.producto) li.className = 'incompleto';
            productos.appendChild(li);
          });
          var pago = document.createElement('p');
          pago.className = 'mp-pago';
          pago.textContent = p.pago ? 'Pago: ' + p.pago.estado.toLowerCase() + ' (' + money(p.pago.monto) + ')'
            : (errores.length ? 'Pago: dato no disponible' : 'Pago: sin pago registrado');
          tarjeta.appendChild(cab);
          tarjeta.appendChild(meta);
          tarjeta.appendChild(productos);
          tarjeta.appendChild(pago);
          lista.appendChild(tarjeta);
        });
      })
      .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, cargar); });
    }
    cargar();
  }

  // ---------- Portada: destacados desde el API Gateway (GET /api/v1/products) ----------
  function setupDestacados() {
    var cont = document.getElementById('destacados');
    if (!cont) return;
    var estado = document.getElementById('destacados-estado');
    llamarApi('GET', '/products', undefined, false)
      .then(function (res) {
        if (res.status !== 200) throw new Error();
        var lista = res.datos.filter(function (p) { return p.disponible; });
        lista.sort(function (a, b) { return (b.precio_oferta ? 1 : 0) - (a.precio_oferta ? 1 : 0); });
        if (lista.length === 0) {
          estado.textContent = 'Por ahora no hay productos disponibles.';
          return;
        }
        estado.remove();
        lista.slice(0, 3).forEach(function (p) {
          var card = document.createElement('a');
          card.className = 'product-card';
          card.href = 'catalogo.php';
          var thumb = document.createElement('div');
          thumb.className = 'product-thumb';
          var img = document.createElement('img');
          img.src = p.imagen;
          img.alt = p.nombre;
          thumb.appendChild(img);
          var info = document.createElement('div');
          info.className = 'product-info';
          var nombre = document.createElement('div');
          nombre.className = 'name';
          nombre.textContent = p.nombre;
          var meta = document.createElement('div');
          meta.className = 'meta';
          meta.textContent = (CATEGORIAS[p.categoria] || p.categoria) + (p.precio_oferta ? ' · En oferta' : '');
          info.appendChild(nombre);
          info.appendChild(meta);
          var precio = document.createElement('div');
          precio.className = 'product-price';
          precio.textContent = money(p.precio_oferta || p.precio);
          card.appendChild(thumb);
          card.appendChild(info);
          card.appendChild(precio);
          cont.appendChild(card);
        });
      })
      .catch(function () { estado.textContent = 'No pudimos cargar los destacados.'; });
  }

  // Si el backend responde 403, la pagina muestra que no hay permiso
  function sinPermiso(res, aviso) {
    if (res.status !== 403) return false;
    mostrarAviso(aviso, 'No tienes permiso para ver esta sección.', 'error');
    return true;
  }

  // ---------- Despacho: ordenes y cambio de estado (GET /admin/dispatch-orders, PUT /admin/orders/{id}/status) ----------
  var SIGUIENTE = { PAGADO: ['EN_PREPARACION'], EN_PREPARACION: ['LISTO'], LISTO: ['EN_CAMINO', 'ENTREGADO'], EN_CAMINO: ['ENTREGADO'] };

  function setupDespacho() {
    var lista = document.getElementById('des-lista');
    if (!lista) return;
    var aviso = document.getElementById('des-aviso');
    if (!leerSesion()) { irALogin(); return; }

    function boton(texto, clase, accion) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn-chico' + (clase ? ' ' + clase : '');
      b.textContent = texto;
      b.addEventListener('click', accion);
      return b;
    }

    function cambiar(id, estado) {
      llamarApi('PUT', '/admin/orders/' + encodeURIComponent(id) + '/status', { estado: estado }, true)
        .then(function (res) {
          if (res.status === 200) return cargar(['Pedido ' + id + ': ' + ESTADOS[estado] + '.', 'ok']);
          mostrarAviso(aviso, mensajeError(res), 'error');
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
    }

    function cargar(mensaje) {
      return llamarApi('GET', '/admin/dispatch-orders', undefined, true)
        .then(function (res) {
          if (sinPermiso(res, aviso)) return;
          if (res.status !== 200) { errorDeCarga(aviso, mensajeError(res), function () { cargar(); }); return; }
          lista.textContent = '';
          if (mensaje) mostrarAviso(aviso, mensaje[0], mensaje[1]);
          else if (res.datos.length === 0) mostrarAviso(aviso, 'No hay órdenes pendientes de despacho.');
          else ocultarAviso(aviso);
          res.datos.forEach(function (o) {
            var tarjeta = document.createElement('article');
            tarjeta.className = 'mp-pedido';
            var cab = document.createElement('div');
            cab.className = 'mp-cab';
            var titulo = document.createElement('strong');
            titulo.textContent = o.id;
            var chip = document.createElement('span');
            chipEstado(chip, o.estado);
            cab.appendChild(titulo);
            cab.appendChild(chip);
            var meta = document.createElement('p');
            meta.className = 'mp-meta';
            meta.textContent = 'Pagado: ' + fecha(o.pagado_en) + ' · ' + ENTREGAS[o.tipo_entrega] +
              (o.direccion ? ': ' + o.direccion + ', ' + o.comuna : '');
            var productos = document.createElement('ul');
            productos.className = 'mp-productos';
            o.productos.forEach(function (l) {
              var li = document.createElement('li');
              li.textContent = l.cantidad + ' × ' + l.nombre;
              productos.appendChild(li);
            });
            var cliente = document.createElement('p');
            cliente.className = 'mp-meta';
            var acciones = document.createElement('div');
            acciones.className = 'pasarela-botones';
            (SIGUIENTE[o.estado] || []).forEach(function (estado) {
              var corresponde = o.estado !== 'LISTO' || (estado === 'EN_CAMINO') === (o.tipo_entrega === 'delivery');
              if (corresponde) acciones.appendChild(boton('Marcar ' + ESTADOS[estado].toLowerCase(), '', function () { cambiar(o.id, estado); }));
            });
            acciones.appendChild(boton('Datos del cliente', '', function () {
              llamarApi('GET', '/admin/clients/' + encodeURIComponent(o.user_id), undefined, true).then(function (r) {
                cliente.textContent = r.status === 200
                  ? 'Cliente: ' + r.datos.nombre + (r.datos.telefono ? ' · Tel: ' + r.datos.telefono : '')
                  : mensajeError(r);
              });
            }));
            tarjeta.appendChild(cab);
            tarjeta.appendChild(meta);
            tarjeta.appendChild(productos);
            tarjeta.appendChild(cliente);
            tarjeta.appendChild(acciones);
            lista.appendChild(tarjeta);
          });
        })
        .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, function () { cargar(); }); });
    }
    cargar();
  }

  // ---------- Ventas de la caja web (GET /admin/sales) ----------
  function setupVentas() {
    var filas = document.getElementById('ven-filas');
    if (!filas) return;
    var aviso = document.getElementById('ven-aviso');
    if (!leerSesion()) { irALogin(); return; }
    function cargar() {
    llamarApi('GET', '/admin/sales', undefined, true)
      .then(function (res) {
        if (sinPermiso(res, aviso)) return;
        if (res.status !== 200) { errorDeCarga(aviso, mensajeError(res), cargar); return; }
        filas.textContent = '';
        res.datos.forEach(function (v) {
          filas.appendChild(filaTabla([v.folio, v.pedido, fecha(v.fecha), money(v.total), ESTADOS[v.estado] || v.estado]));
        });
        document.getElementById('ven-cantidad').textContent = res.datos.length;
        document.getElementById('ven-total').textContent = money(res.datos.reduce(function (s, v) { return s + v.total; }, 0));
        document.getElementById('ven-resumen').hidden = false;
        document.getElementById('ven-tabla').hidden = res.datos.length === 0;
        if (res.datos.length === 0) mostrarAviso(aviso, 'Todavía no hay ventas registradas.');
        else ocultarAviso(aviso);
      })
      .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, cargar); });
    }
    cargar();
  }

  // ---------- Reporte de ventas del dueno (GET /admin/reports/sales, servicio analitica) ----------
  function setupReportes() {
    var contenido = document.getElementById('rep-contenido');
    if (!contenido) return;
    var aviso = document.getElementById('rep-aviso');
    if (!leerSesion()) { irALogin(); return; }

    function cargar() {
      mostrarAviso(aviso, 'Cargando el reporte…');
      llamarApi('GET', '/admin/reports/sales', undefined, true)
        .then(function (res) {
          if (sinPermiso(res, aviso)) { contenido.hidden = true; return; }
          if (res.status !== 200) { errorDeCarga(aviso, mensajeError(res), cargar); return; }
          var r = res.datos;
          document.getElementById('rep-pedidos').textContent = r.pedidos;
          document.getElementById('rep-total').textContent = money(r.total_vendido);
          document.getElementById('rep-ticket').textContent = money(r.ticket_promedio);
          document.getElementById('rep-hora').textContent = 'Datos consultados a las ' +
            new Date().toLocaleTimeString('es-CL') + '. Cada pedido pagado se suma al reporte al momento del pago.';
          var productos = document.getElementById('rep-productos');
          productos.textContent = '';
          r.mas_vendidos.forEach(function (p) {
            productos.appendChild(filaTabla([p.nombre, String(p.cantidad), money(p.total)]));
          });
          var dias = document.getElementById('rep-dias');
          dias.textContent = '';
          r.por_dia.forEach(function (d) { dias.appendChild(filaTabla([d.dia, String(d.pedidos), money(d.total)])); });
          contenido.hidden = false;
          if (r.pedidos === 0) mostrarAviso(aviso, 'Todavía no hay ventas pagadas.');
          else ocultarAviso(aviso);
        })
        .catch(function () { errorDeCarga(aviso, ERROR_CONEXION, cargar); });
    }
    document.getElementById('rep-actualizar').addEventListener('click', cargar);
    cargar();
  }

  // ---------- Administracion: usuarios, perfiles y mensajes de contacto ----------
  var PERFILES = { cliente: 'Cliente', cajero: 'Cajero', despacho: 'Encargado de despacho', dueno: 'Dueño', admin: 'Administrador' };

  function setupAdmin() {
    var usuarios = document.getElementById('adm-usuarios');
    if (!usuarios) return;
    var aviso = document.getElementById('adm-aviso');
    var form = document.getElementById('adm-funcionario');
    var sesion = leerSesion();
    if (!sesion) { irALogin(); return; }

    function cargarUsuarios() {
      return llamarApi('GET', '/admin/users', undefined, true).then(function (res) {
        if (sinPermiso(res, aviso)) return;
        if (res.status !== 200) { errorDeCarga(aviso, mensajeError(res), cargarUsuarios); return; }
        usuarios.textContent = '';
        res.datos.forEach(function (u) {
          var tr = filaTabla([u.user_id, u.email]);
          var tdRol = document.createElement('td');
          var select = document.createElement('select');
          select.setAttribute('aria-label', 'Perfil de ' + u.email);
          Object.keys(PERFILES).forEach(function (rol) {
            var op = document.createElement('option');
            op.value = rol;
            op.textContent = PERFILES[rol];
            op.selected = rol === u.rol;
            select.appendChild(op);
          });
          tdRol.appendChild(select);
          tr.appendChild(tdRol);
          var tdVer = document.createElement('td');
          tdVer.textContent = u.correo_verificado ? 'Sí' : 'No';
          tr.appendChild(tdVer);
          var tdAccion = document.createElement('td');
          var guardar = document.createElement('button');
          guardar.type = 'button';
          guardar.className = 'btn-chico';
          guardar.textContent = 'Guardar perfil';
          guardar.addEventListener('click', function () {
            llamarApi('PUT', '/admin/users/' + encodeURIComponent(u.user_id) + '/role', { rol: select.value }, true)
              .then(function (r) {
                if (r.status === 200) {
                  mostrarAviso(aviso, 'Perfil de ' + u.email + ': ' + PERFILES[select.value] + '. Debe volver a iniciar sesión.', 'ok');
                  cargarUsuarios();
                } else {
                  mostrarAviso(aviso, mensajeError(r), 'error');
                }
              })
              .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
          });
          tdAccion.appendChild(guardar);
          tr.appendChild(tdAccion);
          usuarios.appendChild(tr);
        });
      }).catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
    }

    function cargarContacto() {
      llamarApi('GET', '/admin/contact', undefined, true).then(function (res) {
        if (res.status !== 200) return;
        var cuerpo = document.getElementById('adm-contacto');
        cuerpo.textContent = '';
        res.datos.forEach(function (m) {
          cuerpo.appendChild(filaTabla([fecha(m.creado_en), m.nombre, m.motivo, m.mensaje]));
        });
      });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = leerFormulario(form);
      d.password = form.elements.password.value;
      if (!d.email || d.password.length < 8) {
        mostrarAviso(aviso, 'Escribe el correo y una contraseña de al menos 8 caracteres.', 'error');
        return;
      }
      bloquear(form, true);
      llamarApi('POST', '/admin/users', d, true)
        .then(function (res) {
          if (res.status === 201) {
            form.reset();
            mostrarAviso(aviso, 'Cuenta creada: ' + res.datos.email + ' (' + PERFILES[res.datos.rol] + ').', 'ok');
            cargarUsuarios();
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(form, false); });
    });

    var formCliente = document.getElementById('adm-cliente');
    formCliente.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = leerFormulario(formCliente);
      d.password = formCliente.elements.password.value;
      if (!d.nombre || !d.email || d.password.length < 8) {
        mostrarAviso(aviso, 'Completa nombre, correo y una contraseña de al menos 8 caracteres.', 'error');
        return;
      }
      d.email = d.email.toLowerCase();
      bloquear(formCliente, true);
      llamarApi('POST', '/admin/clients', d, true)
        .then(function (res) {
          if (res.status === 201) {
            formCliente.reset();
            mostrarAviso(aviso, 'Cliente registrado (' + d.email + '). Debe verificar su correo con el código que le llegó.', 'ok');
            cargarUsuarios();
          } else {
            mostrarAviso(aviso, mensajeError(res), 'error');
          }
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); })
        .then(function () { bloquear(formCliente, false); });
    });

    cargarUsuarios();
    cargarContacto();
  }

  document.addEventListener('DOMContentLoaded', function () {
    pintarEncabezado();
    updateCartBadge();
    setupAddButtons();
    cargarCatalogo();
    renderCart();
    setupFilters();
    setupSearch();
    setupContactForm();
    setupPayButton();
    setupLogin();
    setupRegistro();
    setupCuenta();
    setupInventario();
    setupPedido();
    setupMisPedidos();
    setupDestacados();
    setupDespacho();
    setupVentas();
    setupReportes();
    setupAdmin();
  });
})();