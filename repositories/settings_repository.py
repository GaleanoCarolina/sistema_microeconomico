from repositories.base_repository import BaseRepository
from database.connection import transaction

class SettingsRepository(BaseRepository):
    def get(self, key, default=None):
        row = self.fetchone('SELECT value FROM settings WHERE key=?', (key,))
        return row['value'] if row else default
    def all(self):
        return {r['key']: r['value'] for r in self.fetchall('SELECT key,value FROM settings')}
    def set(self, key, value):
        with transaction(self.db_path) as con:
            con.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
            con.execute('INSERT INTO audit_log(event_type,entity_type,description) VALUES(?,?,?)', ('SETTING_CHANGED','SETTING',f'{key} actualizado'))
