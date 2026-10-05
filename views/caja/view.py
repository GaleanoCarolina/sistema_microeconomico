from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt,QStringListModel
from views.components.widgets import QuantityInput,ArrowComboBox

class CheckoutDialog(QDialog):
    new_customer_requested=pyqtSignal()
    def __init__(self,total_cents,customers,credit_enabled=True,parent=None):
        super().__init__(parent); self.total_cents=total_cents; self.setWindowTitle('Cobrar venta'); self.resize(500,390); root=QVBoxLayout(self)
        title=QLabel('Cobrar venta'); title.setObjectName('dialogTitle'); root.addWidget(title); self.total=QLabel(f'Total a cobrar: Q{total_cents/100:,.2f}'); self.total.setStyleSheet('font-size:24px;font-weight:800;'); root.addWidget(self.total)
        form=QFormLayout(); self.method=ArrowComboBox(); self.method.addItem('Efectivo','CASH')
        if credit_enabled:self.method.addItem('Fiado','CREDIT'); self.method.addItem('Pago parcial + fiado','PARTIAL')
        self.method.addItem('Otro método','OTHER'); form.addRow('¿Cómo pagará?',self.method)
        self.paid=QDoubleSpinBox(); self.paid.setRange(0,9999999); self.paid.setDecimals(2); self.paid.setPrefix('Q '); self.paid.setValue(total_cents/100); form.addRow('Efectivo / pago recibido',self.paid)
        client_box=QWidget(); ch=QHBoxLayout(client_box); ch.setContentsMargins(0,0,0,0); self.customer=ArrowComboBox(); self.customer.setEditable(True); self.customer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); ch.addWidget(self.customer,1); self.new_customer=QPushButton('+ Crear cliente'); self.new_customer.setProperty('class','secondary'); self.new_customer.clicked.connect(self.new_customer_requested); ch.addWidget(self.new_customer); form.addRow('Cliente para el fiado',client_box)
        self.change=QLabel('Cambio: Q0.00'); self.change.setObjectName('successText'); form.addRow('',self.change); root.addLayout(form)
        note=QLabel('Si el cliente no existe, créalo aquí mismo. No perderás la venta que ya preparaste.'); note.setObjectName('help'); note.setWordWrap(True); root.addWidget(note)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Confirmar cobro'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)
        self.set_customers(customers); self.method.currentIndexChanged.connect(self._sync); self.paid.valueChanged.connect(self._sync); self._sync()
    def set_customers(self,customers,select_id=None):
        current=select_id if select_id is not None else self.customer.currentData() if self.customer.count() else None; self.customer.clear(); self.customer.addItem('Buscar o seleccionar cliente…',None)
        for c in customers:self.customer.addItem(f"{c['name']}" + (f" — {c['phone']}" if c['phone'] else ''),c['id'])
        if current is not None:
            idx=self.customer.findData(current)
            if idx>=0:self.customer.setCurrentIndex(idx)
    def add_customer(self,cid,name,phone=''):
        self.customer.addItem(name+(f' — {phone}' if phone else ''),cid); self.customer.setCurrentIndex(self.customer.count()-1)
    def _sync(self):
        method=self.method.currentData(); total=self.total_cents/100; credit=method in ('CREDIT','PARTIAL'); self.customer.setEnabled(credit); self.new_customer.setEnabled(credit)
        if method=='CREDIT': self.paid.blockSignals(True); self.paid.setValue(0); self.paid.setMaximum(0); self.paid.blockSignals(False)
        elif method=='PARTIAL': self.paid.setMaximum(max(0,total-.01));
        elif method=='CASH':
            self.paid.setMaximum(9999999)
            if self.paid.value()<=0: self.paid.setValue(total)
        else: self.paid.setMaximum(total); self.paid.setValue(total)
        self.change.setText(f'Cambio: Q{max(0,self.paid.value()-total):,.2f}' if method=='CASH' else ('Saldo que quedará fiado: Q{:,.2f}'.format(max(0,total-self.paid.value())) if credit else ''))
    def data(self): return {'payment_method':self.method.currentData(),'paid_amount':self.paid.value(),'customer_id':self.customer.currentData()}

