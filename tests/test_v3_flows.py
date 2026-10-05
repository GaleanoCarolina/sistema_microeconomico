from datetime import timedelta
from decimal import Decimal
from database.connection import connect, transaction
from repositories.product_repository import ProductRepository
from repositories.history_repository import HistoryRepository
from services.purchase_service import PurchaseService
from services.sales_service import SalesService
from services.inventory_service import InventoryService
from services.analytics_service import AnalyticsService
from services.pricing_service import PricingService
from services.recommendation_service import RecommendationService
from utils.dates import local_today


def test_received_purchase_visible_for_multiple_products(db):
    pr=ProductRepository(db); ps=PurchaseService(db)
    ids=[pr.add(n,None,0,5,0) for n in ['Arroz','Tortrix','Coca-Cola','Aceite']]
    ps.create_purchase([{'product_id':pid,'quantity':q,'unit_cost':c} for pid,q,c in zip(ids,[10,25,12,8],[4,1,6,10])])
    rows={r['name']:r for r in pr.inventory_rows()}
    assert set(rows)=={'Arroz','Tortrix','Coca-Cola','Aceite'}
    assert [rows[n]['lot_stock'] for n in ['Arroz','Tortrix','Coca-Cola','Aceite']]==[10,25,12,8]


def test_zero_stock_product_remains_in_inventory(db):
    pr=ProductRepository(db); pid=pr.add('Arroz',None,5,10,10)
    SalesService(db).create_sale([{'product_id':pid,'quantity':10}])
    row=next(r for r in pr.inventory_rows() if r['id']==pid)
    assert row['lot_stock']==0


def test_pending_purchase_does_not_increase_then_receipt_does(db):
    pr=ProductRepository(db); pid=pr.add('Aceite',None,10,15,0); ps=PurchaseService(db)
    purchase_id,_=ps.create_purchase([{'product_id':pid,'quantity':8,'unit_cost':10}],status='PENDING')
    assert pr.get(pid)['stock_qty']==0
    assert next(r for r in pr.inventory_rows() if r['id']==pid)['lot_stock']==0
    ps.receive_purchase(purchase_id)
    assert pr.get(pid)['stock_qty']==8
    assert next(r for r in pr.inventory_rows() if r['id']==pid)['lot_stock']==8


def test_purchase_total_and_history_amount(db):
    pr=ProductRepository(db); a=pr.add('Tortrix',None,0,3,0); c=pr.add('Coca-Cola',None,0,8,0)
    pid,_=PurchaseService(db).create_purchase([{'product_id':a,'quantity':10,'unit_cost':2},{'product_id':c,'quantity':5,'unit_cost':6}])
    con=connect(db)
    try:
        pu=con.execute('SELECT subtotal_cents,total_cents FROM purchases WHERE id=?',(pid,)).fetchone(); assert pu['subtotal_cents']==5000 and pu['total_cents']==5000
        details=con.execute('SELECT subtotal_cents FROM purchase_details WHERE purchase_id=? ORDER BY id',(pid,)).fetchall(); assert [x['subtotal_cents'] for x in details]==[2000,3000]
    finally: con.close()
    hist=[r for r in HistoryRepository(db).activity() if r['tipo']=='PURCHASE' and r['ref']==pid][0]; assert hist['monto']==5000


def test_purchase_discount_and_additional_costs_persist(db):
    pr=ProductRepository(db); pid=pr.add('Producto',None,0,10,0)
    pu,_=PurchaseService(db).create_purchase([{'product_id':pid,'quantity':10,'unit_cost':5}],discount=3,additional_costs=2)
    con=connect(db)
    try:
        r=con.execute('SELECT subtotal_cents,discount_cents,additional_costs_cents,total_cents FROM purchases WHERE id=?',(pu,)).fetchone()
        assert tuple(r)==(5000,300,200,4900)
    finally:con.close()


def test_inventory_reconciliation_matches_lots_and_movements(db):
    pr=ProductRepository(db); pid=pr.add('Leche',None,5,8,0,expires=True)
    PurchaseService(db).create_purchase([{'product_id':pid,'quantity':10,'unit_cost':5,'expiry_date':(local_today()+timedelta(days=20)).isoformat()}])
    SalesService(db).create_sale([{'product_id':pid,'quantity':3}])
    assert InventoryService(db).reconcile()==[]


