from decimal import Decimal
from utils.money import D


def reorder_point(daily_demand, lead_days, safety_stock):
    return D(daily_demand) * D(lead_days) + D(safety_stock)


def coverage_days(stock, daily_demand):
    demand=D(daily_demand)
    return None if demand<=0 else D(stock)/demand


def gross_margin_pct(price_cents, cost_cents):
    if not price_cents: return Decimal('0')
    return (D(price_cents-cost_cents)/D(price_cents))*Decimal('100')
