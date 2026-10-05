from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QCalendarWidget,QDialogButtonBox,QLabel,QFrame
from PyQt6.QtCore import QDate,Qt
from PyQt6.QtGui import QTextCharFormat,QColor,QFont

class CalendarDialog(QDialog):
    def __init__(self,parent=None,title='Seleccionar fecha',initial=None):
        super().__init__(parent); self.setWindowTitle(title); self.setMinimumWidth(390)
        lay=QVBoxLayout(self); lay.setContentsMargins(20,18,20,18); lay.setSpacing(12)
        h=QLabel(title); h.setObjectName('dialogTitle'); lay.addWidget(h); helper=QLabel('Haz clic en una fecha. La selección queda resaltada claramente.'); helper.setObjectName('muted'); lay.addWidget(helper)
        self.cal=QCalendarWidget(); self.cal.setGridVisible(False); self.cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.cal.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        if initial:
            d=QDate.fromString(initial,'yyyy-MM-dd')
            if d.isValid(): self.cal.setSelectedDate(d); self.cal.setCurrentPage(d.year(),d.month())
        today=QDate.currentDate(); fmt=QTextCharFormat(); fmt.setForeground(QColor('#6B8E12')); fmt.setFontWeight(QFont.Weight.Bold); self.cal.setDateTextFormat(today,fmt)
        lay.addWidget(self.cal)
        legend=QHBoxLayout(); a=QLabel('HOY'); a.setStyleSheet('color:#6B8E12;font-weight:800;'); legend.addWidget(a); legend.addSpacing(14); b=QLabel('FECHA SELECCIONADA'); b.setStyleSheet('background:#111827;color:#B9F227;padding:4px 8px;border-radius:7px;font-weight:800;'); legend.addWidget(b); legend.addStretch(); lay.addLayout(legend)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Usar esta fecha'); bb.button(QDialogButtonBox.StandardButton.Ok).setProperty('class','accent'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lay.addWidget(bb)
    def iso_date(self): return self.cal.selectedDate().toString('yyyy-MM-dd')

class DateRangeDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle('Elegir período'); self.resize(820,430)
        root=QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(12); title=QLabel('Período personalizado'); title.setObjectName('dialogTitle'); root.addWidget(title); sub=QLabel('Selecciona una fecha inicial y una fecha final.'); sub.setObjectName('muted'); root.addWidget(sub)
        row=QHBoxLayout(); left=QVBoxLayout(); left.addWidget(QLabel('Desde')); self.start=QCalendarWidget(); self.start.setGridVisible(False); self.start.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader); left.addWidget(self.start); row.addLayout(left); right=QVBoxLayout(); right.addWidget(QLabel('Hasta')); self.end=QCalendarWidget(); self.end.setGridVisible(False); self.end.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader); right.addWidget(self.end); row.addLayout(right); root.addLayout(row)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); bb.button(QDialogButtonBox.StandardButton.Ok).setText('Aplicar período'); bb.button(QDialogButtonBox.StandardButton.Ok).setProperty('class','accent'); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)
    def accept(self):
        if self.start.selectedDate()>self.end.selectedDate(): self.end.setSelectedDate(self.start.selectedDate())
        super().accept()
    def range(self): return self.start.selectedDate().toString('yyyy-MM-dd'),self.end.selectedDate().toString('yyyy-MM-dd')
