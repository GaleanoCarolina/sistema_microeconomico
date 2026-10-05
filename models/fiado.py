from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Fiado:
    id: int | None
    cliente_id: int
    venta_id: int
    saldo: Decimal
