from decimal import Decimal
from database.connection import transaction
from services.inventory_service import InventoryService
from utils.money import D, to_cents
from utils.dates import iso_now, iso_date

class SalesService:
    def __init__(self,db_path=None): self.db_path=db_path; self.inventory=InventoryService(db_path)

    def create_sale(self,items,payment_method='CASH',customer_id=None,paid_amount=None,notes='',authorize_credit_over_limit=False):
        if not items: raise ValueError('Agrega al menos un producto antes de cobrar.')
        now=iso_now()
        with transaction(self.db_path) as con:
            total=0; prepared=[]
            for item in items:
                pid=int(item['product_id']); qty=D(item['quantity'])
                if qty<=0: raise ValueError('La cantidad debe ser mayor que cero.')
                p=con.execute('SELECT * FROM products WHERE id=? AND active=1',(pid,)).fetchone()
                if not p: raise ValueError('Uno de los productos ya no está disponible.')
                subtotal=int((qty*Decimal(p['price_cents'])).to_integral_value())
                total+=subtotal; prepared.append((p,qty,subtotal))
            method=payment_method.upper()
            tendered=to_cents(paid_amount if paid_amount is not None else total/100)
            if method=='CASH':
                if tendered<total: raise ValueError('El efectivo recibido es menor que el total de la venta.')
                paid=total; credit=0
            elif method=='CREDIT':
                paid=0; credit=total
            elif method=='PARTIAL':
                paid=tendered; credit=total-paid
                if paid<=0 or paid>=total: raise ValueError('Para pago parcial, el monto pagado debe ser mayor que Q0 y menor que el total.')
            else:
                paid=total; credit=0
            if credit>0 and not customer_id: raise ValueError('Selecciona o crea un cliente para registrar el saldo fiado.')
            if credit>0:
                c=con.execute('SELECT * FROM customers WHERE id=? AND active=1',(customer_id,)).fetchone()
                if not c: raise ValueError('El cliente seleccionado ya no existe.')
                current=con.execute("SELECT COALESCE(SUM(balance_cents),0) b FROM receivables WHERE customer_id=? AND status='PENDING'",(customer_id,)).fetchone()['b']
                if c['credit_limit_cents']>0 and current+credit>c['credit_limit_cents'] and not authorize_credit_over_limit:
                    excess=current+credit-c['credit_limit_cents']; raise ValueError(f'Esta venta superará el límite configurado por Q{excess/100:,.2f}.')
            sale_id=con.execute('''INSERT INTO sales(customer_id,total_cents,paid_cents,credit_cents,payment_method,notes,sold_at)
                                   VALUES(?,?,?,?,?,?,?)''',(customer_id,total,paid,credit,method,notes,now)).lastrowid
            total_cost=0
            for p,qty,subtotal in prepared:
                allocations=self.inventory.consume_fefo(con,p['id'],qty,now=now)
                # FEFO decide qué lote físico sale; el costo contable de la venta usa el CPP
                # vigente del producto, tal como exige la política contable del sistema.
                cost_total=int((qty*Decimal(p['cpp_cents'])).to_integral_value())
                total_cost+=cost_total
                avg_cost=p['cpp_cents']
                detail_id=con.execute('''INSERT INTO sale_details(sale_id,product_id,quantity,unit_price_cents,unit_cost_cents,subtotal_cents,cost_total_cents)
                                        VALUES(?,?,?,?,?,?,?)''',(sale_id,p['id'],float(qty),p['price_cents'],avg_cost,subtotal,cost_total)).lastrowid
                for lot_id,take,cost in allocations:
                    con.execute('INSERT INTO sale_lot_allocations(sale_detail_id,lot_id,quantity,unit_cost_cents) VALUES(?,?,?,?)',(detail_id,lot_id,float(take),cost))
                    con.execute('''INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,reference_type,reference_id,created_at,notes)
                                   VALUES(?,?,?,?,?,?,?,?,?)''',(p['id'],lot_id,'SALE',-float(take),cost,'SALE',sale_id,now,'Venta'))
            profit=total-total_cost
            con.execute('UPDATE sales SET cost_cents=?,gross_profit_cents=? WHERE id=?',(total_cost,profit,sale_id))
            for p,_,_ in prepared:
                available=con.execute('''SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND quantity_remaining>0 AND status='ACTIVE' AND (expiry_date IS NULL OR expiry_date>=?)''',(p['id'],iso_date())).fetchone()['q']
                if available<=0: con.execute('INSERT OR IGNORE INTO stockout_days(product_id,day) VALUES(?,?)',(p['id'],iso_date()))
            if credit>0:
                con.execute('''INSERT INTO receivables(sale_id,customer_id,original_cents,balance_cents,created_at)
                               VALUES(?,?,?,?,?)''',(sale_id,customer_id,credit,credit,now))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('SALE_CREATED','SALE',sale_id,f'Venta registrada por Q{total/100:,.2f}',now))
            return {'sale_id':sale_id,'total_cents':total,'paid_cents':paid,'credit_cents':credit,'gross_profit_cents':profit,'change_cents':max(0,tendered-total) if method=='CASH' else 0}

    def void_sale(self,sale_id,reason='Anulación'):
        now=iso_now()
        with transaction(self.db_path) as con:
            sale=con.execute("SELECT * FROM sales WHERE id=? AND status='COMPLETED'",(sale_id,)).fetchone()
            if not sale: raise ValueError('Venta no encontrada o ya anulada.')
            rec=con.execute('SELECT * FROM receivables WHERE sale_id=?',(sale_id,)).fetchone()
            if rec and rec['balance_cents'] != rec['original_cents']: raise ValueError('Esta venta tiene abonos. Anula primero esos abonos para conservar la trazabilidad.')
            for a in con.execute('''SELECT a.*,d.product_id FROM sale_lot_allocations a JOIN sale_details d ON d.id=a.sale_detail_id WHERE d.sale_id=?''',(sale_id,)).fetchall():
                con.execute('UPDATE lots SET quantity_remaining=quantity_remaining+? WHERE id=?',(a['quantity'],a['lot_id']))
                con.execute('UPDATE products SET stock_qty=stock_qty+?,updated_at=? WHERE id=?',(a['quantity'],now,a['product_id']))
                con.execute('''INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,reference_type,reference_id,created_at,notes)
                               VALUES(?,?,?,?,?,?,?,?,?)''',(a['product_id'],a['lot_id'],'SALE_VOID',a['quantity'],a['unit_cost_cents'],'SALE',sale_id,now,reason))
            if rec: con.execute("UPDATE receivables SET status='VOID',balance_cents=0 WHERE id=?",(rec['id'],))
            con.execute("UPDATE sales SET status='VOID',notes=COALESCE(notes,'') || ? WHERE id=?",(f' | Anulada: {reason}',sale_id))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('SALE_VOID','SALE',sale_id,reason,now))
