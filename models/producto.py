from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Producto:
    id: int | None
    nombre: str
    categoria_id: int | None = None
    stock: Decimal = Decimal('0')
    cpp: Decimal = Decimal('0')
    precio: Decimal = Decimal('0')
    recargo_pct: Decimal = Decimal('25')
    stock_minimo: Decimal = Decimal('5')
    caduca: bool = False
