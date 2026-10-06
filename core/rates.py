from core.clock import today as local_today, local_now
"""Preferencias de rendimiento: se guardan sin alterar saldos ni crear ingresos."""
from datetime import date
import math
import re
from core.database import con


def update_rate(db, account_id, enabled, rate, rate_type):
    rate = float(rate)
    if not math.isfinite(rate) or rate < 0 or rate > 10000 or rate_type not in ['TNA','TEA']:
        raise ValueError('Ingresá una tasa entre 0 y 10.000 y elegí TNA o TEA.')
    with con(db) as connection:
        connection.execute('UPDATE cuentas SET genera_rendimiento=?,tasa_anual=?,tipo_tasa=?,fecha_tasa=? WHERE id=? AND activa=1',
                           (int(bool(enabled)),rate,rate_type,local_today().isoformat(),int(account_id)))


def parse_rate(raw):
    text = str(raw).strip().removesuffix('%').strip()
    if not re.fullmatch(r'\d+(?:[.,]\d{1,4})?', text):
        return None
    value = float(text.replace(',', '.'))
    return value if math.isfinite(value) and 0 <= value <= 10000 else None


def update_rate_field(db, account_id, field, value):
    """Only the edited field changes, even when PC and phone are open together."""
    columns = {'enabled':'genera_rendimiento', 'rate':'tasa_anual', 'type':'tipo_tasa'}
    if field not in columns:
        raise ValueError('Campo no permitido.')
    if field == 'rate':
        value = parse_rate(value)
        if value is None:
            raise ValueError('Tasa inválida.')
    elif field == 'type':
        if value not in ['TNA','TEA']:
            raise ValueError('Elegí TNA o TEA.')
    else:
        value = int(bool(value))
    with con(db) as connection:
        connection.execute(f'UPDATE cuentas SET {columns[field]}=?,fecha_tasa=? WHERE id=? AND activa=1', (value,local_today().isoformat(),int(account_id)))
        return connection.execute('SELECT genera_rendimiento,tasa_anual,tipo_tasa FROM cuentas WHERE id=?', (int(account_id),)).fetchone()
