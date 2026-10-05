from dataclasses import dataclass
from decimal import Decimal
@dataclass
class DetalleCompra:
    producto_id: int
    cantidad: Decimal
    costo_unitario: Decimal
    vencimiento: str | None = None
