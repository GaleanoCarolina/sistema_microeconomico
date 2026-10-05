from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt,pyqtSignal
from views.components.calendar_dialog import CalendarDialog
from utils.quantities import infer_quantity_mode,format_qty
from services.pricing_service import PricingService
from views.components.widgets import ArrowComboBox
from config.catalog_options import DEFAULT_CATEGORIES, DEFAULT_UNITS



def _editable_catalog_field(combo, tooltip='Ver opciones disponibles'):
    """Envuelve un QComboBox editable con un botón de lista siempre visible.

    El QComboBox sigue permitiendo escribir valores nuevos, pero el botón ▼ deja
    claro visualmente que también existe un catálogo de opciones predefinidas.
    """
    box=QWidget(); box.setObjectName('editableCatalogField')
    lay=QHBoxLayout(box); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
    lay.addWidget(combo,1)
    btn=QPushButton('▼'); btn.setProperty('class','comboDropButton'); btn.setToolTip(tooltip)
    btn.setAccessibleName(tooltip); btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    btn.clicked.connect(combo.showPopup)
    lay.addWidget(btn,0)
    return box

class QuickCustomerDialog(QDialog):
    def __init__(self,candidates=None,parent=None):
        super().__init__(parent); self.setWindowTitle('Crear cliente'); self.setMinimumWidth(450); root=QVBoxLayout(self); root.setContentsMargins(22,20,22,20); root.setSpacing(12)
        t=QLabel('Crear cliente rápido'); t.setObjectName('dialogTitle'); root.addWidget(t); s=QLabel('Solo el nombre es obligatorio. Podrás completar los demás datos después.'); s.setObjectName('muted'); s.setWordWrap(True); root.addWidget(s)
        if candidates:
            box=QGroupBox('¿Es alguno de estos clientes?'); bl=QVBoxLayout(box)
            for c in candidates[:4]: bl.addWidget(QLabel(f"• {c['name']}  {c.get('phone') or ''}"))
            root.addWidget(box)
        form=QFormLayout(); form.setVerticalSpacing(12); self.name=QLineEdit(); self.phone=QLineEdit(); self.address=QLineEdit(); form.addRow('Nombre *',self.name); form.addRow('Teléfono (opcional)',self.phone); form.addRow('Dirección (opcional)',self.address); root.addLayout(form)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Crear y usar'); bb.button(QDialogButtonBox.StandardButton.Ok).setProperty('class','accent'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)
    def data(self): return {'name':self.name.text().strip(),'phone':self.phone.text().strip(),'address':self.address.text().strip(),'notes':'','credit_limit':0}

class QuickSupplierDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle('Nuevo proveedor'); self.setMinimumWidth(440); root=QVBoxLayout(self); root.setContentsMargins(22,20,22,20); root.setSpacing(12); t=QLabel('Crear proveedor'); t.setObjectName('dialogTitle'); root.addWidget(t); h=QLabel('Registra lo mínimo para continuar con la compra.'); h.setObjectName('muted'); root.addWidget(h)
        f=QFormLayout(); f.setVerticalSpacing(12); self.name=QLineEdit(); self.phone=QLineEdit(); self.address=QLineEdit(); f.addRow('Nombre *',self.name); f.addRow('Teléfono',self.phone); f.addRow('Dirección',self.address); root.addLayout(f); bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Guardar y usar'); bb.button(QDialogButtonBox.StandardButton.Ok).setProperty('class','accent'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)
    def data(self): return {'name':self.name.text().strip(),'phone':self.phone.text().strip(),'address':self.address.text().strip()}

