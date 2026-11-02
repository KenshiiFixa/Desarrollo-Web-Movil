# Productor STOMP - Semana de mensajería
# Base: código entregado por el profesor en clases.
# Cambios míos: corrección de errores (ver "CORRECCIÓN") y comentarios explicativos.
#
# Ejemplos de uso:
#   Texto libre:   python productor.py --formato texto --mensaje "Hola mundo Stomp"
#   Ancho fijo:    python productor.py --formato fijo --id 123 --cliente "Ernesto Vivanco" --monto 123.45
#   XML:           python productor.py --formato xml  --id 123 --cliente "Ernesto Vivanco" --monto 123.45
#   JSON:          python productor.py --formato json --id 123 --cliente "Ernesto Vivanco" --monto 123.45

import argparse
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

import stomp

DESTINO = "/queue/pedidos"   # cola a la que se envían los pedidos


def construir_mensaje(formato: str, pedido: dict, texto: str) -> tuple[str, str]:
    """Convierte el pedido al formato pedido. Devuelve (cuerpo, tipo MIME)."""
    if formato == "texto":
        return texto, "text/plain; charset=utf-8"

    if formato == "fijo":
        # Contrato de ancho fijo = 36 caracteres: ID[6] + CLIENTE[20] + MONTO[10]
        identificador = str(pedido["id"])
        cliente = str(pedido["cliente"])
        monto = Decimal(pedido["monto"])
        monto_campo = f"{monto:010.2f}"          # ej: 123.45 -> "0000123.45"
        if not (identificador.isascii() and identificador.isdigit() and len(identificador) <= 6):
            raise ValueError("En formato fijo, --id debe tener hasta 6 digitos ASCII")
        if len(cliente) > 20 or any(ord(c) > 127 for c in cliente):
            raise ValueError("En formato fijo, --cliente admite hasta 20 caracteres ASCII")
        if monto < 0 or len(monto_campo) != 10:
            raise ValueError("En formato fijo, --monto debe estar entre 0 y 99999999.99")
        # zfill rellena el id con ceros a la izquierda; :<20 rellena el cliente con espacios
        return f"{identificador.zfill(6)}{cliente:<20}{monto_campo}", "text/plain; charset=utf-8"

    if formato == "json":
        return json.dumps(pedido, ensure_ascii=False), "application/json; charset=utf-8"

    if formato == "xml":
        raiz = ET.Element("pedido")
        for clave, valor in pedido.items():
            ET.SubElement(raiz, clave).text = str(valor)
        return ET.tostring(raiz, encoding="unicode"), "application/xml; charset=utf-8"

    raise ValueError(f"Formato desconocido: {formato}")


def main():
    parser = argparse.ArgumentParser(description="Productor STOMP")
    parser.add_argument("--formato", choices=["texto", "fijo", "xml", "json"], required=True)
    parser.add_argument("--mensaje", default="Hola desde el productor STOMP")
    parser.add_argument("--id", default="123")
    parser.add_argument("--cliente", default="Ed jobs")
    parser.add_argument("--monto", default="123.45")
    parser.add_argument("--host", default="127.0.0.1")
    # CORRECCIÓN 1: el puerto debe ser un número; sin type=int llegaba como texto si se escribía por consola.
    parser.add_argument("--port", type=int, default=61613)
    parser.add_argument("--usuario", default="demo")
    parser.add_argument("--clave", default="demo123")
    args = parser.parse_args()

    # Validar que el monto sea un número finito
    try:
        monto = Decimal(args.monto)
        if not monto.is_finite():
            raise ValueError("El monto debe ser un número finito")
    except (InvalidOperation, ValueError):   # antes solo capturaba InvalidOperation
        parser.error(f"Monto no válido: {args.monto}")

    pedido = {"id": args.id, "cliente": args.cliente, "monto": str(monto)}

    # CORRECCIÓN 2: la variable se llamaba "excc" pero se usaba "exc" (NameError al fallar la validación).
    try:
        cuerpo, mime = construir_mensaje(args.formato, pedido, args.mensaje)
    except ValueError as exc:
        parser.error(str(exc))

    # Enviar el mensaje al broker
    conexion = stomp.Connection12([(args.host, args.port)], vhost="/")
    try:
        conexion.connect(args.usuario, args.clave, wait=True)
        conexion.send(
            destination=DESTINO,
            body=cuerpo,
            headers={
                "content-type": mime,
                "x-formato": args.formato,   # el consumidor usa este encabezado para saber cómo leerlo
                "persistent": "true",        # el broker guarda el mensaje aunque se reinicie
            },
        )
        print(f"Mensaje enviado a {DESTINO} (formato={args.formato}):\n{cuerpo}")
    finally:
        if conexion.is_connected():
            conexion.disconnect()


if __name__ == "__main__":
    main()
