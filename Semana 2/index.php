<!DOCTYPE html>
<html lang="es">
<head>
    <title>Esencia | Perfumes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <head>
    <title>Esencia | Perfumes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fff8ed; }
        nav, footer { background-color: #176b78; }
        .navbar-brand, .nav-link.active { color: #ffd166; }
        header { background-color: #dff3f0; border-radius: 16px; }
        header h1, .card h2 { color: #176b78; }
        .btn-primary { background-color: #ef6f61; border-color: #ef6f61; }
        .card { border: 2px solid #abebff; }
        .banner-portada {
            background-image: url('Imagen Esencia portada1.jpg');
            background-size: cover;
            background-position: center;
        }
        .capa-oscura {
            background-color: rgba(0, 0, 0, 0.6); 
        }
    </style>
</head>
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
                        <a class="nav-link" href="catalogo.php">Catálogo</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="contacto.php">Contacto</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <header class="container mt-5 mb-5 p-0 text-center rounded-4 shadow overflow-hidden banner-portada">
        <div class="capa-oscura py-5">
            <h1 class="display-4 fw-bold text-white mt-4">Esencia</h1>
            <p class="lead text-light mb-4">Perfumes para cada momento y personalidad.</p>
            <a class="btn btn-light btn-lg mb-4 fw-bold" href="catalogo.php">Conocer el catálogo</a>
        </div>
    </header>

    <main class="container mt-5 pt-3 mb-5">
        <!-- justify-content-center centra las tarjetas al hacerlas más pequeñas -->
        <div class="row justify-content-center g-4 text-center">
            
            <!-- Tarjeta Variedad -->
            <div class="col-md-4 ">
                <div class="card h-100 shadow-sm text-bg-dark border-secondary overflow-hidden">
                    <img src="variedad.jpg" class="card-img-top opacity-50" alt="Variedad de perfumes" style="height: 140px; object-fit: cover;">
                    <div class="card-body">
                        <h2 class="h5 text-white">Variedad</h2>
                        <p class="text-secondary mb-0">Aromas florales, cítricos y amaderados.</p>
                    </div>
                </div>
            </div>

            <!-- Tarjeta Calidad -->
            <div class="col-md-4 ">
                <div class="card h-100 shadow-sm text-bg-dark border-secondary overflow-hidden">
                    <img src="calidad.jpg" class="card-img-top opacity-50" alt="Calidad premium" style="height: 140px; object-fit: cover;">
                    <div class="card-body">
                        <h2 class="h5 text-white">Calidad</h2>
                        <p class="text-secondary mb-0">Fragancias escogidas para acompañarte.</p>
                    </div>
                </div>
            </div>

            <!-- Tarjeta Compra Simple -->
            <div class="col-md-4 ">
                <div class="card h-100 shadow-sm text-bg-dark border-secondary overflow-hidden">
                    <img src="compra.jpg" class="card-img-top opacity-50" alt="Compra online" style="height: 140px; object-fit: cover;">
                    <div class="card-body">
                        <h2 class="h5 text-white">Compra simple</h2>
                        <p class="text-secondary mb-0">Agrega tus productos al carrito fácilmente.</p>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- Pie de Página -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p class="mb-0">&copy; 2026 Esencia</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>