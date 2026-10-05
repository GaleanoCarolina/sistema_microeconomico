from datetime import datetime, date, timedelta, timezone
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        LOCAL_TZ = ZoneInfo('America/Guatemala')
    except ZoneInfoNotFoundError:
        # Guatemala usa UTC-6 durante todo el año. Este respaldo permite arrancar en Windows
        # incluso si el paquete tzdata todavía no está instalado.
        LOCAL_TZ = timezone(timedelta(hours=-6), name='Guatemala')
except Exception:
    LOCAL_TZ = timezone(timedelta(hours=-6), name='Guatemala')

def local_now(): return datetime.now(LOCAL_TZ)
def iso_now(): return local_now().strftime('%Y-%m-%d %H:%M:%S')
def local_today(): return local_now().date()
def iso_date(value=None): return (value or local_today()).strftime('%Y-%m-%d')

def period_bounds(kind='Hoy', start=None, end=None):
    today = local_today()
    if kind == 'Hoy': return today, today
    if kind == 'Últimos 7 días': return today - timedelta(days=6), today
    if kind == 'Últimos 30 días': return today - timedelta(days=29), today
    if kind == 'Este mes': return today.replace(day=1), today
    if start and end:
        if isinstance(start, str): start = date.fromisoformat(start)
        if isinstance(end, str): end = date.fromisoformat(end)
        return (start, end) if start <= end else (end, start)
    return today, today
