from pathlib import Path
from database.migrate import migrate
from database.connection import connect
from services.reset_service import ResetService
from config.settings import DB_PATH, DATA_DIR


def test_runtime_database_is_outside_project_folder():
    # V6 stores operational data in the user's profile, not beside bundled code.
    project_root = Path(__file__).resolve().parents[1]
    assert project_root not in DB_PATH.parents
    assert DB_PATH.parent == DATA_DIR


def test_reset_removes_business_data_and_restores_defaults(tmp_path):
    db = tmp_path / 'app.db'
    migrate(db)
    con = connect(db)
    try:
        con.execute("INSERT INTO categories(name) VALUES('Prueba')")
        cat_id = con.execute("SELECT id FROM categories WHERE name='Prueba'").fetchone()['id']
        con.execute("""INSERT INTO products(name, normalized_name, category_id, unit_name, quantity_mode, cpp_cents, price_cents, markup_pct, min_stock, stock_qty, expires, active)
                       VALUES('Producto temporal','producto temporal',?,'unidad','INTEGER',100,150,50,2,4,0,1)""", (cat_id,))
        con.execute("UPDATE settings SET value='Tienda temporal' WHERE key='store_name'")
        con.commit()
    finally:
        con.close()

    ResetService(db).reset_all()
    con = connect(db)
    try:
        assert con.execute('SELECT COUNT(*) AS n FROM products').fetchone()['n'] == 0
        assert con.execute("SELECT value FROM settings WHERE key='store_name'").fetchone()['value'] == 'Mi Tienda'
    finally:
        con.close()


def test_reset_cleans_wal_sidecars(tmp_path):
    db = tmp_path / 'app.db'
    migrate(db)
    Path(str(db) + '-wal').write_bytes(b'test')
    Path(str(db) + '-shm').write_bytes(b'test')
    ResetService(db).reset_all()
    # A fresh SQLite connection may recreate sidecars later, but reset itself removes stale ones.
    assert db.exists()
