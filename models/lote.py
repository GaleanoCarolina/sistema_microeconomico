from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Lote:
    id: int | None
    producto_id: int
    restante: Decimal
    costo_unitario: Decimal
    vencimiento: str | None = None
