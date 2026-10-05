from database.migrate import migrate
from database.connection import connect
from config.catalog_options import DEFAULT_CATEGORIES, DEFAULT_UNITS


def test_default_categories_are_created_in_empty_database(tmp_path):
    db = tmp_path / 'catalog.db'
    migrate(db)
    con = connect(db)
    try:
        names = {r['name'] for r in con.execute('SELECT name FROM categories WHERE active=1').fetchall()}
    finally:
        con.close()
    assert set(DEFAULT_CATEGORIES).issubset(names)


def test_expected_default_units_exist():
    for unit in ('unidad','caja','kilogramo','libra','botella','lata','litro'):
        assert unit in DEFAULT_UNITS
