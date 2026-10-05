from datetime import timedelta
from database.connection import connect,transaction
from database.migrate import migrate
from repositories.product_repository import ProductRepository
from repositories.customer_repository import CustomerRepository
from repositories.supplier_repository import SupplierRepository
from services.purchase_service import PurchaseService
from services.sales_service import SalesService
from services.credit_service import CreditService
from utils.dates import local_today,iso_now


def seed_demo(db_path=None):
    migrate(db_path); con=connect(db_path)
    try:
        if con.execute('SELECT COUNT(*) c FROM products').fetchone()['c']>0:return False
    finally:con.close()
    pr=ProductRepository(db_path); cr=CustomerRepository(db_path); sr=SupplierRepository(db_path); ps=PurchaseService(db_path); ss=SalesService(db_path); cs=CreditService(db_path); today=local_today()
    cats={n:pr.ensure_category(n) for n in ['Granos','Bebidas','Lácteos','Abarrotes','Limpieza','Higiene','Golosinas']}; sup1=sr.ensure('Distribuidora Jalapa',3); sup2=sr.ensure('Mayorista Oriente',5); sup3=sr.ensure('Lácteos del Valle',2)
    specs=[('Arroz Blanco 1 lb','Granos',6,8,20,5,False),('Frijol Negro 1 lb','Granos',8.5,11.5,16,5,False),('Aceite 900 ml','Abarrotes',16,21,12,4,False),('Azúcar 1 lb','Granos',4.5,6.5,18,5,False),('Huevos docena','Abarrotes',28,35,10,4,False),('Leche Entera 1 L','Lácteos',9.5,12,0,4,True),('Coca-Cola 2.5 L','Bebidas',13.5,18,0,6,True),('Pepsi 2.5 L','Bebidas',12.5,17,14,5,False),('Pan Sandwich','Abarrotes',12,16,0,3,True),('Galleta Chocolate X','Golosinas',4,6,45,5,False),('Detergente 500 g','Limpieza',10,14,15,4,False),('Jabón de baño','Higiene',3.5,5,25,5,False),('Papel higiénico 4 rollos','Higiene',12,16.5,11,4,False),('Shampoo 400 ml','Higiene',22,30,7,2,False)]
    products={}
    for name,cat,cost,price,qty,min_s,exp in specs:products[name]=pr.add(name,cats[cat],cost,price,qty,25,min_s,exp,None,'unidad')
    with transaction(db_path) as con:
        for name,pid in products.items():con.execute('UPDATE products SET usual_supplier_id=? WHERE id=?',(sup3 if 'Leche' in name else sup1,pid))
    # Lotes independientes de Coca-Cola: 10, 15 y 5 unidades; el último sin fecha.
    ps.create_purchase([{'product_id':products['Coca-Cola 2.5 L'],'quantity':10,'unit_cost':13.5,'expiry_date':(today+timedelta(days=47)).isoformat()}],sup1)
    ps.create_purchase([{'product_id':products['Coca-Cola 2.5 L'],'quantity':15,'unit_cost':14.5,'expiry_date':(today+timedelta(days=72)).isoformat()}],sup2)
    ps.create_purchase([{'product_id':products['Coca-Cola 2.5 L'],'quantity':5,'unit_cost':14.8,'expiry_date':None}],sup2)
    ps.create_purchase([{'product_id':products['Leche Entera 1 L'],'quantity':12,'unit_cost':9.5,'expiry_date':(today+timedelta(days=3)).isoformat()}],sup3)
    ps.create_purchase([{'product_id':products['Pan Sandwich'],'quantity':9,'unit_cost':12,'expiry_date':(today+timedelta(days=8)).isoformat()}],sup1)
    # Historial con fechas locales consistentes.
    sale_ids=[]
    for d in range(18,0,-1):
        try:r=ss.create_sale([{'product_id':products['Arroz Blanco 1 lb'],'quantity':1+(d%2)},{'product_id':products['Coca-Cola 2.5 L'],'quantity':1}],'CASH'); sale_ids.append((r['sale_id'],d))
        except ValueError:break
    for sid,d in sale_ids:
        with transaction(db_path) as con:con.execute('UPDATE sales SET sold_at=? WHERE id=?',((today-timedelta(days=d)).isoformat()+' 12:00:00',sid))
    r=ss.create_sale([{'product_id':products['Galleta Chocolate X'],'quantity':2}],'CASH')
    with transaction(db_path) as con:
        con.execute('UPDATE sales SET sold_at=? WHERE id=?',((today-timedelta(days=75)).isoformat()+' 12:00:00',r['sale_id'])); con.execute('UPDATE products SET created_at=? WHERE id=?',((today-timedelta(days=100)).isoformat()+' 09:00:00',products['Galleta Chocolate X']))
    juan=cr.add('Juan Pérez','5555-0101','Jalapa','Cliente frecuente',500); maria=cr.add('María López','5555-0202','Jalapa','',300)
    ss.create_sale([{'product_id':products['Frijol Negro 1 lb'],'quantity':2},{'product_id':products['Aceite 900 ml'],'quantity':1}],'PARTIAL',juan,10); ss.create_sale([{'product_id':products['Pepsi 2.5 L'],'quantity':2}],'CREDIT',maria,0); cs.add_payment(juan,5,'Abono de demostración')
    return True
