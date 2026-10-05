from dataclasses import dataclass
from decimal import Decimal
@dataclass
class DetalleVenta:
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
