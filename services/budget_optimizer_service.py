from decimal import Decimal
from services.analytics_service import AnalyticsService
from services.recommendation_service import RecommendationService
from utils.money import D

class BudgetOptimizerService:
    def __init__(self, db_path=None):
        self.analytics=AnalyticsService(db_path); self.recommender=RecommendationService(db_path)

    def optimize(self, budget):
        budget_cents=int((D(budget)*100).to_integral_value()); candidates=[]
        for m in self.analytics.product_metrics(30):
            if m['cpp_cents']<=0 or m['daily_demand']<=0 or m['stagnant']: continue
            # No comprar automáticamente si existe riesgo inmediato de vencimiento.
            if m.get('next_expiry') and (m.get('coverage_days') or 0) > 0 and m['coverage_days'] > 30: continue
            need=self.recommender.suggested_purchase(m)
            if D(need)<=0: continue
            scarcity=1/(max(m['coverage_days'] or 0.1,0.1)); margin=max(m['margin_pct'],0)/100
            score=(m['daily_demand']*2)+(scarcity*5)+(margin*2)
            candidates.append((score,m,D(need)))
        candidates.sort(key=lambda x:x[0],reverse=True); remaining=budget_cents; proposal=[]
        for score,m,need in candidates:
            if m['quantity_mode']=='INTEGER':
                affordable=remaining//m['cpp_cents']; qty=min(int(need),affordable)
            else:
                # Para fraccionarios se trabaja en pasos de 0.25 de la unidad configurada.
                step=Decimal('0.25'); affordable=(Decimal(remaining)/Decimal(m['cpp_cents'])/step).to_integral_value(rounding='ROUND_FLOOR')*step; qty=min(need,affordable)
            if D(qty)<=0: continue
            investment=int((D(qty)*Decimal(m['cpp_cents'])).to_integral_value()); remaining-=investment
            proposal.append({'product_id':m['id'],'product':m['name'],'quantity':float(qty) if m['quantity_mode']=='FRACTIONAL' else int(qty),'investment_cents':investment,
                             'reason':f"Demanda {m['daily_demand']:.2f}/día, existencias disponibles {m['available_stock']:.2f}, plazo {m['lead_days']} días" + (f", cobertura {m['coverage_days']:.1f} días" if m['coverage_days'] is not None else ''),
                             'score':score})
        return {'budget_cents':budget_cents,'recommended_cents':budget_cents-remaining,'remaining_cents':remaining,'items':proposal}