class CashView(QWidget):
    request_products=pyqtSignal(str); checkout_requested=pyqtSignal()
    def __init__(self):
        super().__init__(); self.product_map={}; root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(12)
        t=QLabel('Caja'); t.setObjectName('pageTitle'); root.addWidget(t); h=QLabel('Busca por nombre, agrega productos y cobra en pocos pasos.'); h.setObjectName('muted'); root.addWidget(h)
        top=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Buscar producto: coca, arroz, 2.5…'); self.search.setMinimumHeight(46); top.addWidget(self.search,1); clear=QPushButton('Vaciar carrito'); clear.setProperty('class','secondary'); clear.clicked.connect(self.clear_cart); top.addWidget(clear); root.addLayout(top)
        self.completer=QCompleter([]); self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); self.completer.setFilterMode(Qt.MatchFlag.MatchContains); self.search.setCompleter(self.completer); self.search.textEdited.connect(self.request_products); self.search.returnPressed.connect(self._add_from_search); self.completer.activated.connect(self._add_by_name)
        box=QFrame(); box.setObjectName('card'); self.quick=QHBoxLayout(box); self.quick.addWidget(QLabel('Más vendidos:')); self.quick.addStretch(); root.addWidget(box)
        self.table=QTableWidget(0,5); self.table.setHorizontalHeaderLabels(['Producto','Cantidad','Precio','Subtotal','Acciones']); hdr=self.table.horizontalHeader(); hdr.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch); hdr.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents); hdr.setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents); hdr.setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents); hdr.setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents); self.table.setAlternatingRowColors(True); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.verticalHeader().setDefaultSectionSize(46); root.addWidget(self.table,1)
        bottom=QHBoxLayout(); self.total=QLabel('TOTAL: Q0.00'); self.total.setObjectName('pageTitle'); bottom.addWidget(self.total); bottom.addStretch(); self.pay=QPushButton('COBRAR  ·  F4'); self.pay.setMinimumSize(190,50); self.pay.clicked.connect(self.checkout_requested); bottom.addWidget(self.pay); root.addLayout(bottom)
        self.pay.setShortcut('F4')
    def set_products(self,rows): self.product_map={r['name']:dict(r) for r in rows}; self.completer.setModel(QStringListModel(list(self.product_map)))
    def set_quick_products(self,rows):
        while self.quick.count()>2:
            item=self.quick.takeAt(1); w=item.widget();
            if w:w.deleteLater()
        for r in rows[:7]:
            b=QPushButton(r['name']); b.setProperty('class','secondary'); b.clicked.connect(lambda _=False,p=dict(r):self.add_product(p)); self.quick.insertWidget(self.quick.count()-1,b)
    def _add_from_search(self):
        text=self.search.text().strip().lower(); matches=[p for n,p in self.product_map.items() if text in n.lower()]
        if matches:self.add_product(matches[0])
    def _add_by_name(self,name):
        if name in self.product_map:self.add_product(self.product_map[name])
    def add_product(self,p):
        if float(p['stock_qty'])<=0:return
        for row in range(self.table.rowCount()):
            if self.table.item(row,0).data(Qt.ItemDataRole.UserRole)==p['id']:
                spin=self.table.cellWidget(row,1); spin.setValue(min(spin.maximum(),spin.value()+1)); self._focus(); return
        row=self.table.rowCount(); self.table.insertRow(row); item=QTableWidgetItem(p['name']); item.setData(Qt.ItemDataRole.UserRole,p['id']); item.setData(Qt.ItemDataRole.UserRole+1,p['price_cents']); self.table.setItem(row,0,item)
        fractional=(p.get('quantity_mode') or 'INTEGER')=='FRACTIONAL'
        qty=QuantityInput(fractional); qty.setRange(.01 if fractional else 1,float(p['stock_qty'])); qty.setSingleStep(.25 if fractional else 1); qty.setValue(1); qty.setMinimumWidth(150)
        qty.valueChanged.connect(self.recalc); self.table.setCellWidget(row,1,qty); self.table.setItem(row,2,QTableWidgetItem(f"Q{p['price_cents']/100:,.2f}")); self.table.setItem(row,3,QTableWidgetItem(''))
        rem=QPushButton('🗑'); rem.setProperty('class','iconDanger'); rem.setToolTip('Eliminar'); rem.setAccessibleName('Eliminar'); rem.clicked.connect(lambda _=False,w=rem:self._remove_widget(w)); self.table.setCellWidget(row,4,rem); self.recalc(); self._focus()
    def _remove_widget(self,w):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r,4) is w:self.table.removeRow(r); break
        self.recalc(); self._focus()
    def _focus(self): self.search.clear(); self.search.setFocus()
    def recalc(self):
        total=0
        for r in range(self.table.rowCount()):
            qty=self.table.cellWidget(r,1).value(); price=self.table.item(r,0).data(Qt.ItemDataRole.UserRole+1); sub=round(qty*price); total+=sub; self.table.item(r,3).setText(f'Q{sub/100:,.2f}')
        self.total_cents=total; self.total.setText(f'TOTAL: Q{total/100:,.2f}')
    def cart(self): return [{'product_id':self.table.item(r,0).data(Qt.ItemDataRole.UserRole),'quantity':self.table.cellWidget(r,1).value()} for r in range(self.table.rowCount())]
    def clear_cart(self): self.table.setRowCount(0); self.recalc(); self._focus()
