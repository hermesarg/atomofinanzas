import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ["ATOMO_DATA_DIR"] = tempfile.mkdtemp(prefix="atomo-electro-qa-")
sys.path.insert(0, str(ROOT))

from core.finance import _ecg_points, atomo_profile


def y_span(points):
    ys = [float(pair.split(",")[1]) for pair in points.split()]
    return max(ys) - min(ys)


calm = y_span(_ecg_points(95))
middle = y_span(_ecg_points(55))
stressed = y_span(_ecg_points(15))

assert calm < middle < stressed, (calm, middle, stressed)
assert stressed >= calm * 2.8, (calm, stressed)

electro = {
    "liquidity": 60,
    "solvency": 60,
    "flow": 60,
    "_history": pd.DataFrame(),
    "_flex_target_pct": 15,
}
profile = atomo_profile("2026-10", electro=electro)
assert profile["level"] == "Átomo"
assert profile["next_level"] == "Agua"

print("PASS Electro: línea fina con contraste de amplitud y perfil inicial Átomo")
