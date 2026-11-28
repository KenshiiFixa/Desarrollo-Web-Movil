# 10. Diagramas

El modelo C4 está en `Backend/docs/arquitectura/AromaCafe.dsl` (Structurizr DSL). En esta unidad se agregó la vista de despliegue
**DEP_Docker**, que muestra dónde corre cada componente; las llamadas entre servicios están en las vistas C2 y dinámicas. Las demás vistas
vienen de la Unidad 2 y siguen siendo válidas.

## Vistas del modelo

| Archivo | Vista del DSL | Qué muestra |
|---|---|---|
| `diagramas/01-contenedores.png` | `C2_Contenedores` | Frontend, gateway, Auth, Vault, servicios privados, GraphQL y bases |
| `diagramas/02-despliegue-docker.png` | `DEP_Docker` | Contenedores, redes pública y privada, puertos publicados |
| `diagramas/03-gateway-seguridad.png` | `C3_API_Gateway` | Límite de solicitudes, tabla de rutas, validación con Auth y secretos |
| `diagramas/04-auth.png` | `C3_Auth_Service` | Sesiones, credenciales y verificación del secreto |
| `diagramas/05-pedido.png` | `D_F02_Exito` | Recorrido de un pedido: gateway → Auth → orders → inventory (gRPC) → MongoDB |
| `diagramas/06-pedido-ajeno.png` | `D_F03_Ajeno` | Rechazo de un pedido ajeno |
| `diagramas/07-graphql-parcial.png` | `D_F04_GraphQL_Parcial` | GraphQL con una dependencia caída: respuesta parcial con aviso |

## Diagramas

### C2 – Contenedores
![Contenedores](diagramas/01-contenedores.png)

### Despliegue en Docker: redes, contenedores y la única entrada desde el navegador
![Despliegue Docker](diagramas/02-despliegue-docker.png)

### C3 – API Gateway: entrada, límite de solicitudes, tabla de rutas, filtro de acceso con Auth y secretos
![API Gateway](diagramas/03-gateway-seguridad.png)

### Pedido: registro exitoso (gateway → Auth → orders → inventory por gRPC → MongoDB)
![Registro de pedido](diagramas/05-pedido.png)

### Pedido ajeno: rechazo sin revelar datos
![Pedido ajeno](diagramas/06-pedido-ajeno.png)

### GraphQL con una dependencia caída: respuesta parcial con aviso
![GraphQL parcial](diagramas/07-graphql-parcial.png)

### C3 – Auth Service: sesiones, credenciales y secretos
![Auth Service](diagramas/04-auth.png)

## Recorrido de una solicitud con sesión (vista resumida)

```mermaid
sequenceDiagram
    participant N as Navegador (frontend)
    participant G as API Gateway
    participant A as Auth Service
    participant V as Vault
    participant S as Servicio (ej. orders)
    participant I as inventory (gRPC)
    participant M as MongoDB
    Note over G,S: Cada servicio leyó su secreto desde Vault al iniciar
    N->>G: POST /api/v1/orders + Bearer (CORS: solo localhost:8080)
    G->>G: Tabla de rutas (S09), límite por IP, X-Request-ID
    G->>A: POST /introspect + secreto gateway→auth
    A->>M: busca la sesión (auth.sesiones)
    A-->>G: token válido, rol=cliente
    G->>S: POST /orders + secreto gateway→orders + identidad
    S->>S: verifica el secreto (403 si no coincide)
    S->>I: ReservarStock (gRPC con TLS, plazo 3 s)
    I->>M: descuenta stock (inventory.productos)
    S->>M: guarda el pedido (orders.pedidos)
    S-->>G: 201 pedido
    G-->>N: 201 + X-Request-ID
```
