<head>
    <title>Pagina Principal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="bg-light">

    <!-- Barra de Navegación -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="index.php">Mi Proyecto</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="index.php">Inicio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="caracteristicas.php">Características</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="contacto.php">Contacto</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
        <!-- Contenido Principal -->
    <main class="container mt-4">
    <div class="row justify-content-center g-4">
        
        <!-- Tarjeta izquierda -->
        <div class="col-md-6">
            <div class="card shadow-sm border-0">
                <div class="card-body text-center">
                    <h3 class="h5 card-title">Contacto</h3>
                    <p class="card-text text-muted mb-1">E-mail: i.arroyovillanueva@uandresbello.edu</p>
                    <p class="card-text text-muted mb-1">E-mail: a.martnezhernndez@uandresbello.edu</p>
                    <p class="card-text text-muted mb-1">Telefono: (2) 2456-7890</p>
                    <p class="card-text text-muted mb-0">Hora de atención: Lunes a Viernes</p>
                </div>
            </div>
        </div>

        <!-- Tarjeta derecha -->
        <div class="col-md-6">
            <div class="card h-100 shadow-sm border-0">
                <div class="card-body p-4">
                    <label for="email" class="form-label">Email:</label>
                    <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
                </div>                
                <label for="comment">Comentarios</label>
                <textarea class="form-control" rows="5" id="comment" name="text"></textarea>
                <button type="button" class="btn btn-outline-primary mt-2">Enviar</button>
                </div>
            </div>
        </div>

    </div>
</main>
    <!-- Pie de Página -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p class="mb-0">&copy; 2026 Mi Proyecto. Todos los derechos reservados.</p>
        </div>
    </footer>
