from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt

class CustomersView(QWidget):
    search_changed=pyqtSignal(str); add_requested=pyqtSignal(); payment_requested=pyqtSignal(int)
    def __init__(self):
        super().__init__(); root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(12)
        t=QLabel('Clientes y Fiados'); t.setObjectName('pageTitle'); root.addWidget(t); s=QLabel('Aquí ves únicamente dinero pendiente de cobro. Los abonos no se cuentan como nuevas ventas.'); s.setObjectName('muted'); s.setWordWrap(True); root.addWidget(s)
        top=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Buscar cliente por nombre o teléfono…'); self.search.textChanged.connect(self.search_changed); top.addWidget(self.search,1); add=QPushButton('+ Nuevo cliente'); add.setProperty('class','accent'); add.clicked.connect(self.add_requested); top.addWidget(add); root.addLayout(top)
        self.summary=QLabel('Pendiente total: Q0.00'); self.summary.setObjectName('sectionTitle'); root.addWidget(self.summary)
        self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(['Cliente','Teléfono','Saldo pendiente','Deuda más antigua','Última compra fiada','Último abono','Acción'])
        hdr=self.table.horizontalHeader(); hdr.setMinimumSectionSize(90); hdr.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        for c in (1,2,3,4,5): hdr.setSectionResizeMode(c,QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6,QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(6,104)
        self.table.setAlternatingRowColors(True); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.verticalHeader().setDefaultSectionSize(46); root.addWidget(self.table,1)
        self.empty=QLabel('No tienes saldos pendientes por cobrar.'); self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter); self.empty.setObjectName('muted'); root.addWidget(self.empty); self.empty.hide()
    def set_rows(self,rows):
        rows=[dict(r) for r in rows]; self.table.setRowCount(len(rows)); total=0
        for i,r in enumerate(rows):
            total+=r['balance_cents']; vals=[r['name'],r['phone'] or '—',f"Q{r['balance_cents']/100:,.2f}",(r['oldest'] or '')[:10],(r['last_credit'] or '')[:10],(r['last_payment'] or '')[:10]]
            for c,v in enumerate(vals): self.table.setItem(i,c,QTableWidgetItem(v or '—'))
            b=QPushButton('ABONAR'); b.setProperty('class','tableAction'); b.setToolTip('Registrar abono'); b.clicked.connect(lambda _=False,cid=r['id']:self.payment_requested.emit(cid)); self.table.setCellWidget(i,6,b)
        self.summary.setText(f'Pendiente total: Q{total/100:,.2f}'); self.empty.setVisible(not rows); self.table.setVisible(bool(rows))
