(function () {
  var CART_KEY = 'aroma_cart';

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
    var envio = total > 0 && total < 15000 ? 1500 : 0;

    var subtotalEl = document.getElementById('cart-subtotal');
    if (subtotalEl) subtotalEl.textContent = money(total);

    var envioEl = document.getElementById('cart-envio');
    if (envioEl) envioEl.textContent = total === 0 ? '-' : (envio === 0 ? 'Gratis' : money(envio));

    if (totalEl) totalEl.textContent = money(total + envio);

    var payBtn = document.getElementById('btn-pay');
    if (payBtn) payBtn.disabled = total === 0;
  }

  function setupAddButtons() {
    document.querySelectorAll('[data-add-to-cart]').forEach(function (btn) {
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

  function setupContactForm() {
    var form = document.getElementById('contact-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var note = document.getElementById('form-note');
      form.reset();
      if (note) {
        note.textContent = 'Gracias, tu mensaje quedó registrado. Te responderemos pronto.';
        note.classList.add('show');
      }
    });
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
    updateCartBadge();
    setupAddButtons();
    renderCart();
    setupFilters();
    setupSearch();
    setupContactForm();
    setupPayButton();
  });
})();