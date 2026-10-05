from difflib import SequenceMatcher
from repositories.base_repository import BaseRepository
from database.connection import transaction
from utils.money import to_cents
from utils.text import normalize_name
from utils.dates import iso_now

class CustomerRepository(BaseRepository):
    def search(self,text='',limit=50):
        return self.fetchall('''SELECT c.*,COALESCE(SUM(r.balance_cents),0) balance_cents
            FROM customers c LEFT JOIN receivables r ON r.customer_id=c.id AND r.status='PENDING'
            WHERE c.active=1 AND (c.name LIKE ? OR COALESCE(c.phone,'') LIKE ?)
            GROUP BY c.id ORDER BY c.name LIMIT ?''',(f'%{(text or "").strip()}%',f'%{(text or "").strip()}%',limit))
    def similar(self,name,limit=5):
        target=normalize_name(name); out=[]
        for r in self.fetchall('SELECT * FROM customers WHERE active=1'):
            other=normalize_name(r['name']); ratio=SequenceMatcher(None,target,other).ratio()
            if target==other or ratio>=.78: out.append((ratio,dict(r)))
        out.sort(key=lambda x:x[0],reverse=True); return [x[1] for x in out[:limit]]
    def add(self,name,phone='',address='',notes='',credit_limit=0,allow_similar=False):
        if not (name or '').strip(): raise ValueError('El nombre del cliente es obligatorio.')
        if not allow_similar:
            exact=[x for x in self.similar(name) if normalize_name(x['name'])==normalize_name(name) and (not phone or not x['phone'] or x['phone']==phone)]
            if exact: raise ValueError(f"Ya existe un cliente parecido: {exact[0]['name']}.")
        with transaction(self.db_path) as con:
            now=iso_now(); cid=con.execute('INSERT INTO customers(name,phone,address,notes,credit_limit_cents,created_at) VALUES(?,?,?,?,?,?)',((name or '').strip(),(phone or '').strip(),(address or '').strip(),(notes or '').strip(),to_cents(credit_limit),now)).lastrowid
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('CUSTOMER_CREATED','CUSTOMER',cid,f'Cliente creado: {name.strip()}',now)); return cid
    def get(self,customer_id): return self.fetchone('SELECT * FROM customers WHERE id=?',(customer_id,))
