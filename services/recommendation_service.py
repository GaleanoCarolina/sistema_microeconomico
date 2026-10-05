from datetime import date
from decimal import Decimal
from database.connection import connect
from repositories.settings_repository import SettingsRepository
from services.analytics_service import AnalyticsService
from models.recomendacion import Recomendacion
from utils.dates import local_today
from utils.quantities import rounded_reorder_qty

class RecommendationService:
    """Motor determinista. La misma información siempre produce la misma recomendación."""
    BUFFER_DAYS=3
    def __init__(self,db_path=None): self.db_path=db_path; self.analytics=AnalyticsService(db_path); self.settings=SettingsRepository(db_path)
    def suggested_purchase(self,m):
        demand=Decimal(str(max(0,m.get('daily_demand',0))))
        lead=Decimal(str(max(0,m.get('lead_days',0))))
        safety=Decimal(str(max(0,m.get('safety_stock',0))))
        available=Decimal(str(max(0,m.get('available_stock',0))))
        pending=Decimal(str(max(0,m.get('pending_qty',0))))
        target=demand*(lead+Decimal(self.BUFFER_DAYS))+safety
        need=max(Decimal('0'),target-available-pending)
        return rounded_reorder_qty(need,m.get('quantity_mode','INTEGER'))
    def calculation_text(self,m,suggested):
        target=Decimal(str(m['daily_demand']))*Decimal(str(m['lead_days']+self.BUFFER_DAYS))+Decimal(str(m['safety_stock']))
        return (f"Demanda diaria: {m['daily_demand']:.2f} {m['unit_name']}/día\n"
                f"Existencias disponibles: {m['available_stock']:.2f} {m['unit_name']}\n"
                f"Pedidos pendientes: {m.get('pending_qty',0):.2f} {m['unit_name']}\n"
                f"Plazo del proveedor: {m['lead_days']} días\n"
                f"Colchón operativo: {self.BUFFER_DAYS} días\n"
                f"Stock de seguridad: {m['safety_stock']:.2f}\n"
                f"Stock objetivo calculado: {target:.2f}\n"
                f"Cantidad sugerida: {suggested}")
    def generate(self):
        metrics=self.analytics.product_metrics(30); con=connect(self.db_path); recs=[]; today=local_today()
        try:
            urgent=int(self.settings.get('expiry_urgent_days','5')); warn=int(self.settings.get('expiry_warning_days','15'))
            for m in metrics:
                p=con.execute('SELECT usual_supplier_id FROM products WHERE id=?',(m['id'],)).fetchone(); supplier_id=p['usual_supplier_id'] if p else None
                conf='Alta' if m['units_sold']>=20 else ('Media' if m['units_sold']>=5 else 'Baja')
                exp=con.execute("SELECT MIN(expiry_date) d,SUM(CASE WHEN expiry_date IS NOT NULL THEN quantity_remaining ELSE 0 END) q FROM lots WHERE product_id=? AND status='ACTIVE' AND quantity_remaining>0",(m['id'],)).fetchone()
                exp_risk=False
                if exp['d']:
                    days=(date.fromisoformat(exp['d'])-today).days
                    if days<0:
                        exp_risk=True; recs.append(Recomendacion(m['id'],m['name'],'RETIRAR PRODUCTO VENCIDO','URGENTE','Hay mercancía vencida.',f'El lote más antiguo venció el {exp["d"]}. No puede venderse.',conf))
                    elif days<=urgent:
                        exp_risk=True; recs.append(Recomendacion(m['id'],m['name'],'PRIORIZAR VENTA POR VENCIMIENTO','URGENTE',f'El lote más próximo vence en {days} días.',f'Quedan aproximadamente {exp["q"] or 0:.2f} {m["unit_name"]} con fecha registrada. Antes de comprar más, da salida a ese lote.',conf))
                    elif days<=warn:
                        exp_risk=True; recs.append(Recomendacion(m['id'],m['name'],'APLICAR PROMOCIÓN','ALTA',f'Hay mercancía que vence en {days} días.','Conviene darle salida antes de volver a comprar.',conf))
                if m.get('expires') and m['unknown_expiry_qty']>0:
                    recs.append(Recomendacion(m['id'],m['name'],'COMPLETAR FECHA DE LOTE','MEDIA',f'Hay {m["unknown_expiry_qty"]:.2f} {m["unit_name"]} sin fecha de vencimiento registrada.','Puedes completar la fecha desde Inventario > Ver lotes.',conf))
                if m['age_days']<7 and m['units_sold']<3:
                    recs.append(Recomendacion(m['id'],m['name'],'OBSERVAR PRODUCTO','INFORMATIVA','Es un producto nuevo o con poco historial.','Aún no hay información suficiente para recomendar cuánto comprar.','Baja')); continue
                suggested=self.suggested_purchase(m)
                reorder_trigger=max(float(m['reorder_point']),float(m['min_stock']))
                should_buy=(not exp_risk and not m['stagnant'] and m['daily_demand']>0 and m['available_stock']<=reorder_trigger and float(suggested)>0)
                if should_buy:
                    pri='URGENTE' if (m['available_stock']<=0 or (m['coverage_days'] is not None and m['coverage_days']<1)) else 'ALTA'
                    qty_text=f'{suggested:g}' if hasattr(suggested,'__format__') else str(suggested)
                    investment=int(Decimal(str(suggested))*Decimal(m['cpp_cents']))
                    recs.append(Recomendacion(m['id'],m['name'],'COMPRAR PRONTO',pri,f'Te quedan {m["available_stock"]:.2f} {m["unit_name"]} y se venden aproximadamente {m["daily_demand"]:.2f} por día.',f'Plazo del proveedor: {m["lead_days"]} días. Stock de seguridad: {m["safety_stock"]:.2f}. Cantidad sugerida: {qty_text}.',conf,float(suggested),supplier_id,investment,self.calculation_text(m,suggested)))
                if m['stagnant']:
                    recs.append(Recomendacion(m['id'],m['name'],'NO COMPRAR POR AHORA','ALTA',f'Lleva {m["days_since_sale"]} días sin venta y todavía hay existencias.',f'Hay aproximadamente Q{m["inventory_value_cents"]/100:,.2f} invertidos. Considera una promoción antes de comprar más.',conf))
                elif m['coverage_days'] is not None and m['coverage_days']>90:
                    recs.append(Recomendacion(m['id'],m['name'],'COMPRAR MENOS','MEDIA',f'El inventario podría durar {m["coverage_days"]:.0f} días al ritmo reciente.','Tienes más mercancía de la necesaria para la demanda observada.',conf))
                if m['margin_pct']<8 and m['units_sold']>0:
                    recs.append(Recomendacion(m['id'],m['name'],'REVISAR PRECIO','MEDIA',f'La ganancia configurada es aproximadamente {m["margin_pct"]:.1f}%.','Revisa el precio antes de la próxima compra.',conf))
            receivable=sum(r['balance_cents'] for r in self.analytics.receivables())
            if receivable>0: recs.append(Recomendacion(0,'Cartera de fiados','CUIDAR LIQUIDEZ','MEDIA',f'Tienes Q{receivable/100:,.2f} pendientes por cobrar.','Ese dinero pertenece a ventas realizadas, pero todavía no está disponible para comprar mercancía.','Alta'))
            order={'URGENTE':0,'ALTA':1,'MEDIA':2,'BAJA':3,'INFORMATIVA':4}; return sorted(recs,key=lambda r:(order.get(r.prioridad,9),r.producto))
        finally: con.close()