def test_multiple_lots_same_product_one_master_row(db):
    pr=ProductRepository(db); pid=pr.add('Leche',None,0,8,0,expires=True); ps=PurchaseService(db)
    d1=(local_today()+timedelta(days=10)).isoformat(); d2=(local_today()+timedelta(days=20)).isoformat()
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':5,'expiry_date':d1}]); ps.create_purchase([{'product_id':pid,'quantity':20,'unit_cost':6,'expiry_date':d2}])
    rows=[r for r in pr.inventory_rows() if r['id']==pid]; assert len(rows)==1 and rows[0]['lot_stock']==30 and rows[0]['next_expiry']==d1
    assert len(pr.lots(pid))==2


def test_fractional_quantity_product(db):
    pr=ProductRepository(db); pid=pr.add('Frijol a granel',None,10,15,0,unit_name='libra',quantity_mode='FRACTIONAL')
    PurchaseService(db).create_purchase([{'product_id':pid,'quantity':1.5,'unit_cost':10}])
    assert next(r for r in pr.inventory_rows() if r['id']==pid)['lot_stock']==1.5
    SalesService(db).create_sale([{'product_id':pid,'quantity':0.5}])
    assert next(r for r in pr.inventory_rows() if r['id']==pid)['lot_stock']==1.0


def test_price_markup_coherence(db):
    pr=ProductRepository(db); pid=pr.add('Producto',None,10,13,0,markup_pct=30)
    pr.set_price(pid,1400)
    p=pr.get(pid); assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('40.00')
    assert PricingService.price_from_markup(1000,40)==1400


def test_cpp_and_historical_purchase_costs_do_not_change(db):
    pr=ProductRepository(db); pid=pr.add('Tortrix',None,0,4,0); ps=PurchaseService(db)
    p1,_=ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':2}]); p2,_=ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':3}])
    assert pr.get(pid)['cpp_cents']==250
    con=connect(db)
    try:
        assert con.execute('SELECT unit_cost_cents FROM purchase_details WHERE purchase_id=?',(p1,)).fetchone()['unit_cost_cents']==200
        assert con.execute('SELECT unit_cost_cents FROM purchase_details WHERE purchase_id=?',(p2,)).fetchone()['unit_cost_cents']==300
    finally:con.close()


def test_purchase_period_and_gross_profit_are_distinct(db):
    pr=ProductRepository(db); pid=pr.add('Tortrix',None,0,3,0); ps=PurchaseService(db)
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':2}])
    SalesService(db).create_sale([{'product_id':pid,'quantity':5}])
    d=AnalyticsService(db).dashboard('Hoy')
    assert d['purchases_cents']==2000 and d['sales_cents']==1500 and d['cogs_cents']==1000 and d['profit_cents']==500
    assert d['inventory_cents']==1000


def test_recommendation_calculation_is_deterministic_and_integer(db):
    svc=RecommendationService(db)
    m={'daily_demand':0.72,'lead_days':4,'safety_stock':5,'available_stock':5,'pending_qty':0,'quantity_mode':'INTEGER'}
    a=svc.suggested_purchase(m); b=svc.suggested_purchase(m)
    assert a==b and isinstance(a,int) and a>0


def test_inventory_not_hardcoded_to_demo_product(db):
    pr=ProductRepository(db); pid=pr.add('Tortrix Barbacoa',None,0,2,0)
    PurchaseService(db).create_purchase([{'product_id':pid,'quantity':7,'unit_cost':1}])
    rows=pr.inventory_rows(); assert len(rows)==1 and rows[0]['name']=='Tortrix Barbacoa' and rows[0]['lot_stock']==7

def test_cogs_uses_cpp_while_fefo_controls_physical_lots(db):
    pr=ProductRepository(db); pid=pr.add('Producto CPP',None,0,5,0); ps=PurchaseService(db)
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':2}])
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':4}])
    assert pr.get(pid)['cpp_cents']==300
    sale=SalesService(db).create_sale([{'product_id':pid,'quantity':2}])
    assert sale['gross_profit_cents']==400  # Q10 venta - Q6 CPP de lo vendido
    con=connect(db)
    try:
        sd=con.execute('SELECT unit_cost_cents,cost_total_cents FROM sale_details WHERE sale_id=?',(sale['sale_id'],)).fetchone()
        assert sd['unit_cost_cents']==300 and sd['cost_total_cents']==600
        lots=con.execute('SELECT unit_cost_cents,quantity_remaining FROM lots WHERE product_id=? ORDER BY id',(pid,)).fetchall()
        assert lots[0]['unit_cost_cents']==200 and lots[0]['quantity_remaining']==8
    finally: con.close()
