from decimal import Decimal
from utils.money import D, from_cents, to_cents

class PricingService:
    MARKUP='MARKUP'
    MARGIN='MARGIN'

    @staticmethod
    def price_from_markup(cpp_cents, markup_pct):
        cpp = from_cents(cpp_cents)
        pct = D(markup_pct) / Decimal('100')
        return to_cents(cpp * (Decimal('1') + pct))

    @staticmethod
    def markup_from_price(cpp_cents, price_cents):
        if cpp_cents <= 0:
            return Decimal('0')
        return ((D(price_cents) - D(cpp_cents)) / D(cpp_cents) * Decimal('100')).quantize(Decimal('0.01'))

    @staticmethod
    def price_from_margin(cpp_cents, margin_pct):
        margin = D(margin_pct) / Decimal('100')
        if margin >= 1:
            raise ValueError('El margen sobre venta debe ser menor a 100%.')
        return to_cents(from_cents(cpp_cents) / (Decimal('1') - margin))

    @staticmethod
    def margin_from_price(cpp_cents, price_cents):
        price=D(price_cents)
        if price <= 0 or cpp_cents <= 0:
            return Decimal('0')
        return ((price-D(cpp_cents))/price*Decimal('100')).quantize(Decimal('0.01'))

    @classmethod
    def price_from_percent(cls, cpp_cents, pct, policy='MARKUP'):
        return cls.price_from_margin(cpp_cents,pct) if str(policy).upper()==cls.MARGIN else cls.price_from_markup(cpp_cents,pct)

    @classmethod
    def percent_from_price(cls, cpp_cents, price_cents, policy='MARKUP'):
        return cls.margin_from_price(cpp_cents,price_cents) if str(policy).upper()==cls.MARGIN else cls.markup_from_price(cpp_cents,price_cents)

    @classmethod
    def policy_label(cls, policy='MARKUP'):
        return 'Margen sobre ventas' if str(policy).upper()==cls.MARGIN else 'Recargo sobre costo'
