"""Pruebas de acceso, persistencia, importación, backups y zona horaria; bases ficticias."""
import os,sys,tempfile,sqlite3,time,secrets
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(tempfile.mkdtemp(prefix='atomo-private-qa-'))
os.environ['ATOMO_DATA_DIR']=str(DATA)
os.environ['ATOMO_WEB_PRIVATE']='1'
os.environ['ATOMO_SETUP_TOKEN']=secrets.token_urlsafe(40)
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from core.config import LIVE_DB,BACKUP_DIR
from core.security import create_owner,authenticate,valid_session,owner,security_db
from core.database import init_db,con,insert_movement
from core.storage import snapshot,daily_backup,validate_database,import_initial,import_available
from core.clock import today
from servir_web import validate_environment

app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
assert not app.exception
assert not LIVE_DB.exists(), 'No abrir la base financiera antes del ingreso'
assert any(x.label=='Código de activación' for x in app.text_input)
password='Contraseña ficticia de QA 2026'
assert create_owner('equivocado','qa',password,password) is None
result=create_owner(os.environ['ATOMO_SETUP_TOKEN'],'qauser',password,password)
assert result and owner()[0]=='qauser'
assert password.encode() not in (DATA/'acceso.db').read_bytes()
assert authenticate('qauser','incorrecta')[0] is None
assert authenticate('otra-persona',password)[0] is None
assert authenticate('qauser',password)[0]==result
state={'_private_access':{'user':result[0],'version':result[1],'issued':time.time()}}
assert valid_session(state)
assert not valid_session(state,time.time()+12*3600+1)
assert not valid_session({'_private_access':dict(state['_private_access'],version='vieja')})
for _ in range(5):authenticate('qauser','incorrecta')
assert 'Demasiados' in authenticate('qauser',password)[1]
with security_db() as c:c.execute('DELETE FROM intentos')
# El alta ya consumió el token, incluso con otro navegador.
try:create_owner(os.environ['ATOMO_SETUP_TOKEN'],'otro',password,password)
except ValueError:pass
else:raise AssertionError('No permitir otro propietario')
app.run();assert not LIVE_DB.exists()
next(x for x in app.text_input if x.label=='Usuario').set_value('qauser')
next(x for x in app.text_input if x.label=='Contraseña').set_value(password)
next(x for x in app.button if x.label=='Entrar').click().run()
assert not app.exception and LIVE_DB.exists()
assert 'access_password' not in app.session_state
assert import_available(LIVE_DB)
fixture=DATA/'origen.db';init_db(fixture)
with con(fixture) as c:
 c.execute("INSERT INTO cuentas(nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES ('Cuenta QA','Otra','ARS',100000,?,?)",(today().isoformat(),today().isoformat()))
insert_movement(today(),'Ingreso','Historial QA','Otros',500,db=fixture)
content=snapshot(fixture);counts=validate_database(content)
assert counts['cuentas']==1 and counts['movimientos']==1
import_initial(content,LIVE_DB)
with con(LIVE_DB) as c:assert c.execute('SELECT descripcion FROM movimientos').fetchone()[0]=='Historial QA'
assert not import_available(LIVE_DB)
try:import_initial(content,LIVE_DB)
except ValueError:pass
else:raise AssertionError('No reemplazar registros')
for content in [b'invalido',b'SQLite format 3\0'+b'invalido']:
 try:validate_database(content)
 except ValueError:pass
 else:raise AssertionError('Rechazar archivo inválido')
with con(fixture) as c:c.execute('CREATE TRIGGER ajeno AFTER INSERT ON cuentas BEGIN DELETE FROM movimientos; END;')
try:validate_database(snapshot(fixture))
except ValueError:pass
else:raise AssertionError('No aceptar triggers ajenos')
backup=daily_backup(LIVE_DB,BACKUP_DIR,True)
with sqlite3.connect(backup) as c:assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
insert_movement(today(),'Gasto','Luego del respaldo','Otros',50,db=LIVE_DB)
with sqlite3.connect(backup) as c:assert c.execute('SELECT COUNT(*) FROM movimientos').fetchone()[0]==1
for day in range(1,32):(BACKUP_DIR/f'finanzas_diario_202501{day:02}.db').write_bytes(b'ficticio')
daily_backup(LIVE_DB,BACKUP_DIR,True);assert len(list(BACKUP_DIR.glob('finanzas_diario_*.db')))==30
# Fecha argentina cuando UTC ya pasó al día siguiente.
class FakeDateTime:
 @staticmethod
 def now(zone):return datetime(2026,10,7,1,30,tzinfo=timezone.utc).astimezone(zone)
with patch('core.clock.datetime',FakeDateTime):assert today().isoformat()=='2026-10-06'
assert validate_environment()==8501
with patch.dict(os.environ,{'RENDER':'true'}):
 try:validate_environment()
 except ValueError as e:assert 'persistente' in str(e)
 else:raise AssertionError('No iniciar Render sin disco montado')
app.run()
app.selectbox(key='sidebar_group').select('Más').run()
before_rate=None
with con(LIVE_DB) as c:before_rate=c.execute('SELECT tasa_anual FROM cuentas WHERE id=1').fetchone()[0]
record=dict(app.session_state['_private_access']);record['issued']=time.time()-13*3600
app.session_state['_private_access']=record
app.text_input(key='yield_rate_1').set_value('45').run()
assert not app.exception and any(x.label=='Contraseña' for x in app.text_input)
with con(LIVE_DB) as c:assert c.execute('SELECT tasa_anual FROM cuentas WHERE id=1').fetchone()[0]==before_rate
next(x for x in app.text_input if x.label=='Usuario').set_value('qauser')
next(x for x in app.text_input if x.label=='Contraseña').set_value(password)
next(x for x in app.button if x.label=='Entrar').click().run()
app.button(key='private_logout').click().run()
assert not app.exception and any(x.label=='Contraseña' for x in app.text_input)
assert not app.dataframe and not app.get('file_uploader')
with con(LIVE_DB) as c:assert c.execute('SELECT COUNT(*) FROM movimientos').fetchone()[0]==2
print('PASS acceso privado bloqueado antes de SQLite, contraseña derivada, intentos persistentes, sesión expirada/revocada, ingreso/salida, importación inicial protegida, archivos inválidos, snapshot íntegro/retención y fecha argentina')
