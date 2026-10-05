from dataclasses import dataclass
from typing import Optional

@dataclass
class Recomendacion:
    producto_id: int
    producto: str
    accion: str
    prioridad: str
    motivo: str
    detalle: str
    confianza: str
    cantidad_sugerida: Optional[float] = None
    proveedor_id: Optional[int] = None
    costo_estimado_cents: Optional[int] = None
    calculo: Optional[str] = None
