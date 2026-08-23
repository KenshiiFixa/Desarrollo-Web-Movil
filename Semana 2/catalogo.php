<!DOCTYPE html>
<html lang="es">
<head>
    <title>Esencia | Catálogo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fff8ed !important; }
        nav, footer { background-color: #176b78 !important; }
        .navbar-brand, .nav-link.active { color: #ffd166 !important; }
        header { background-color: #dff3f0; border-radius: 16px; }
        header h1, .card h3 { color: #176b78; }
        .btn-primary { background-color: #ef6f61; border-color: #ef6f61; }
        .btn-dark { background-color: #176b78; border-color: #176b78; }
        .card { border: 2px solid #ffd166; }
        .imagen-perfume { height: 240px; object-fit: cover; }
        .banner-catalogo {
            background-image: url('catalogo.jpg');
            background-size: cover;
            background-position: center;
        }
        .capa-oscura {
            background-color: rgba(0, 0, 0, 0.6); 
            min-height: 320px; /* Esta es la altura aproximada de tu portada */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="bg-light">

    <!-- Barra de Navegación -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-black shadow-sm border-bottom border-secondary">
        <div class="container-fluid">
            <a class="navbar-brand" href="index.php">Esencia</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="index.php">Inicio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="catalogo.php">Catálogo</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="contacto.php">Contacto</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    <header class="container mt-5 p-0 text-center rounded-4 shadow overflow-hidden banner-catalogo">
        <div class="capa-oscura">
            <h1 class="display-4 fw-bold text-white">Catálogo de perfumes</h1>
            <p class="lead text-light mb-0">Elige tu aroma favorito y agrégalo al carrito.</p>
        </div>
    </header>

    <main class="container mt-5 mb-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="h3 mb-0">Nuestros productos</h2>
            <button class="btn btn-dark" data-bs-toggle="modal" data-bs-target="#modalCarrito">
                Carrito (<span id="contador-carrito">0</span>)
            </button>
        </div>

        <div class="row g-4">
            <div class="col-md-4"><div class="card h-100 shadow-sm"><img src="https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=600&q=80" class="card-img-top imagen-perfume" alt="Frasco de perfume floral"><div class="card-body"><h3 class="h5">Aroma Floral</h3><p class="text-muted">Una fragancia suave y fresca.</p><p class="fw-bold">$24.990</p><button class="btn btn-primary agregar-carrito" data-producto="Aroma Floral" data-precio="24990">Agregar al carrito</button></div></div></div>
            <div class="col-md-4"><div class="card h-100 shadow-sm"><img src="https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=600&q=80" class="card-img-top imagen-perfume" alt="Frasco de perfume amaderado"><div class="card-body"><h3 class="h5">Aroma Amaderado</h3><p class="text-muted">Un aroma intenso y elegante.</p><p class="fw-bold">$29.990</p><button class="btn btn-primary agregar-carrito" data-producto="Aroma Amaderado" data-precio="29990">Agregar al carrito</button></div></div></div>
            <div class="col-md-4"><div class="card h-100 shadow-sm"><img src="https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=600&q=80" class="card-img-top imagen-perfume" alt="Frasco de perfume cítrico"><div class="card-body"><h3 class="h5">Aroma Cítrico</h3><p class="text-muted">Una fragancia alegre para el día.</p><p class="fw-bold">$19.990</p><button class="btn btn-primary agregar-carrito" data-producto="Aroma Cítrico" data-precio="19990">Agregar al carrito</button></div></div></div>
        </div>
    </main>

    <div class="modal fade" id="modalCarrito" tabindex="-1" aria-labelledby="tituloCarrito" aria-hidden="true">
        <div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h2 class="modal-title h5" id="tituloCarrito">Mi carrito</h2><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button></div><div class="modal-body"><ul id="lista-carrito" class="list-group mb-3"><li class="list-group-item">El carrito está vacío.</li></ul><p class="fw-bold mb-0">Total: $<span id="total-carrito">0</span></p></div></div></div>
    </div>
    <!-- Pie de Página -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p class="mb-0">&copy; 2026 Esencia</p>
        </div>
    </footer>
    <script src="script.js"></script>
</body>
</html>
