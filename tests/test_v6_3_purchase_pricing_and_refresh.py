from decimal import Decimal
from database.connection import connect
from repositories.product_repository import ProductRepository
from services.purchase_service import PurchaseService


def test_received_purchase_can_update_sale_price_and_percentage(db):
    pr=ProductRepository(db)
    # Inventario inicial: 10 unidades a Q22, venta Q25.
    pid=pr.add('Coca-Cola',None,22,25,10,markup_pct='13.64')
    ps=PurchaseService(db)
    ps.create_purchase([{'product_id':pid,'quantity':10,'unit_cost':24,'sale_price':27}])
    p=pr.get(pid)
    assert p['cpp_cents']==2300
    assert p['price_cents']==2700
    # Recargo coherente con el nuevo CPP: (27-23)/23 = 17.39%
    assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('17.39')
    con=connect(db)
    try:
        row=con.execute('SELECT desired_price_cents FROM purchase_details WHERE product_id=? ORDER BY id DESC LIMIT 1',(pid,)).fetchone()
        assert row['desired_price_cents']==2700
        ph=con.execute('SELECT old_price_cents,new_price_cents FROM price_history WHERE product_id=? ORDER BY id DESC LIMIT 1',(pid,)).fetchone()
        assert tuple(ph)==(2500,2700)
    finally:
        con.close()


def test_pending_purchase_applies_chosen_price_when_received(db):
    pr=ProductRepository(db); pid=pr.add('Aceite',None,10,13,5,markup_pct='30')
    ps=PurchaseService(db)
    purchase_id,_=ps.create_purchase([{'product_id':pid,'quantity':5,'unit_cost':12,'sale_price':15}],status='PENDING')
    assert pr.get(pid)['price_cents']==1300
    ps.receive_purchase(purchase_id)
    p=pr.get(pid)
    assert p['cpp_cents']==1100
    assert p['price_cents']==1500
    assert Decimal(p['markup_pct']).quantize(Decimal('0.01'))==Decimal('36.36')


def test_sale_event_refreshes_clients_and_fiados_statically():
    from pathlib import Path
    src=(Path(__file__).resolve().parents[1]/'controllers'/'app_controller.py').read_text(encoding='utf-8')
    assert "self.events.sale_changed.connect(lambda:(self.refresh_inventory(''),self.refresh_cash_products(''),self.refresh_customers('')" in src


def test_all_regular_list_combos_use_visible_arrow_component():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]/'views'
    offenders=[]
    for file in root.rglob('*.py'):
        text=file.read_text(encoding='utf-8')
        if file.name=='dialogs.py':
            # Categoría y unidad usan su propio botón ▼ externo editable.
            text=text.replace('self.category=QComboBox()','').replace('self.unit=QComboBox()','')
        if 'QComboBox()' in text:
            offenders.append(str(file.relative_to(root)))
    assert offenders==[]
