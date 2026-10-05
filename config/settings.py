import os
from pathlib import Path

APP_NAME = 'Sistema de Gestión Microeconómica e Inventarios'
BASE_DIR = Path(__file__).resolve().parents[1]

# Los datos del negocio se guardan fuera de la carpeta del programa.
# Esto es especialmente importante para la versión .exe: cerrar, actualizar o
# mover el programa no borra las ventas/inventario del usuario.
def _user_data_dir():
    local = os.environ.get('LOCALAPPDATA')
    if local:
        return Path(local) / 'Sistema_Gestion_Microeconomica'
    # Fallback multiplataforma para ejecución desde código fuente.
    return Path.home() / '.sistema_gestion_microeconomica'

DATA_DIR = _user_data_dir()
DB_PATH = DATA_DIR / 'app.db'
BACKUP_DIR = DATA_DIR / 'backups'
CURRENCY_SYMBOL = 'Q'
DEFAULT_SETTINGS = {
    'store_name': 'Mi Tienda',
    'store_address': 'Jalapa, Guatemala',
    'currency': 'GTQ',
    'timezone': 'America/Guatemala',
    'default_markup_pct': '25',
    'default_min_stock': '5',
    'safety_stock': '3',
    'low_rotation_days': '30',
    'stagnant_days': '60',
    'min_history_less_sold_days': '14',
    'expiry_warning_days': '15',
    'expiry_urgent_days': '5',
    'supplier_lead_days': '4',
    'default_budget': '1000',
    'credit_enabled': '1',
    'default_credit_limit_cents': '0',
    'old_debt_days': '30',
    'abc_a_pct': '80',
    'abc_b_pct': '95',
    'price_mode': 'confirm',
    'profit_policy': 'MARKUP',
    'unknown_expiry_policy': 'DATED_FIRST',
}
