import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
pytest.importorskip('PyQt6')
from PyQt6.QtWidgets import QApplication
from views.components.widgets import QuantityInput
from views.components.dialogs import ProductDialog
from views.decisiones.view import DecisionsView

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])

def test_quantity_control_formats_integer_and_fractional(app):
    integer=QuantityInput(False); integer.setValue(100); assert integer.edit.text()=='100'; assert integer.value()==100
    fractional=QuantityInput(True); fractional.setValue(100.75); assert fractional.edit.text()=='100.75'; assert fractional.value()==100.75

def test_product_dialog_is_resizable_scrollable_and_shared_modes(app):
    cats=[{'name':'Abarrotes'}]
    full=ProductDialog(cats,compact=False,catalog=[]); quick=ProductDialog(cats,compact=True,catalog=[])
    assert full.minimumHeight()<=520
    assert full.scroll.widgetResizable()
    assert quick.scroll.widgetResizable()
    assert not quick.advanced.isVisible()
    quick.more.setChecked(True); assert quick.advanced.isVisible()

def test_decisions_exposes_vertical_scrollbar(app):
    view=DecisionsView()
    assert view.scroll.verticalScrollBarPolicy().name=='ScrollBarAsNeeded'
