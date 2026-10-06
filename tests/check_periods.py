import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ["ATOMO_DATA_DIR"] = tempfile.mkdtemp(prefix="atomo-periods-qa-")
sys.path.insert(0, str(ROOT))

from core.database import init_db, get_config
from core.periods import (
    active_period,
    ensure_active_period,
    period_for_date,
    save_preference,
    start_period,
)


def fresh(name):
    db = Path(tempfile.mkdtemp(prefix="atomo-period-db-")) / f"{name}.db"
    init_db(db)
    return db


fixed = fresh("fixed")
with patch("core.periods.local_today", return_value=date(2026, 10, 6)):
    save_preference("salary_fixed", 8, fixed)
    info = active_period(fixed)
    assert info["periodo"] == "2026-09"
    assert info["inicio"] == "2026-09-08"
    assert info["fin"] == "2026-10-07"
    assert period_for_date(date(2026, 10, 6), fixed) == "2026-09"
    assert period_for_date(date(2026, 10, 8), fixed) == "2026-10"

    # Cambiar el criterio no reescribe el período actual ni el historial.
    save_preference("calendar", None, fixed)
    info = active_period(fixed)
    assert info["periodo"] == "2026-09"
    assert info["criterio"] == "Desde mi fecha habitual de cobro"
    assert info["fin"] == "2026-10-31"
    assert get_config("periodo_modo", "", fixed) == "calendar"

assert ensure_active_period(fixed, today=date(2026, 11, 1)) == "2026-11"
info = active_period(fixed)
assert info["inicio"] == "2026-11-01"
assert info["criterio"] == "Mes calendario"

manual = fresh("manual")
save_preference("salary_manual", None, manual)
assert get_config("periodo_activo", "", manual) == ""
start_period(date(2026, 9, 9), manual, mode="salary_manual")
start_period(date(2026, 10, 9), manual, mode="salary_manual")
assert period_for_date(date(2026, 10, 8), manual) == "2026-09"
assert period_for_date(date(2026, 10, 9), manual) == "2026-10"

print("PASS períodos: sueldo, calendario, cambio hacia adelante y apertura manual sin reescribir historial")
