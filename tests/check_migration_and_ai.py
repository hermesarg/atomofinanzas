import os, sys, tempfile, sqlite3
from pathlib import Path
from unittest.mock import patch, Mock
ROOT=Path(__file__).resolve().parents[1]
os.environ['ATOMO_DATA_DIR']=tempfile.mkdtemp(prefix='atomo-extra-')
sys.path.insert(0,str(ROOT))
from core.database import init_db,con,dfq,insert_movement
from core.config import LIVE_DB
from streamlit.testing.v1 import AppTest
# Legacy v1 migration preserves rows, repeated migration is idempotent.
old=Path(tempfile.mkdtemp())/'legacy.db'
with sqlite3.connect(old) as c:
    c.execute('CREATE TABLE movimientos(id INTEGER PRIMARY KEY AUTOINCREMENT,fecha TEXT NOT NULL,tipo TEXT NOT NULL,descripcion TEXT NOT NULL,categoria TEXT NOT NULL,monto REAL NOT NULL,cuenta TEXT,notas TEXT,creado_en TEXT NOT NULL)')
    c.execute("INSERT INTO movimientos(fecha,tipo,descripcion,categoria,monto,creado_en) VALUES ('2026-09-30','Ingreso','LEGACY','Otros',123,'2026-09-30')")
init_db(old); init_db(old)
assert dfq('select descripcion,monto from movimientos',db=old).iloc[0].tolist()==['LEGACY',123.0]
assert dfq('PRAGMA integrity_check',db=old).iloc[0,0]=='ok'
try:
    with con(old) as c:
        c.execute("update movimientos set monto=999")
        raise RuntimeError('rollback test')
except RuntimeError: pass
assert dfq('select monto from movimientos',db=old).iloc[0,0]==123
print('PASS migración antigua/idempotencia/preservación y rollback')
# API tested with a mocked client: no key or request to a provider.
app=AppTest.from_file(str(ROOT/'app.py')).run()
app.selectbox(key='sidebar_group').select('Más').run()
app.button(key='detail_more_Preguntale a Átomo').click().run()
assert len(app.error)==1 and not app.exception
import screens.assistant as screen
original_getenv=os.getenv
client=Mock(); client.responses.create.return_value.output_text='Respuesta ficticia QA'
# getenv checks are mocked rather than providing any secret or example credential.
def fake_env(name, default=None):
    return True if name=='OPENAI_API_KEY' else original_getenv(name,default)
with patch.object(screen.os,'getenv',side_effect=fake_env), patch.object(screen,'OpenAI',return_value=client):
    app.run(); app.text_area[0].set_value('Consulta ficticia QA'); app.button[-1].click().run()
    assert not app.exception and any('Respuesta ficticia QA' in x.value for x in app.markdown)
    client.responses.create.side_effect=RuntimeError('private diagnostic that must not be shown')
    app.button[-1].click().run()
    assert not app.exception and app.error and 'private diagnostic' not in app.error[0].value
print('PASS IA: sin clave, respuesta simulada y excepción sin revelar diagnósticos')
