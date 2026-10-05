from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Abono:
    id: int | None
    fiado_id: int
    monto: Decimal