class ProductDialog(QDialog):
    """Única fuente de verdad para crear/editar productos.

    Se reutiliza desde Inventario y Compras. En modo rápido oculta inicialmente las
    opciones que no son imprescindibles, pero el mismo componente y validaciones
    siguen disponibles mediante “Más opciones”.
    """
    def __init__(self,categories,existing=None,parent=None,compact=False,catalog=None,profit_policy='MARKUP'):
        super().__init__(parent); self.existing=existing; self.compact=compact; self.catalog=[dict(x) for x in (catalog or [])]; self._syncing=False; self.profit_policy=str(profit_policy or 'MARKUP').upper()
        self.setWindowTitle('Editar producto' if existing else 'Agregar nuevo producto'); self.setMinimumSize(520,520); self.resize(720,700 if not compact else 620); self.setSizeGripEnabled(True)
        root=QVBoxLayout(self); root.setContentsMargins(18,16,18,16); root.setSpacing(10)
        header=QWidget(); hv=QVBoxLayout(header); hv.setContentsMargins(2,0,2,0); hv.setSpacing(4)
        t=QLabel('Editar producto' if existing else 'Agregar nuevo producto'); t.setObjectName('dialogTitle'); hv.addWidget(t)
        sub=QLabel('Modifica la configuración del producto. El costo promedio se calcula con las compras y no se edita manualmente.' if existing else ('Crea el producto sin salir de la compra. Cantidad, costo y vencimiento de este pedido se registran después en la línea de compra.' if compact else 'Crea el artículo una sola vez. Las cantidades y vencimientos de nuevas compras se registran por lote.')); sub.setObjectName('muted'); sub.setWordWrap(True); hv.addWidget(sub); root.addWidget(header)

        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        body=QWidget(); body.setObjectName('productFormBody'); self.body_layout=QVBoxLayout(body); self.body_layout.setContentsMargins(4,4,10,8); self.body_layout.setSpacing(10); self.scroll.setWidget(body); root.addWidget(self.scroll,1)

        g1=QGroupBox('Información básica'); f1=QFormLayout(g1); f1.setVerticalSpacing(11); f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.name=QLineEdit(); self.name.setPlaceholderText('Ej. Coca-Cola 2.5 L'); self.category=QComboBox(); self.category.setEditable(True)
        category_names=[]
        for name in [*(c['name'] for c in categories), *DEFAULT_CATEGORIES]:
            if name and name.casefold() not in {x.casefold() for x in category_names}: category_names.append(name)
        self.category.addItems(sorted(category_names, key=str.casefold)); self.category.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.category.lineEdit().setPlaceholderText('Elige una categoría o escribe una nueva')
        self.unit=QComboBox(); self.unit.setEditable(True); self.unit.addItems(DEFAULT_UNITS); self.unit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.unit.lineEdit().setPlaceholderText('Elige una unidad o escribe otra')
        self.qty_mode=ArrowComboBox(); self.qty_mode.addItem('Unidades enteras','INTEGER'); self.qty_mode.addItem('Peso / cantidad fraccionaria','FRACTIONAL')
        for w in (self.name,self.category,self.unit,self.qty_mode): w.setMinimumWidth(280); w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.category.setToolTip('Selecciona una categoría existente de la lista o escribe una nueva si no existe.')
        self.unit.setToolTip('Selecciona una unidad de medida de la lista o escribe una nueva si no existe.')
        category_field=_editable_catalog_field(self.category,'Abrir lista de categorías')
        unit_field=_editable_catalog_field(self.unit,'Abrir lista de unidades de medida')
        f1.addRow('Nombre del producto *',self.name); self.matches=QLabel('Escribe el nombre para revisar coincidencias existentes.'); self.matches.setObjectName('help'); self.matches.setWordWrap(True); self.matches.setMinimumHeight(36); self.matches.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.MinimumExpanding); f1.addRow('Productos parecidos',self.matches); self.name.textChanged.connect(self._show_matches); f1.addRow('Categoría (lista editable)',category_field); f1.addRow('Unidad de medida (lista editable)',unit_field); f1.addRow('Tipo de cantidad',self.qty_mode); self.unit.currentTextChanged.connect(self._unit_changed)
        self.expires=QCheckBox('Este producto puede vencer'); f1.addRow('Caducidad',self.expires); exphelp=QLabel('La fecha de vencimiento pertenece a cada lote recibido, no al producto general.'); exphelp.setObjectName('help'); exphelp.setWordWrap(True); f1.addRow('',exphelp); self.body_layout.addWidget(g1)

        self.more=QPushButton('Mostrar más opciones'); self.more.setCheckable(True); self.more.setProperty('class','secondary'); self.more.toggled.connect(self._toggle_advanced); self.body_layout.addWidget(self.more)

        self.advanced=QWidget(); self.advanced.setObjectName('advancedPanel'); av=QVBoxLayout(self.advanced); av.setContentsMargins(0,0,0,0); av.setSpacing(10)
        g2=QGroupBox('Precio y ganancia'); f2=QFormLayout(g2); f2.setVerticalSpacing(11); f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.cost=QDoubleSpinBox(); self.cost.setMaximum(999999); self.cost.setPrefix('Q '); self.cost.setDecimals(2); self.cost.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.price=QDoubleSpinBox(); self.price.setMaximum(999999); self.price.setPrefix('Q '); self.price.setDecimals(2); self.price.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.markup=QDoubleSpinBox(); self.markup.setRange(-99 if self.profit_policy=='MARGIN' else -1000,99.99 if self.profit_policy=='MARGIN' else 1000); self.markup.setSuffix(' %'); self.markup.setDecimals(2); self.markup.setValue(25); self.markup.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        for w in (self.cost,self.price,self.markup): w.setMinimumWidth(220); w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.policy_label=QLabel(PricingService.policy_label(self.profit_policy)); self.policy_label.setStyleSheet('font-weight:800;color:#5C7F0C;'); self.policy_help=QLabel('Precio y porcentaje permanecen sincronizados. El costo promedio solo cambia mediante compras o ajustes autorizados.'); self.policy_help.setObjectName('help'); self.policy_help.setWordWrap(True)
        f2.addRow('Costo promedio actual',self.cost); f2.addRow('Política activa',self.policy_label); f2.addRow('Precio de venta',self.price); f2.addRow('Ganancia configurada',self.markup); f2.addRow('',self.policy_help); av.addWidget(g2)
        self.price.valueChanged.connect(self._price_changed); self.markup.valueChanged.connect(self._percent_changed)

        g3=QGroupBox('Inventario y avisos'); f3=QFormLayout(g3); f3.setVerticalSpacing(11); f3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.qty=QDoubleSpinBox(); self.qty.setMaximum(999999); self.qty.setDecimals(2); self.qty.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons); self.min_stock=QDoubleSpinBox(); self.min_stock.setMaximum(999999); self.min_stock.setValue(5); self.min_stock.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        for w in (self.qty,self.min_stock): w.setMinimumWidth(220); w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        f3.addRow('Cantidad que tienes ahora',self.qty); f3.addRow('Stock mínimo para recibir aviso',self.min_stock)
        self.initial_expiry=QPushButton('Elegir vencimiento del inventario inicial'); self.initial_expiry.setProperty('class','secondary'); self.initial_expiry.setProperty('expiry',''); self.initial_expiry.clicked.connect(self._choose_initial_expiry); f3.addRow('Vencimiento inicial (opcional)',self.initial_expiry); av.addWidget(g3)
        self.body_layout.addWidget(self.advanced); self.body_layout.addStretch()

        # En una compra la cantidad/costo/vencimiento pertenecen a la línea de compra, no al producto.
        if compact:
            self.qty.setValue(0); g3.setVisible(False); self.cost.setValue(0); self.cost.setEnabled(False); self.advanced.setVisible(False); self.more.setChecked(False)
        elif existing:
            g3.setVisible(False); self.more.setChecked(True); self.advanced.setVisible(True)
        else:
            self.more.setChecked(True); self.advanced.setVisible(True)

        footer=QFrame(); footer.setObjectName('softCard'); fl=QHBoxLayout(footer); fl.setContentsMargins(12,9,12,9); fl.addStretch(); cancel=QPushButton('Cancelar'); cancel.setProperty('class','secondary'); cancel.clicked.connect(self.reject); save=QPushButton('Guardar producto'); save.setProperty('class','accent'); save.setDefault(True); save.clicked.connect(self._validate_and_accept); fl.addWidget(cancel); fl.addWidget(save); root.addWidget(footer)
        if existing:self._load(existing)
        else:self._unit_changed(self.unit.currentText())

    def _toggle_advanced(self,checked):
        self.advanced.setVisible(checked); self.more.setText('Ocultar opciones adicionales' if checked else 'Mostrar más opciones')
    def _show_matches(self,text):
        q=' '.join((text or '').lower().replace('-',' ').split())
        if not q:self.matches.setText('Escribe el nombre para revisar coincidencias existentes.'); return
        found=[x['name'] for x in self.catalog if q in ' '.join(x['name'].lower().replace('-',' ').split()) or ' '.join(x['name'].lower().replace('-',' ').split()) in q]
        self.matches.setText('Ya existen: '+', '.join(found[:4]) if found else 'No se encontraron coincidencias directas.')
        self.matches.setToolTip(', '.join(found[:8]) if found else '')
    def _unit_changed(self,text):
        mode=infer_quantity_mode(text); idx=self.qty_mode.findData(mode)
        if idx>=0:self.qty_mode.setCurrentIndex(idx)
    def _choose_initial_expiry(self):
        dlg=CalendarDialog(self,'Vencimiento del inventario inicial',self.initial_expiry.property('expiry'))
        if dlg.exec(): self.initial_expiry.setProperty('expiry',dlg.iso_date()); self.initial_expiry.setText(dlg.cal.selectedDate().toString('dd/MM/yyyy'))
    def _price_changed(self):
        if self._syncing:return
        cost=self.cost.value(); price=self.price.value()
        if cost<=0:return
        self._syncing=True
        try:self.markup.setValue(float(PricingService.percent_from_price(round(cost*100),round(price*100),self.profit_policy)))
        finally:self._syncing=False
    def _percent_changed(self):
        if self._syncing:return
        cost=self.cost.value()
        if cost<=0:return
        self._syncing=True
        try:self.price.setValue(PricingService.price_from_percent(round(cost*100),self.markup.value(),self.profit_policy)/100)
        except ValueError:pass
        finally:self._syncing=False
    def _load(self,p):
        self._syncing=True
        try:
            self.name.setText(p['name']); self.category.setCurrentText(p.get('category_name') or ''); self.unit.setCurrentText(p.get('unit_name') or 'unidad'); self.qty_mode.setCurrentIndex(max(0,self.qty_mode.findData(p.get('quantity_mode') or infer_quantity_mode(p.get('unit_name')))))
            self.cost.setValue((p.get('cpp_cents') or 0)/100); self.cost.setEnabled(False); self.price.setValue((p.get('price_cents') or 0)/100); self.min_stock.setValue(float(p.get('min_stock') or 5)); self.expires.setChecked(bool(p.get('expires')))
            pct=PricingService.percent_from_price(int(p.get('cpp_cents') or 0),int(p.get('price_cents') or 0),self.profit_policy) if p.get('cpp_cents') else p.get('markup_pct',25); self.markup.setValue(float(pct or 0))
        finally:self._syncing=False
    def _validate_and_accept(self):
        if not self.name.text().strip():
            self.name.setProperty('error',True); self.name.style().unpolish(self.name); self.name.style().polish(self.name); self.name.setFocus(); return
        self.name.setProperty('error',False)
        if self.cost.value()>0:self._price_changed()
        self.accept()
    def data(self):
        return {'name':self.name.text().strip(),'category':self.category.currentText().strip(),'unit_name':self.unit.currentText().strip() or 'unidad','quantity_mode':self.qty_mode.currentData(),'cost':self.cost.value(),'price':self.price.value(),'markup_pct':self.markup.value(),'quantity':self.qty.value(),'min_stock':self.min_stock.value(),'expires':self.expires.isChecked(),'expiry_date':self.initial_expiry.property('expiry') if self.initial_expiry else None}

