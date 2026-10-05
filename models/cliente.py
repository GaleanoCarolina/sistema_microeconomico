from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Cliente:
    id: int | None
    nombre: str
    telefono: str = ''
    direccion: str = ''
    observaciones: str = ''
    limite_credito: Decimal = Decimal('0')
