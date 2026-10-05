import logging
from PyQt6.QtCore import QObject,pyqtSignal
from PyQt6.QtWidgets import QFileDialog,QMessageBox,QInputDialog
from repositories.product_repository import ProductRepository
from repositories.customer_repository import CustomerRepository
from repositories.supplier_repository import SupplierRepository
from repositories.settings_repository import SettingsRepository
from repositories.history_repository import HistoryRepository
from services.sales_service import SalesService
from services.purchase_service import PurchaseService
from services.credit_service import CreditService
from services.inventory_service import InventoryService
from services.analytics_service import AnalyticsService
from services.recommendation_service import RecommendationService
from services.budget_optimizer_service import BudgetOptimizerService
from services.report_service import ReportService
from services.backup_service import BackupService
from services.reset_service import ResetService
from views.caja.view import CheckoutDialog
from views.components.dialogs import ProductDialog,QuickCustomerDialog,QuickSupplierDialog,PaymentDialog,LotDialog
from views.components.widgets import info,error,confirm
from utils.money import to_cents,q

log=logging.getLogger(__name__)

class DataEvents(QObject):
    sale_changed=pyqtSignal(); purchase_changed=pyqtSignal(); inventory_changed=pyqtSignal(); credit_changed=pyqtSignal(); master_changed=pyqtSignal()

