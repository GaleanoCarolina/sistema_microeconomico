from dataclasses import dataclass
@dataclass
class Proveedor:
    id: int | None
    nombre: str
    telefono: str = ''
    plazo_dias: int = 4
