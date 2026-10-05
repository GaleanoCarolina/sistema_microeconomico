from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal,Qt,QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter,MaxNLocator
from views.components.widgets import KPIButton,clear_layout
from views.components.calendar_dialog import DateRangeDialog
from utils.money import q

class DashboardView(QWidget):
    go_to=pyqtSignal(str,str); quick_action=pyqtSignal(str); period_changed=pyqtSignal(str,str,str)
    PERIODS=['Hoy','Últimos 7 días','Últimos 30 días','Este mes','Personalizado']
    def __init__(self):
        super().__init__(); self.custom_start=''; self.custom_end=''; self.current_period='Hoy'; self._last_columns=None
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.scroll=QScrollArea(); self.scroll.setObjectName('pageScroll'); self.scroll.setWidgetResizable(True); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); outer.addWidget(self.scroll)
        page=QWidget(); page.setObjectName('dashboardPage'); page.setStyleSheet('QWidget#dashboardPage{background:#F2F4F7;}'); self.scroll.setWidget(page); self.root=QVBoxLayout(page); self.root.setContentsMargins(24,20,24,26); self.root.setSpacing(12)
        head=QVBoxLayout(); first=QHBoxLayout(); left=QVBoxLayout(); title=QLabel('Dashboard'); title.setObjectName('pageTitle'); left.addWidget(title); sub=QLabel('Lo importante del negocio, explicado con datos reales.'); sub.setObjectName('muted'); left.addWidget(sub); first.addLayout(left); first.addStretch(); head.addLayout(first)
        periodbar=QHBoxLayout(); periodbar.addWidget(QLabel('Período:')); self.period_buttons={}
        for text in self.PERIODS:
            b=QPushButton(text); b.setCheckable(True); b.setProperty('class','filter'); b.clicked.connect(lambda _=False,t=text:self._period(t)); self.period_buttons[text]=b; periodbar.addWidget(b)
        periodbar.addStretch(); self.period_buttons['Hoy'].setChecked(True); head.addLayout(periodbar); self.root.addLayout(head)

        self.top=QGridLayout(); self.top.setHorizontalSpacing(10); self.top.setVerticalSpacing(10); self.root.addLayout(self.top)
        self.cards={
          'sales':KPIButton('Ventas','Q0.00','Todo lo vendido, incluso lo fiado.','dark','▣'),
          'profit':KPIButton('Ganancia bruta','Q0.00','Ventas menos costo de la mercancía vendida.','accent','↗'),
          'paid':KPIButton('Cobrado','Q0.00','Dinero realmente recibido.','dark','✓'),
          'receivable':KPIButton('Pendiente por cobrar','Q0.00','Saldo de fiados aún no cobrado.','light','◷'),
          'inventory':KPIButton('Dinero en inventario','Q0.00','Valor contable de existencias actuales.','light','▦'),
          'purchases':KPIButton('Compras del período','Q0.00','Valor de adquisiciones registradas.','light','↓'),
          'low':KPIButton('Por agotarse','0','Productos con existencias bajas.','light','!'),
          'expiry':KPIButton('Por vencer','0','Productos con lotes próximos a vencer.','light','◴')}
        self.order=['sales','profit','paid','receivable','inventory','purchases','low','expiry']
        self.cards['receivable'].clicked.connect(lambda:self.go_to.emit('Clientes y Fiados','')); self.cards['low'].clicked.connect(lambda:self.go_to.emit('Inventario','low')); self.cards['expiry'].clicked.connect(lambda:self.go_to.emit('Decisiones','VENCIMIENTO')); self.cards['purchases'].clicked.connect(lambda:self.go_to.emit('Historial','PURCHASE'))

        self.middle=QGridLayout(); self.middle.setSpacing(12); self.root.addLayout(self.middle)
        self.chart=QFrame(); self.chart.setObjectName('card'); cl=QVBoxLayout(self.chart); cl.setContentsMargins(18,16,18,14); chart_head=QHBoxLayout(); self.chart_title=QLabel('Ventas'); self.chart_title.setObjectName('sectionTitle'); chart_head.addWidget(self.chart_title); chart_head.addStretch(); note=QLabel('Evolución monetaria'); note.setObjectName('help'); chart_head.addWidget(note); cl.addLayout(chart_head); self.figure=Figure(figsize=(6.6,3.1),tight_layout=True,facecolor='#FFFFFF'); self.canvas=FigureCanvas(self.figure); self.canvas.setMinimumHeight(235); cl.addWidget(self.canvas); self.empty_chart=QLabel(''); self.empty_chart.setObjectName('muted'); self.empty_chart.setWordWrap(True); cl.addWidget(self.empty_chart)
        self.today=QFrame(); self.today.setObjectName('darkCard'); tl=QVBoxLayout(self.today); tl.setContentsMargins(18,16,18,16); tt=QLabel('RESUMEN DE HOY'); tt.setStyleSheet('color:#B9F227;font-weight:900;letter-spacing:.5px;'); tl.addWidget(tt); self.today_labels={}
        for key,label in [('sales','Ventas'),('paid','Cobrado'),('profit','Ganancia bruta'),('purchases','Compras'),('payments','Abonos'),('tickets','Número de ventas')]:
            row=QHBoxLayout(); a=QLabel(label); a.setStyleSheet('color:#CBD5E1;'); a.setWordWrap(True); b=QLabel('Q0.00' if key!='tickets' else '0'); b.setStyleSheet('color:#FFFFFF;font-weight:900;font-size:15px;'); b.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter); row.addWidget(a,1); row.addWidget(b); tl.addLayout(row); self.today_labels[key]=b
        tl.addStretch()

        self.lower=QGridLayout(); self.lower.setSpacing(12); self.root.addLayout(self.lower)
        self.attention=QFrame(); self.attention.setObjectName('card'); al=QVBoxLayout(self.attention); at=QLabel('Atención requerida'); at.setObjectName('sectionTitle'); al.addWidget(at); self.attention_box=QVBoxLayout(); al.addLayout(self.attention_box); al.addStretch()
        self.products=QFrame(); self.products.setObjectName('card'); pl=QVBoxLayout(self.products); pt=QLabel('Productos destacados'); pt.setObjectName('sectionTitle'); pl.addWidget(pt); self.best_name=QLabel('Aún no hay ventas'); self.best_name.setStyleSheet('font-size:18px;font-weight:900;'); self.best_name.setWordWrap(True); pl.addWidget(self.best_name); self.best_units=QLabel(''); self.best_units.setObjectName('muted'); self.best_units.setWordWrap(True); pl.addWidget(self.best_units); self.best_profit=QLabel(''); self.best_profit.setWordWrap(True); self.best_profit.setObjectName('help'); pl.addWidget(self.best_profit); self.least=QLabel(''); self.least.setWordWrap(True); self.least.setObjectName('help'); pl.addWidget(self.least); pl.addStretch()
        self.recent=QFrame(); self.recent.setObjectName('card'); rl=QVBoxLayout(self.recent); rt=QLabel('Actividad reciente'); rt.setObjectName('sectionTitle'); rl.addWidget(rt); self.recent_box=QVBoxLayout(); self.recent_box.setSpacing(5); rl.addLayout(self.recent_box); rl.addStretch()

        quick=QFrame(); quick.setObjectName('softCard'); self.quick_layout=QHBoxLayout(quick); self.quick_layout.setContentsMargins(14,12,14,12); self.quick_layout.addWidget(QLabel('Acciones rápidas'))
        for text,key in [('Nueva venta','Caja'),('Nueva compra','Compras'),('Registrar abono','Clientes y Fiados'),('Agregar producto','Inventario'),('Ver recomendaciones','Decisiones')]:
            b=QPushButton(text); b.setProperty('class','accent' if key=='Caja' else 'secondary'); b.clicked.connect(lambda _=False,k=key:self.quick_action.emit(k)); self.quick_layout.addWidget(b)
        self.quick_layout.addStretch(); self.root.addWidget(quick)
        QTimer.singleShot(0,self._reflow)

    def resizeEvent(self,event):
        super().resizeEvent(event); QTimer.singleShot(0,self._reflow)
    def _reflow(self):
        w=max(1,self.scroll.viewport().width()); cols=4 if w>=1180 else (2 if w>=720 else 1)
        if cols!=self._last_columns:
            for c in self.cards.values(): self.top.removeWidget(c)
            for i,k in enumerate(self.order): self.top.addWidget(self.cards[k],i//cols,i%cols)
            for c in range(cols): self.top.setColumnStretch(c,1)
            self.middle.removeWidget(self.chart); self.middle.removeWidget(self.today)
            if w>=980:
                self.middle.addWidget(self.chart,0,0); self.middle.addWidget(self.today,0,1); self.middle.setColumnStretch(0,3); self.middle.setColumnStretch(1,1)
            else:
                self.middle.addWidget(self.chart,0,0); self.middle.addWidget(self.today,1,0); self.middle.setColumnStretch(0,1)
            for widget in (self.attention,self.products,self.recent): self.lower.removeWidget(widget)
            if w>=1100:
                self.lower.addWidget(self.attention,0,0); self.lower.addWidget(self.products,0,1); self.lower.addWidget(self.recent,0,2)
                for c in range(3): self.lower.setColumnStretch(c,1)
            elif w>=700:
                self.lower.addWidget(self.attention,0,0); self.lower.addWidget(self.products,0,1); self.lower.addWidget(self.recent,1,0,1,2); self.lower.setColumnStretch(0,1); self.lower.setColumnStretch(1,1)
            else:
                self.lower.addWidget(self.attention,0,0); self.lower.addWidget(self.products,1,0); self.lower.addWidget(self.recent,2,0); self.lower.setColumnStretch(0,1)
            self._last_columns=cols

    def _period(self,text):
        if text=='Personalizado':
            dlg=DateRangeDialog(self)
            if not dlg.exec():
                for k,b in self.period_buttons.items(): b.setChecked(k==self.current_period)
                return
            self.custom_start,self.custom_end=dlg.range()
        else:self.custom_start=self.custom_end=''
        self.current_period=text
        for k,b in self.period_buttons.items(): b.setChecked(k==text)
        self.period_changed.emit(text,self.custom_start,self.custom_end)
    def update_kpis(self,d):
        self.cards['sales'].set_data(q(d['sales_cents']),f"{d['tickets']} ventas • Ticket promedio {q(d['avg_ticket_cents'])}" if d['tickets'] else 'Aún no hay ventas en este período.')
        self.cards['profit'].set_data(q(d['profit_cents']),f"Ventas {q(d['sales_cents'])} − costo vendido {q(d.get('cogs_cents',0))}")
        self.cards['paid'].set_data(q(d['paid_cents']),f"Ventas cobradas {q(d['sale_paid_cents'])} • Abonos {q(d['payments_cents'])}")
        self.cards['receivable'].set_data(q(d['receivable_cents'])); self.cards['inventory'].set_data(q(d['inventory_cents'])); self.cards['purchases'].set_data(q(d.get('purchases_cents',0))); self.cards['low'].set_data(str(d['low_stock_count'])); self.cards['expiry'].set_data(str(d['expiring_count']))
        best=d.get('best_product')
        if best:self.best_name.setText(best['name']); self.best_units.setText(f"Más vendido: {best['units']:.0f} unidades • {q(best['revenue'])}")
        else:self.best_name.setText('Aún no hay ventas'); self.best_units.setText('No existe información suficiente en este período.')
        bp=d.get('best_profit_product'); self.best_profit.setText(f"Mayor ganancia: {bp['name']} • {q(bp['profit'])}" if bp else 'Mayor ganancia: sin datos suficientes.')
        least=d.get('least_product'); self.least.setText(f"Menor rotación observada: {least['name']} ({least['units']:.0f} unidades)." if least else 'Menor rotación: aparecerá cuando exista historial suficiente.')
        ts=d.get('today_summary',{}); self.today_labels['sales'].setText(q(ts.get('sales_cents',0))); self.today_labels['paid'].setText(q(ts.get('paid_cents',0))); self.today_labels['profit'].setText(q(ts.get('profit_cents',0))); self.today_labels['purchases'].setText(q(ts.get('purchases_cents',0))); self.today_labels['payments'].setText(q(ts.get('payments_cents',0))); self.today_labels['tickets'].setText(str(ts.get('tickets',0)))
        clear_layout(self.attention_box)
        att=[(d['low_stock_count'],'productos por agotarse',lambda:self.go_to.emit('Inventario','low')),(d['expiring_count'],'productos por vencer',lambda:self.go_to.emit('Decisiones','VENCIMIENTO')),(d['stagnant_count'],'productos estancados',lambda:self.go_to.emit('Decisiones','NO COMPRAR'))]
        if d.get('receivable_cents',0)>0: att.append((q(d['receivable_cents']),'pendientes por cobrar',lambda:self.go_to.emit('Clientes y Fiados','')))
        if d.get('stagnant_capital_cents',0)>0: att.append((q(d['stagnant_capital_cents']),'en productos estancados',lambda:self.go_to.emit('Decisiones','NO COMPRAR')))
        for value,text,fn in att[:5]:
            b=QPushButton(f'{value}  ·  {text}'); b.setProperty('class','secondary'); b.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred); b.clicked.connect(fn); self.attention_box.addWidget(b)
        if not att:
            lab=QLabel('No hay alertas importantes en este momento.'); lab.setObjectName('muted'); lab.setWordWrap(True); self.attention_box.addWidget(lab)
        clear_layout(self.recent_box)
        recent=d.get('recent_activity',[])
        for r in recent[:5]:
            card=QFrame(); card.setObjectName('softCard'); row=QGridLayout(card); row.setContentsMargins(10,8,10,8); row.setHorizontalSpacing(10)
            kind=QLabel(r['kind']); kind.setStyleSheet('font-weight:850;color:#101828;'); full_descr=str(r['descr']); shown_descr=full_descr if len(full_descr)<=42 else full_descr[:39]+'…'; descr=QLabel(shown_descr); descr.setObjectName('help'); descr.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction); descr.setToolTip(full_descr); descr.setMinimumWidth(0); descr.setWordWrap(False)
            amount=QLabel(q(r['amount'])); amount.setStyleSheet('font-weight:900;color:#101828;'); amount.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            when=QLabel(str(r['ts'])[:16]); when.setObjectName('help'); when.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(kind,0,0); row.addWidget(amount,0,1); row.addWidget(descr,1,0); row.addWidget(when,1,1); row.setColumnStretch(0,1); self.recent_box.addWidget(card)
        if not recent:
            lab=QLabel('Todavía no hay actividad reciente.'); lab.setObjectName('muted'); self.recent_box.addWidget(lab)
    def update_chart(self,rows,start,end):
        self.figure.clear(); ax=self.figure.add_subplot(111); ax.set_facecolor('#FFFFFF'); nonzero=any(v for _,v in rows); labels=[d[5:] for d,_ in rows]; vals=[v/100 for _,v in rows]
        if rows:
            step=max(1,len(labels)//8); x=list(range(len(labels))); ax.plot(x,vals,marker='o',linewidth=2.4,markersize=4.5,color='#111827'); ax.fill_between(x,vals,alpha=.25,color='#B9F227'); ax.set_xticks(x[::step]); ax.set_xticklabels(labels[::step],rotation=0,ha='center',fontsize=8,color='#667085'); ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_: f'Q{y:,.0f}')); ax.yaxis.set_major_locator(MaxNLocator(nbins=5)); ax.tick_params(axis='y',labelsize=8,colors='#667085'); ax.grid(axis='y',alpha=.15,color='#98A2B3'); ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color('#D0D5DD')
        self.empty_chart.setText('' if nonzero else 'Aún no hay ventas registradas para este período.'); self.chart_title.setText(f'Ventas • {start} a {end}'); self.canvas.draw_idle()
