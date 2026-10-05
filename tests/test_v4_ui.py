import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
pytest.importorskip('PyQt6')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate
from views.components.dialogs import ProductDialog
from views.components.calendar_dialog import CalendarDialog
from views.inventario.view import InventoryView

@pytest.fixture(scope='module')
def app():
    inst=QApplication.instance() or QApplication([])
    return inst

def test_product_dialog_price_margin_sync(app):
    p={'name':'Producto','category_name':'Abarrotes','unit_name':'unidad','quantity_mode':'INTEGER','cpp_cents':1000,'price_cents':1300,'markup_pct':'30','min_stock':5,'expires':0}
    dlg=ProductDialog([{'name':'Abarrotes'}],existing=p,catalog=[],profit_policy='MARKUP')
    dlg.price.setValue(15)
    assert round(dlg.markup.value(),2)==50.00
    dlg.markup.setValue(20)
    assert round(dlg.price.value(),2)==12.00

def test_calendar_selected_date_is_persistent(app):
    dlg=CalendarDialog(None,'Fecha','2026-10-27')
    assert dlg.cal.selectedDate()==QDate(2026,10,27)
    assert dlg.iso_date()=='2026-10-27'

def test_inventory_programmatic_selection(app):
    v=InventoryView(); v.set_rows([{'id':7,'name':'Coca-Cola','category_name':'Bebidas','lot_stock':3,'stock_qty':3,'unit_name':'unidad','cpp_cents':500,'price_cents':700,'margin_pct':40,'min_stock':1,'stagnant':False,'next_expiry':None,'unknown_expiry_qty':0}])
    assert v.select_product(7)
    assert v.table.currentRow()==0
