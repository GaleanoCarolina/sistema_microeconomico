from repositories.base_repository import BaseRepository
class ReportRepository(BaseRepository):
    def sales(self,start=None,end=None,limit=500):
        where=["s.status IN ('COMPLETED','VOID')"]; params=[]
        if start: where.append('date(s.sold_at)>=?'); params.append(start)
        if end: where.append('date(s.sold_at)<=?'); params.append(end)
        params.append(limit); return self.fetchall(f'''SELECT s.id,s.sold_at,s.total_cents,s.cost_cents,s.paid_cents,s.credit_cents,s.gross_profit_cents,s.payment_method,s.status,c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE {' AND '.join(where)} ORDER BY s.sold_at DESC LIMIT ?''',tuple(params))
    def purchases(self,start=None,end=None,limit=500):
        where=[]; params=[]
        if start: where.append('date(p.purchased_at)>=?'); params.append(start)
        if end: where.append('date(p.purchased_at)<=?'); params.append(end)
        params.append(limit); filt='WHERE '+' AND '.join(where) if where else ''
        return self.fetchall(f'''SELECT p.id,p.purchased_at,p.received_at,p.subtotal_cents,p.discount_cents,p.additional_costs_cents,p.total_cents,p.status,s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id {filt} ORDER BY p.purchased_at DESC LIMIT ?''',tuple(params))
    def expiries(self): return self.fetchall('''SELECT p.name,p.quantity_mode,l.id lot_id,l.received_at,l.expiry_date,l.quantity_remaining,l.status FROM lots l JOIN products p ON p.id=l.product_id WHERE l.quantity_remaining>0 ORDER BY CASE WHEN l.expiry_date IS NULL THEN 1 ELSE 0 END,l.expiry_date,l.received_at''')