class AppController:
    def __init__(self,window,db_path=None):
        self.window=window; self.db_path=db_path; self.products=ProductRepository(db_path); self.customers=CustomerRepository(db_path); self.suppliers=SupplierRepository(db_path); self.settings=SettingsRepository(db_path); self.history=HistoryRepository(db_path)
        self.sales=SalesService(db_path); self.purchases=PurchaseService(db_path); self.credit=CreditService(db_path); self.inventory=InventoryService(db_path); self.analytics=AnalyticsService(db_path); self.recommendations=RecommendationService(db_path); self.optimizer=BudgetOptimizerService(db_path); self.reports=ReportService(db_path); self.backups=BackupService(); self.resetter=ResetService(db_path)
        self.events=DataEvents(); self.dashboard_period=('Hoy','',''); self._wire(); self._wire_events(); self.window.pages['Compras'].set_profit_policy(self.settings.get('profit_policy','MARKUP')); self.refresh_all()
    def _wire(self):
        d=self.window.pages['Dashboard']; d.go_to.connect(self._dashboard_nav); d.quick_action.connect(self._quick_nav); d.period_changed.connect(self._dashboard_period)
        c=self.window.pages['Caja']; c.request_products.connect(self.refresh_cash_products); c.checkout_requested.connect(self.checkout)
        p=self.window.pages['Compras']; p.request_products.connect(self.refresh_purchase_products); p.save_requested.connect(self.save_purchase); p.new_product_requested.connect(self.add_product_from_purchase); p.new_supplier_requested.connect(self.add_supplier_from_purchase); p.pending_requested.connect(self.receive_pending_purchase)
        i=self.window.pages['Inventario']; i.search_changed.connect(self.refresh_inventory); i.add_requested.connect(self.add_product); i.edit_requested.connect(self.edit_product); i.lots_requested.connect(self.show_lots); i.purchase_requested.connect(self.purchase_selected); i.detail_requested.connect(self.show_product_detail)
        cu=self.window.pages['Clientes y Fiados']; cu.search_changed.connect(self.refresh_customers); cu.add_requested.connect(self.add_customer); cu.payment_requested.connect(self.add_payment)
        de=self.window.pages['Decisiones']; de.refresh_requested.connect(self.refresh_decisions); de.optimize_requested.connect(self.optimize_budget); de.product_action.connect(self.recommendation_action)
        h=self.window.pages['Historial']; h.refresh_requested.connect(self.refresh_history); h.detail_requested.connect(self.show_history_detail)
        r=self.window.pages['Reportes']; r.generate_requested.connect(self.generate_report); r.abc_requested.connect(self.generate_abc)
        s=self.window.pages['Configuración']; s.save_requested.connect(self.save_settings); s.backup_requested.connect(self.create_backup); s.restore_requested.connect(self.restore_backup); s.reset_requested.connect(self.reset_all_data)
    def _wire_events(self):
        for sig in (self.events.sale_changed,self.events.purchase_changed,self.events.inventory_changed,self.events.credit_changed,self.events.master_changed): sig.connect(self.refresh_dashboard)
        self.events.sale_changed.connect(lambda:(self.refresh_inventory(''),self.refresh_cash_products(''),self.refresh_customers(''),self.refresh_decisions(),self.refresh_history()))
        self.events.purchase_changed.connect(lambda:(self.refresh_inventory(''),self.refresh_cash_products(''),self.refresh_decisions(),self.refresh_history()))
        self.events.inventory_changed.connect(lambda:(self.refresh_inventory(''),self.refresh_cash_products(''),self.refresh_decisions(),self.refresh_history()))
        self.events.credit_changed.connect(lambda:(self.refresh_customers(''),self.refresh_decisions(),self.refresh_history()))
        self.events.master_changed.connect(lambda:(self.refresh_inventory(''),self.refresh_cash_products(''),self.refresh_purchase_products(''),self.refresh_customers('')))
    def refresh_all(self):
        self.refresh_dashboard(); self.refresh_cash_products(''); self.refresh_purchase_products(''); self.refresh_inventory(''); self.refresh_customers(''); self.refresh_decisions(); self.refresh_history(); self.refresh_settings(); self.refresh_suppliers()
    def _dashboard_period(self,period,start,end): self.dashboard_period=(period,start,end); self.refresh_dashboard()
    def refresh_dashboard(self):
        period,start,end=self.dashboard_period; d=self.analytics.dashboard(period,start or None,end or None); self.window.pages['Dashboard'].update_kpis(d); self.window.pages['Dashboard'].update_chart(self.analytics.sales_series(d['start'],d['end']),d['start'],d['end'])
    def _dashboard_nav(self,name,filter_value):
        self.window.navigate(name)
        if name=='Inventario': self.window.pages['Inventario'].set_filter(filter_value); self.refresh_inventory(self.window.pages['Inventario'].search.text())
        elif name=='Decisiones': self.window.pages['Decisiones'].set_filter(filter_value); self.refresh_decisions()
        elif name=='Clientes y Fiados': self.refresh_customers('')
        elif name=='Historial': self.refresh_history(); self.window.pages['Historial'].set_operation_filter(filter_value)
    def _quick_nav(self,name):
        self.window.navigate(name)
        if name=='Inventario': self.add_product()
    def refresh_cash_products(self,text=''):
        rows=self.products.search(text,limit=80); v=self.window.pages['Caja']; v.set_products(rows)
        quick=self.products.fetchall('''SELECT p.*,COALESCE(SUM(CASE WHEN s.status='COMPLETED' THEN sd.quantity ELSE 0 END),0) sold FROM products p LEFT JOIN sale_details sd ON sd.product_id=p.id LEFT JOIN sales s ON s.id=sd.sale_id WHERE p.active=1 GROUP BY p.id ORDER BY p.favorite DESC,sold DESC,p.name LIMIT 8'''); v.set_quick_products(quick)
    def checkout(self):
        v=self.window.pages['Caja']; cart=v.cart()
        if not cart:return error(v,'Agrega al menos un producto antes de cobrar.')
        dlg=CheckoutDialog(v.total_cents,self.customers.search('',100),self.settings.get('credit_enabled','1')=='1',v)
        def create_inline_customer():
            qd=QuickCustomerDialog(parent=dlg)
            if qd.exec():
                d=qd.data(); sims=self.customers.similar(d['name'])
                if sims and not confirm(dlg,'Cliente parecido',f"Ya existe un cliente parecido: {sims[0]['name']}.\n\n¿Seguro que deseas crear otro?"): return
                try:
                    cid=self.customers.add(**d,allow_similar=True); dlg.add_customer(cid,d['name'],d['phone']); self.events.master_changed.emit()
                except Exception as exc:error(dlg,str(exc))
        dlg.new_customer_requested.connect(create_inline_customer)
        if not dlg.exec():return
        data=dlg.data()
        try:
            try:res=self.sales.create_sale(cart,**data)
            except ValueError as exc:
                if 'superará el límite' in str(exc) and confirm(v,'Límite de crédito',str(exc)+'\n\n¿Deseas autorizar la excepción?'): res=self.sales.create_sale(cart,authorize_credit_over_limit=True,**data)
                else: raise
            text=f"Venta registrada correctamente.\n\nTotal: {q(res['total_cents'])}\nCobrado: {q(res['paid_cents'])}\nPendiente: {q(res['credit_cents'])}"
            if res['change_cents']:text+=f"\nCambio: {q(res['change_cents'])}"
            info(v,'Venta registrada',text); v.clear_cart(); self.events.sale_changed.emit()
        except Exception as exc: log.exception('checkout'); error(v,str(exc))
    def refresh_purchase_products(self,text=''): self.window.pages['Compras'].set_products(self.products.search(text,limit=80))
    def refresh_suppliers(self): self.window.pages['Compras'].set_suppliers(self.suppliers.list_all())
    def add_supplier_from_purchase(self):
        v=self.window.pages['Compras']; dlg=QuickSupplierDialog(v)
        if dlg.exec():
            d=dlg.data()
            try:sid=self.suppliers.add(**d,lead_days=int(self.settings.get('supplier_lead_days','4'))); v.add_supplier(sid,d['name']); self.events.master_changed.emit()
            except Exception as exc:error(v,str(exc))
    def _new_product_dialog(self,parent,compact=False,add_to_purchase=False):
        dlg=ProductDialog([dict(r) for r in self.products.categories()],parent=parent,compact=compact,catalog=self.products.search('',limit=500),profit_policy=self.settings.get('profit_policy','MARKUP'))
        if not dlg.exec():return None
        d=dlg.data(); sims=self.products.duplicate_candidates(d['name'])
        if sims:
            names='\n'.join('• '+r['name'] for r in sims[:4])
            if not confirm(parent,'Posible producto duplicado',f'Encontramos productos parecidos:\n\n{names}\n\n¿Estás seguro de que este es un producto diferente?'): return None
        try:
            cat=self.products.ensure_category(d['category']); pid=self.products.add(d['name'],cat,d['cost'],d['price'],0 if compact else d['quantity'],d['markup_pct'],d['min_stock'],d['expires'],d.get('expiry_date') if not compact else None,d['unit_name'],allow_similar=True,quantity_mode=d.get('quantity_mode')); self.events.master_changed.emit(); return pid
        except Exception as exc:error(parent,str(exc)); return None
    def add_product(self):
        pid=self._new_product_dialog(self.window.pages['Inventario'])
        if pid:info(self.window.pages['Inventario'],'Producto creado','Producto agregado correctamente. Las futuras fechas de vencimiento se registrarán por lote en cada compra.')
    def add_product_from_purchase(self):
        v=self.window.pages['Compras']; pid=self._new_product_dialog(v,compact=True)
        if pid:
            p=dict(self.products.get(pid)); v.add_product(p); self.refresh_purchase_products('')
    def edit_product(self,pid):
        v=self.window.pages['Inventario']; p=dict(self.products.get(pid)); dlg=ProductDialog([dict(r) for r in self.products.categories()],p,v,catalog=self.products.search('',limit=500),profit_policy=self.settings.get('profit_policy','MARKUP'))
        if dlg.exec():
            d=dlg.data()
            try:self.products.update(pid,name=d['name'],category_id=self.products.ensure_category(d['category']),price=d['price'],markup_pct=d['markup_pct'],min_stock=d['min_stock'],expires=d['expires'],unit_name=d['unit_name'],quantity_mode=d.get('quantity_mode'),profit_policy=self.settings.get('profit_policy','MARKUP')); self.events.master_changed.emit(); info(v,'Producto actualizado','Los datos del producto se guardaron correctamente.')
            except Exception as exc:error(v,str(exc))
    def purchase_selected(self,pid):
        self.window.navigate('Compras'); p=self.products.get(pid)
        if p:self.window.pages['Compras'].add_product(dict(p))
    def receive_pending_purchase(self):
        v=self.window.pages['Compras']; rows=self.purchases.pending_purchases()
        if not rows:
            return info(v,'Compras pendientes','No hay compras pendientes de recibir.')
        labels=[f"Compra #{r['id']} • {r['supplier']} • {q(r['total_cents'])} • {str(r['purchased_at'])[:10]}" for r in rows]
        chosen,ok=QInputDialog.getItem(v,'Recibir compra pendiente','Selecciona la compra cuya mercancía ya llegó:',labels,0,False)
        if not ok:return
        idx=labels.index(chosen); purchase_id=rows[idx]['id']
        if not confirm(v,'Confirmar recepción','Al confirmar, la mercancía entrará al inventario y se crearán sus lotes. ¿Continuar?'):return
        try:
            self.purchases.receive_purchase(purchase_id); info(v,'Compra recibida',f'La compra #{purchase_id} entró al inventario correctamente.'); self.events.purchase_changed.emit()
        except Exception as exc: log.exception('receive pending'); error(v,str(exc))

    def save_purchase(self):
        v=self.window.pages['Compras']; items=v.payload()
        if not items:return error(v,'Agrega al menos un producto a la compra.')
        missing=[]
        for item in items:
            p=self.products.get(item['product_id'])
            if p and p['expires'] and not item.get('expiry_date'):missing.append(p['name'])
        if missing and not confirm(v,'Fecha no registrada','Estos productos pueden vencer y no tienen fecha para este lote:\n\n'+'\n'.join('• '+x for x in missing)+'\n\nPuedes continuar y completar la fecha después desde Inventario > Ver lotes. ¿Continuar?'):return
        try:
            sid=v.supplier.currentData()
            if sid is None and v.supplier.currentText().strip() not in ('','Sin proveedor'): sid=self.suppliers.ensure(v.supplier.currentText().strip(),int(self.settings.get('supplier_lead_days','4')))
            pd,rd,status,discount,additional=v.purchase_meta(); purchase_id,changes=self.purchases.create_purchase(items,sid,purchase_date=pd,received_date=rd,status=status,discount=discount,additional_costs=additional)
            changed_names=[]
            for ch in changes:
                if ch.get('final_price_cents')!=ch.get('old_price_cents'):
                    p=self.products.get(ch['product_id']); changed_names.append(p['name'] if p else str(ch['product_id']))
            msg=f"Compra #{purchase_id} {'recibida correctamente' if status=='RECEIVED' else 'guardada como pendiente de recibir'}."
            if changed_names: msg+=f"\nPrecio de venta actualizado: {', '.join(changed_names)}."
            elif status=='PENDING': msg+='\nEl precio elegido quedará aplicado cuando recibas la mercancía.'
            info(v,'Compra registrada',msg); v.clear_form(); self.events.purchase_changed.emit()
        except Exception as exc:log.exception('purchase'); error(v,str(exc))
    def refresh_inventory(self,text=''):
        base=[dict(r) for r in self.products.inventory_rows(text)]
        metrics={m['id']:m for m in self.analytics.product_metrics(30)}
        rows=[]
        for r in base:
            m=metrics.get(r['id'],{})
            r.update({'stagnant':m.get('stagnant',False),'margin_pct':m.get('margin_pct',0),'rotation_ratio':m.get('rotation_ratio',0),'units_sold':m.get('units_sold',0)})
            rows.append(r)
        self.window.pages['Inventario'].set_rows(rows)
    def show_product_detail(self,pid):
        p=dict(self.products.get(pid)); lots=self.products.lots(pid); metrics=next((m for m in self.analytics.product_metrics(30) if m['id']==pid),None)
        if not p:return
        stock=sum(float(l['quantity_remaining']) for l in lots if l['status']=='ACTIVE'); value=int(round(stock*p['cpp_cents']))
        text=(f"{p['name']}\n\nCategoría: {p.get('category_name') or 'Sin categoría'}\nExistencias: {stock:g} {p.get('unit_name') or 'unidad'}\nCosto promedio: {q(p['cpp_cents'])}\nPrecio de venta: {q(p['price_cents'])}\nGanancia sobre costo: {float(p.get('markup_pct') or 0):.1f}%\nValor actual del inventario: {q(value)}\nStock mínimo: {float(p['min_stock']):g}\nÚltima venta: {metrics['days_since_sale']} días desde la última venta" if metrics else f"{p['name']}")
        QMessageBox.information(self.window,'Detalle del producto',text)
    def show_lots(self,pid):
        v=self.window.pages['Inventario']; p=dict(self.products.get(pid)); dlg=LotDialog(p,self.products.lots(pid),v)
        def update(lot_id,expiry):
            try:self.inventory.update_lot_expiry(lot_id,expiry); dlg.set_rows(self.products.lots(pid)); self.events.inventory_changed.emit(); info(dlg,'Fecha actualizada','La fecha quedó asociada únicamente a este lote.')
            except Exception as exc:error(dlg,str(exc))
        dlg.update_requested.connect(update); dlg.exec()
    def refresh_customers(self,text=''):
        rows=self.analytics.receivables(); t=(text or '').lower().strip(); self.window.pages['Clientes y Fiados'].set_rows([r for r in rows if not t or t in r['name'].lower() or t in (r['phone'] or '').lower()])
    def add_customer(self):
        v=self.window.pages['Clientes y Fiados']; dlg=QuickCustomerDialog(parent=v)
        if dlg.exec():
            try:self.customers.add(**dlg.data()); info(v,'Cliente creado','Cliente registrado correctamente.'); self.events.master_changed.emit(); self.refresh_customers('')
            except Exception as exc:error(v,str(exc))
    def add_payment(self,cid):
        v=self.window.pages['Clientes y Fiados']; c=self.customers.get(cid); bal=self.credit.customer_balance_cents(cid); dlg=PaymentDialog(c['name'],bal,v)
        if dlg.exec():
            try:new=self.credit.add_payment(cid,dlg.amount.value()); info(v,'Abono registrado',f"Abono guardado correctamente.\nNuevo saldo: {q(new)}"); self.events.credit_changed.emit()
            except Exception as exc:error(v,str(exc))
    def refresh_decisions(self): self.window.pages['Decisiones'].set_recommendations(self.recommendations.generate())
    def optimize_budget(self,value): self.window.pages['Decisiones'].set_budget_result(self.optimizer.optimize(value))
    def recommendation_action(self,pid,action):
        if 'COMPR' in action and 'NO COMPRAR' not in action:
            rec=next((r for r in self.recommendations.generate() if r.producto_id==pid and r.accion==action),None)
            self.window.navigate('Compras'); p=self.products.get(pid)
            if p:
                qty=(rec.cantidad_sugerida if rec and rec.cantidad_sugerida else 1)
                reason=(rec.detalle if rec else '')
                self.window.pages['Compras'].load_proposal(dict(p),qty,rec.proveedor_id if rec else None,reason)
        else:
            self.window.navigate('Inventario'); self.refresh_inventory(''); self.window.pages['Inventario'].select_product(pid)
            if 'VENC' in action or 'LOTE' in action: self.show_lots(pid)
    def refresh_history(self,start='',end=''): self.window.pages['Historial'].set_rows(self.history.activity(start or None,end or None))
    def show_history_detail(self,kind,ref):
        head,lines=self.history.details(kind,ref)
        if not head:return
        if kind=='SALE':
            body='\n'.join(f"• {r['name']}: {r['quantity']:.2f} × {q(r['unit_price_cents'])} = {q(r['subtotal_cents'])}" for r in lines); text=f"Venta #{ref}\nFecha: {head['sold_at']}\nCliente: {head['customer'] or 'Venta sin cliente'}\nTotal: {q(head['total_cents'])}\nCobrado: {q(head['paid_cents'])}\nFiado: {q(head['credit_cents'])}\n\n{body}"
        else:
            body='\n'.join(f"• {r['name']}: {r['quantity']:.2f} × {q(r['unit_cost_cents'])} = {q(r['subtotal_cents'])} • Vence: {r['expiry_date'] or 'Sin fecha'}" for r in lines); text=f"Compra #{ref}\nFecha: {head['purchased_at']}\nProveedor: {head['supplier'] or 'Sin proveedor'}\nTotal: {q(head['total_cents'])}\n\n{body}"
        QMessageBox.information(self.window,'Detalle de operación',text)
    def generate_report(self,kind,period,start,end):
        summary,headers,rows=self.reports.generate(kind,period,start or None,end or None); self.window.pages['Reportes'].show_rows(summary,headers,rows)
    def generate_abc(self):
        rows=self.analytics.abc_analysis(90); headers=['Clase','Producto','Ventas 90 días','Participación acumulada']; data=[[r['abc'],r['name'],q(r['revenue_cents']),f"{r['cumulative_pct']:.1f}%"] for r in rows]; self.window.pages['Reportes'].show_rows('Análisis ABC: A concentra aproximadamente el 80% del valor vendido; B el siguiente tramo; C el restante.',headers,data)
    def refresh_settings(self): self.window.pages['Configuración'].set_values(self.settings.all())
    def save_settings(self,data):
        old_policy=self.settings.get('profit_policy','MARKUP')
        for k,v in data.items():self.settings.set(k,v)
        new_policy=str(data.get('profit_policy',old_policy)).upper()
        if new_policy!=str(old_policy).upper(): self.products.recalculate_percentages(new_policy)
        self.window.pages['Compras'].set_profit_policy(new_policy)
        info(self.window.pages['Configuración'],'Configuración guardada','Los cambios se guardaron correctamente.'); self.events.master_changed.emit()
    def create_backup(self):
        try:path=self.backups.create(); info(self.window,'Respaldo creado',f'Respaldo guardado en:\n{path}')
        except Exception as exc:error(self.window,str(exc))
    def restore_backup(self):
        path,_=QFileDialog.getOpenFileName(self.window,'Seleccionar respaldo','','Base de datos (*.db);;Todos los archivos (*)')
        if not path:return
        if not confirm(self.window,'Restaurar respaldo','La base actual será reemplazada por el respaldo seleccionado. ¿Continuar?'):return
        try:self.backups.restore(path); self.refresh_all(); info(self.window,'Respaldo restaurado','La información fue restaurada correctamente.')
        except Exception as exc:error(self.window,str(exc))
    def reset_all_data(self):
        v=self.window.pages['Configuración']
        first=QMessageBox.warning(
            v,
            'Borrar todos los datos',
            'Esta acción eliminará TODOS los datos del negocio y no se puede deshacer.\n\nProductos, ventas, compras, inventario, clientes, fiados, abonos, lotes, historial y configuración volverán a cero.\n\n¿Deseas continuar?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if first!=QMessageBox.StandardButton.Yes:
            return
        phrase,ok=QInputDialog.getText(v,'Confirmación final','Para confirmar, escribe exactamente: REINICIAR')
        if not ok or phrase.strip().upper()!='REINICIAR':
            if ok: error(v,'No se borró nada. La palabra de confirmación no coincide.')
            return
        try:
            self.resetter.reset_all()
            self.dashboard_period=('Hoy','','')
            self.refresh_all()
            info(v,'Sistema reiniciado','Todos los datos fueron eliminados. El sistema quedó listo para comenzar desde cero.')
        except Exception as exc:
            log.exception('reset database')
            error(v,'No fue posible reiniciar el sistema. No continúes operando hasta revisar el error.\n\n'+str(exc))

