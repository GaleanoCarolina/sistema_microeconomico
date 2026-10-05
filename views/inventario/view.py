from datetime import date
from utils.dates import local_today
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt
from PyQt6.QtGui import QColor,QBrush,QFont
from utils.quantities import format_qty

class InventoryView(QWidget):
    search_changed=pyqtSignal(str); add_requested=pyqtSignal(); edit_requested=pyqtSignal(int); lots_requested=pyqtSignal(int); purchase_requested=pyqtSignal(int); detail_requested=pyqtSignal(int)
    def __init__(self):
        super().__init__(); self.filter_mode='all'; root=QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        head=QHBoxLayout(); titles=QVBoxLayout(); t=QLabel('Inventario'); t.setObjectName('pageTitle'); titles.addWidget(t); sub=QLabel('Administra tus productos, existencias, precios y lotes desde un solo lugar.'); sub.setObjectName('muted'); titles.addWidget(sub); head.addLayout(titles); head.addStretch(); add=QPushButton('+ Agregar producto'); add.setProperty('class','accent'); add.clicked.connect(self.add_requested); head.addWidget(add); root.addLayout(head)
        tools=QFrame(); tools.setObjectName('softCard'); tl=QVBoxLayout(tools); tl.setContentsMargins(12,11,12,11); top=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Buscar por nombre, categoría o estado…'); self.search.setMinimumHeight(42); self.search.textChanged.connect(self.search_changed); top.addWidget(self.search,1); self.count=QLabel('0 productos'); self.count.setObjectName('muted'); top.addWidget(self.count); tl.addLayout(top)
        filters=QHBoxLayout(); filters.addWidget(QLabel('Filtros:')); self.filter_buttons={}
        for text,key in [('Todos','all'),('En stock','stock'),('Stock bajo','low'),('Agotados','out'),('Por vencer','expiry'),('Vencidos','expired'),('Estancados','stagnant')]:
            b=QPushButton(text); b.setCheckable(True); b.setProperty('class','filter'); b.clicked.connect(lambda _=False,k=key:self._set_filter(k)); filters.addWidget(b); self.filter_buttons[key]=b
        self.filter_buttons['all'].setChecked(True); filters.addStretch(); tl.addLayout(filters); root.addWidget(tools)
        actions=QHBoxLayout(); self.buy=QPushButton('Registrar compra / existencia'); self.buy.setProperty('class','secondary'); self.buy.clicked.connect(lambda:self._emit_selected(self.purchase_requested)); actions.addWidget(self.buy); self.edit=QPushButton('Editar precio y producto'); self.edit.setProperty('class','secondary'); self.edit.clicked.connect(lambda:self._emit_selected(self.edit_requested)); actions.addWidget(self.edit); self.lots=QPushButton('Ver lotes y vencimientos'); self.lots.setProperty('class','secondary'); self.lots.clicked.connect(lambda:self._emit_selected(self.lots_requested)); actions.addWidget(self.lots); actions.addStretch(); hint=QLabel('Doble clic: ver detalle'); hint.setObjectName('help'); actions.addWidget(hint); root.addLayout(actions)
        self.table=QTableWidget(0,10); self.table.setHorizontalHeaderLabels(['Producto','Categoría','Existencias','Unidad','Costo promedio','Precio','Ganancia','Stock mínimo','Estado','Próximo vencimiento']); self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch); self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(8,QHeaderView.ResizeMode.ResizeToContents); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); self.table.setAlternatingRowColors(True); self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.setShowGrid(False); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.verticalHeader().setDefaultSectionSize(40); self.table.doubleClicked.connect(lambda:self._emit_selected(self.detail_requested)); root.addWidget(self.table,1); self._all_rows=[]
    def _set_filter(self,key):
        self.filter_mode=key
        for k,b in self.filter_buttons.items(): b.setChecked(k==key)
        self._render()
    def _emit_selected(self,sig):
        r=self.table.currentRow()
        if r>=0 and self.table.item(r,0):sig.emit(self.table.item(r,0).data(Qt.ItemDataRole.UserRole))
    def set_filter(self,mode=''):
        key=mode or 'all'
        if key not in self.filter_buttons:key='all'
        self._set_filter(key)
    def set_rows(self,rows): self._all_rows=list(rows); self._render()
    def _state(self,r):
        stock=float(r.get('lot_stock',r.get('stock',0)) or 0); min_stock=float(r.get('min_stock',0) or 0); expiry=r.get('next_expiry'); today=local_today()
        if expiry:
            days=(date.fromisoformat(expiry)-today).days
            if days<0:return 'Vencido','expired'
            if days<=15:return 'Vence pronto','expiry'
        if stock<=0:return 'Agotado','out'
        if stock<=min_stock:return 'Stock bajo','low'
        if r.get('stagnant'):return 'Venta lenta','stagnant'
        return 'Normal','normal'
    def _filtered(self):
        out=[]
        for r in self._all_rows:
            label,key=self._state(r); stock=float(r.get('lot_stock',r.get('stock',0)) or 0)
            ok=self.filter_mode=='all' or (self.filter_mode=='stock' and stock>0) or self.filter_mode==key
            if ok: out.append((r,label,key))
        return out
    def _render(self):
        rows=self._filtered(); self.table.setRowCount(len(rows)); self.count.setText(f'Mostrando {len(rows)} producto'+('s' if len(rows)!=1 else ''))
        badge={'normal':('#ECFDF3','#067647'),'low':('#FFF8D8','#8A5B00'),'out':('#FDECEC','#B42318'),'expiry':('#FFF3E8','#B54708'),'expired':('#FADADA','#B42318'),'stagnant':('#F2F4F7','#475467')}
        for i,(r,status,key) in enumerate(rows):
            mode=r.get('quantity_mode','INTEGER'); stock=r.get('lot_stock',r.get('stock',0)); margin=float(r.get('margin_pct',0) or 0)
            vals=[r['name'],r.get('category_name') or r.get('category') or 'Sin categoría',format_qty(stock,mode),r.get('unit_name') or 'unidad',f"Q{int(r.get('cpp_cents',0))/100:,.2f}",f"Q{int(r.get('price_cents',0))/100:,.2f}",f"{margin:.1f}%",format_qty(r.get('min_stock',0),mode),status,r.get('next_expiry') or ('Fecha pendiente' if float(r.get('unknown_expiry_qty',0) or 0)>0 else '—')]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(str(v)); self.table.setItem(i,c,it)
            self.table.item(i,0).setData(Qt.ItemDataRole.UserRole,r['id']); self.table.item(i,0).setFont(QFont('Segoe UI',9,QFont.Weight.DemiBold))
            bg,fg=badge[key]; state=self.table.item(i,8); state.setBackground(QBrush(QColor(bg))); state.setForeground(QBrush(QColor(fg))); state.setFont(QFont('Segoe UI',9,QFont.Weight.Bold)); state.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if key in ('expiry','expired'):
                ex=self.table.item(i,9); ex.setBackground(QBrush(QColor(bg))); ex.setForeground(QBrush(QColor(fg)))
    def select_product(self,pid):
        self.filter_mode='all'
        for k,b in self.filter_buttons.items():b.setChecked(k=='all')
        self._render()
        for r in range(self.table.rowCount()):
            if self.table.item(r,0).data(Qt.ItemDataRole.UserRole)==pid:
                self.table.selectRow(r); self.table.setCurrentCell(r,0); self.table.scrollToItem(self.table.item(r,0)); self.table.setFocus(); return True
        return False
