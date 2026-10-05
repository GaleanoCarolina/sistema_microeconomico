from PyQt6.QtWidgets import QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QStackedWidget,QFrame
from PyQt6.QtCore import Qt
from views.components.theme import APP_STYLESHEET
from views.dashboard.view import DashboardView
from views.caja.view import CashView
from views.compras.view import PurchaseView
from views.inventario.view import InventoryView
from views.clientes.view import CustomersView
from views.decisiones.view import DecisionsView
from views.trazabilidad.view import HistoryView
from views.reportes.view import ReportsView
from views.configuracion.view import SettingsView

class MainWindow(QMainWindow):
    NAV=[('Dashboard','▦'),('Caja','▣'),('Compras','↓'),('Inventario','▤'),('Clientes y Fiados','◉'),('Decisiones','◆'),('Historial','◷'),('Reportes','▥'),('Configuración','⚙')]
    def __init__(self):
        super().__init__(); self.setWindowTitle('Sistema de Gestión Microeconómica e Inventarios'); self.resize(1440,900); self.setMinimumSize(900,620); self.setStyleSheet(APP_STYLESHEET)
        shell=QWidget(); lay=QHBoxLayout(shell); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0); self.setCentralWidget(shell)
        side=QFrame(); side.setObjectName('sidebar'); side.setMinimumWidth(190); side.setMaximumWidth(218); s=QVBoxLayout(side); s.setContentsMargins(14,18,14,16); s.setSpacing(4)
        brand=QLabel('●  MI INVENTARIO'); brand.setObjectName('brand'); s.addWidget(brand); accent=QLabel('GESTIÓN MICROECONÓMICA'); accent.setObjectName('brandAccent'); s.addWidget(accent)
        self.stack=QStackedWidget(); self.stack.setObjectName('contentRoot'); self.pages={'Dashboard':DashboardView(),'Caja':CashView(),'Compras':PurchaseView(),'Inventario':InventoryView(),'Clientes y Fiados':CustomersView(),'Decisiones':DecisionsView(),'Historial':HistoryView(),'Reportes':ReportsView(),'Configuración':SettingsView()}; self.buttons={}
        for name,icon in self.NAV:
            page=self.pages[name]; b=QPushButton(f'{icon}   {name}'); b.setCheckable(True); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(lambda _=False,n=name:self.navigate(n)); s.addWidget(b); self.buttons[name]=b; self.stack.addWidget(page)
        s.addStretch(); footer_box=QFrame(); footer_box.setStyleSheet('background:#111827;border:1px solid #27364B;border-radius:12px;'); fl=QVBoxLayout(footer_box); fl.setContentsMargins(12,10,12,10); status=QLabel('●  Sistema local'); status.setStyleSheet('color:#B9F227;font-weight:800;'); fl.addWidget(status); self.footer=QLabel('Jalapa, Guatemala\nMoneda: GTQ'); self.footer.setStyleSheet('color:#AAB4C4;'); fl.addWidget(self.footer); s.addWidget(footer_box); lay.addWidget(side); lay.addWidget(self.stack,1); self.navigate('Dashboard')
    def navigate(self,name):
        if name not in self.pages:return
        self.stack.setCurrentWidget(self.pages[name])
        for n,b in self.buttons.items():b.setChecked(n==name)
