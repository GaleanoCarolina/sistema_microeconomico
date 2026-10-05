from pathlib import Path
from database.connection import connect
from config.settings import DEFAULT_SETTINGS
from config.catalog_options import DEFAULT_CATEGORIES
from utils.text import normalize_name


def migrate(db_path=None):
    con = connect(db_path)
    try:
        con.execute('CREATE TABLE IF NOT EXISTS schema_migrations(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        migrations = sorted((Path(__file__).parent / 'migrations').glob('*.sql'))
        for sql_file in migrations:
            already = con.execute('SELECT 1 FROM schema_migrations WHERE name=?', (sql_file.name,)).fetchone()
            if already:
                continue
            try:
                con.executescript(sql_file.read_text(encoding='utf-8'))
            except Exception as exc:
                # Compatibilidad con bases de la V1 que pudieron ejecutar 001 sin tabla de control.
                if sql_file.name == '001_initial.sql' and 'already exists' in str(exc).lower():
                    pass
                elif sql_file.name in ('002_v2.sql','003_v3.sql','004_v6_3.sql') and 'duplicate column name' in str(exc).lower():
                    pass
                else:
                    raise
            con.execute('INSERT OR IGNORE INTO schema_migrations(name) VALUES(?)', (sql_file.name,))
        for key, value in DEFAULT_SETTINGS.items():
            con.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)', (key, value))
        # Categorías comunes disponibles desde la primera ejecución. No son
        # obligatorias: el usuario puede escribir y crear cualquier categoría nueva.
        for category_name in DEFAULT_CATEGORIES:
            con.execute('INSERT OR IGNORE INTO categories(name,active) VALUES(?,1)', (category_name,))
        # Normalización de nombres, realizada en Python para manejar tildes y puntuación.
        cols = {r['name'] for r in con.execute('PRAGMA table_info(products)').fetchall()}
        if 'normalized_name' in cols:
            for row in con.execute('SELECT id,name FROM products').fetchall():
                con.execute('UPDATE products SET normalized_name=? WHERE id=?', (normalize_name(row['name']), row['id']))
        con.commit()
    finally:
        con.close()
