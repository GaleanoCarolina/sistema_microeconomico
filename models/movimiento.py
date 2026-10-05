from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Movimiento:
    producto_id: int
    tipo: str
    cantidad: Decimal
    referencia: str = ''
