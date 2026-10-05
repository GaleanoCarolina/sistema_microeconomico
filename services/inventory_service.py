from decimal import Decimal
from database.connection import transaction,connect
from services.fefo_service import FEFOService
from utils.money import D
from utils.dates import iso_now,iso_date

class InventoryService:
    def __init__(self,db_path=None): self.db_path=db_path
    def available_qty(self,product_id):
        con=connect(self.db_path)
        try:return D(con.execute('''SELECT COALESCE(SUM(quantity_remaining),0) qty FROM lots WHERE product_id=? AND quantity_remaining>0 AND status='ACTIVE' AND (expiry_date IS NULL OR expiry_date>=?)''',(product_id,iso_date())).fetchone()['qty'])
        finally: con.close()

    @staticmethod
    def _physical_stock(con,product_id):
        return D(con.execute("SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND status='ACTIVE'",(product_id,)).fetchone()['q'])

    def reconcile(self,fix=False):
        con=connect(self.db_path); issues=[]
        try:
            for p in con.execute('SELECT id,name,stock_qty FROM products').fetchall():
                physical=self._physical_stock(con,p['id']); recorded=D(p['stock_qty'])
                # Entradas/salidas acumuladas sirven como verificación adicional; pueden incluir ajustes históricos.
                movements=D(con.execute('SELECT COALESCE(SUM(quantity),0) q FROM inventory_movements WHERE product_id=?',(p['id'],)).fetchone()['q'])
                if abs(physical-recorded)>Decimal('0.000001') or abs(physical-movements)>Decimal('0.000001'):
                    issues.append({'product_id':p['id'],'name':p['name'],'recorded':recorded,'lots':physical,'movements':movements})
                    if fix: con.execute('UPDATE products SET stock_qty=?,updated_at=? WHERE id=?',(float(physical),iso_now(),p['id']))
            if fix: con.commit()
            return issues
        finally: con.close()

    def consume_fefo(self,con,product_id,quantity,now=None):
        need=D(quantity); allocations=[]
        for lot in FEFOService.eligible_lots(con,product_id):
            if need<=0: break
            avail=D(lot['quantity_remaining']); take=min(avail,need)
            con.execute('UPDATE lots SET quantity_remaining=quantity_remaining-? WHERE id=?',(float(take),lot['id']))
            allocations.append((lot['id'],take,lot['unit_cost_cents'])); need-=take
        if need>Decimal('0.000001'): raise ValueError('No hay inventario disponible suficiente. Puede existir mercancía vencida que no se permite vender.')
        physical=self._physical_stock(con,product_id); con.execute('UPDATE products SET stock_qty=?,updated_at=? WHERE id=?',(float(physical),now or iso_now(),product_id)); return allocations

    def update_lot_expiry(self,lot_id,expiry_date):
        with transaction(self.db_path) as con:
            lot=con.execute('SELECT * FROM lots WHERE id=?',(lot_id,)).fetchone()
            if not lot: raise ValueError('Lote no encontrado.')
            now=iso_now(); con.execute('UPDATE lots SET expiry_date=?,expiry_updated_at=?,status=? WHERE id=?',(expiry_date or None,now,'ACTIVE',lot_id))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('LOT_EXPIRY_UPDATED','LOT',lot_id,f'Fecha de vencimiento actualizada a {expiry_date or "sin registrar"}',now))

    def adjust(self,product_id,delta,movement_type='ADJUSTMENT',notes='Ajuste manual'):
        delta=D(delta); now=iso_now()
        with transaction(self.db_path) as con:
            p=con.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
            if not p: raise ValueError('Producto no encontrado.')
            if self._physical_stock(con,product_id)+delta<0: raise ValueError('El ajuste produciría existencias negativas.')
            lot_id=None
            if delta>0:
                lot_id=con.execute('INSERT INTO lots(product_id,quantity_initial,quantity_remaining,unit_cost_cents,received_at) VALUES(?,?,?,?,?)',(product_id,float(delta),float(delta),p['cpp_cents'],now)).lastrowid
            elif delta<0:
                allocations=self.consume_fefo(con,product_id,-delta,now=now); lot_id=allocations[0][0] if allocations else None
            physical=self._physical_stock(con,product_id); con.execute('UPDATE products SET stock_qty=?,updated_at=? WHERE id=?',(float(physical),now,product_id))
            con.execute('INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,created_at,notes) VALUES(?,?,?,?,?,?,?)',(product_id,lot_id,movement_type,float(delta),p['cpp_cents'],now,notes))

    def register_waste_or_return(self,product_id,quantity,action='WASTE',notes=''):
        qty=D(quantity)
        if qty<=0: raise ValueError('La cantidad debe ser mayor que cero.')
        now=iso_now()
        with transaction(self.db_path) as con:
            allocations=self.consume_fefo(con,product_id,qty,now=now)
            for lot_id,take,cost in allocations:
                con.execute('INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,created_at,notes) VALUES(?,?,?,?,?,?,?)',(product_id,lot_id,action,-float(take),cost,now,notes))
