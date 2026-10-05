from decimal import Decimal
from database.connection import transaction, connect
from services.cpp_service import CPPService
from services.pricing_service import PricingService
from repositories.settings_repository import SettingsRepository
from utils.money import D,to_cents
from utils.dates import iso_now

class PurchaseService:
    def __init__(self,db_path=None): self.db_path=db_path; self.settings=SettingsRepository(db_path)

    @staticmethod
    def _sync_stock(con,pid,now):
        physical=D(con.execute("SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND status='ACTIVE'",(pid,)).fetchone()['q'])
        con.execute('UPDATE products SET stock_qty=?,updated_at=? WHERE id=?',(float(physical),now,pid))
        return physical

    def _apply_purchase_price(self,con,product,new_cpp_cents,desired_price_cents,now,reason):
        """Aplica el precio decidido en Compras y mantiene coherente el porcentaje."""
        if desired_price_cents is None:
            return product['price_cents']
        desired_price_cents=int(desired_price_cents)
        if desired_price_cents < 0:
            raise ValueError('El precio de venta no puede ser negativo.')
        policy=self.settings.get('profit_policy','MARKUP')
        pct=PricingService.percent_from_price(new_cpp_cents,desired_price_cents,policy) if new_cpp_cents>0 else D(product['markup_pct'] or 0)
        old_price=int(product['price_cents'])
        con.execute('UPDATE products SET price_cents=?,markup_pct=?,updated_at=? WHERE id=?',(desired_price_cents,str(pct),now,product['id']))
        if desired_price_cents!=old_price:
            con.execute('INSERT INTO price_history(product_id,old_price_cents,new_price_cents,reason,changed_at) VALUES(?,?,?,?,?)',(product['id'],old_price,desired_price_cents,reason,now))
        return desired_price_cents

    def create_purchase(self,items,supplier_id=None,notes='',purchase_date=None,received_date=None,status='RECEIVED',discount=0,additional_costs=0,payment_method=None):
        if not items: raise ValueError('Agrega al menos un producto a la compra.')
        status=(status or 'RECEIVED').upper()
        if status not in ('RECEIVED','PENDING'): raise ValueError('El estado de la compra no es válido.')
        now=iso_now(); purchased_at=(purchase_date+' 12:00:00') if purchase_date else now
        received_at=((received_date or purchase_date)+' 12:00:00') if status=='RECEIVED' and (received_date or purchase_date) else (now if status=='RECEIVED' else None)
        result=[]; subtotal_total=0
        discount_cents=max(0,to_cents(discount)); additional_cents=max(0,to_cents(additional_costs))
        with transaction(self.db_path) as con:
            purchase_id=con.execute('''INSERT INTO purchases(supplier_id,notes,purchased_at,received_at,status,subtotal_cents,discount_cents,additional_costs_cents,total_cents,payment_method,expected_received_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(supplier_id,notes,purchased_at,received_at,status,0,discount_cents,additional_cents,0,payment_method,None if status=='RECEIVED' else (received_date+' 12:00:00' if received_date else None))).lastrowid
            for item in items:
                pid=int(item['product_id']); qty=D(item['quantity']); cost_cents=to_cents(item['unit_cost']); desired_price_cents=to_cents(item['sale_price']) if item.get('sale_price') is not None else None
                if qty<=0: raise ValueError('La cantidad comprada debe ser mayor que cero.')
                if cost_cents<0: raise ValueError('El costo no puede ser negativo.')
                p=con.execute('SELECT * FROM products WHERE id=? AND active=1',(pid,)).fetchone()
                if not p: raise ValueError('Producto no encontrado o inactivo.')
                subtotal=int((qty*Decimal(cost_cents)).to_integral_value()); subtotal_total+=subtotal; expiry=item.get('expiry_date') or None
                detail_id=con.execute('''INSERT INTO purchase_details(purchase_id,product_id,quantity,unit_cost_cents,subtotal_cents,expiry_date,desired_price_cents)
                                         VALUES(?,?,?,?,?,?,?)''',(purchase_id,pid,float(qty),cost_cents,subtotal,expiry,desired_price_cents)).lastrowid
                if status=='RECEIVED':
                    old_cpp=p['cpp_cents']; old_qty=D(p['stock_qty']); new_cpp=CPPService.calculate(old_qty,old_cpp,qty,cost_cents)
                    lot_id=con.execute('''INSERT INTO lots(product_id,purchase_detail_id,quantity_initial,quantity_remaining,unit_cost_cents,expiry_date,received_at,status)
                                          VALUES(?,?,?,?,?,?,?,'ACTIVE')''',(pid,detail_id,float(qty),float(qty),cost_cents,expiry,received_at)).lastrowid
                    con.execute('UPDATE products SET cpp_cents=?,usual_supplier_id=COALESCE(?,usual_supplier_id),updated_at=? WHERE id=?',(new_cpp,supplier_id,now,pid))
                    self._sync_stock(con,pid,now)
                    final_price=self._apply_purchase_price(con,p,new_cpp,desired_price_cents,now,'Precio definido al registrar compra')
                    con.execute('INSERT INTO cost_history(product_id,old_cpp_cents,new_cpp_cents,reason,changed_at) VALUES(?,?,?,?,?)',(pid,old_cpp,new_cpp,'Compra recibida',now))
                    con.execute('''INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,reference_type,reference_id,created_at,notes)
                                   VALUES(?,?,?,?,?,?,?,?,?)''',(pid,lot_id,'PURCHASE',float(qty),cost_cents,'PURCHASE',purchase_id,now,'Compra recibida'))
                    suggested=PricingService.price_from_percent(new_cpp,p['markup_pct'],self.settings.get('profit_policy','MARKUP'))
                    result.append({'product_id':pid,'lot_id':lot_id,'old_cpp_cents':old_cpp,'new_cpp_cents':new_cpp,'old_price_cents':p['price_cents'],'final_price_cents':final_price,'suggested_price_cents':suggested})
            total=max(0,subtotal_total-discount_cents+additional_cents)
            con.execute('UPDATE purchases SET subtotal_cents=?,total_cents=? WHERE id=?',(subtotal_total,total,purchase_id))
            desc=('Compra recibida' if status=='RECEIVED' else 'Compra pendiente')+f' por Q{total/100:,.2f}'
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PURCHASE_CREATED','PURCHASE',purchase_id,desc,now))
            return purchase_id,result

    def receive_purchase(self,purchase_id,received_date=None):
        """Convierte una compra pendiente en recibida de forma transaccional."""
        now=iso_now(); received_at=(received_date+' 12:00:00') if received_date else now; changes=[]
        with transaction(self.db_path) as con:
            pu=con.execute("SELECT * FROM purchases WHERE id=? AND status='PENDING'",(purchase_id,)).fetchone()
            if not pu: raise ValueError('La compra no existe o ya fue recibida/cancelada.')
            details=con.execute('SELECT * FROM purchase_details WHERE purchase_id=? ORDER BY id',(purchase_id,)).fetchall()
            for d in details:
                p=con.execute('SELECT * FROM products WHERE id=?',(d['product_id'],)).fetchone(); qty=D(d['quantity']); cost=d['unit_cost_cents']
                old_cpp=p['cpp_cents']; old_qty=D(p['stock_qty']); new_cpp=CPPService.calculate(old_qty,old_cpp,qty,cost)
                lot_id=con.execute('''INSERT INTO lots(product_id,purchase_detail_id,quantity_initial,quantity_remaining,unit_cost_cents,expiry_date,received_at,status)
                                      VALUES(?,?,?,?,?,?,?,'ACTIVE')''',(p['id'],d['id'],float(qty),float(qty),cost,d['expiry_date'],received_at)).lastrowid
                con.execute('UPDATE products SET cpp_cents=?,usual_supplier_id=COALESCE(?,usual_supplier_id),updated_at=? WHERE id=?',(new_cpp,pu['supplier_id'],now,p['id']))
                self._sync_stock(con,p['id'],now)
                final_price=self._apply_purchase_price(con,p,new_cpp,d['desired_price_cents'],now,'Precio definido en compra pendiente al recibir')
                con.execute('INSERT INTO cost_history(product_id,old_cpp_cents,new_cpp_cents,reason,changed_at) VALUES(?,?,?,?,?)',(p['id'],old_cpp,new_cpp,'Compra recibida',now))
                con.execute('''INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,reference_type,reference_id,created_at,notes)
                               VALUES(?,?,?,?,?,?,?,?,?)''',(p['id'],lot_id,'PURCHASE',float(qty),cost,'PURCHASE',purchase_id,now,'Compra recibida'))
                changes.append({'product_id':p['id'],'lot_id':lot_id,'old_cpp_cents':old_cpp,'new_cpp_cents':new_cpp,'old_price_cents':p['price_cents'],'final_price_cents':final_price,'suggested_price_cents':PricingService.price_from_percent(new_cpp,p['markup_pct'],self.settings.get('profit_policy','MARKUP'))})
            con.execute("UPDATE purchases SET status='RECEIVED',received_at=? WHERE id=?",(received_at,purchase_id))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PURCHASE_RECEIVED','PURCHASE',purchase_id,'Compra marcada como recibida',now))
        return changes


    def pending_purchases(self):
        con=connect(self.db_path)
        try:
            return con.execute("""SELECT p.id,p.purchased_at,p.expected_received_at,p.total_cents,COALESCE(s.name,'Sin proveedor') supplier
                                  FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id
                                  WHERE p.status='PENDING' ORDER BY p.purchased_at,p.id""").fetchall()
        finally: con.close()

    def period_total_cents(self,start,end):
        con=connect(self.db_path)
        try:
            return con.execute("SELECT COALESCE(SUM(total_cents),0) v FROM purchases WHERE status<>'CANCELLED' AND date(purchased_at) BETWEEN ? AND ?",(start,end)).fetchone()['v']
        finally: con.close()
