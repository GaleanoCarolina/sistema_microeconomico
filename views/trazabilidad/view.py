from views.components.widgets import ArrowComboBox
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal
from views.components.calendar_dialog import DateRangeDialog

class HistoryView(QWidget):
    refresh_requested=pyqtSignal(str,str); detail_requested=pyqtSignal(str,int)
    def __init__(self):
        super().__init__(); self.start=''; self.end=''; self.operation_filter='Todos'; root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(12)
        t=QLabel('Historial'); t.setObjectName('pageTitle'); root.addWidget(t); s=QLabel('Registro de operaciones en lenguaje claro. Nada importante se elimina silenciosamente.'); s.setObjectName('muted'); root.addWidget(s)
        top=QHBoxLayout(); date=QPushButton('Filtrar por fechas…'); date.setProperty('class','secondary'); date.clicked.connect(self._range); top.addWidget(date); top.addWidget(QLabel('Operación:')); self.filter=ArrowComboBox(); self.filter.addItems(['Todos','Ventas','Compras','Abonos','Inventario']); self.filter.currentTextChanged.connect(self._apply); top.addWidget(self.filter); top.addStretch(); ref=QPushButton('Actualizar'); ref.clicked.connect(lambda:self.refresh_requested.emit(self.start,self.end)); top.addWidget(ref); root.addLayout(top)
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(['Fecha','Hora','Operación','Descripción','Monto','Estado']); self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setAlternatingRowColors(True); self.table.doubleClicked.connect(self._detail); root.addWidget(self.table,1); self.rows=[]; self.raw=[]
        h=QLabel('Consejo: haz doble clic en una venta o compra para ver productos, cantidades y montos.'); h.setObjectName('help'); root.addWidget(h)
    def _range(self):
        dlg=DateRangeDialog(self)
        if dlg.exec(): self.start,self.end=dlg.range(); self.refresh_requested.emit(self.start,self.end)
    def set_operation_filter(self,kind):
        mapping={'PURCHASE':'Compras','SALE':'Ventas','PAYMENT':'Abonos','MOVEMENT':'Inventario'}; self.filter.setCurrentText(mapping.get(kind,'Todos'))
    def set_rows(self,rows): self.raw=[dict(r) for r in rows]; self._apply()
    def _apply(self):
        mode=self.filter.currentText(); kinds={'Ventas':{'SALE'},'Compras':{'PURCHASE'},'Abonos':{'PAYMENT'},'Inventario':{'MOVEMENT'}}
        self.rows=[r for r in self.raw if mode=='Todos' or r['tipo'] in kinds.get(mode,set())]; self.table.setRowCount(len(self.rows))
        for i,r in enumerate(self.rows):
            fecha=(r['fecha'] or '').split(' '); vals=[fecha[0] if fecha else '',fecha[1][:5] if len(fecha)>1 else '',r['operacion'],r['descripcion'],f"Q{r['monto']/100:,.2f}" if r['monto'] is not None else '—',r['estado'] or '—']
            for c,v in enumerate(vals):self.table.setItem(i,c,QTableWidgetItem(str(v)))
    def _detail(self,index):
        r=self.rows[index.row()]
        if r['tipo'] in ('SALE','PURCHASE'): self.detail_requested.emit(r['tipo'],r['ref'])
