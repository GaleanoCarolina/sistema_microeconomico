from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_single_product_dialog_is_reused_by_controller():
    src=read('controllers/app_controller.py')
    assert src.count('ProductDialog(')>=2
    assert '_new_product_dialog' in src
    assert 'compact=True' in src

def test_product_dialog_uses_scroll_and_fixed_footer_pattern():
    src=read('views/components/dialogs.py')
    assert 'self.scroll=QScrollArea()' in src
    assert 'self.scroll.setWidgetResizable(True)' in src
    assert "footer=QFrame()" in src
    assert "Mostrar más opciones" in src

def test_quantity_control_is_shared_by_sales_and_purchases():
    cash=read('views/caja/view.py'); purchases=read('views/compras/view.py')
    assert 'QuantityInput' in cash
    assert 'QuantityInput' in purchases
    assert "class QuantityInput" in read('views/components/widgets.py')

def test_decisions_and_global_theme_have_visible_scrollbars():
    dec=read('views/decisiones/view.py'); theme=read('views/components/theme.py')
    assert 'ScrollBarAsNeeded' in dec
    assert 'QScrollBar:vertical' in theme
    assert 'min-height:38px' in theme

def test_main_views_do_not_use_absolute_positioning():
    offenders=[]
    for p in (ROOT/'views').rglob('*.py'):
        text=p.read_text(encoding='utf-8')
        # Toast positioning is intentionally floating and not part of a page layout.
        if p.name=='widgets.py': text=text.replace('self.move(QPoint(x,y))','')
        if 'setGeometry(' in text or '.move(' in text: offenders.append(str(p.relative_to(ROOT)))
    assert offenders==[]