class PaymentDialog(QDialog):
    def __init__(self,name,balance_cents,parent=None):
        super().__init__(parent); self.setWindowTitle('Registrar abono'); self.setMinimumWidth(410); root=QVBoxLayout(self); root.setContentsMargins(22,20,22,20); t=QLabel(f'Abono de {name}'); t.setObjectName('dialogTitle'); root.addWidget(t); bal=QLabel(f'Saldo pendiente: Q{balance_cents/100:,.2f}'); bal.setObjectName('sectionTitle'); root.addWidget(bal); self.amount=QDoubleSpinBox(); self.amount.setMaximum(balance_cents/100); self.amount.setDecimals(2); self.amount.setPrefix('Q '); root.addWidget(self.amount); bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Registrar abono'); bb.button(QDialogButtonBox.StandardButton.Ok).setProperty('class','accent'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)

class LotDialog(QDialog):
    update_requested=pyqtSignal(int,str)
    def __init__(self,product,rows,parent=None,highlight_lot=None):
        super().__init__(parent); self.product=product; self.highlight_lot=highlight_lot; self.setWindowTitle('Lotes del producto'); self.resize(900,520); root=QVBoxLayout(self); root.setContentsMargins(22,20,22,20); t=QLabel(f"Lotes de {product['name']}"); t.setObjectName('dialogTitle'); root.addWidget(t); s=QLabel('Cada recepción conserva cantidad, costo y fecha de vencimiento propios. El costo promedio del producto se mantiene por separado.'); s.setObjectName('muted'); s.setWordWrap(True); root.addWidget(s)
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(['Lote','Recibido','Cantidad inicial','Disponible','Costo de entrada','Vencimiento']); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); root.addWidget(self.table,1); self.set_rows(rows)
        row=QHBoxLayout(); self.edit=QPushButton('Agregar / corregir fecha'); self.edit.clicked.connect(self._edit); row.addWidget(self.edit); row.addStretch(); close=QPushButton('Cerrar'); close.setProperty('class','secondary'); close.clicked.connect(self.accept); row.addWidget(close); root.addLayout(row)
    def set_rows(self,rows):
        self.rows=[dict(r) for r in rows]; self.table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[f"Lote {r['id']}",(r['received_at'] or '')[:10],format_qty(r['quantity_initial'],self.product.get('quantity_mode','INTEGER')),format_qty(r['quantity_remaining'],self.product.get('quantity_mode','INTEGER')),f"Q{r['unit_cost_cents']/100:,.2f}",r['expiry_date'] or 'Sin fecha registrada']
            for c,v in enumerate(vals):self.table.setItem(i,c,QTableWidgetItem(v))
            if self.highlight_lot and r['id']==self.highlight_lot:self.table.selectRow(i)
    def _edit(self):
        row=self.table.currentRow()
        if row<0:return
        lot=self.rows[row]; dlg=CalendarDialog(self,'Fecha de vencimiento',lot.get('expiry_date'))
        if dlg.exec(): self.update_requested.emit(lot['id'],dlg.iso_date())
