"""Fechas del producto, independientes de la zona horaria del alojamiento."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def local_now():
    return datetime.now(ZoneInfo(os.getenv('ATOMO_TIMEZONE', 'America/Argentina/Buenos_Aires')))


def today():
    return local_now().date()
