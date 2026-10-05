from dataclasses import dataclass, field
from decimal import Decimal
@dataclass
class Compra:
    id: int | None
    proveedor_id: int | None = None
    total: Decimal = Decimal('0')
    detalles: list = field(default_factory=list)
