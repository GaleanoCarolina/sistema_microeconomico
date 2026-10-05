from database.connection import connect

class BaseRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def fetchall(self, sql, params=()):
        con = connect(self.db_path)
        try:
            return con.execute(sql, params).fetchall()
        finally:
            con.close()

    def fetchone(self, sql, params=()):
        con = connect(self.db_path)
        try:
            return con.execute(sql, params).fetchone()
        finally:
            con.close()
