from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt

class RecommendationCard(QFrame):
    action_requested=pyqtSignal(int,str)
    def __init__(self,r,parent=None):
        super().__init__(parent); self.setObjectName('recommendationCard'); self.r=r
        lay=QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(8)
        colors={'URGENTE':('#FDECEC','#B42318'),'ALTA':('#FFF3E8','#B54708'),'MEDIA':('#FFF8D8','#8A5B00'),'BAJA':('#EEF4FF','#3538CD'),'INFORMATIVA':('#F2F4F7','#475467')}
        bg,fg=colors.get(r.prioridad,colors['INFORMATIVA']);
        top=QHBoxLayout(); badge=QLabel(r.prioridad); badge.setStyleSheet(f'background:{bg};color:{fg};padding:5px 9px;border:1px solid {fg};border-radius:8px;font-weight:900;'); top.addWidget(badge); top.addStretch(); conf=QLabel(f'Confianza: {r.confianza}'); conf.setObjectName('muted'); top.addWidget(conf); lay.addLayout(top)
        title=QLabel(r.accion); title.setStyleSheet('font-size:18px;font-weight:900;color:#101828;'); lay.addWidget(title)
        prod=QLabel(r.producto); prod.setStyleSheet('font-size:16px;font-weight:800;color:#344054;'); lay.addWidget(prod)
        what=QLabel(r.motivo); what.setWordWrap(True); lay.addWidget(what)
        why=QLabel('Por qué: '+r.detalle); why.setObjectName('muted'); why.setWordWrap(True); lay.addWidget(why)
        self.calc=QLabel(r.calculo or ''); self.calc.setWordWrap(True); self.calc.setVisible(False); self.calc.setStyleSheet('background:#F8FAFC;border:1px solid #E4E7EC;border-radius:10px;padding:10px;color:#475467;'); lay.addWidget(self.calc)
        actions=QHBoxLayout()
        if r.calculo:
            how=QPushButton('¿Cómo se calculó?'); how.setProperty('class','ghost'); how.clicked.connect(lambda:self.calc.setVisible(not self.calc.isVisible())); actions.addWidget(how)
        actions.addStretch()
        if r.producto_id:
            b=QPushButton('Crear propuesta de compra' if 'COMPR' in r.accion and 'NO COMPRAR' not in r.accion else 'Ver producto'); b.setProperty('class','accent' if 'COMPR' in r.accion and 'NO COMPRAR' not in r.accion else 'secondary'); b.clicked.connect(lambda:self.action_requested.emit(r.producto_id,r.accion)); actions.addWidget(b)
        lay.addLayout(actions)

