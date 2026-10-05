from decimal import Decimal
import pytest
from repositories.product_repository import ProductRepository
from repositories.settings_repository import SettingsRepository
from services.pricing_service import PricingService
from services.recommendation_service import RecommendationService
from services.purchase_service import PurchaseService
from services.sales_service import SalesService


def test_price_to_percent_and_percent_to_price_markup():
    assert PricingService.percent_from_price(1000,1500,'MARKUP') == Decimal('50.00')
    assert PricingService.price_from_percent(1000,20,'MARKUP') == 1200


def test_price_to_percent_and_percent_to_price_margin():
    assert PricingService.percent_from_price(1000,1250,'MARGIN') == Decimal('20.00')
    assert PricingService.price_from_percent(1000,20,'MARGIN') == 1250


def test_repository_reconciles_percent_before_save(db):
    pr=ProductRepository(db); pid=pr.add('Prueba precio',None,10,13,0,markup_pct=30)
    pr.update(pid,name='Prueba precio',price=15,markup_pct=30,profit_policy='MARKUP')
    p=pr.get(pid)
    assert p['price_cents']==1500
    assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('50.00')
    pr.update(pid,name='Prueba precio',price=12,markup_pct=20,profit_policy='MARKUP')
    p=pr.get(pid)
    assert p['price_cents']==1200
    assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('20.00')


def test_replenishment_respects_stock_pending_and_rounding(db):
    svc=RecommendationService(db)
    base={'daily_demand':4,'lead_days':3,'safety_stock':2,'available_stock':5,'pending_qty':0,'quantity_mode':'INTEGER'}
    assert svc.suggested_purchase(base)==21


def test_replenishment_pending_order_reduces_suggestion(db):
    svc=RecommendationService(db)
    m={'daily_demand':1,'lead_days':4,'safety_stock':3,'available_stock':5,'pending_qty':4,'quantity_mode':'INTEGER'}
    # objetivo = 1*(4+3)+3 = 10; 10 - 5 - 4 = 1
    assert svc.suggested_purchase(m)==1
    m['pending_qty']=10
    assert svc.suggested_purchase(m)==0

def test_fractional_replenishment_uses_quarter_steps(db):
    svc=RecommendationService(db)
    m={'daily_demand':0.33,'lead_days':4,'safety_stock':0.5,'available_stock':1,'pending_qty':0,'quantity_mode':'FRACTIONAL'}
    result=svc.suggested_purchase(m)
    assert Decimal(str(result)) % Decimal('0.25') == 0

def test_profit_policy_setting_persists_without_schema_change(db):
    s=SettingsRepository(db); s.set('profit_policy','MARGIN')
    assert s.get('profit_policy')=='MARGIN'

def test_high_stock_does_not_need_replenishment(db):
    svc=RecommendationService(db)
    m={'daily_demand':1,'lead_days':3,'safety_stock':2,'available_stock':50,'pending_qty':0,'quantity_mode':'INTEGER'}
    assert svc.suggested_purchase(m)==0


def test_expiring_inventory_is_not_recommended_for_purchase(db):
    from datetime import timedelta
    from utils.dates import local_today
    pr=ProductRepository(db); pid=pr.add('Yogur',None,5,8,0,expires=True)
    ps=PurchaseService(db); ps.create_purchase([{'product_id':pid,'quantity':20,'unit_cost':5,'expiry_date':(local_today()+timedelta(days=2)).isoformat()}])
    # Generar algunas ventas recientes para que exista demanda histórica.
    SalesService(db).create_sale([{'product_id':pid,'quantity':2}])
    recs=RecommendationService(db).generate()
    actions=[r.accion for r in recs if r.producto_id==pid]
    assert 'PRIORIZAR VENTA POR VENCIMIENTO' in actions
    assert 'COMPRAR PRONTO' not in actions

def test_change_profit_policy_can_recalculate_without_changing_price(db):
    pr=ProductRepository(db); pid=pr.add('Política',None,10,15,0,markup_pct=50)
    pr.recalculate_percentages('MARGIN')
    p=pr.get(pid)
    assert p['price_cents']==1500 and p['cpp_cents']==1000
    assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('33.33')
