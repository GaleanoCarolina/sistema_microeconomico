from repositories.report_repository import ReportRepository
from services.analytics_service import AnalyticsService
from services.recommendation_service import RecommendationService
from utils.money import q
from utils.dates import period_bounds
from utils.quantities import format_qty

METHOD={'CASH':'Efectivo','CREDIT':'Fiado','PARTIAL':'Pago parcial + fiado','OTHER':'Otro'}; STATUS={'COMPLETED':'Completada','VOID':'Anulada','RECEIVED':'Recibida','PENDING':'Pendiente de recibir','CANCELLED':'Cancelada'}
class ReportService:
    def __init__(self,db_path=None): self.repo=ReportRepository(db_path); self.analytics=AnalyticsService(db_path); self.recs=RecommendationService(db_path)
    def generate(self,kind,period='Últimos 30 días',start=None,end=None):
        a,b=period_bounds(period,start,end); ai,bi=a.isoformat(),b.isoformat()
        if kind=='Ventas':
            rs=self.repo.sales(ai,bi); d=self.analytics.dashboard(period,start,end); summary=f"Ventas: {q(d['sales_cents'])}  •  Costo de lo vendido: {q(d['cogs_cents'])}  •  Ganancia bruta: {q(d['profit_cents'])}  •  Cobrado: {q(d['paid_cents'])}  •  Fiado generado: {q(d['credit_cents'])}"
            return summary,['Fecha','Venta','Total','Costo vendido','Cobrado inicial','Fiado','Ganancia bruta','Método','Estado','Cliente'],[[(r['sold_at'] or '')[:16],f"#{r['id']}",q(r['total_cents']),q(r['cost_cents']),q(r['paid_cents']),q(r['credit_cents']),q(r['gross_profit_cents']),METHOD.get(r['payment_method'],r['payment_method']),STATUS.get(r['status'],r['status']),r['customer'] or '—'] for r in rs]
        if kind=='Compras':
            rs=self.repo.purchases(ai,bi); total=sum(r['total_cents'] for r in rs if r['status']!='CANCELLED'); return f'Valor de compras del período: {q(total)}. Esto no es lo mismo que el valor actual del inventario.',['Fecha','Compra','Proveedor','Subtotal','Descuento','Costos adicionales','Total','Estado'],[[(r['purchased_at'] or '')[:16],f"#{r['id']}",r['supplier'] or 'Sin proveedor',q(r['subtotal_cents']),q(r['discount_cents']),q(r['additional_costs_cents']),q(r['total_cents']),STATUS.get(r['status'],r['status'])] for r in rs]
        if kind=='Inversión y resultados':
            d=self.analytics.dashboard(period,start,end); summary=f"Compras: {q(d['purchases_cents'])}  •  Ventas: {q(d['sales_cents'])}  •  Costo vendido: {q(d['cogs_cents'])}  •  Ganancia bruta: {q(d['profit_cents'])}  •  Cobrado: {q(d['paid_cents'])}  •  Pendiente: {q(d['receivable_cents'])}  •  Inventario actual: {q(d['inventory_cents'])}"
            rows=[]
            for r in self.analytics.product_profitability(ai,bi):
                profit=r['revenue_cents']-r['cogs_cents']; inv=int(round(float(r['stock'])*r['cpp_cents']))
                rows.append([r['name'],f"{r['bought_qty']:g}",q(r['invested_cents']),f"{r['sold_qty']:g}",q(r['revenue_cents']),q(r['cogs_cents']),q(profit),q(inv)])
            return summary,['Producto','Comprado','Invertido','Vendido','Ingresos','Costo vendido','Ganancia bruta','Inventario actual'],rows
        if kind=='Inventario':
            ms=self.analytics.product_metrics(30); total=sum(m['inventory_value_cents'] for m in ms); return f'Valor aproximado actual del inventario: {q(total)}',['Producto','Existencias','Costo promedio','Precio','Valor','Cobertura','Cómo se vende'],[[m['name'],format_qty(m['stock'],m['quantity_mode']),q(m['cpp_cents']),q(m['price_cents']),q(m['inventory_value_cents']),f"{m['coverage_days']:.1f} días" if m['coverage_days'] is not None else 'Sin demanda reciente','Rápido' if m['rotation_ratio']>=2 else ('Medio' if m['rotation_ratio']>=.5 else 'Lento')] for m in ms]
        if kind=='Fiados':
            rs=self.analytics.receivables(); total=sum(r['balance_cents'] for r in rs); return f'Pendiente por cobrar: {q(total)}',['Cliente','Saldo','Deuda más antigua','Última compra fiada','Último abono'],[[r['name'],q(r['balance_cents']),(r['oldest'] or '')[:10],(r['last_credit'] or '')[:10],(r['last_payment'] or '')[:10]] for r in rs]
        if kind=='Caducidades':
            rs=self.repo.expiries(); return 'Lotes con existencias actuales. Las fechas pertenecen a cada lote.',['Producto','Lote','Recibido','Vencimiento','Cantidad'],[[r['name'],f"Lote {r['lot_id']}",(r['received_at'] or '')[:10],r['expiry_date'] or 'Sin fecha registrada',format_qty(r['quantity_remaining'],r['quantity_mode'])] for r in rs]
        rs=self.recs.generate(); return f'{len(rs)} recomendaciones actuales',['Prioridad','Producto','Qué hacer','Explicación'],[[r.prioridad,r.producto,r.accion,f'{r.motivo} {r.detalle}'] for r in rs]