class DecisionsView(QWidget):
    refresh_requested=pyqtSignal(); optimize_requested=pyqtSignal(float); product_action=pyqtSignal(int,str)
    MODES=[('Todas','Todas'),('Comprar pronto','COMPRAR PRONTO'),('No comprar','NO COMPRAR'),('Vencimiento','VENCIMIENTO'),('Precio','REVISAR PRECIO'),('Observar','OBSERVAR'),('Fiados / liquidez','FIADOS / LIQUIDEZ')]
    def __init__(self):
        super().__init__(); root=QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(14)
        head=QHBoxLayout(); v=QVBoxLayout(); t=QLabel('Decisiones'); t.setObjectName('pageTitle'); v.addWidget(t); s=QLabel('Recomendaciones explicadas con datos reales del negocio.'); s.setObjectName('muted'); v.addWidget(s); head.addLayout(v); head.addStretch(); ref=QPushButton('Actualizar recomendaciones'); ref.setProperty('class','secondary'); ref.clicked.connect(self.refresh_requested); head.addWidget(ref); root.addLayout(head)
        filter_scroll=QScrollArea(); filter_scroll.setWidgetResizable(True); filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); filter_scroll.setMinimumHeight(58); filter_host=QWidget(); filt=QHBoxLayout(filter_host); filt.setContentsMargins(0,0,0,4); filt.addWidget(QLabel('Mostrar:')); self.filter_buttons={}; self.mode='Todas'
        for label,key in self.MODES:
            b=QPushButton(label); b.setCheckable(True); b.setProperty('class','filter'); b.clicked.connect(lambda _=False,k=key:self._set_mode(k)); filt.addWidget(b); self.filter_buttons[key]=b
        self.filter_buttons['Todas'].setChecked(True); filt.addStretch(); filter_scroll.setWidget(filter_host); root.addWidget(filter_scroll)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.scroll.setFocusPolicy(Qt.FocusPolicy.StrongFocus); self.content=QWidget(); self.cards=QVBoxLayout(self.content); self.cards.setSpacing(12); self.cards.setAlignment(Qt.AlignmentFlag.AlignTop); self.scroll.setWidget(self.content); root.addWidget(self.scroll,1)
        budget=QFrame(); budget.setObjectName('darkCard'); bl=QHBoxLayout(budget); bl.setContentsMargins(16,13,16,13); lab=QLabel('Presupuesto para comprar'); lab.setStyleSheet('color:#FFFFFF;font-weight:800;'); bl.addWidget(lab); self.budget=QDoubleSpinBox(); self.budget.setRange(0,9999999); self.budget.setPrefix('Q '); self.budget.setValue(500); bl.addWidget(self.budget); calc=QPushButton('Calcular propuesta'); calc.setProperty('class','accent'); calc.clicked.connect(lambda:self.optimize_requested.emit(self.budget.value())); bl.addWidget(calc); self.budget_result=QLabel(''); self.budget_result.setStyleSheet('color:#CBD5E1;'); self.budget_result.setWordWrap(True); bl.addWidget(self.budget_result,1); root.addWidget(budget); self._all=[]
    def _set_mode(self,key):
        self.mode=key
        for k,b in self.filter_buttons.items(): b.setChecked(k==key)
        self._render()
    def set_filter(self,text):
        if text=='NO COMPRAR':self._set_mode('NO COMPRAR')
        elif text=='VENCIMIENTO':self._set_mode('VENCIMIENTO')
        else:self._set_mode('Todas')
    def set_recommendations(self,recs): self._all=list(recs); self._render()
    def _matches(self,r):
        mode=self.mode; text=(r.accion+' '+r.motivo+' '+r.producto).upper()
        return mode=='Todas' or (mode=='COMPRAR PRONTO' and 'COMPR' in text and 'NO COMPRAR' not in text) or (mode=='NO COMPRAR' and 'NO COMPRAR' in text) or (mode=='VENCIMIENTO' and ('VENC' in text or 'LOTE' in text)) or (mode=='REVISAR PRECIO' and 'PRECIO' in text) or (mode=='OBSERVAR' and 'OBSERVAR' in text) or (mode=='FIADOS / LIQUIDEZ' and ('LIQUIDEZ' in text or 'FIADO' in text))
    def _render(self):
        while self.cards.count():
            it=self.cards.takeAt(0); w=it.widget()
            if w:w.deleteLater()
        shown=[r for r in self._all if self._matches(r)]
        if not shown:
            box=QFrame(); box.setObjectName('softCard'); l=QVBoxLayout(box); lab=QLabel('No se detectaron decisiones urgentes en esta categoría.'); lab.setAlignment(Qt.AlignmentFlag.AlignCenter); lab.setObjectName('muted'); l.addWidget(lab); self.cards.addWidget(box)
        for r in shown:
            c=RecommendationCard(r); c.action_requested.connect(self.product_action); self.cards.addWidget(c)
        self.cards.addStretch()
    def set_budget_result(self,result):
        if not result['items']: self.budget_result.setText('No se recomienda invertir este presupuesto en nuevas compras con los datos actuales.'); return
        bits=[f"{x['product']}: {x['quantity']} (Q{x['investment_cents']/100:,.2f})" for x in result['items'][:4]]; self.budget_result.setText('Sugerencia: '+' • '.join(bits)+f" • Restante Q{result['remaining_cents']/100:,.2f}")
