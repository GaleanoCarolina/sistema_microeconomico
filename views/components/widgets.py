from PyQt6.QtWidgets import (
    QFrame,QVBoxLayout,QHBoxLayout,QLabel,QMessageBox,QPushButton,QLineEdit,
    QSizePolicy,QComboBox
)
from PyQt6.QtCore import pyqtSignal,Qt,QTimer,QPoint
from PyQt6.QtGui import QIntValidator,QDoubleValidator,QPainter,QColor,QFont



class ArrowComboBox(QComboBox):
    """QComboBox con una flecha ▼ pintada siempre de forma visible.

    Evita depender de la flecha nativa del estilo de Windows, que puede desaparecer
    con QSS. El área derecha también abre explícitamente la lista.
    """
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setStyleSheet('QComboBox { padding-right: 34px; }')
        self.setToolTip('Puedes escribir o abrir la lista de opciones con la flecha ▼.')

    def paintEvent(self,event):
        super().paintEvent(event)
        painter=QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        painter.setPen(QColor('#344054'))
        font=QFont(self.font()); font.setBold(True); font.setPointSize(max(8,font.pointSize()))
        painter.setFont(font)
        rect=self.rect().adjusted(max(0,self.width()-31),2,-5,-2)
        painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,'▼')
        painter.end()

    def mousePressEvent(self,event):
        # Dejar que QComboBox gestione de forma nativa la apertura/cierre del popup.
        # Abrir manualmente en mousePress hacía que el mismo mouseRelease se
        # interpretara dentro del popup y éste se cerrara inmediatamente, obligando
        # al usuario a mantener presionado el botón del mouse.
        super().mousePressEvent(event)

class KPIButton(QFrame):
    clicked=pyqtSignal()
    def __init__(self,title,value='—',subtitle='',variant='light',icon=''):
        super().__init__(); self.variant=variant
        self.setObjectName('accentCard' if variant=='accent' else ('darkCard' if variant=='dark' else 'clickCard'))
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setMinimumHeight(108); self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred); self.setToolTip(subtitle)
        lay=QVBoxLayout(self); lay.setContentsMargins(16,14,16,13); lay.setSpacing(5)
        head=QHBoxLayout(); self.title=QLabel((icon+'  ' if icon else '')+title); self.title.setObjectName('darkCardTitle' if variant=='dark' else 'kpiTitle'); self.title.setWordWrap(True); head.addWidget(self.title,1); self.dot=QLabel('●'); self.dot.setStyleSheet('color:#B9F227;' if variant=='dark' else 'color:#98A2B3;'); head.addWidget(self.dot); lay.addLayout(head)
        self.value=QLabel(value); self.value.setObjectName('accentValue' if variant=='accent' else ('darkCardValue' if variant=='dark' else 'kpiValue')); self.value.setMinimumWidth(0)
        self.subtitle=QLabel(subtitle); self.subtitle.setWordWrap(True); self.subtitle.setStyleSheet('color:#AAB4C4;' if variant=='dark' else 'color:#667085;')
        lay.addWidget(self.value); lay.addWidget(self.subtitle)
    def set_data(self,value,subtitle=None):
        self.value.setText(value)
        if subtitle is not None:self.subtitle.setText(subtitle); self.setToolTip(subtitle)
    def mousePressEvent(self,e):
        self.setProperty('pressed',True); self.style().unpolish(self); self.style().polish(self); self.clicked.emit(); super().mousePressEvent(e)
    def mouseReleaseEvent(self,e):
        self.setProperty('pressed',False); self.style().unpolish(self); self.style().polish(self); super().mouseReleaseEvent(e)

