from datetime import timedelta,date
from decimal import Decimal
from database.connection import connect
from repositories.settings_repository import SettingsRepository
from utils.money import D
from utils.dates import local_today,period_bounds,iso_date
from services.pricing_service import PricingService

class AnalyticsService:
    def __init__(self,db_path=None): self.db_path=db_path; self.settings=SettingsRepository(db_path)

    def dashboard(self,period='Hoy',start=None,end=None):
        start_d,end_d=period_bounds(period,start,end); a=start_d.isoformat(); b=end_d.isoformat(); con=connect(self.db_path)
        try:
            sale=con.execute('''SELECT COALESCE(SUM(total_cents),0) sales,COALESCE(SUM(paid_cents),0) sale_paid,
                                      COALESCE(SUM(credit_cents),0) credit,COALESCE(SUM(gross_profit_cents),0) profit,
                                      COALESCE(SUM(cost_cents),0) cogs,COUNT(*) tickets
                               FROM sales WHERE status='COMPLETED' AND date(sold_at) BETWEEN ? AND ?''',(a,b)).fetchone()
            payments=con.execute("SELECT COALESCE(SUM(amount_cents),0) v FROM payments WHERE status='VALID' AND date(paid_at) BETWEEN ? AND ?",(a,b)).fetchone()['v']
            purchases=con.execute("SELECT COALESCE(SUM(total_cents),0) v FROM purchases WHERE status<>'CANCELLED' AND date(purchased_at) BETWEEN ? AND ?",(a,b)).fetchone()['v']
            inv=con.execute("SELECT COALESCE(SUM(l.quantity_remaining*p.cpp_cents),0) v FROM lots l JOIN products p ON p.id=l.product_id WHERE p.active=1 AND l.status='ACTIVE'").fetchone()['v']
            recv=con.execute("SELECT COALESCE(SUM(balance_cents),0) v FROM receivables WHERE status='PENDING'").fetchone()['v']
            low=0
            for r in con.execute('''SELECT p.id,p.min_stock,COALESCE(SUM(CASE WHEN l.status='ACTIVE' AND l.quantity_remaining>0 AND (l.expiry_date IS NULL OR l.expiry_date>=?) THEN l.quantity_remaining ELSE 0 END),0) available
                                    FROM products p LEFT JOIN lots l ON l.product_id=p.id WHERE p.active=1 GROUP BY p.id''',(iso_date(),)).fetchall():
                if r['available']<=r['min_stock']: low+=1
            warn=int(self.settings.get('expiry_warning_days','15')); expiry=(local_today()+timedelta(days=warn)).isoformat()
            exp=con.execute('''SELECT COUNT(DISTINCT product_id) c FROM lots WHERE status='ACTIVE' AND quantity_remaining>0 AND expiry_date IS NOT NULL AND expiry_date BETWEEN ? AND ?''',(iso_date(),expiry)).fetchone()['c']
            stalled_metrics=self.product_metrics(30,only_stagnant=True); stalled=len(stalled_metrics)
            best=con.execute('''SELECT p.id,p.name,SUM(sd.quantity) units,SUM(sd.subtotal_cents) revenue FROM sale_details sd JOIN sales s ON s.id=sd.sale_id JOIN products p ON p.id=sd.product_id
                                WHERE s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? GROUP BY p.id ORDER BY units DESC,revenue DESC LIMIT 1''',(a,b)).fetchone()
            min_days=int(self.settings.get('min_history_less_sold_days','14'))
            worst=con.execute('''SELECT p.id,p.name,COALESCE(SUM(CASE WHEN s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? THEN sd.quantity ELSE 0 END),0) units
                                 FROM products p LEFT JOIN sale_details sd ON sd.product_id=p.id LEFT JOIN sales s ON s.id=sd.sale_id
                                 WHERE p.active=1 AND date(p.created_at)<=? GROUP BY p.id ORDER BY units ASC,p.name LIMIT 1''',(a,b,(local_today()-timedelta(days=min_days)).isoformat())).fetchone()
            best_profit=con.execute('''SELECT p.id,p.name,COALESCE(SUM(sd.subtotal_cents-sd.cost_total_cents),0) profit,COALESCE(SUM(sd.quantity),0) units
                                       FROM sale_details sd JOIN sales s ON s.id=sd.sale_id JOIN products p ON p.id=sd.product_id
                                       WHERE s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? GROUP BY p.id ORDER BY profit DESC LIMIT 1''',(a,b)).fetchone()
            top_products=con.execute('''SELECT p.id,p.name,COALESCE(SUM(sd.quantity),0) units,COALESCE(SUM(sd.subtotal_cents),0) revenue
                                        FROM sale_details sd JOIN sales s ON s.id=sd.sale_id JOIN products p ON p.id=sd.product_id
                                        WHERE s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? GROUP BY p.id ORDER BY units DESC,revenue DESC LIMIT 5''',(a,b)).fetchall()
            today=iso_date()
            today_sale=con.execute('''SELECT COALESCE(SUM(total_cents),0) sales,COALESCE(SUM(gross_profit_cents),0) profit,COALESCE(SUM(paid_cents),0) paid,COUNT(*) tickets
                                      FROM sales WHERE status='COMPLETED' AND date(sold_at)=?''',(today,)).fetchone()
            today_pay=con.execute("SELECT COALESCE(SUM(amount_cents),0) v FROM payments WHERE status='VALID' AND date(paid_at)=?",(today,)).fetchone()['v']
            today_buy=con.execute("SELECT COALESCE(SUM(total_cents),0) v FROM purchases WHERE status<>'CANCELLED' AND date(purchased_at)=?",(today,)).fetchone()['v']
            recent=[]
            for r in con.execute('''SELECT * FROM (
                SELECT sold_at ts,'Venta' kind,total_cents amount,'Venta #'||id descr FROM sales WHERE status='COMPLETED'
                UNION ALL SELECT purchased_at ts,'Compra' kind,total_cents amount,'Compra #'||id descr FROM purchases WHERE status<>'CANCELLED'
                UNION ALL SELECT paid_at ts,'Abono' kind,amount_cents amount,'Abono registrado' descr FROM payments WHERE status='VALID'
                ) ORDER BY ts DESC LIMIT 5''').fetchall(): recent.append(dict(r))
            expiring=con.execute('''SELECT p.id,p.name,SUM(l.quantity_remaining) qty,MIN(l.expiry_date) expiry
                                    FROM lots l JOIN products p ON p.id=l.product_id WHERE p.active=1 AND l.status='ACTIVE' AND l.quantity_remaining>0
                                    AND l.expiry_date IS NOT NULL AND l.expiry_date BETWEEN ? AND ? GROUP BY p.id ORDER BY expiry LIMIT 4''',(today,expiry)).fetchall()
            oldest=con.execute('''SELECT c.name,r.balance_cents,r.created_at FROM receivables r JOIN customers c ON c.id=r.customer_id
                                  WHERE r.status='PENDING' AND r.balance_cents>0 ORDER BY r.created_at LIMIT 1''').fetchone()
            stagnant_capital=sum(x['inventory_value_cents'] for x in stalled_metrics)
            return {'sales_cents':sale['sales'],'profit_cents':sale['profit'],'cogs_cents':sale['cogs'],'sale_paid_cents':sale['sale_paid'],'payments_cents':payments,'paid_cents':sale['sale_paid']+payments,
                    'credit_cents':sale['credit'],'purchases_cents':purchases,'inventory_cents':int(inv),'receivable_cents':recv,'low_stock_count':low,'expiring_count':exp,'stagnant_count':stalled,
                    'tickets':sale['tickets'],'avg_ticket_cents':int(sale['sales']/sale['tickets']) if sale['tickets'] else 0,
                    'best_product':dict(best) if best else None,'least_product':dict(worst) if worst else None,'best_profit_product':dict(best_profit) if best_profit else None,
                    'top_products':[dict(x) for x in top_products],'recent_activity':recent,'expiring_items':[dict(x) for x in expiring],'oldest_receivable':dict(oldest) if oldest else None,
                    'stagnant_capital_cents':int(stagnant_capital),'today_summary':{'sales_cents':today_sale['sales'],'profit_cents':today_sale['profit'],'paid_cents':today_sale['paid']+today_pay,'purchases_cents':today_buy,'payments_cents':today_pay,'tickets':today_sale['tickets']},
                    'start':a,'end':b}
        finally: con.close()

    def sales_series(self,start,end):
        if isinstance(start,str): start=date.fromisoformat(start)
        if isinstance(end,str): end=date.fromisoformat(end)
        con=connect(self.db_path)
        try:
            raw={r['d']:r['total'] for r in con.execute('''SELECT date(sold_at) d,COALESCE(SUM(total_cents),0) total FROM sales WHERE status='COMPLETED' AND date(sold_at) BETWEEN ? AND ? GROUP BY date(sold_at)''',(start.isoformat(),end.isoformat())).fetchall()}
            out=[]; d=start
            while d<=end: out.append((d.isoformat(),raw.get(d.isoformat(),0))); d+=timedelta(days=1)
            return out
        finally: con.close()

    def product_metrics(self,days=30,only_stagnant=False):
        con=connect(self.db_path); today=local_today()
        try:
            start=(today-timedelta(days=days-1)).isoformat(); products=con.execute('''SELECT p.*,c.name category_name,s.default_lead_days FROM products p LEFT JOIN categories c ON c.id=p.category_id LEFT JOIN suppliers s ON s.id=p.usual_supplier_id WHERE p.active=1 ORDER BY p.name''').fetchall()
            results=[]; stagnant_days=int(self.settings.get('stagnant_days','60'))
            for p in products:
                sold=con.execute('''SELECT COALESCE(SUM(sd.quantity),0) qty,COALESCE(SUM(sd.cost_total_cents),0) cogs,COALESCE(SUM(sd.subtotal_cents),0) revenue
                                    FROM sale_details sd JOIN sales s ON s.id=sd.sale_id WHERE sd.product_id=? AND s.status='COMPLETED' AND date(s.sold_at)>=?''',(p['id'],start)).fetchone()
                stockout=con.execute('SELECT COUNT(*) c FROM stockout_days WHERE product_id=? AND day>=?',(p['id'],start)).fetchone()['c']; effective=max(1,days-stockout)
                demand=D(sold['qty'])/D(effective)
                physical=con.execute("SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND status='ACTIVE'",(p['id'],)).fetchone()['q']
                available=con.execute('''SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND quantity_remaining>0 AND status='ACTIVE' AND (expiry_date IS NULL OR expiry_date>=?)''',(p['id'],iso_date())).fetchone()['q']
                pending=con.execute('''SELECT COALESCE(SUM(pd.quantity),0) q FROM purchase_details pd JOIN purchases pu ON pu.id=pd.purchase_id WHERE pd.product_id=? AND pu.status='PENDING' ''',(p['id'],)).fetchone()['q']
                coverage=(D(available)/demand) if demand>0 else None
                last_any=con.execute("SELECT MAX(date(s.sold_at)) d FROM sale_details sd JOIN sales s ON s.id=sd.sale_id WHERE sd.product_id=? AND s.status='COMPLETED'",(p['id'],)).fetchone()['d']
                created=date.fromisoformat(p['created_at'][:10]); days_since=(today-date.fromisoformat(last_any)).days if last_any else (today-created).days
                age=(today-created).days; stagnant=days_since>=stagnant_days and D(available)>0 and age>=min(stagnant_days,14)
                inv_value=int(D(physical)*Decimal(p['cpp_cents'])); purchased=con.execute('''SELECT COALESCE(SUM(pd.subtotal_cents),0) v FROM purchase_details pd JOIN purchases pu ON pu.id=pd.purchase_id WHERE pd.product_id=? AND pu.status='RECEIVED' AND date(pu.purchased_at)>=?''',(p['id'],start)).fetchone()['v']
                opening_est=max(0,inv_value+int(sold['cogs'])-int(purchased)); avg_inventory=max(1,(opening_est+inv_value)/2); rotation=float(int(sold['cogs'])/avg_inventory) if avg_inventory else 0
                lead=p['default_lead_days'] or int(self.settings.get('supplier_lead_days','4')); safety=D(p['safety_stock']); reorder=float(demand*D(lead)+safety); margin=float(PricingService.percent_from_price(p['cpp_cents'],p['price_cents'],self.settings.get('profit_policy','MARKUP'))) if p['cpp_cents'] else 0
                next_exp=con.execute("SELECT MIN(expiry_date) d FROM lots WHERE product_id=? AND status='ACTIVE' AND quantity_remaining>0 AND expiry_date>=?",(p['id'],iso_date())).fetchone()['d']; unknown=con.execute("SELECT COALESCE(SUM(quantity_remaining),0) q FROM lots WHERE product_id=? AND status='ACTIVE' AND quantity_remaining>0 AND expiry_date IS NULL",(p['id'],)).fetchone()['q']
                results.append({'id':p['id'],'name':p['name'],'category':p['category_name'] or 'Sin categoría','stock':float(physical),'recorded_stock':p['stock_qty'],'available_stock':float(available),'pending_qty':float(pending),'cpp_cents':p['cpp_cents'],'price_cents':p['price_cents'],'min_stock':p['min_stock'],'safety_stock':p['safety_stock'],'quantity_mode':p['quantity_mode'] if 'quantity_mode' in p.keys() else 'INTEGER','unit_name':p['unit_name'],'daily_demand':float(demand),'coverage_days':float(coverage) if coverage is not None else None,'days_since_sale':days_since,'age_days':age,'stagnant':stagnant,'inventory_value_cents':inv_value,'reorder_point':reorder,'lead_days':lead,'margin_pct':margin,'units_sold':float(D(sold['qty'])),'revenue_cents':sold['revenue'],'cogs_cents':sold['cogs'],'next_expiry':next_exp,'unknown_expiry_qty':float(unknown),'expires':bool(p['expires']),'rotation_ratio':rotation})
            return [r for r in results if r['stagnant']] if only_stagnant else results
        finally: con.close()

    def receivables(self):
        con=connect(self.db_path)
        try:return con.execute('''SELECT c.id,c.name,c.phone,COALESCE(SUM(r.balance_cents),0) balance_cents,MIN(r.created_at) oldest,MAX(s.sold_at) last_credit,
          (SELECT MAX(p.paid_at) FROM payments p WHERE p.customer_id=c.id AND p.status='VALID') last_payment,COALESCE(SUM(r.original_cents),0) credit_total
          FROM customers c LEFT JOIN receivables r ON r.customer_id=c.id AND r.status='PENDING' LEFT JOIN sales s ON s.id=r.sale_id WHERE c.active=1 GROUP BY c.id HAVING balance_cents>0 ORDER BY balance_cents DESC''').fetchall()
        finally: con.close()

    def product_profitability(self,start,end):
        con=connect(self.db_path)
        try:
            return con.execute('''SELECT p.id,p.name,
              COALESCE((SELECT SUM(pd.quantity) FROM purchase_details pd JOIN purchases pu ON pu.id=pd.purchase_id WHERE pd.product_id=p.id AND pu.status='RECEIVED' AND date(pu.purchased_at) BETWEEN ? AND ?),0) bought_qty,
              COALESCE((SELECT SUM(pd.subtotal_cents) FROM purchase_details pd JOIN purchases pu ON pu.id=pd.purchase_id WHERE pd.product_id=p.id AND pu.status='RECEIVED' AND date(pu.purchased_at) BETWEEN ? AND ?),0) invested_cents,
              COALESCE(SUM(CASE WHEN s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? THEN sd.quantity ELSE 0 END),0) sold_qty,
              COALESCE(SUM(CASE WHEN s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? THEN sd.subtotal_cents ELSE 0 END),0) revenue_cents,
              COALESCE(SUM(CASE WHEN s.status='COMPLETED' AND date(s.sold_at) BETWEEN ? AND ? THEN sd.cost_total_cents ELSE 0 END),0) cogs_cents,
              p.cpp_cents, COALESCE((SELECT SUM(l.quantity_remaining) FROM lots l WHERE l.product_id=p.id AND l.status='ACTIVE'),0) stock
              FROM products p LEFT JOIN sale_details sd ON sd.product_id=p.id LEFT JOIN sales s ON s.id=sd.sale_id
              WHERE p.active=1 GROUP BY p.id ORDER BY revenue_cents DESC''',(start,end,start,end,start,end,start,end,start,end)).fetchall()
        finally: con.close()

    def abc_analysis(self,days=90):
        metrics=self.product_metrics(days); metrics.sort(key=lambda r:r['revenue_cents'],reverse=True); total=sum(r['revenue_cents'] for r in metrics) or 1; cum=0; out=[]; a=float(self.settings.get('abc_a_pct','80')); b=float(self.settings.get('abc_b_pct','95'))
        for r in metrics:
            prev=cum/total*100; cum+=r['revenue_cents']; out.append({**r,'abc':'A' if prev<a else ('B' if prev<b else 'C'),'cumulative_pct':cum/total*100})
        return out
