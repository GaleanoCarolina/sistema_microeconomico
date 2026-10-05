from pathlib import Path
from config.settings import DB_PATH
from database.migrate import migrate


class ResetService:
    """Reinicia por completo la base de datos del negocio.

    No conserva ventas, compras, productos, clientes, fiados, lotes ni
    configuración. Después crea una base nueva con el esquema y valores por
    defecto. No toca los respaldos externos existentes.
    """
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or DB_PATH)

    def reset_all(self):
        path = self.db_path
        # SQLite WAL puede dejar archivos auxiliares junto a la base.
        for candidate in (path, Path(str(path) + '-wal'), Path(str(path) + '-shm')):
            try:
                if candidate.exists():
                    candidate.unlink()
            except FileNotFoundError:
                pass
        migrate(path)
        return path
