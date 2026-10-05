from database.connection import transaction,connect
from utils.money import to_cents
from utils.dates import iso_now

class CreditService:
    def __init__(self,db_path=None): self.db_path=db_path
    def customer_balance_cents(self,customer_id):
        con=connect(self.db_path)
        try:return con.execute("SELECT COALESCE(SUM(balance_cents),0) b FROM receivables WHERE customer_id=? AND status='PENDING'",(customer_id,)).fetchone()['b']
        finally: con.close()
    def add_payment(self,customer_id,amount,notes=''):
        cents=to_cents(amount)
        if cents<=0: raise ValueError('El abono debe ser mayor que cero.')
        now=iso_now()
        with transaction(self.db_path) as con:
            balance=con.execute("SELECT COALESCE(SUM(balance_cents),0) b FROM receivables WHERE customer_id=? AND status='PENDING'",(customer_id,)).fetchone()['b']
            if cents>balance: raise ValueError('El abono no puede ser mayor al saldo pendiente.')
            remaining=cents
            for r in con.execute("SELECT * FROM receivables WHERE customer_id=? AND status='PENDING' ORDER BY created_at,id",(customer_id,)).fetchall():
                if remaining<=0: break
                apply=min(remaining,r['balance_cents']); new_balance=r['balance_cents']-apply
                con.execute('INSERT INTO payments(receivable_id,customer_id,amount_cents,notes,paid_at) VALUES(?,?,?,?,?)',(r['id'],customer_id,apply,notes,now))
                if new_balance==0: con.execute("UPDATE receivables SET balance_cents=0,status='PAID',paid_at=? WHERE id=?",(now,r['id']))
                else: con.execute('UPDATE receivables SET balance_cents=? WHERE id=?',(new_balance,r['id']))
                remaining-=apply
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PAYMENT','CUSTOMER',customer_id,f'Abono por Q{cents/100:,.2f}',now))
            return balance-cents
    def reverse_payment(self,payment_id,reason='Corrección'):
        now=iso_now()
        with transaction(self.db_path) as con:
            p=con.execute("SELECT * FROM payments WHERE id=? AND status='VALID'",(payment_id,)).fetchone()
            if not p: raise ValueError('Abono no encontrado o ya anulado.')
            con.execute("UPDATE payments SET status='REVERSED',notes=COALESCE(notes,'') || ? WHERE id=?",(f' | Anulado: {reason}',payment_id))
            con.execute("UPDATE receivables SET balance_cents=balance_cents+?,status='PENDING',paid_at=NULL WHERE id=?",(p['amount_cents'],p['receivable_id']))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PAYMENT_REVERSED','PAYMENT',payment_id,reason,now))
