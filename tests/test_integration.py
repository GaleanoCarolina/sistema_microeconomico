from database.seeds.demo import seed_demo
from services.analytics_service import AnalyticsService
from services.recommendation_service import RecommendationService

def test_integral_demo(db):
    assert seed_demo(db) is True
    a=AnalyticsService(db); d=a.dashboard(); assert d['inventory_cents']>0 and d['receivable_cents']>0
    recs=RecommendationService(db).generate(); assert len(recs)>0
