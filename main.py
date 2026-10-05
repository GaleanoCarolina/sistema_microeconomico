import sys,argparse
from PyQt6.QtWidgets import QApplication
from database.migrate import migrate
from utils.logging_config import setup_logging
from views.main_window import MainWindow
from controllers.app_controller import AppController

def parse_args():
    p=argparse.ArgumentParser(); p.add_argument('--demo',action='store_true',help='Carga datos ficticios si la base está vacía'); return p.parse_args()

def main():
    args=parse_args(); setup_logging(); migrate()
    if args.demo:
        from database.seeds.demo import seed_demo
        seed_demo()
    app=QApplication(sys.argv); app.setApplicationName('Sistema Microeconómico'); win=MainWindow(); controller=AppController(win); win.show(); return app.exec()

if __name__=='__main__': raise SystemExit(main())
