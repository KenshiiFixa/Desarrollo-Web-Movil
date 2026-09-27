import os
import secrets

from fastapi import (FastAPI, Header, HTTPException, Depends)

app = FastAPI(
    title = "Protected Backend API en",
    description = "API ubicada y enrutada por API gateway"
)

INTERNAL_GATEWAY_SECRET = os.getenv(
    "INTERNAL_GATEWAY_SECRET"
)
if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no configurado.")

def verify_gateway(x_gateway_secret: str = Header(default="")):
    valid_key = secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET)
    if not valid_key:
        raise HTTPException(
            status_code=403,
            detail="No autorizado"
        )

@app.get(
        "/health",
        dependencies=[Depends(verify_gateway)]
        )
def health():
    return {
        "status": "ok",
        "service": "Backend API"
    }

@app.get(
        "/products",
        dependencies=[Depends(verify_gateway)]
        )
def products(
    x_authenticated_client: str | None = Header(default=None)
):
    return {
        "x_authenticated_client": x_authenticated_client,
        "products": [
            {"id": 1, "name": "Notebook", "price": 900000},
            {"id": 2, "name": "Monitor", "price": 250000},
        ]
    }

@app.get(
        "/orders",
        dependencies=[Depends(verify_gateway)]
        )
def orders(
    x_authenticated_client: str | None = Header(default=None)
):
    return {
        "authenticated_client": x_authenticated_client,
        "orders": [
            {"id": 1001, "status": "paid"},
            {"id": 1002, "status": "pending"},
        ]
    }