from repositories.base_repository import BaseRepository
from database.connection import transaction
from utils.dates import iso_now

class SupplierRepository(BaseRepository):
    def list_all(self): return self.fetchall('SELECT * FROM suppliers WHERE active=1 ORDER BY name')
    def search(self,text=''): return self.fetchall('SELECT * FROM suppliers WHERE active=1 AND name LIKE ? ORDER BY name LIMIT 30',(f'%{text.strip()}%',))
    def ensure(self,name,lead_days=4,phone='',address=''):
        if not name or not name.strip(): return None
        with transaction(self.db_path) as con:
            con.execute('INSERT OR IGNORE INTO suppliers(name,phone,address,default_lead_days) VALUES(?,?,?,?)',(name.strip(),phone.strip(),address.strip(),int(lead_days)))
            return con.execute('SELECT id FROM suppliers WHERE name=? COLLATE NOCASE',(name.strip(),)).fetchone()['id']
    def add(self,name,phone='',address='',lead_days=4):
        if not name.strip(): raise ValueError('El nombre del proveedor es obligatorio.')
        with transaction(self.db_path) as con:
            exists=con.execute('SELECT id FROM suppliers WHERE name=? COLLATE NOCASE',(name.strip(),)).fetchone()
            if exists: return exists['id']
            sid=con.execute('INSERT INTO suppliers(name,phone,address,default_lead_days) VALUES(?,?,?,?)',(name.strip(),phone.strip(),address.strip(),int(lead_days))).lastrowid
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('SUPPLIER_CREATED','SUPPLIER',sid,f'Proveedor creado: {name.strip()}',iso_now())); return sid
