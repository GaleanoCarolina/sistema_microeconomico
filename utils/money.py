from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def D(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def to_cents(value) -> int:
    return int((D(value).quantize(CENT, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def from_cents(cents: int) -> Decimal:
    return (Decimal(int(cents)) / 100).quantize(CENT)


def q(cents: int) -> str:
    return f"Q{from_cents(cents):,.2f}"
