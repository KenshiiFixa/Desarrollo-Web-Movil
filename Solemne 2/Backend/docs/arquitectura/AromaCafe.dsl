workspace "AromaYCafe" "Plataforma Aroma & Cafe - Backend Evaluacion 2" {

    !identifiers hierarchical

    model {
        visitante = person "Visitante" "Persona que consulta el menu sin iniciar sesion."
        cliente = person "Cliente" "Persona registrada que compra, paga y revisa sus pedidos."
        cajero = person "Cajero virtual" "Funcionario que revisa las ventas de la caja web."
        despacho = person "Encargado de despacho" "Prepara y entrega los pedidos."
        dueno = person "Dueno" "Revisa las ventas y los productos."
        admin = person "Administrador" "Mantiene usuarios, clientes y perfiles."

        proveedor = softwareSystem "Proveedor de pagos" "Plataforma externa de pagos. En el proyecto se usa un simulador." {
            tags "SistemaExterno"
        }

        sistema = softwareSystem "Sistema Aroma & Cafe" "Plataforma que integra el menu, los pedidos, los pagos, el despacho y los reportes de la cafeteria." {
            tags "SistemaEvaluado"

            frontend = container "Frontend responsivo" "Interfaz web para visitantes, clientes y personal." "Aplicacion web" {
                tags "Frontend"
            }

            apiGateway = container "API Gateway" "Punto de entrada al backend; enruta peticiones y aplica controles de acceso." "Servicio HTTP" {
                tags "Gateway"

                // C3 - Componentes internos del API Gateway.
                httpEntry = component "Adaptador HTTP" "Recibe solicitudes y genera respuestas HTTP." "Modulo de entrada" {
                    tags "EntradaC3"
                }
                rateLimiter = component "Limite de solicitudes" "Limita cuantas solicitudes puede hacer cada IP por minuto." "Modulo de seguridad" {
                    tags "ControlC3"
                }
                routeTable = component "Tabla de rutas" "Lista de rutas permitidas con su destino y perfiles." "Modulo de enrutamiento" {
                    tags "ControlC3"
                }
                identityFilter = component "Filtro de acceso" "Valida el token con el Auth Service y revisa el perfil." "Modulo de seguridad" {
                    tags "ControlC3"
                }
                dispatcher = component "Despachador de rutas" "Envia la solicitud al servicio interno con la identidad verificada." "Modulo de enrutamiento" {
                    tags "AplicacionC3"
                }
                errorMapper = component "Traductor de errores" "Responde errores controlados sin mostrar detalles internos." "Modulo de errores" {
                    tags "ErrorC3"
                }
            }

            authService = container "Auth Service" "Registra usuarios, inicia sesion y valida la identidad." "Servicio de identidad" {
                tags "Seguridad"

                // C3 - Componentes internos del Auth Service.
                identityApi = component "API de identidad" "Atiende el registro, el inicio de sesion y la validacion del token." "API interna" {
                    tags "EntradaC3"
                }
                credentialsVerifier = component "Verificador de credenciales" "Comprueba la clave sin guardarla en texto plano." "Servicio de validacion" {
                    tags "ControlC3"
                }
                sessionManager = component "Gestor de sesiones" "Crea las sesiones y controla su vigencia." "Servicio de identidad" {
                    tags "AplicacionC3"
                }
                emailVerification = component "Verificacion de correo" "Genera el codigo que se envia al correo del cliente." "Servicio de identidad" {
                    tags "AplicacionC3"
                }
                usersAdmin = component "Mantenedor de usuarios" "Crea funcionarios y cambia perfiles." "Servicio de administracion" {
                    tags "AplicacionC3"
                }
                identityRepo = component "Repositorio de identidades" "Accede a los usuarios y sesiones guardados." "Acceso a datos" {
                    tags "PersistenciaC3"
                }
                secretsClient = component "Cliente de secretos" "Obtiene los secretos del servicio." "Adaptador de integracion" {
                    tags "IntegracionC3"
                }
            }

            secretManager = container "Administrador de secretos" "Guarda los secretos y los entrega solo a los servicios autorizados." "HashiCorp Vault" {
                tags "Seguridad"
            }

            inventory = container "Catalogo y Menu" "Gestiona los productos, precios, ofertas y stock de la cafeteria." "Servicio privado" {
                tags "Privado"
            }

            orders = container "Pedidos" "Gestiona el ciclo de vida de los pedidos, la boleta y el despacho." "Servicio privado" {
                tags "Privado"

                // C3 - Componentes internos de Pedidos.
                ordersApi = component "API de pedidos" "Recibe solicitudes del gateway y de pagos." "API interna" {
                    tags "EntradaC3"
                }
                accessPolicy = component "Politica de acceso a pedidos" "Restringe operaciones por rol y por dueno del pedido." "Reglas de autorizacion" {
                    tags "ControlC3"
                }
                paidControl = component "Control de pago repetido" "Evita procesar dos veces el mismo pago." "Regla de negocio" {
                    tags "ControlC3"
                }
                orderWorkflow = component "Servicio de pedidos" "Coordina las reglas del pedido: total, despacho y estados." "Servicio de aplicacion" {
                    tags "AplicacionC3"
                }
                inventoryAdapter = component "Adaptador de menu" "Reserva y libera stock en el catalogo." "Adaptador gRPC" {
                    tags "IntegracionC3"
                }
                notifier = component "Avisos de venta" "Envia la boleta y la venta cuando el pedido se paga." "Adaptador privado" {
                    tags "IntegracionC3"
                }
                ordersRepo = component "Repositorio de pedidos" "Persiste los pedidos y su historial." "Acceso a datos" {
                    tags "PersistenciaC3"
                }
            }

            clients = container "Clientes" "Gestiona la ficha de los clientes y los mensajes de contacto." "Servicio privado" {
                tags "Privado"
            }

            payments = container "Pagos" "Gestiona los pagos y verifica los avisos del proveedor." "Servicio privado" {
                tags "Privado"
            }

            notificaciones = container "Notificaciones" "Envia el codigo de verificacion y la boleta por correo (simulado)." "Servicio privado" {
                tags "Privado"
            }

            analitica = container "Analitica" "Calcula el reporte de ventas para el dueno." "Servicio privado" {
                tags "Analitica"
            }

            graphqlGateway = container "GraphQL Gateway" "Junta informacion de pedidos, productos y pagos en una sola consulta." "Servicio GraphQL" {
                tags "Gateway"

                // C3 - Componentes internos del GraphQL Gateway.
                graphqlEndpoint = component "Endpoint GraphQL" "Recibe las consultas que llegan desde el API Gateway." "Adaptador GraphQL" {
                    tags "EntradaC3"
                }
                queryValidator = component "Validador de consultas" "Valida los limites de profundidad y alias." "Validacion GraphQL" {
                    tags "ControlC3"
                }
                fieldAccess = component "Politica de acceso a campos" "Comprueba permisos para los campos solicitados." "Modulo de autorizacion" {
                    tags "ControlC3"
                }
                resolvers = component "Resolvers de negocio" "Resuelven resumenPedido, misPedidos y reporteVentas." "Resolvers GraphQL" {
                    tags "AplicacionC3"
                }
                serviceConnectors = component "Conectores de subsistemas" "Consultan pedidos, productos y pagos por sus APIs internas." "Adaptadores de integracion" {
                    tags "IntegracionC3"
                }
                responseComposer = component "Compositor de respuestas" "Avisa cuando falta informacion en vez de mostrarla como completa." "Modulo de resultados" {
                    tags "ErrorC3"
                }
            }

            // Una base por servicio (todas en el mismo MongoDB, cada una con su usuario)
            dbIdentity = container "Datos de identidad" "Persistencia de usuarios y sesiones." "MongoDB" {
                tags "BaseDatos"
            }
            dbInventory = container "Datos del menu" "Persistencia de los productos." "MongoDB" {
                tags "BaseDatos"
            }
            dbOrders = container "Datos de pedidos" "Persistencia de los pedidos." "MongoDB" {
                tags "BaseDatos"
            }
            dbClients = container "Datos de clientes" "Persistencia de las fichas." "MongoDB" {
                tags "BaseDatos"
            }
            dbPayments = container "Datos de pagos" "Persistencia de los pagos y avisos." "MongoDB" {
                tags "BaseDatos"
            }
            dbNotificaciones = container "Datos de notificaciones" "Persistencia de los correos enviados." "MongoDB" {
                tags "BaseDatos"
            }
            dbAnalitica = container "Datos de analitica" "Persistencia de las ventas (sin datos personales)." "MongoDB" {
                tags "BaseDatos"
            }
        }

        // Relaciones de contexto (C1).
        visitante -> sistema "Consulta la carta y las ofertas"
        cliente -> sistema "Se registra, compra y sigue sus pedidos"
        cajero -> sistema "Revisa las ventas de la caja web"
        despacho -> sistema "Obtiene las ordenes de despacho y actualiza estados"
        dueno -> sistema "Revisa ventas y disponibilidad de productos"
        admin -> sistema "Mantiene usuarios, clientes y perfiles"
        sistema -> proveedor "Solicita el cobro" "HTTPS/JSON"
        proveedor -> sistema "Avisa el resultado del pago" "Aviso firmado"

        // Relaciones entre los actores, el frontend y los contenedores (C2).
        visitante -> sistema.frontend "Navega la carta" "Navegador web"
        cliente -> sistema.frontend "Arma su pedido y paga" "Navegador web"
        cajero -> sistema.frontend "Revisa la caja" "Navegador web"
        despacho -> sistema.frontend "Gestiona despachos" "Navegador web"
        dueno -> sistema.frontend "Revisa reportes" "Navegador web"
        admin -> sistema.frontend "Administra usuarios" "Navegador web"
        sistema.frontend -> sistema.apiGateway "Envia solicitudes de la interfaz" "HTTPS/JSON"

        sistema.apiGateway -> sistema.authService "Solicita validacion de identidad" "HTTPS/JSON"
        sistema.apiGateway -> sistema.inventory "Enruta catalogo y productos" "HTTPS/JSON"
        sistema.apiGateway -> sistema.orders "Enruta pedidos, despacho y ventas" "HTTPS/JSON"
        sistema.apiGateway -> sistema.clients "Enruta fichas y contacto" "HTTPS/JSON"
        sistema.apiGateway -> sistema.payments "Enruta pagos y el webhook" "HTTPS/JSON"
        sistema.apiGateway -> sistema.graphqlGateway "Enruta consultas GraphQL" "HTTPS/GraphQL"
        sistema.apiGateway -> sistema.analitica "Enruta el reporte de ventas" "HTTPS/JSON"
        sistema.apiGateway -> sistema.notificaciones "Enruta el listado de correos" "HTTPS/JSON"

        sistema.orders -> sistema.inventory "Reserva y libera stock" "gRPC/TLS"
        sistema.orders -> sistema.notificaciones "Envia la boleta del pedido pagado" "HTTPS/JSON"
        sistema.orders -> sistema.analitica "Envia la venta (sin datos personales)" "HTTPS/JSON"
        sistema.payments -> sistema.orders "Confirma que el pedido esta pagado" "HTTPS/JSON"
        sistema.payments -> proveedor "Solicita el cobro" "HTTPS/JSON"
        proveedor -> sistema.apiGateway "Avisa el resultado del pago" "HTTPS/JSON firmado"
        sistema.authService -> sistema.clients "Crea la ficha del cliente" "HTTPS/JSON"
        sistema.authService -> sistema.notificaciones "Manda el codigo de verificacion" "HTTPS/JSON"
        sistema.notificaciones -> sistema.clients "Pide nombre y correo del cliente" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.orders "Consulta pedidos autorizados" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.inventory "Consulta productos por lote" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.payments "Consulta pagos por pedido" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.clients "Consulta datos del cliente" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.analitica "Consulta el reporte" "HTTPS/JSON"

        sistema.authService -> sistema.dbIdentity "Lee y escribe usuarios y sesiones" "Acceso a datos"
        sistema.inventory -> sistema.dbInventory "Lee y escribe productos y reservas" "Acceso a datos"
        sistema.orders -> sistema.dbOrders "Lee y escribe pedidos" "Acceso a datos"
        sistema.clients -> sistema.dbClients "Lee y escribe fichas" "Acceso a datos"
        sistema.payments -> sistema.dbPayments "Lee y escribe pagos y avisos" "Acceso a datos"
        sistema.notificaciones -> sistema.dbNotificaciones "Guarda los correos enviados" "Acceso a datos"
        sistema.analitica -> sistema.dbAnalitica "Guarda y agrega ventas" "Acceso a datos"
        sistema.apiGateway -> sistema.secretManager "Lee sus secretos" "HTTPS + token propio"
        sistema.authService -> sistema.secretManager "Lee sus secretos" "HTTPS + token propio"
        sistema.orders -> sistema.secretManager "Lee sus secretos" "HTTPS + token propio"
        sistema.payments -> sistema.secretManager "Lee sus secretos" "HTTPS + token propio"

        // C3: relaciones internas del API Gateway.
        sistema.frontend -> sistema.apiGateway.httpEntry "Envia la solicitud" "HTTPS/JSON"
        sistema.apiGateway.httpEntry -> sistema.apiGateway.routeTable "Busca si la ruta existe"
        sistema.apiGateway.routeTable -> sistema.apiGateway.rateLimiter "Ruta permitida"
        sistema.apiGateway.rateLimiter -> sistema.apiGateway.identityFilter "Si la ruta no es publica"
        sistema.apiGateway.identityFilter -> sistema.authService "Valida el token" "HTTPS/JSON"
        sistema.apiGateway.identityFilter -> sistema.apiGateway.dispatcher "Token y perfil validos"
        sistema.apiGateway.dispatcher -> sistema.inventory "Reenvia" "HTTPS/JSON"
        sistema.apiGateway.dispatcher -> sistema.orders "Reenvia" "HTTPS/JSON"
        sistema.apiGateway.dispatcher -> sistema.payments "Reenvia" "HTTPS/JSON"
        sistema.apiGateway.dispatcher -> sistema.graphqlGateway "Reenvia" "HTTPS/GraphQL"
        sistema.apiGateway.dispatcher -> sistema.apiGateway.errorMapper "El servicio fallo o no responde"
        sistema.apiGateway.dispatcher -> sistema.secretManager "Obtiene secretos" "HTTPS + token propio"

        // C3: validacion y agregacion GraphQL.
        sistema.apiGateway -> sistema.graphqlGateway.graphqlEndpoint "Remite operaciones GraphQL" "HTTPS/GraphQL"
        sistema.graphqlGateway.graphqlEndpoint -> sistema.graphqlGateway.queryValidator "Valida la consulta"
        sistema.graphqlGateway.queryValidator -> sistema.graphqlGateway.resolvers "Consulta valida"
        sistema.graphqlGateway.resolvers -> sistema.graphqlGateway.fieldAccess "Revisa campos restringidos"
        sistema.graphqlGateway.resolvers -> sistema.graphqlGateway.serviceConnectors "Pide datos agregados"
        sistema.graphqlGateway.serviceConnectors -> sistema.orders "Pedidos" "HTTPS/JSON"
        sistema.graphqlGateway.serviceConnectors -> sistema.inventory "Productos por lote" "HTTPS/JSON"
        sistema.graphqlGateway.serviceConnectors -> sistema.payments "Pagos por pedido" "HTTPS/JSON"
        sistema.graphqlGateway.resolvers -> sistema.graphqlGateway.responseComposer "Datos y avisos"
        sistema.graphqlGateway.queryValidator -> sistema.graphqlGateway.responseComposer "Consulta rechazada"

        // C3: relaciones internas del Auth Service.
        sistema.apiGateway -> sistema.authService.identityApi "Login, registro, introspect" "HTTPS/JSON"
        sistema.authService.identityApi -> sistema.authService.credentialsVerifier "Verifica la clave"
        sistema.authService.identityApi -> sistema.authService.sessionManager "Crea o revisa la sesion"
        sistema.authService.identityApi -> sistema.authService.emailVerification "Registro y codigo"
        sistema.authService.identityApi -> sistema.authService.usersAdmin "Mantenedor (solo admin)"
        sistema.authService.credentialsVerifier -> sistema.authService.identityRepo "Busca el usuario"
        sistema.authService.sessionManager -> sistema.authService.identityRepo "Guarda el hash del token"
        sistema.authService.emailVerification -> sistema.authService.identityRepo "Guarda el hash del codigo"
        sistema.authService.emailVerification -> sistema.notificaciones "Envia el codigo" "HTTPS/JSON"
        sistema.authService.usersAdmin -> sistema.authService.identityRepo "Cambia perfiles"
        sistema.authService.identityRepo -> sistema.dbIdentity "Lee y escribe" "Acceso a datos"
        sistema.authService.secretsClient -> sistema.secretManager "Obtiene sus secretos" "HTTPS + token propio"

        // C3: relaciones internas de Pedidos.
        sistema.apiGateway -> sistema.orders.ordersApi "Operaciones de pedidos" "HTTPS/JSON"
        sistema.payments -> sistema.orders.ordersApi "Confirma el pago" "HTTPS/JSON"
        sistema.orders.ordersApi -> sistema.orders.accessPolicy "Revisa perfil y propiedad"
        sistema.orders.accessPolicy -> sistema.orders.orderWorkflow "Operacion autorizada"
        sistema.orders.ordersApi -> sistema.orders.paidControl "Aviso de pago"
        sistema.orders.paidControl -> sistema.orders.ordersRepo "Busca si ya estaba pagado"
        sistema.orders.paidControl -> sistema.orders.notifier "Pedido recien pagado"
        sistema.orders.orderWorkflow -> sistema.orders.inventoryAdapter "Reservar / liberar stock"
        sistema.orders.orderWorkflow -> sistema.orders.ordersRepo "Guarda pedido y estado"
        sistema.orders.inventoryAdapter -> sistema.inventory "ReservarStock / LiberarStock" "gRPC/TLS"
        sistema.orders.notifier -> sistema.notificaciones "Boleta" "HTTPS/JSON"
        sistema.orders.notifier -> sistema.analitica "Venta" "HTTPS/JSON"
        sistema.orders.ordersRepo -> sistema.dbOrders "Lee y escribe" "Acceso a datos"

        // Respuestas (para las vistas dinamicas de ida y vuelta).
        sistema.dbInventory -> sistema.inventory "Devuelve productos" "Acceso a datos"
        sistema.inventory -> sistema.apiGateway "Responde el catalogo" "HTTPS/JSON"
        sistema.apiGateway -> sistema.frontend "Respuesta o error controlado" "HTTPS/JSON"
        sistema.frontend -> visitante "Muestra la carta o el error"
        sistema.frontend -> cliente "Muestra el resultado"
        sistema.authService -> sistema.apiGateway "Responde si el token esta activo" "HTTPS/JSON"
        sistema.inventory -> sistema.orders "Lineas con el precio vigente" "gRPC/TLS"
        sistema.dbOrders -> sistema.orders "Devuelve el pedido" "Acceso a datos"
        sistema.orders -> sistema.apiGateway "Responde la operacion" "HTTPS/JSON"
        sistema.orders -> sistema.payments "Responde (pagado / ya estaba pagado)" "HTTPS/JSON"
        sistema.dbPayments -> sistema.payments "Indica si el event_id ya existia" "Acceso a datos"
        sistema.payments -> sistema.apiGateway "Responde al webhook" "HTTPS/JSON"
        sistema.apiGateway -> proveedor "Responde al webhook" "HTTPS/JSON"
        sistema.orders -> sistema.graphqlGateway "Pedidos autorizados" "HTTPS/JSON"
        sistema.inventory -> sistema.graphqlGateway "Productos" "HTTPS/JSON"
        sistema.payments -> sistema.graphqlGateway "Pagos" "HTTPS/JSON"
        sistema.graphqlGateway -> sistema.apiGateway "Resultado agregado o con avisos" "HTTPS/GraphQL"
        sistema.graphqlGateway.queryValidator -> sistema.graphqlGateway.graphqlEndpoint "Rechaza la consulta"
        sistema.graphqlGateway.graphqlEndpoint -> sistema.apiGateway "Error de validacion" "HTTPS/GraphQL"

        // Despliegue local: los servicios y Vault corren en el equipo con iniciar.py; MongoDB en Docker.
        local = deploymentEnvironment "Local" {
            deploymentNode "Dispositivo del usuario" "Equipo con navegador web o Postman." "Equipo cliente" {
                tags "ZonaCliente"
                deploymentNode "Navegador web" "Ejecuta el frontend responsivo." "Navegador" {
                    containerInstance sistema.frontend
                }
            }
            deploymentNode "Equipo de desarrollo" "Equipo local donde iniciar.py levanta todos los procesos." "Estacion de trabajo" {
                tags "ZonaEntorno"
                deploymentNode "Proceso de entrada" "API Gateway local (HTTPS, puerto 8000)." "Proceso local" {
                    tags "ZonaPublica"
                    containerInstance sistema.apiGateway
                }
                deploymentNode "Procesos privados" "Servicios internos con HTTPS; solo aceptan llamadas del mismo equipo y con su secreto." "Procesos locales" {
                    tags "ZonaPrivada"
                    containerInstance sistema.authService
                    containerInstance sistema.inventory
                    containerInstance sistema.orders
                    containerInstance sistema.clients
                    containerInstance sistema.payments
                    containerInstance sistema.notificaciones
                    containerInstance sistema.analitica
                    containerInstance sistema.graphqlGateway
                }
                deploymentNode "Contenedor de MongoDB" "MongoDB en Docker (solo 127.0.0.1:27018), un usuario por base y datos ficticios." "Docker" {
                    tags "ZonaDatos"
                    containerInstance sistema.dbIdentity
                    containerInstance sistema.dbInventory
                    containerInstance sistema.dbOrders
                    containerInstance sistema.dbClients
                    containerInstance sistema.dbPayments
                    containerInstance sistema.dbNotificaciones
                    containerInstance sistema.dbAnalitica
                }
                deploymentNode "Secretos locales" "Vault en modo desarrollo con TLS y secretos de prueba." "HashiCorp Vault" {
                    tags "ZonaSecretos"
                    containerInstance sistema.secretManager
                }
                deploymentNode "Proveedor simulado" "Simulador del proveedor de pagos externo." "Proceso local" {
                    tags "ZonaExterna"
                    softwareSystemInstance proveedor
                }
            }
        }
    }

    views {
        systemContext sistema "C1_Contexto" "Contexto de negocio: actores y dependencias externas." {
            title "C1 - Contexto"
            include *
            autoLayout lr
        }

        container sistema "C2_Contenedores" "Aplicaciones y almacenes de datos de la Plataforma Aroma & Cafe." {
            title "C2 - Contenedores"
            include *
            autoLayout lr
        }

        container sistema "C2_Catalogo" "Recorrido estructural relacionado con la consulta del menu." {
            include visitante sistema.frontend sistema.apiGateway sistema.inventory sistema.dbInventory
            autoLayout lr
        }

        container sistema "C2_Pedidos" "Recorrido estructural relacionado con el pedido y el pago." {
            include cliente sistema.frontend sistema.apiGateway sistema.authService sistema.orders sistema.inventory sistema.payments proveedor sistema.notificaciones sistema.analitica sistema.dbOrders sistema.dbPayments
            autoLayout lr
        }

        component sistema.apiGateway "C3_API_Gateway" "Componentes internos del punto de entrada HTTP." {
            title "C3 - API Gateway"
            include *
            autoLayout lr
        }

        component sistema.graphqlGateway "C3_GraphQL" "Validacion, autorizacion y agregacion de datos." {
            title "C3 - GraphQL Gateway"
            include *
            autoLayout lr
        }

        component sistema.authService "C3_Auth_Service" "Identidad, sesiones, credenciales y secretos." {
            title "C3 - Auth Service"
            include *
            autoLayout lr
        }

        component sistema.orders "C3_Orders" "Autorizacion, reglas, pagos repetidos y persistencia de pedidos." {
            title "C3 - Pedidos"
            include *
            autoLayout lr
        }

        dynamic sistema "D_F01_Exito" "Lectura desde el navegador hasta el menu y regreso." {
            title "F01 - Consulta de menu: exito"
            1: visitante -> sistema.frontend "Abre el menu"
            2: sistema.frontend -> sistema.apiGateway "GET /products"
            3: sistema.apiGateway -> sistema.inventory "Consulta el menu"
            4: sistema.inventory -> sistema.dbInventory "Busca productos activos"
            5: sistema.dbInventory -> sistema.inventory "Devuelve productos"
            6: sistema.inventory -> sistema.apiGateway "Responde productos disponibles"
            7: sistema.apiGateway -> sistema.frontend "Devuelve el listado"
            8: sistema.frontend -> visitante "Muestra el menu"
            autoLayout lr
        }

        dynamic sistema "D_F01_Recuperacion" "El menu no responde, se muestra un error y se reintenta cuando vuelve." {
            title "F01 - Fallo controlado y recuperacion"
            1: visitante -> sistema.frontend "Abre el menu"
            2: sistema.frontend -> sistema.apiGateway "GET /products"
            3: sistema.apiGateway -> sistema.inventory "Consulta el menu; no responde"
            4: sistema.apiGateway -> sistema.frontend "Error controlado"
            5: sistema.frontend -> visitante "Muestra el error sin datos falsos"
            6: visitante -> sistema.frontend "Reintenta mas tarde"
            7: sistema.frontend -> sistema.apiGateway "GET /products"
            8: sistema.apiGateway -> sistema.inventory "Consulta el menu recuperado"
            9: sistema.inventory -> sistema.dbInventory "Busca productos"
            10: sistema.dbInventory -> sistema.inventory "Devuelve productos"
            11: sistema.inventory -> sistema.apiGateway "Responde el listado"
            12: sistema.apiGateway -> sistema.frontend "Devuelve el listado"
            13: sistema.frontend -> visitante "Muestra los productos recuperados"
            autoLayout lr
        }

        dynamic sistema "D_F02_Exito" "Pedido con validacion de identidad, reserva de stock y persistencia." {
            title "F02 - Registro de pedido: exito"
            1: cliente -> sistema.frontend "Confirma el carrito"
            2: sistema.frontend -> sistema.apiGateway "POST /orders"
            3: sistema.apiGateway -> sistema.authService "POST /introspect"
            4: sistema.authService -> sistema.apiGateway "Identidad valida"
            5: sistema.apiGateway -> sistema.orders "Envia el pedido con la identidad"
            6: sistema.orders -> sistema.inventory "Reserva stock (gRPC)"
            7: sistema.inventory -> sistema.orders "Devuelve precios vigentes"
            8: sistema.orders -> sistema.dbOrders "Guarda el pedido"
            9: sistema.dbOrders -> sistema.orders "Confirmado"
            10: sistema.orders -> sistema.apiGateway "Pedido creado"
            11: sistema.apiGateway -> sistema.frontend "Pedido creado"
            12: sistema.frontend -> cliente "Muestra el pedido para pagar"
            autoLayout lr
        }

        // No usamos clave de idempotencia en POST /orders; el reintento que dibujamos es el aviso de pago repetido.
        dynamic sistema "D_F02_Reintento" "El proveedor manda el mismo aviso dos veces y no se procesa doble." {
            title "F02 - Aviso de pago repetido: sin duplicacion"
            1: proveedor -> sistema.apiGateway "Reenvia el mismo webhook firmado"
            2: sistema.apiGateway -> sistema.payments "Entrega el aviso"
            3: sistema.payments -> sistema.dbPayments "Registra el aviso"
            4: sistema.dbPayments -> sistema.payments "El aviso ya existia"
            5: sistema.payments -> sistema.apiGateway "Responde sin repetir el pago"
            6: sistema.apiGateway -> proveedor "Confirma la recepcion"
            autoLayout lr
        }

        dynamic sistema.orders "D_F02_Pago_repetido_C3" "Detalle de un pago repetido al interior de Pedidos." {
            title "F02 - Pago repetido dentro de Pedidos"
            1: sistema.payments -> sistema.orders.ordersApi "Confirma el pago"
            2: sistema.orders.ordersApi -> sistema.orders.paidControl "Revisa el pedido"
            3: sistema.orders.paidControl -> sistema.orders.ordersRepo "Busca el pedido"
            4: sistema.orders.ordersRepo -> sistema.dbOrders "El pedido ya estaba pagado"
            5: sistema.orders.paidControl -> sistema.orders.ordersApi "Responde sin generar otra boleta"
            autoLayout lr
        }

        dynamic sistema "D_F03_Propio" "Lectura autorizada de un pedido propio." {
            title "F03 - Consulta protegida: pedido propio"
            1: cliente -> sistema.frontend "Abre su pedido"
            2: sistema.frontend -> sistema.apiGateway "GET /orders/{id}"
            3: sistema.apiGateway -> sistema.authService "Comprueba la sesion"
            4: sistema.authService -> sistema.apiGateway "Sesion valida"
            5: sistema.apiGateway -> sistema.orders "Consulta con la identidad"
            6: sistema.orders -> sistema.dbOrders "Busca el pedido"
            7: sistema.dbOrders -> sistema.orders "Pedido del mismo cliente"
            8: sistema.orders -> sistema.apiGateway "Responde el pedido"
            9: sistema.apiGateway -> sistema.frontend "Devuelve el pedido"
            10: sistema.frontend -> cliente "Muestra estado y total"
            autoLayout lr
        }

        dynamic sistema "D_F03_Ajeno" "Prueba negativa de autorizacion por dueno del pedido." {
            title "F03 - Consulta protegida: pedido ajeno"
            1: cliente -> sistema.frontend "Intenta abrir un pedido de otra persona"
            2: sistema.frontend -> sistema.apiGateway "GET /orders/{idAjeno}"
            3: sistema.apiGateway -> sistema.authService "Comprueba la sesion"
            4: sistema.authService -> sistema.apiGateway "Sesion valida (no da acceso al pedido)"
            5: sistema.apiGateway -> sistema.orders "Consulta con la identidad"
            6: sistema.orders -> sistema.dbOrders "Busca el pedido"
            7: sistema.dbOrders -> sistema.orders "El dueno es otro usuario"
            8: sistema.orders -> sistema.apiGateway "No revela el pedido ajeno"
            9: sistema.apiGateway -> sistema.frontend "Pedido no encontrado"
            10: sistema.frontend -> cliente "Muestra el rechazo sin datos ajenos"
            autoLayout lr
        }

        dynamic sistema "D_F03_Expirada" "El gateway rechaza la solicitud antes de llegar a Pedidos." {
            title "F03 - Sesion expirada: rechazo temprano"
            1: cliente -> sistema.frontend "Consulta un pedido con la sesion vencida"
            2: sistema.frontend -> sistema.apiGateway "GET /orders/{id}"
            3: sistema.apiGateway -> sistema.authService "Comprueba la sesion"
            4: sistema.authService -> sistema.apiGateway "Sesion vencida"
            5: sistema.apiGateway -> sistema.frontend "Rechaza la solicitud"
            6: sistema.frontend -> cliente "Pide iniciar sesion de nuevo"
            autoLayout lr
        }

        dynamic sistema "D_F04_GraphQL_Exito" "La pantalla muestra informacion combinada de pedidos, productos y pagos." {
            title "F04 - GraphQL: agregacion exitosa"
            1: cliente -> sistema.frontend "Abre el detalle de su pedido"
            2: sistema.frontend -> sistema.apiGateway "POST /graphql resumenPedido"
            3: sistema.apiGateway -> sistema.graphqlGateway "Remite la consulta con la identidad"
            4: sistema.graphqlGateway -> sistema.orders "Consulta el pedido"
            5: sistema.orders -> sistema.graphqlGateway "Pedido"
            6: sistema.graphqlGateway -> sistema.inventory "Consulta los productos"
            7: sistema.inventory -> sistema.graphqlGateway "Nombres y disponibilidad"
            8: sistema.graphqlGateway -> sistema.payments "Consulta el pago"
            9: sistema.payments -> sistema.graphqlGateway "Estado del pago"
            10: sistema.graphqlGateway -> sistema.apiGateway "Respuesta combinada"
            11: sistema.apiGateway -> sistema.frontend "Devuelve la respuesta"
            12: sistema.frontend -> cliente "Muestra pedido, productos y pago"
            autoLayout lr
        }

        dynamic sistema "D_F04_GraphQL_Parcial" "No se presenta una respuesta parcial como informacion completa." {
            title "F04 - GraphQL: respuesta parcial"
            1: cliente -> sistema.frontend "Abre el detalle de su pedido"
            2: sistema.frontend -> sistema.apiGateway "POST /graphql"
            3: sistema.apiGateway -> sistema.graphqlGateway "Remite la consulta"
            4: sistema.graphqlGateway -> sistema.orders "Consulta el pedido"
            5: sistema.orders -> sistema.graphqlGateway "Pedido"
            6: sistema.graphqlGateway -> sistema.inventory "Consulta los productos; no responde"
            7: sistema.graphqlGateway -> sistema.apiGateway "Datos del pedido con aviso de respuesta incompleta"
            8: sistema.apiGateway -> sistema.frontend "Devuelve datos y aviso"
            9: sistema.frontend -> cliente "Avisa que faltan datos"
            autoLayout lr
        }

        dynamic sistema.graphqlGateway "D_F04_GraphQL_Limite_C3" "Rechazo antes de ejecutar resolvers o consultar servicios privados." {
            title "F04 - GraphQL: consulta excede el limite"
            1: sistema.apiGateway -> sistema.graphqlGateway.graphqlEndpoint "Consulta con demasiados alias"
            2: sistema.graphqlGateway.graphqlEndpoint -> sistema.graphqlGateway.queryValidator "Valida limites"
            3: sistema.graphqlGateway.queryValidator -> sistema.graphqlGateway.graphqlEndpoint "Rechaza la consulta"
            4: sistema.graphqlGateway.graphqlEndpoint -> sistema.apiGateway "Error de validacion"
            autoLayout lr
        }

        deployment sistema local "DEP_Local" "Todos los servicios del caso en un equipo local." {
            title "Despliegue - Local"
            include *
            autoLayout lr
        }

        styles {
            element "Deployment Node" {
                background #E9EFF5
                color #213F56
                stroke #8FA5B7
            }
            element "Infrastructure Node" {
                shape roundedbox
                background #EDF0F3
                color #334454
            }
            element "ZonaCliente" {
                background #F1F5F9
                color #173B5D
            }
            element "ZonaEntorno" {
                background #F4F6F8
                color #213F56
            }
            element "ZonaPublica" {
                background #DCEAF7
                color #173B5D
            }
            element "ZonaPrivada" {
                background #E5EEE8
                color #20513D
            }
            element "ZonaDatos" {
                background #ECEAF2
                color #463D64
            }
            element "ZonaSecretos" {
                background #EEE5E1
                color #68483C
            }
            element "ZonaExterna" {
                background #F1EDE7
                color #544633
            }
            element "ZonaLocal" {
                background #F0F3F6
                color #243F56
            }
            element "Person" {
                shape person
                background #56718A
                color #FFFFFF
            }
            element "Software System" {
                shape roundedbox
                background #0C527A
                color #FFFFFF
            }
            element "SistemaEvaluado" {
                background #173B5D
                color #FFFFFF
            }
            element "Container" {
                shape roundedbox
                background #E3ECF5
                color #173B5D
            }
            element "Frontend" {
                shape webbrowser
                background #CDE5F7
                color #153E5B
            }
            element "Gateway" {
                background #2B6289
                color #FFFFFF
            }
            element "Seguridad" {
                background #3F6171
                color #FFFFFF
            }
            element "Privado" {
                background #D5E8EF
                color #173B5D
            }
            element "BaseDatos" {
                shape cylinder
                background #E5EAF0
                color #243F56
            }
            element "SistemaExterno" {
                background #F1EDE7
                color #544633
                stroke #A89D8A
            }
            element "Analitica" {
                background #E7E0F2
                color #453166
            }
            element "Component" {
                shape roundedbox
                background #EDF3F7
                color #173B5D
            }
            element "EntradaC3" {
                background #D3E9F7
                color #153F62
            }
            element "ControlC3" {
                background #DBE4EC
                color #213F56
            }
            element "AplicacionC3" {
                background #D7E9DE
                color #20533E
            }
            element "IntegracionC3" {
                background #E9E2F2
                color #4A3666
            }
            element "PersistenciaC3" {
                background #E9EBEE
                color #334454
            }
            element "ErrorC3" {
                background #F2E6DB
                color #70462C
            }
            relationship "Relationship" {
                color #60758A
                thickness 2
            }
        }
    }
}
