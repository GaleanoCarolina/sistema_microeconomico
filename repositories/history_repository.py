from repositories.base_repository import BaseRepository

class HistoryRepository(BaseRepository):
    def activity(self,start=None,end=None,limit=500):
        where=[]; params=[]
        if start: where.append('date(fecha)>=?'); params.append(start)
        if end: where.append('date(fecha)<=?'); params.append(end)
        filt=(' WHERE '+' AND '.join(where)) if where else ''
        sql=f'''SELECT * FROM (
          SELECT s.sold_at fecha,'Venta' operacion,'Venta #'||s.id||CASE WHEN c.name IS NOT NULL THEN ' • '||c.name ELSE '' END descripcion,s.total_cents monto,
                 CASE s.status WHEN 'COMPLETED' THEN 'Completada' WHEN 'VOID' THEN 'Anulada' ELSE s.status END estado,'SALE' tipo,s.id ref
          FROM sales s LEFT JOIN customers c ON c.id=s.customer_id
          UNION ALL
          SELECT p.purchased_at,'Compra','Compra #'||p.id||' • '||COALESCE(sp.name,'Sin proveedor'),p.total_cents,
                 CASE p.status WHEN 'RECEIVED' THEN 'Recibida' WHEN 'PENDING' THEN 'Pendiente de recibir' WHEN 'CANCELLED' THEN 'Cancelada' ELSE p.status END,'PURCHASE',p.id
          FROM purchases p LEFT JOIN suppliers sp ON sp.id=p.supplier_id
          UNION ALL SELECT pay.paid_at,'Abono','Abono de '||c.name,pay.amount_cents,
                 CASE pay.status WHEN 'VALID' THEN 'Registrado' ELSE 'Anulado' END,'PAYMENT',pay.id FROM payments pay JOIN customers c ON c.id=pay.customer_id
          UNION ALL SELECT m.created_at,
             CASE m.movement_type WHEN 'WASTE' THEN 'Merma' WHEN 'RETURN' THEN 'Devolución' WHEN 'ADJUSTMENT' THEN 'Ajuste de inventario' WHEN 'PURCHASE' THEN 'Entrada de inventario' WHEN 'SALE' THEN 'Salida de inventario' WHEN 'SALE_VOID' THEN 'Reversión de venta' ELSE 'Movimiento de inventario' END,
             COALESCE(pr.name,'')||CASE WHEN m.notes IS NOT NULL AND m.notes<>'' THEN ' — '||m.notes ELSE '' END,
             NULL,'Registrado','MOVEMENT',m.id FROM inventory_movements m JOIN products pr ON pr.id=m.product_id
        ) {filt} ORDER BY fecha DESC LIMIT ?'''
        params.append(limit); return self.fetchall(sql,tuple(params))
    def details(self,kind,ref):
        if kind=='SALE':
            head=self.fetchone('''SELECT s.*,c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?''',(ref,)); lines=self.fetchall('''SELECT p.name,p.quantity_mode,p.unit_name,sd.quantity,sd.unit_price_cents,sd.subtotal_cents,sd.cost_total_cents FROM sale_details sd JOIN products p ON p.id=sd.product_id WHERE sd.sale_id=?''',(ref,)); return head,lines
        if kind=='PURCHASE':
            head=self.fetchone('''SELECT p.*,s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.id=?''',(ref,)); lines=self.fetchall('''SELECT pr.name,pr.quantity_mode,pr.unit_name,pd.quantity,pd.unit_cost_cents,pd.subtotal_cents,pd.expiry_date FROM purchase_details pd JOIN products pr ON pr.id=pd.product_id WHERE pd.purchase_id=?''',(ref,)); return head,lines
        return None,[]