class QuantityInput(QFrame):
    """Control de cantidad robusto: [-] valor [+]. No usa los subcontroles estrechos de QSpinBox."""
    valueChanged=pyqtSignal(float)
    def __init__(self,fractional=False,parent=None):
        super().__init__(parent); self.setObjectName('quantityControl'); self.fractional=bool(fractional); self._min=.01 if self.fractional else 1; self._max=999999.0; self._step=.25 if self.fractional else 1.0; self._value=1.0
        lay=QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        self.minus=QPushButton('−'); self.minus.setProperty('class','quantityButton'); self.minus.setFixedWidth(36); self.minus.setToolTip('Disminuir cantidad')
        self.edit=QLineEdit(); self.edit.setObjectName('quantityValue'); self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter); self.edit.setMinimumWidth(82); self.edit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.plus=QPushButton('+'); self.plus.setProperty('class','quantityButton'); self.plus.setFixedWidth(36); self.plus.setToolTip('Aumentar cantidad')
        lay.addWidget(self.minus); lay.addWidget(self.edit,1); lay.addWidget(self.plus)
        self.minus.clicked.connect(lambda:self.setValue(self._value-self._step)); self.plus.clicked.connect(lambda:self.setValue(self._value+self._step)); self.edit.editingFinished.connect(self._commit)
        self._set_validator(); self.setValue(1)
    def _set_validator(self):
        if self.fractional:
            validator=QDoubleValidator(0.0,999999.0,2,self); validator.setNotation(QDoubleValidator.Notation.StandardNotation); self.edit.setValidator(validator)
        else:self.edit.setValidator(QIntValidator(0,999999,self))
    def setRange(self,minimum,maximum): self._min=float(minimum); self._max=max(float(maximum),self._min); self.setValue(self._value)
    def setMinimum(self,v): self.setRange(v,self._max)
    def setMaximum(self,v): self.setRange(self._min,v)
    def minimum(self): return self._min
    def maximum(self): return self._max
    def setSingleStep(self,v): self._step=float(v)
    def value(self): return float(self._value) if self.fractional else int(round(self._value))
    def setValue(self,v):
        try:v=float(v)
        except Exception:v=self._min
        v=max(self._min,min(self._max,v));
        if not self.fractional:v=float(int(round(v)))
        changed=abs(v-self._value)>1e-9; self._value=v; self.edit.setText(f'{v:.2f}' if self.fractional else str(int(round(v))))
        if changed:self.valueChanged.emit(self.value())
    def _commit(self):
        text=self.edit.text().strip().replace(',','.')
        try:self.setValue(float(text))
        except Exception:self.setValue(self._value)
    def setFocus(self,reason=Qt.FocusReason.OtherFocusReason): self.edit.setFocus(reason); self.edit.selectAll()

class EmptyState(QFrame):
    def __init__(self,title,text=''):
        super().__init__(); self.setObjectName('panel'); lay=QVBoxLayout(self); lay.setContentsMargins(20,30,20,30); t=QLabel(title); t.setObjectName('sectionTitle'); t.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(t)
        if text:
            s=QLabel(text); s.setObjectName('muted'); s.setWordWrap(True); s.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(s)

class Toast(QFrame):
    """Notificación ligera; no bloquea el flujo. Se destruye sola."""
    def __init__(self,parent,title,text,kind='success',duration=2800):
        host=parent.window() if parent is not None else None
        super().__init__(host); self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,True)
        palette={'success':('#ECFDF3','#067647','✓'),'warning':('#FFF7ED','#B54708','!'),'error':('#FEF3F2','#B42318','×'),'info':('#EEF4FF','#3538CD','i')}
        bg,fg,icon=palette.get(kind,palette['info']); self.setStyleSheet(f'QFrame{{background:{bg};border:1px solid {fg};border-radius:12px;}} QLabel{{color:{fg};background:transparent;}}')
        lay=QHBoxLayout(self); lay.setContentsMargins(14,11,14,11); badge=QLabel(icon); badge.setStyleSheet(f'font-size:18px;font-weight:900;color:{fg};'); lay.addWidget(badge)
        box=QVBoxLayout(); t=QLabel(title); t.setStyleSheet('font-weight:900;'); box.addWidget(t); s=QLabel(text); s.setWordWrap(True); box.addWidget(s); lay.addLayout(box,1)
        self.setMaximumWidth(390); self.setMinimumWidth(280); self.adjustSize(); self._place(); self.show(); self.raise_(); QTimer.singleShot(duration,self.close)
    def _place(self):
        if not self.parentWidget():return
        p=self.parentWidget(); margin=22; x=max(margin,p.width()-self.width()-margin); y=margin
        self.move(QPoint(x,y))

def clear_layout(layout):
    """Elimina widgets y layouts anidados; evita restos que pueden terminar superpuestos."""
    while layout.count():
        item=layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        elif item.layout(): clear_layout(item.layout()); item.layout().deleteLater()

def info(parent,title,text):
    try: Toast(parent,title,text,'success')
    except Exception: QMessageBox.information(parent,title,text)

def error(parent,text): QMessageBox.warning(parent,'Revisa la operación',text)
def confirm(parent,title,text): return QMessageBox.question(parent,title,text)==QMessageBox.StandardButton.Yes
