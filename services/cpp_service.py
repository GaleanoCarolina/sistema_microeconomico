from decimal import Decimal, ROUND_HALF_UP
from utils.money import D, to_cents, from_cents

class CPPService:
    @staticmethod
    def calculate(old_qty, old_cpp_cents, new_qty, new_cost_cents):
        old_qty = D(old_qty); new_qty = D(new_qty)
        total_qty = old_qty + new_qty
        if total_qty <= 0:
            return 0
        old_cost = from_cents(old_cpp_cents)
        new_cost = from_cents(new_cost_cents)
        cpp = ((old_qty * old_cost) + (new_qty * new_cost)) / total_qty
        return to_cents(cpp)
