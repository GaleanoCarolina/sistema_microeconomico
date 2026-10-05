from datetime import timedelta
from repositories.product_repository import ProductRepository
from repositories.customer_repository import CustomerRepository
from services.purchase_service import PurchaseService
from services.sales_service import SalesService
from services.credit_service import CreditService
from services.analytics_service import AnalyticsService
from services.inventory_service import InventoryService
from database.connection import connect
from utils.dates import local_today


def test_dashboard_sale_credit_and_payment_are_separated(db):
    pr=ProductRepository(db); cr=CustomerRepository(db)
    pid=pr.add('Arroz Premium',None,5,10,20); cid=cr.add('Juan Pérez')
    ss=SalesService(db); cs=CreditService(db); a=AnalyticsService(db)
    ss.create_sale([{'product_id':pid,'quantity':1}],'CASH',paid_amount=20)
    ss.create_sale([{'product_id':pid,'quantity':2}],'CREDIT',cid,0)
    ss.create_sale([{'product_id':pid,'quantity':1}],'PARTIAL',cid,5)
    d=a.dashboard('Hoy')
    assert d['sales_cents']==4000
    assert d['sale_paid_cents']==1500
    assert d['paid_cents']==1500
    assert d['credit_cents']==2500
    cs.add_payment(cid,10)
    d=a.dashboard('Hoy')
    assert d['sales_cents']==4000
    assert d['payments_cents']==1000
    assert d['paid_cents']==2500
    assert d['receivable_cents']==1500
    assert d['profit_cents']==2000


def test_best_seller_by_units(db):
    pr=ProductRepository(db); a=AnalyticsService(db); ss=SalesService(db)
    a_id=pr.add('Pan',None,1,2,50); b_id=pr.add('Aceite',None,10,20,50)
    ss.create_sale([{'product_id':a_id,'quantity':6},{'product_id':b_id,'quantity':2}])
    d=a.dashboard('Hoy')
    assert d['best_product']['name']=='Pan'
    assert d['best_product']['units']==6


def test_duplicate_normalization(db):
    pr=ProductRepository(db); pr.add('Coca-Cola 2.5 L',None,10,15,0)
    found=pr.duplicate_candidates('coca cola 2.5l')
    assert found and found[0]['name']=='Coca-Cola 2.5 L'


def test_independent_lots_and_fefo_unknown_last(db):
    pr=ProductRepository(db); pid=pr.add('Coca-Cola 2.5 L',None,10,15,0,25,5,True)
    ps=PurchaseService(db); ss=SalesService(db); today=local_today()
    d1=(today+timedelta(days=30)).isoformat(); d2=(today+timedelta(days=60)).isoformat()
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':10,'expiry_date':d1}])
    ps.create_purchase([{'product_id':pid,'quantity':15,'unit_cost':11,'expiry_date':d2}])
    ps.create_purchase([{'product_id':pid,'quantity':5,'unit_cost':12,'expiry_date':None}])
    ss.create_sale([{'product_id':pid,'quantity':12}])
    con=connect(db)
    try:
        lots=con.execute('SELECT expiry_date,quantity_remaining FROM lots WHERE product_id=? ORDER BY CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END,expiry_date',(pid,)).fetchall()
        assert lots[0]['expiry_date']==d1 and lots[0]['quantity_remaining']==0
        assert lots[1]['expiry_date']==d2 and lots[1]['quantity_remaining']==13
        assert lots[2]['expiry_date'] is None and lots[2]['quantity_remaining']==5
    finally: con.close()


def test_lot_expiry_can_be_added_later(db):
    pr=ProductRepository(db); pid=pr.add('Leche',None,5,8,0,25,2,True)
    _,changes=PurchaseService(db).create_purchase([{'product_id':pid,'quantity':3,'unit_cost':5,'expiry_date':None}])
    lot_id=changes[0]['lot_id']; expiry=(local_today()+timedelta(days=10)).isoformat(); InventoryService(db).update_lot_expiry(lot_id,expiry)
    assert pr.lots(pid)[0]['expiry_date']==expiry
