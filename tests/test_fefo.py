from datetime import timedelta
from utils.dates import local_today
from repositories.product_repository import ProductRepository
from services.purchase_service import PurchaseService
from services.sales_service import SalesService
from database.connection import connect

def test_fefo_consumes_earliest(db):
    pr=ProductRepository(db); pid=pr.add('Leche',None,10,15,0,25,2,True)
    ps=PurchaseService(db); ss=SalesService(db)
    early=(local_today()+timedelta(days=5)).isoformat(); late=(local_today()+timedelta(days=20)).isoformat()
    ps.create_purchase([{'product_id':pid,'quantity':3,'unit_cost':10,'expiry_date':late}])
    ps.create_purchase([{'product_id':pid,'quantity':2,'unit_cost':11,'expiry_date':early}])
    ss.create_sale([{'product_id':pid,'quantity':2}])
    con=connect(db)
    try:
        rows=con.execute('SELECT expiry_date,quantity_remaining FROM lots WHERE product_id=? ORDER BY expiry_date',(pid,)).fetchall()
        assert rows[0]['expiry_date']==early and rows[0]['quantity_remaining']==0
        assert rows[1]['quantity_remaining']==3
    finally: con.close()

def test_expired_not_sold(db):
    pr=ProductRepository(db); pid=pr.add('Yogur',None,5,8,0,25,1,True)
    ps=PurchaseService(db); ss=SalesService(db)
    ps.create_purchase([{'product_id':pid,'quantity':2,'unit_cost':5,'expiry_date':(local_today()-timedelta(days=1)).isoformat()}])
    try: ss.create_sale([{'product_id':pid,'quantity':1}]); assert False
    except ValueError as e: assert 'inventario' in str(e).lower()
