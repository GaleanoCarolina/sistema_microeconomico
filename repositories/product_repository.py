from difflib import SequenceMatcher
from repositories.base_repository import BaseRepository
from database.connection import transaction
from utils.money import to_cents
from utils.text import normalize_name
from utils.dates import iso_now, iso_date
from utils.quantities import infer_quantity_mode

class ProductRepository(BaseRepository):
    def search(self, text='', active_only=True, limit=50):
        raw=(text or '').strip(); like=f'%{raw}%'; norm=f'%{normalize_name(raw)}%'
        sql='''SELECT p.*, c.name category_name, s.name supplier_name
               FROM products p LEFT JOIN categories c ON c.id=p.category_id
               LEFT JOIN suppliers s ON s.id=p.usual_supplier_id
               WHERE (p.name LIKE ? OR COALESCE(p.normalized_name,'') LIKE ? OR COALESCE(c.name,'') LIKE ?)'''
        params=[like,norm,like]
        if active_only: sql += ' AND p.active=1'
        sql += ' ORDER BY p.favorite DESC,p.name LIMIT ?'; params.append(limit)
        return self.fetchall(sql,tuple(params))

    def inventory_rows(self, text='', include_inactive=False):
        """Maestro de inventario: una fila por producto, aun con stock cero.
        El stock visible se deriva de lotes (fuente física) y se compara con el acumulado del producto.
        """
        raw=(text or '').strip(); like=f'%{raw}%'; norm=f'%{normalize_name(raw)}%'
        sql='''SELECT p.*, c.name category_name, s.name supplier_name,
                 COALESCE(SUM(CASE WHEN l.status='ACTIVE' THEN l.quantity_remaining ELSE 0 END),0) lot_stock,
                 MIN(CASE WHEN l.status='ACTIVE' AND l.quantity_remaining>0 AND l.expiry_date IS NOT NULL THEN l.expiry_date END) next_expiry,
                 COALESCE(SUM(CASE WHEN l.status='ACTIVE' AND l.quantity_remaining>0 AND l.expiry_date IS NULL THEN l.quantity_remaining ELSE 0 END),0) unknown_expiry_qty,
                 MAX(l.received_at) last_received_at
               FROM products p
               LEFT JOIN categories c ON c.id=p.category_id
               LEFT JOIN suppliers s ON s.id=p.usual_supplier_id
               LEFT JOIN lots l ON l.product_id=p.id
               WHERE (p.name LIKE ? OR COALESCE(p.normalized_name,'') LIKE ? OR COALESCE(c.name,'') LIKE ?)'''
        params=[like,norm,like]
        if not include_inactive: sql += ' AND p.active=1'
        sql += ' GROUP BY p.id ORDER BY p.name'
        return self.fetchall(sql,tuple(params))

    def get(self, product_id):
        return self.fetchone('''SELECT p.*,c.name category_name,s.name supplier_name FROM products p
                              LEFT JOIN categories c ON c.id=p.category_id LEFT JOIN suppliers s ON s.id=p.usual_supplier_id
                              WHERE p.id=?''',(product_id,))

    def duplicate_candidates(self, name, limit=6):
        target=normalize_name(name)
        if not target: return []
        rows=self.fetchall('SELECT id,name,normalized_name,price_cents,stock_qty FROM products WHERE active=1 ORDER BY name')
        scored=[]
        for r in rows:
            other=r['normalized_name'] or normalize_name(r['name']); ratio=SequenceMatcher(None,target,other).ratio()
            if target==other or target in other or other in target or ratio>=0.72: scored.append((1 if target==other else ratio,dict(r)))
        scored.sort(key=lambda x:x[0], reverse=True); return [r for _,r in scored[:limit]]

    def add(self,name,category_id=None,cost=0,price=0,quantity=0,markup_pct='25',min_stock=5,expires=False,expiry_date=None,unit_name='unidad',allow_similar=False,quantity_mode=None):
        name=(name or '').strip()
        if not name: raise ValueError('Escribe el nombre del producto.')
        if not allow_similar:
            dup=self.duplicate_candidates(name,1)
            if dup and normalize_name(dup[0]['name'])==normalize_name(name): raise ValueError(f"Ya existe un producto equivalente: {dup[0]['name']}.")
        mode=quantity_mode or infer_quantity_mode(unit_name)
        with transaction(self.db_path) as con:
            now=iso_now(); qty=float(quantity)
            cur=con.execute('''INSERT INTO products(name,normalized_name,category_id,stock_qty,cpp_cents,price_cents,markup_pct,min_stock,expires,unit_name,quantity_mode,created_at,updated_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(name,normalize_name(name),category_id,qty,to_cents(cost),to_cents(price),str(markup_pct),float(min_stock),int(expires),unit_name or 'unidad',mode,now,now))
            pid=cur.lastrowid
            if qty>0:
                lot=con.execute('''INSERT INTO lots(product_id,quantity_initial,quantity_remaining,unit_cost_cents,expiry_date,received_at)
                                   VALUES(?,?,?,?,?,?)''',(pid,qty,qty,to_cents(cost),expiry_date,now)).lastrowid
                con.execute('''INSERT INTO inventory_movements(product_id,lot_id,movement_type,quantity,unit_cost_cents,reference_type,reference_id,created_at,notes)
                               VALUES(?,?,?,?,?,?,?,?,?)''',(pid,lot,'INITIAL',qty,to_cents(cost),'PRODUCT',pid,now,'Inventario inicial'))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PRODUCT_CREATED','PRODUCT',pid,f'Producto creado: {name}',now))
            return pid

    def update(self, product_id, *, name, category_id=None, price=0, markup_pct='25', min_stock=5, expires=False, unit_name='unidad',quantity_mode=None,profit_policy='MARKUP'):
        name=(name or '').strip()
        if not name: raise ValueError('Escribe el nombre del producto.')
        dup=[r for r in self.duplicate_candidates(name,5) if r['id']!=product_id and normalize_name(r['name'])==normalize_name(name)]
        if dup: raise ValueError(f"Ya existe otro producto equivalente: {dup[0]['name']}.")
        mode=quantity_mode or infer_quantity_mode(unit_name)
        with transaction(self.db_path) as con:
            old=con.execute('SELECT price_cents FROM products WHERE id=?',(product_id,)).fetchone()
            now=iso_now(); new_price=to_cents(price)
            from services.pricing_service import PricingService
            cpp=con.execute('SELECT cpp_cents FROM products WHERE id=?',(product_id,)).fetchone()['cpp_cents']
            coherent_pct=PricingService.percent_from_price(cpp,new_price,profit_policy) if cpp>0 else markup_pct
            con.execute('''UPDATE products SET name=?,normalized_name=?,category_id=?,price_cents=?,markup_pct=?,min_stock=?,expires=?,unit_name=?,quantity_mode=?,updated_at=? WHERE id=?''',
                        (name,normalize_name(name),category_id,new_price,str(coherent_pct),float(min_stock),int(expires),unit_name or 'unidad',mode,now,product_id))
            if old and old['price_cents']!=new_price:
                con.execute('INSERT INTO price_history(product_id,old_price_cents,new_price_cents,reason,changed_at) VALUES(?,?,?,?,?)',(product_id,old['price_cents'],new_price,'Edición de producto',now))
            con.execute('INSERT INTO audit_log(event_type,entity_type,entity_id,description,created_at) VALUES(?,?,?,?,?)',('PRODUCT_UPDATED','PRODUCT',product_id,f'Producto actualizado: {name}',now))

    def set_price(self, product_id, new_price_cents, reason='Cambio manual', markup_pct=None,profit_policy='MARKUP'):
        with transaction(self.db_path) as con:
            old=con.execute('SELECT price_cents,cpp_cents FROM products WHERE id=?',(product_id,)).fetchone()
            if not old: raise ValueError('Producto no encontrado.')
            if markup_pct is None:
                from services.pricing_service import PricingService
                markup_pct = PricingService.percent_from_price(old['cpp_cents'],new_price_cents,profit_policy)
            now=iso_now(); con.execute('UPDATE products SET price_cents=?,markup_pct=?,updated_at=? WHERE id=?',(int(new_price_cents),str(round(float(markup_pct),4)),now,product_id))
            con.execute('INSERT INTO price_history(product_id,old_price_cents,new_price_cents,reason,changed_at) VALUES(?,?,?,?,?)',(product_id,old['price_cents'],int(new_price_cents),reason,now))


    def recalculate_percentages(self, profit_policy='MARKUP'):
        """Reinterpreta el porcentaje almacenado sin alterar CPP ni precio al cambiar la política global."""
        from services.pricing_service import PricingService
        with transaction(self.db_path) as con:
            rows=con.execute('SELECT id,cpp_cents,price_cents FROM products').fetchall(); now=iso_now()
            for r in rows:
                pct=PricingService.percent_from_price(r['cpp_cents'],r['price_cents'],profit_policy) if r['cpp_cents']>0 else 0
                con.execute('UPDATE products SET markup_pct=?,updated_at=? WHERE id=?',(str(pct),now,r['id']))
            con.execute('INSERT INTO audit_log(event_type,entity_type,description,created_at) VALUES(?,?,?,?)',('PRICING_POLICY_RECALCULATED','SETTING',f'Porcentajes recalculados con política {profit_policy}',now))

    def categories(self): return self.fetchall('SELECT * FROM categories WHERE active=1 ORDER BY name')
    def ensure_category(self,name):
        if not name or not name.strip(): return None
        with transaction(self.db_path) as con:
            con.execute('INSERT OR IGNORE INTO categories(name) VALUES(?)',(name.strip(),))
            return con.execute('SELECT id FROM categories WHERE name=? COLLATE NOCASE',(name.strip(),)).fetchone()['id']

    def lots(self, product_id):
        return self.fetchall('''SELECT l.*,pd.purchase_id FROM lots l LEFT JOIN purchase_details pd ON pd.id=l.purchase_detail_id
                                WHERE l.product_id=? ORDER BY CASE WHEN l.expiry_date IS NULL THEN 1 ELSE 0 END,l.expiry_date,l.received_at,l.id''',(product_id,))
