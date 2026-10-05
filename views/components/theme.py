# Sistema visual V4. Inspirado en paneles administrativos oscuros con acento lima,
# superficies claras, tarjetas redondeadas y estados de interacción muy visibles.
COLORS = {
    'ink': '#0B1220',
    'navy': '#111827',
    'navy_2': '#182234',
    'surface': '#FFFFFF',
    'canvas': '#F2F4F7',
    'border': '#D8DEE8',
    'text': '#111827',
    'muted': '#667085',
    'lime': '#B9F227',
    'lime_dark': '#8DCB16',
    'blue': '#4F7CFF',
    'purple': '#7C5CFC',
    'green': '#21A366',
    'amber': '#D97706',
    'red': '#DC4C4C',
}

APP_STYLESHEET = r'''
* { outline: none; }
QWidget { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; color:#111827; }
QMainWindow, QDialog, #contentRoot, QScrollArea#pageScroll { background:#F2F4F7; }
QStackedWidget#contentRoot > QWidget { background:#F2F4F7; }
QScrollArea#pageScroll QWidget#qt_scrollarea_viewport { background:#F2F4F7; }
QWidget#productFormBody, QWidget#advancedPanel { background:#F2F4F7; }
QWidget#settingsPage, QWidget#settingsPage QLabel { background:#F2F4F7; color:#111827; }
QWidget#settingsPage QGroupBox, QWidget#settingsPage QGroupBox QLabel { background:#FFFFFF; color:#1D2939; }
QGroupBox#dangerZone { background:#FFF7F6; border:1px solid #FDA29B; }
QGroupBox#dangerZone::title { background:#FFF7F6; color:#B42318; }
QGroupBox#dangerZone QLabel { background:transparent; }

/* Sidebar */
#sidebar { background:#0B1220; border:none; }
#sidebar QLabel { color:#F8FAFC; }
#brand { font-size:19px; font-weight:900; padding:10px 10px 4px 10px; letter-spacing:.3px; }
#brandAccent { color:#B9F227; font-size:11px; font-weight:800; padding:0 10px 12px 10px; }
#sidebar QPushButton { color:#CBD5E1; background:transparent; border:1px solid transparent; text-align:left; padding:12px 14px; border-radius:11px; font-weight:650; margin:2px 0; }
#sidebar QPushButton:hover { background:#172235; color:#FFFFFF; border-color:#26354B; }
#sidebar QPushButton:pressed { background:#202D42; color:#FFFFFF; }
#sidebar QPushButton:checked { background:#1C293D; color:#FFFFFF; border:1px solid #33445D; border-left:4px solid #B9F227; padding-left:11px; }

/* Botones */
QPushButton { background:#111827; color:#FFFFFF; border:1px solid #111827; border-radius:10px; padding:10px 15px; font-weight:750; min-height:20px; }
QPushButton:hover { background:#1E293B; border-color:#2E3B50; }
QPushButton:pressed { background:#070B13; padding-top:11px; padding-bottom:9px; }
QPushButton:focus { border:2px solid #8DBA1D; }
QPushButton:disabled { background:#E4E7EC; color:#98A2B3; border-color:#E4E7EC; }
QPushButton[class="accent"] { background:#B9F227; color:#0B1220; border-color:#A9E41B; }
QPushButton[class="accent"]:hover { background:#C8F75B; border-color:#B9F227; }
QPushButton[class="accent"]:pressed { background:#9FDB1B; }
QPushButton[class="secondary"] { background:#FFFFFF; color:#344054; border:1px solid #D0D5DD; }
QPushButton[class="secondary"]:hover { background:#F8FAFC; border-color:#98A2B3; }
QPushButton[class="secondary"]:pressed { background:#EAECF0; }
QPushButton[class="secondary"]:checked { background:#EAFBC4; color:#365314; border:1px solid #9FD91A; }
QPushButton[class="danger"] { background:#FEF3F2; color:#B42318; border:1px solid #FDA29B; }
QPushButton[class="danger"]:hover { background:#FEE4E2; }
QPushButton[class="success"] { background:#ECFDF3; color:#067647; border:1px solid #ABEFC6; }
QPushButton[class="ghost"] { background:transparent; color:#344054; border:1px solid transparent; }
QPushButton[class="ghost"]:hover { background:#EAECF0; }
QPushButton[class="filter"] { background:#FFFFFF; color:#475467; border:1px solid #D0D5DD; padding:8px 12px; }
QPushButton[class="filter"]:hover { background:#F9FAFB; border-color:#98A2B3; }
QPushButton[class="filter"]:checked { background:#111827; color:#FFFFFF; border-color:#111827; }

/* Inputs */
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QDateEdit,QTextEdit { background:#FFFFFF; border:1px solid #C7D0DC; border-radius:9px; padding:8px 10px; min-height:22px; selection-background-color:#DDF6A0; selection-color:#0B1220; }
QLineEdit:hover,QComboBox:hover,QSpinBox:hover,QDoubleSpinBox:hover,QDateEdit:hover,QTextEdit:hover { border-color:#98A2B3; }
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus,QDateEdit:focus,QTextEdit:focus { border:2px solid #8FC31F; background:#FDFFF8; }
QLineEdit[error="true"],QComboBox[error="true"],QSpinBox[error="true"],QDoubleSpinBox[error="true"] { border:2px solid #F04438; background:#FFF6F5; }
QComboBox::drop-down { border:none; width:28px; }
QComboBox QAbstractItemView { background:white; border:1px solid #D0D5DD; selection-background-color:#EAFBC4; selection-color:#111827; outline:0; }
QSpinBox,QDoubleSpinBox { min-height:28px; padding-left:10px; padding-right:8px; }
QSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::up-button,QDoubleSpinBox::down-button { width:0px; height:0px; border:none; background:transparent; }
QFrame#quantityControl { background:transparent; border:none; }
QPushButton[class="quantityButton"] { min-height:30px; max-height:34px; min-width:32px; padding:2px 6px; border-radius:8px; background:#EEF2F6; color:#111827; border:1px solid #CDD5DF; font-size:16px; font-weight:900; }
QPushButton[class="quantityButton"]:hover { background:#EAFBC4; border-color:#9FD91A; }
QPushButton[class="quantityButton"]:pressed { background:#DDF6A0; }
QLineEdit#quantityValue { min-height:30px; padding:2px 8px; font-weight:850; background:#FFFFFF; color:#111827; border:1px solid #C7D0DC; }
QPushButton[class="iconDanger"] { background:#FEF3F2; color:#B42318; border:1px solid #FDA29B; border-radius:8px; padding:0px; min-width:34px; max-width:38px; min-height:30px; max-height:34px; font-size:16px; font-weight:900; }
QPushButton[class="iconDanger"]:hover { background:#FEE4E2; border-color:#F97066; }
QPushButton[class="iconDanger"]:pressed { background:#FECDCA; }
QPushButton[class="tableAction"] { padding:5px 10px; min-height:28px; max-height:32px; border-radius:8px; }
QWidget#editableCatalogField { background:transparent; border:none; }
QPushButton[class="comboDropButton"] { background:#F2F4F7; color:#344054; border:1px solid #C7D0DC; border-radius:9px; min-width:42px; max-width:42px; min-height:38px; max-height:40px; padding:0; font-size:14px; font-weight:900; }
QPushButton[class="comboDropButton"]:hover { background:#EAFBC4; color:#365314; border-color:#9FD91A; }
QPushButton[class="comboDropButton"]:pressed { background:#DDF6A0; border-color:#8FC31F; }
QPushButton[class="comboDropButton"]:focus { border:2px solid #8FC31F; }
QPushButton[class="comboInlineArrow"] { background:#F2F4F7; color:#344054; border:1px solid #C7D0DC; border-radius:7px; padding:0; min-width:28px; max-width:32px; min-height:24px; font-size:12px; font-weight:900; }
QPushButton[class="comboInlineArrow"]:hover { background:#EAFBC4; color:#365314; border-color:#9FD91A; }
QPushButton[class="comboInlineArrow"]:pressed { background:#DDF6A0; border-color:#8FC31F; }

/* Check / radio */
QCheckBox, QRadioButton { spacing:8px; color:#344054; }
QCheckBox::indicator, QRadioButton::indicator { width:18px; height:18px; }
QCheckBox::indicator:unchecked { border:1px solid #98A2B3; background:#FFFFFF; border-radius:5px; }
QCheckBox::indicator:checked { border:1px solid #8FC31F; background:#B9F227; border-radius:5px; }
QRadioButton::indicator:unchecked { border:1px solid #98A2B3; background:#FFFFFF; border-radius:9px; }
QRadioButton::indicator:checked { border:5px solid #B9F227; background:#111827; border-radius:9px; }

/* Tablas */
QTableWidget,QTableView { background:#FFFFFF; border:1px solid #D8DEE8; border-radius:12px; gridline-color:#EEF1F5; alternate-background-color:#FAFBFC; selection-background-color:#DDF6A0; selection-color:#111827; }
QTableWidget::item,QTableView::item { padding:7px 8px; border:none; }
QTableWidget::item:hover,QTableView::item:hover { background:#F1F8E4; }
QTableWidget::item:selected,QTableView::item:selected { background:#DDF6A0; color:#111827; border-top:1px solid #A7D93A; border-bottom:1px solid #A7D93A; }
QHeaderView::section { background:#F7F8FA; color:#475467; padding:10px 9px; border:none; border-bottom:1px solid #D8DEE8; font-weight:800; }
QTableCornerButton::section { background:#F7F8FA; border:none; border-bottom:1px solid #D8DEE8; }

/* Tarjetas y paneles */
QGroupBox { background:#FFFFFF; border:1px solid #D8DEE8; border-radius:14px; margin-top:16px; padding:16px 14px 12px 14px; font-weight:800; color:#1D2939; }
QGroupBox::title { subcontrol-origin:margin; left:15px; padding:0 7px; color:#1D2939; background:#FFFFFF; border-radius:6px; }
QFrame#card, QFrame#panel, QFrame#recommendationCard, QFrame#clickCard { background:#FFFFFF; border:1px solid #D8DEE8; border-radius:16px; }
QFrame#darkCard { background:#111827; border:1px solid #253247; border-radius:16px; }
QFrame#accentCard { background:#B9F227; border:1px solid #A6DB23; border-radius:16px; }
QFrame#softCard { background:#F8FAFC; border:1px solid #E4E7EC; border-radius:14px; }
QFrame#clickCard:hover { background:#FBFDF7; border:1px solid #A9D94C; }

/* Tipografía */
QLabel#pageTitle { font-size:26px; font-weight:900; color:#101828; }
QLabel#sectionTitle { font-size:17px; font-weight:850; color:#101828; }
QLabel#dialogTitle { font-size:21px; font-weight:900; color:#101828; }
QLabel#muted { color:#667085; }
QLabel#help { color:#667085; font-size:12px; }
QLabel#kpiValue { font-size:25px; font-weight:900; color:#101828; }
QLabel#kpiTitle { color:#667085; font-weight:800; }
QLabel#successText { color:#067647; font-weight:800; }
QLabel#warningText { color:#B54708; font-weight:800; }
QLabel#dangerText { color:#B42318; font-weight:800; }
QLabel#limeText { color:#76A80C; font-weight:900; }
QLabel#darkCardTitle { color:#D0D5DD; font-weight:800; }
QLabel#darkCardValue { color:#FFFFFF; font-size:25px; font-weight:900; }
QLabel#accentValue { color:#0B1220; font-size:25px; font-weight:900; }

/* Calendario */
QCalendarWidget QWidget { alternate-background-color:#F8FAFC; }
QCalendarWidget QToolButton { color:#111827; background:#FFFFFF; border:1px solid #D0D5DD; border-radius:8px; padding:6px 9px; font-weight:800; }
QCalendarWidget QToolButton:hover { background:#EAFBC4; border-color:#A7D93A; }
QCalendarWidget QMenu { background:#FFFFFF; color:#111827; }
QCalendarWidget QSpinBox { background:#FFFFFF; }
QCalendarWidget QAbstractItemView { background:#FFFFFF; color:#344054; selection-background-color:#111827; selection-color:#B9F227; border:1px solid #E4E7EC; border-radius:10px; outline:0; }
QCalendarWidget QAbstractItemView::item:hover { background:#EAFBC4; color:#111827; }
QCalendarWidget QAbstractItemView::item:selected { background:#111827; color:#B9F227; }

QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { background:#E8ECF2; width:13px; margin:2px 2px 2px 2px; border-radius:6px; }
QScrollBar::handle:vertical { background:#9DBA55; min-height:38px; border-radius:6px; }
QScrollBar::handle:vertical:hover { background:#7FA31E; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0px; }
QScrollBar:horizontal { background:#E8ECF2; height:13px; margin:2px; border-radius:6px; }
QScrollBar::handle:horizontal { background:#9DBA55; min-width:38px; border-radius:6px; }
QScrollBar::handle:horizontal:hover { background:#7FA31E; }
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0px; }
QToolTip { background:#111827; color:#FFFFFF; border:1px solid #344054; padding:7px 9px; border-radius:6px; }
QMessageBox { background:#F8FAFC; }
QStatusBar { background:#0B1220; color:#CBD5E1; }
'''
