from database.seeds.demo import seed_demo
from services.budget_optimizer_service import BudgetOptimizerService

def test_budget_never_exceeded(db):
    seed_demo(db); r=BudgetOptimizerService(db).optimize(500)
    assert r['recommended_cents'] <= 50000
    assert r['remaining_cents'] >= 0
