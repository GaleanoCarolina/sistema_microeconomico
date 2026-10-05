from views.components.widgets import ArrowComboBox
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from views.components.calendar_dialog import DateRangeDialog

class ReportsView(QWidget):
    generate_requested=pyqtSignal(str,str,str,str); abc_requested=pyqtSignal()
    def __init__(self):
        super().__init__(); self.start=''; self.end=''; root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(12)
        t=QLabel('Reportes'); t.setObjectName('pageTitle'); root.addWidget(t); s=QLabel('Primero elige qué quieres revisar y el período. Después verás un resumen y el detalle.'); s.setObjectName('muted'); root.addWidget(s)
        controls=QFrame(); controls.setObjectName('card'); cl=QGridLayout(controls); cl.setHorizontalSpacing(10); cl.setVerticalSpacing(8); cl.addWidget(QLabel('Reporte'),0,0); self.kind=ArrowComboBox(); self.kind.addItems(['Ventas','Compras','Inversión y resultados','Inventario','Fiados','Caducidades','Recomendaciones']); cl.addWidget(self.kind,0,1); cl.addWidget(QLabel('Período'),0,2); self.period=ArrowComboBox(); self.period.addItems(['Hoy','Últimos 7 días','Últimos 30 días','Este mes','Personalizado']); self.period.currentTextChanged.connect(self._period_changed); cl.addWidget(self.period,0,3); gen=QPushButton('Generar'); gen.setProperty('class','accent'); gen.clicked.connect(self._emit); cl.addWidget(gen,1,2); abc=QPushButton('Análisis ABC / Pareto'); abc.setProperty('class','secondary'); abc.clicked.connect(self.abc_requested); cl.addWidget(abc,1,3); cl.setColumnStretch(1,1); cl.setColumnStretch(3,1); root.addWidget(controls)
        self.summary=QLabel('Selecciona un reporte y pulsa Generar.'); self.summary.setObjectName('sectionTitle'); self.summary.setWordWrap(True); root.addWidget(self.summary)
        self.table=QTableWidget(0,1); self.table.setHorizontalHeaderLabels(['Resultado']); self.table.setAlternatingRowColors(True); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); root.addWidget(self.table,1)
    def _period_changed(self,text):
        if text=='Personalizado':
            dlg=DateRangeDialog(self)
            if dlg.exec(): self.start,self.end=dlg.range()
            else:
                self.period.blockSignals(True); self.period.setCurrentText('Últimos 30 días'); self.period.blockSignals(False); self.start=self.end=''
        else:self.start=self.end=''
    def _emit(self): self.generate_requested.emit(self.kind.currentText(),self.period.currentText(),self.start,self.end)
    def show_rows(self,summary,headers,rows):
        self.summary.setText(summary); self.table.setColumnCount(len(headers)); self.table.setHorizontalHeaderLabels(headers); self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for c,val in enumerate(row):self.table.setItem(i,c,QTableWidgetItem(str(val)))
        if headers:self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(len(headers)-1,QHeaderView.ResizeMode.Stretch)
