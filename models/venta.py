from dataclasses import dataclass, field
from decimal import Decimal
@dataclass
class Venta:
    id: int | None
    total: Decimal = Decimal('0')
    cobrado: Decimal = Decimal('0')
    fiado: Decimal = Decimal('0')
    detalles: list = field(default_factory=list)
