const botonesCarrito = document.querySelectorAll('.agregar-carrito');
const contadorCarrito = document.getElementById('contador-carrito');
let cantidadProductos = 0;
let totalCarrito = 0;
const listaCarrito = document.getElementById('lista-carrito');
const totalCarritoElemento = document.getElementById('total-carrito');

botonesCarrito.forEach(function (boton) {
    boton.addEventListener('click', function () {
        cantidadProductos = cantidadProductos + 1;
        totalCarrito = totalCarrito + Number(boton.dataset.precio);

        if (contadorCarrito !== null) {
            contadorCarrito.textContent = cantidadProductos;
        }

        if (listaCarrito !== null) {
            if (listaCarrito.children.length === 1 && listaCarrito.children[0].textContent === 'El carrito está vacío.') {
                listaCarrito.innerHTML = '';
            }
            const producto = document.createElement('li');
            producto.className = 'list-group-item';
            producto.textContent = boton.dataset.producto + ' - $' + boton.dataset.precio;
            listaCarrito.appendChild(producto);
            totalCarritoElemento.textContent = totalCarrito;
        }
    });
});