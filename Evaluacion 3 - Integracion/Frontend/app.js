(function () {
  var CART_KEY = 'aroma_cart';
  // Direccion del API Gateway (unica entrada al backend)
  var API_URL = 'https://127.0.0.1:8000/api/v1';
  var SESION_KEY = 'aroma_sesion';

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
    'Producto no encontrado': 'El producto ya no existe.'
  };

  function mensajeError(res) {
    if (res.status === 429) return 'Demasiados intentos. Espera un minuto y vuelve a intentar.';
    var detalle = res.datos && res.datos.detail;
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

  // Encabezado: con sesion muestra "Hola, nombre", Inventario (dueno o admin) y Cerrar sesion
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
    if (sesion.rol === 'dueno' || sesion.rol === 'admin') {
      var inv = document.createElement('a');
      inv.href = 'inventario.php';
      inv.className = 'btn-login';
      inv.textContent = 'Inventario';
      cont.appendChild(inv);
    }
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
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
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
      list.innerHTML = '';
      if (emptyMsg) emptyMsg.style.display = 'block';
      updateSummary(0);
      return;
    }
    if (emptyMsg) emptyMsg.style.display = 'none';

    list.innerHTML = cart.map(function (item) {
      return (
        '<div class="cart-item" data-id="' + item.id + '">' +
          '<div class="art">' + item.art + '</div>' +
          '<div class="info">' +
            '<h4>' + item.name + '</h4>' +
            '<div class="qty-control">' +
              '<button type="button" data-action="dec" aria-label="Restar">\u2212</button>' +
              '<span>' + item.qty + '</span>' +
              '<button type="button" data-action="inc" aria-label="Sumar">+</button>' +
            '</div>' +
            '<a href="#" class="remove-item" data-action="remove">Quitar</a>' +
          '</div>' +
          '<div class="line-price">' + money(item.price * item.qty) + '</div>' +
        '</div>'
      );
    }).join('');

    list.querySelectorAll('.cart-item').forEach(function (el) {
      var id = el.getAttribute('data-id');
      el.querySelector('[data-action="inc"]').addEventListener('click', function () { changeQty(id, 1); });
      el.querySelector('[data-action="dec"]').addEventListener('click', function () { changeQty(id, -1); });
      el.querySelector('[data-action="remove"]').addEventListener('click', function (e) {
        e.preventDefault();
        removeFromCart(id);
      });
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
        var card = btn.closest('.product-card-lg');
        var art = card ? card.querySelector('.art') : null;
        addToCart({
          id: btn.getAttribute('data-id'),
          name: btn.getAttribute('data-name'),
          price: parseInt(btn.getAttribute('data-price'), 10),
          art: art ? art.innerHTML : ''
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
              var inicio = (sesion.rol === 'dueno' || sesion.rol === 'admin') ? 'inventario.php' : 'catalogo.php';
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

    llamarApi('GET', '/clients/me', undefined, true)
      .then(function (res) {
        if (res.status === 200) {
          rellenar(res.datos);
          ocultarAviso(aviso);
          form.hidden = false;
        } else {
          mostrarAviso(aviso, mensajeError(res), 'error');
        }
      })
      .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });

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
            mostrarAviso(aviso, mensajeError(res), 'error');
            return;
          }
          if (aviso.textContent === 'Cargando el inventario…') ocultarAviso(aviso);
          filas.textContent = '';
          res.datos.forEach(function (p) { filas.appendChild(fila(p)); });
          tabla.hidden = false;
          nuevo.hidden = false;
        })
        .catch(function () { mostrarAviso(aviso, ERROR_CONEXION, 'error'); });
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

  function setupPayButton() {
    var btn = document.getElementById('btn-pay');
    if (!btn) return;
    btn.addEventListener('click', function () {
      showToast('Pedido enviado. Te avisaremos cuando esté listo.');
      localStorage.removeItem(CART_KEY);
      updateCartBadge();
      renderCart();
    });
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
  });
})();