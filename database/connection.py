import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config.settings import DB_PATH, BACKUP_DIR


def connect(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    return con


@contextmanager
def transaction(db_path=None):
    con = connect(db_path)
    try:
        con.execute("BEGIN")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def backup_database(target_path=None, db_path=None):
    source = connect(db_path)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if target_path is None:
        from datetime import datetime
        target_path = BACKUP_DIR / f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close(); source.close()
    return Path(target_path)


def restore_database(source_path, db_path=None):
    source = sqlite3.connect(source_path)
    target = sqlite3.connect(db_path or DB_PATH)
    try:
        source.backup(target)
    finally:
        target.close(); source.close()
