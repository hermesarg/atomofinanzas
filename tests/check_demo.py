import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["ATOMO_DATA_DIR"] = tempfile.mkdtemp(prefix="atomo-demo-qa-")
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest


first = AppTest.from_file(str(ROOT / "app_demo.py"), default_timeout=30).run()
assert not first.exception
path1 = Path(first.session_state["_demo_db_path"])
assert path1.exists()
assert not any(x.label == "Contraseña" for x in first.text_input)

second = AppTest.from_file(str(ROOT / "app_demo.py"), default_timeout=30).run()
assert not second.exception
path2 = Path(second.session_state["_demo_db_path"])
assert path2.exists() and path2 != path1

with sqlite3.connect(path1) as c:
    before1 = c.execute("SELECT COUNT(*) FROM movimientos").fetchone()[0]
    c.execute("DELETE FROM movimientos")

with sqlite3.connect(path2) as c:
    before2 = c.execute("SELECT COUNT(*) FROM movimientos").fetchone()[0]

assert before1 > 0 and before2 == before1
print("PASS demo pública: sin login, datos ficticios y SQLite aislada por sesión")
