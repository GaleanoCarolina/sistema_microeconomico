from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt,QStringListModel,QDate
from views.components.calendar_dialog import CalendarDialog
from views.components.widgets import QuantityInput,ArrowComboBox
from services.cpp_service import CPPService
from services.pricing_service import PricingService


class PurchaseView(QWidget):
    request_products=pyqtSignal(str); save_requested=pyqtSignal(); new_product_requested=pyqtSignal(); new_supplier_requested=pyqtSignal(); pending_requested=pyqtSignal()
    def __init__(self):
        super().__init__(); self.product_map={}; self.profit_policy='MARKUP'; root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(12)
        head=QHBoxLayout(); t=QLabel('Nueva compra'); t.setObjectName('pageTitle'); head.addWidget(t); head.addStretch(); pending=QPushButton('Compras pendientes'); pending.setProperty('class','secondary'); pending.clicked.connect(self.pending_requested); head.addWidget(pending); root.addLayout(head)
        s=QLabel('Registra una compra recibida ahora o déjala pendiente. El costo de entrada actualiza el CPP y puedes definir aquí mismo el precio de venta que quedará vigente.'); s.setObjectName('muted'); s.setWordWrap(True); root.addWidget(s)
        meta=QFrame(); meta.setObjectName('card'); ml=QGridLayout(meta); ml.addWidget(QLabel('Proveedor'),0,0); self.supplier=ArrowComboBox(); self.supplier.setEditable(True); ml.addWidget(self.supplier,0,1); ns=QPushButton('+ Nuevo proveedor'); ns.setProperty('class','secondary'); ns.clicked.connect(self.new_supplier_requested); ml.addWidget(ns,0,2)
        ml.addWidget(QLabel('Fecha de compra'),1,0); self.purchase_date=QDateEdit(QDate.currentDate()); self.purchase_date.setCalendarPopup(True); self.purchase_date.setDisplayFormat('dd/MM/yyyy'); ml.addWidget(self.purchase_date,1,1)
        ml.addWidget(QLabel('Estado'),1,2); self.status=ArrowComboBox(); self.status.addItem('Recibida ahora','RECEIVED'); self.status.addItem('Pendiente de recibir','PENDING'); self.status.currentIndexChanged.connect(self._sync_receipt); ml.addWidget(self.status,1,3)
        self.same_day=QCheckBox('Mercancía recibida el mismo día'); self.same_day.setChecked(True); self.same_day.toggled.connect(self._sync_receipt); ml.addWidget(self.same_day,2,0,1,2); self.received_label=QLabel('Fecha de recepción'); ml.addWidget(self.received_label,2,2); self.received_date=QDateEdit(QDate.currentDate()); self.received_date.setCalendarPopup(True); self.received_date.setDisplayFormat('dd/MM/yyyy'); ml.addWidget(self.received_date,2,3); root.addWidget(meta); self._sync_receipt()
        searchrow=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Buscar producto existente…'); self.search.setMinimumHeight(44); searchrow.addWidget(self.search,1); np=QPushButton('+ Crear producto nuevo'); np.setProperty('class','secondary'); np.clicked.connect(self.new_product_requested); searchrow.addWidget(np); root.addLayout(searchrow)
        self.completer=QCompleter([]); self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); self.completer.setFilterMode(Qt.MatchFlag.MatchContains); self.search.setCompleter(self.completer); self.search.textEdited.connect(self.request_products); self.search.returnPressed.connect(self._add_from_search); self.completer.activated.connect(self._add_by_name)
        self.table=QTableWidget(0,8); self.table.setHorizontalHeaderLabels(['Producto','Cantidad','Costo unitario','CPP después','Precio de venta','Subtotal','Vencimiento','Acciones'])
        hdr=self.table.horizontalHeader(); hdr.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        for c in (1,2,3,4,5,6,7): hdr.setSectionResizeMode(c,QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.verticalHeader().setDefaultSectionSize(48); root.addWidget(self.table,1)
        help_price=QLabel('Precio de venta: se precarga conservando tu porcentaje de ganancia con el CPP estimado. Puedes escribir otro precio y se respetará.'); help_price.setObjectName('help'); help_price.setWordWrap(True); root.addWidget(help_price)
        extras=QFrame(); extras.setObjectName('card'); el=QHBoxLayout(extras); el.addWidget(QLabel('Descuento')); self.discount=QDoubleSpinBox(); self.discount.setPrefix('Q '); self.discount.setMaximum(999999); self.discount.valueChanged.connect(self.recalc); el.addWidget(self.discount); el.addWidget(QLabel('Costos adicionales')); self.additional=QDoubleSpinBox(); self.additional.setPrefix('Q '); self.additional.setMaximum(999999); self.additional.valueChanged.connect(self.recalc); el.addWidget(self.additional); el.addStretch(); root.addWidget(extras)
        bottom=QHBoxLayout(); self.total=QLabel('TOTAL: Q0.00'); self.total.setObjectName('pageTitle'); bottom.addWidget(self.total); self.proposal_hint=QLabel(''); self.proposal_hint.setObjectName('help'); bottom.addWidget(self.proposal_hint); bottom.addStretch(); save=QPushButton('REGISTRAR COMPRA'); save.setProperty('class','accent'); save.setMinimumSize(190,48); save.clicked.connect(self.save_requested); bottom.addWidget(save); root.addLayout(bottom)

    def set_profit_policy(self,policy):
        self.profit_policy=str(policy or 'MARKUP').upper(); self.recalc()

    def _sync_receipt(self):
        received=self.status.currentData()=='RECEIVED'; self.same_day.setVisible(received); show_date=received and not self.same_day.isChecked(); self.received_label.setVisible(show_date); self.received_date.setVisible(show_date)
        if received and self.same_day.isChecked(): self.received_date.setDate(self.purchase_date.date())

    def set_products(self,rows): self.product_map={r['name']:dict(r) for r in rows}; self.completer.setModel(QStringListModel(list(self.product_map)))
    def set_suppliers(self,rows,select_id=None):
        current=select_id if select_id is not None else self.supplier.currentData(); self.supplier.clear(); self.supplier.addItem('Sin proveedor',None)
        for r in rows:self.supplier.addItem(r['name'],r['id'])
        if current is not None:
            idx=self.supplier.findData(current)
            if idx>=0:self.supplier.setCurrentIndex(idx)
    def add_supplier(self,sid,name): self.supplier.addItem(name,sid); self.supplier.setCurrentIndex(self.supplier.count()-1)
    def _add_from_search(self):
        txt=self.search.text().strip().lower(); matches=[p for n,p in self.product_map.items() if txt in n.lower()]
        if matches:self.add_product(matches[0])
    def _add_by_name(self,name):
        if name in self.product_map:self.add_product(self.product_map[name])
    def _qty_control(self,p,value=1):
        fractional=(p.get('quantity_mode') or 'INTEGER')=='FRACTIONAL'; w=QuantityInput(fractional); w.setRange(.01 if fractional else 1,999999); w.setSingleStep(.25 if fractional else 1); w.setValue(float(value)); w.setMinimumWidth(150); w.valueChanged.connect(self.recalc); return w
    def _money_input(self,value=0):
        w=QDoubleSpinBox(); w.setRange(0,999999); w.setDecimals(2); w.setPrefix('Q '); w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons); w.setMinimumWidth(125); w.setValue(float(value)); return w

    def add_product(self,p,quantity=1,suggested=False):
        for r in range(self.table.rowCount()):
            if self.table.item(r,0).data(Qt.ItemDataRole.UserRole)==p['id']:
                self.table.cellWidget(r,1).setValue(quantity if suggested else self.table.cellWidget(r,1).value()+1); self._focus(); return
        r=self.table.rowCount(); self.table.insertRow(r); it=QTableWidgetItem(p['name']); it.setData(Qt.ItemDataRole.UserRole,p['id']); it.setData(Qt.ItemDataRole.UserRole+1,dict(p)); self.table.setItem(r,0,it)
        qty=self._qty_control(p,quantity); self.table.setCellWidget(r,1,qty)
        cost=self._money_input((p.get('cpp_cents') or 0)/100); cost.setToolTip('Costo real pagado por cada unidad en esta compra.'); cost.valueChanged.connect(self.recalc); self.table.setCellWidget(r,2,cost)
        cpp_item=QTableWidgetItem('Q0.00'); cpp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.table.setItem(r,3,cpp_item)
        price=self._money_input((p.get('price_cents') or 0)/100); price.setProperty('manualPrice',False); price.setToolTip('Precio de venta que quedará vigente al recibir esta compra. Se sugiere automáticamente y puedes cambiarlo.'); price.valueChanged.connect(lambda _v,w=price:self._mark_price_manual(w)); self.table.setCellWidget(r,4,price)
        self.table.setItem(r,5,QTableWidgetItem(''))
        if p.get('expires'):
            exp=QPushButton('Elegir fecha'); exp.setProperty('class','secondary'); exp.setProperty('expiry',''); exp.clicked.connect(lambda _=False,w=exp:self._choose_expiry(w)); self.table.setCellWidget(r,6,exp)
        else:
            lab=QLabel('No aplica'); lab.setObjectName('muted'); lab.setAlignment(Qt.AlignmentFlag.AlignCenter); self.table.setCellWidget(r,6,lab)
        rem=QPushButton('🗑'); rem.setProperty('class','iconDanger'); rem.setToolTip('Eliminar'); rem.setAccessibleName('Eliminar'); rem.clicked.connect(lambda _=False,w=rem:self._remove(w)); self.table.setCellWidget(r,7,rem); self.recalc(); self._focus()

    def _mark_price_manual(self,w):
        if not w.property('autoUpdating'):
            w.setProperty('manualPrice',True)

    def _estimated_cpp(self,p,qty,cost_value):
        return CPPService.calculate(p.get('stock_qty') or 0,p.get('cpp_cents') or 0,qty,round(cost_value*100))

    def load_proposal(self,p,quantity,supplier_id=None,reason=''):
        self.clear_form(); self.add_product(p,quantity,True)
        if supplier_id is not None:
            idx=self.supplier.findData(supplier_id)
            if idx>=0:self.supplier.setCurrentIndex(idx)
        self.proposal_hint.setText(f'Cantidad sugerida precargada. {reason}')
    def _choose_expiry(self,w):
        dlg=CalendarDialog(self,'Fecha de vencimiento del lote',w.property('expiry'))
        if dlg.exec(): w.setProperty('expiry',dlg.iso_date()); w.setText(dlg.cal.selectedDate().toString('dd/MM/yyyy'))
    def _remove(self,w):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r,7) is w:self.table.removeRow(r); break
        self.recalc()
    def _focus(self): self.search.clear(); self.search.setFocus()

    def recalc(self):
        subtotal=0
        for r in range(self.table.rowCount()):
            qty=self.table.cellWidget(r,1).value(); cost=self.table.cellWidget(r,2).value(); p=self.table.item(r,0).data(Qt.ItemDataRole.UserRole+1) or {}
            estimated_cpp=self._estimated_cpp(p,qty,cost); self.table.item(r,3).setText(f'Q{estimated_cpp/100:,.2f}')
            price=self.table.cellWidget(r,4)
            suggested=PricingService.price_from_percent(estimated_cpp,p.get('markup_pct') or 0,self.profit_policy) if estimated_cpp>0 else int(p.get('price_cents') or 0)
            if not price.property('manualPrice'):
                price.setProperty('autoUpdating',True); price.blockSignals(True); price.setValue(suggested/100); price.blockSignals(False); price.setProperty('autoUpdating',False)
            price.setToolTip(f"Precio actual: Q{int(p.get('price_cents') or 0)/100:,.2f}\nCPP estimado después: Q{estimated_cpp/100:,.2f}\nPrecio sugerido conservando la ganancia configurada: Q{suggested/100:,.2f}\nPuedes escribir otro precio si lo deseas.")
            sub=round(qty*cost*100); subtotal+=sub; self.table.item(r,5).setText(f'Q{sub/100:,.2f}')
        total=max(0,subtotal-round(self.discount.value()*100)+round(self.additional.value()*100)); self.total.setText(f'TOTAL: Q{total/100:,.2f}')

    def payload(self):
        out=[]
        for r in range(self.table.rowCount()):
            qty=self.table.cellWidget(r,1).value()
            if qty<=0: raise ValueError('Indica una cantidad mayor que cero.')
            w=self.table.cellWidget(r,6); expiry=w.property('expiry') if isinstance(w,QPushButton) else None
            out.append({'product_id':self.table.item(r,0).data(Qt.ItemDataRole.UserRole),'quantity':qty,'unit_cost':self.table.cellWidget(r,2).value(),'sale_price':self.table.cellWidget(r,4).value(),'expiry_date':expiry or None})
        return out
    def purchase_meta(self):
        purchase=self.purchase_date.date().toString('yyyy-MM-dd'); status=self.status.currentData(); received=purchase if status=='RECEIVED' and self.same_day.isChecked() else (self.received_date.date().toString('yyyy-MM-dd') if status=='RECEIVED' else None)
        return purchase,received,status,self.discount.value(),self.additional.value()
    def dates(self):
        p,r,_,_,_=self.purchase_meta(); return p,r
    def clear_form(self): self.table.setRowCount(0); self.discount.setValue(0); self.additional.setValue(0); self.proposal_hint.clear(); self.recalc(); self._focus()
