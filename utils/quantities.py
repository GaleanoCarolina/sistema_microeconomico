from decimal import Decimal, ROUND_HALF_UP

FRACTIONAL_UNITS = {'libra','lb','kilogramo','kg','gramo','g','litro','l','mililitro','ml','metro','m'}

def infer_quantity_mode(unit_name: str) -> str:
    u=(unit_name or 'unidad').strip().lower()
    return 'FRACTIONAL' if u in FRACTIONAL_UNITS else 'INTEGER'

def format_qty(value, mode='INTEGER'):
    d=Decimal(str(value or 0))
    if mode == 'INTEGER':
        return str(int(d.to_integral_value(rounding=ROUND_HALF_UP)))
    s=f'{d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):f}'
    return s.rstrip('0').rstrip('.') if '.' in s else s

def rounded_reorder_qty(value, mode='INTEGER'):
    d=max(Decimal('0'),Decimal(str(value)))
    if mode=='INTEGER':
        return int(d.to_integral_value(rounding='ROUND_CEILING'))
    step=Decimal('0.25')
    return (d/step).to_integral_value(rounding='ROUND_CEILING')*step
