import os,sys,tempfile,sqlite3
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[1];os.environ['ATOMO_DATA_DIR']=tempfile.mkdtemp(prefix='atomo-quick-qa-');sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from core.config import LIVE_DB
from core.database import init_db,con,dfq,balances_df,insert_movement
from core.navigation import GROUPS
from core.finance import yield_snapshot,period_summary
from core.rates import parse_rate,update_rate_field
init_db(LIVE_DB)
with con(LIVE_DB) as c:
 for name,cur in [('QA cuenta','ARS'),('QA reserva','ARS'),('QA dólares','USD')]:
  c.execute("INSERT INTO cuentas(institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES (6,?,'Otra',?,100000,?,?)",(name,cur,date.today().isoformat(),date.today().isoformat()))
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
def check():assert not app.exception,[x.message for x in app.exception]
def get(items,label):return next(x for x in items if x.label==label)
def group(name):app.selectbox(key='sidebar_group').select(name).run();check()
def query(sql):return dfq(sql,db=LIVE_DB)
def source(label,frag):box=get(app.selectbox,label);box.select(next(x for x in box.options if frag in x))
check();assert app.session_state['period_month']==date.today().month
for name in GROUPS:
 group(name);assert app.selectbox(key='mobile_group').value==name
# Empty form validation preserves data.
group('Pagos');get(app.text_input,'¿Qué fue? *').set_value('Gasto rápido QA');get(app.text_input,'Monto *').set_value('2.000,50')
get(app.button,'Guardar pago').click().run();check();assert app.error and not len(query('select * from movimientos'))
source('¿De dónde sale? *','QA cuenta');get(app.button,'Guardar pago').click().run();check()
assert len(query('select * from movimientos'))==1 and query('select * from movimientos').iloc[0].fecha==date.today().isoformat()
assert get(app.text_input,'Monto *').value=='' and get(app.text_input,'¿Qué fue? *').value==''
assert get(app.date_input,'Fecha').value==date.today()
# Repeat routine payment, choose another mode and verify own transfers aren't expenses.
get(app.selectbox,'¿Qué querés cargar?').select('Mover entre mis cuentas').run();check()
get(app.text_input,'¿Qué fue? *').set_value('Propia rápida QA');get(app.text_input,'Monto *').set_value('5.000')
source('¿De dónde sale? *','QA cuenta');source('¿A cuál de tus cuentas va? *','QA dólares');get(app.button,'Guardar pago').click().run();check();assert app.error
source('¿A cuál de tus cuentas va? *','QA reserva');get(app.button,'Guardar pago').click().run();check()
summary,_=period_summary(date.today().strftime('%Y-%m'),LIVE_DB);assert summary['gastos']==2000.5 and summary['transferencias']==5000
get(app.selectbox,'¿Qué querés cargar?').select('Transferir a otra persona').run()
get(app.text_input,'¿Qué fue? *').set_value('Ayuda QA');get(app.text_input,'Monto *').set_value('1.000')
source('¿De dónde sale? *','QA cuenta');get(app.button,'Guardar pago').click().run();check();assert app.error
get(app.text_input,'¿A quién? *').set_value('Persona QA');get(app.button,'Guardar pago').click().run();check()
# Income and explicit backdate; next record starts today.
group('Ingresos');get(app.text_input,'¿Qué fue? *').set_value('Cobro QA');get(app.text_input,'Monto *').set_value('10.000');source('¿Dónde entra? *','QA cuenta')
get(app.date_input,'Fecha').set_value(date.today()-timedelta(days=40));get(app.button,'Guardar ingreso').click().run();check()
assert get(app.date_input,'Fecha').value==date.today()
assert query("select fecha from movimientos where descripcion='Cobro QA'").iloc[0,0]==(date.today()-timedelta(days=40)).isoformat()
# A generic pendiente doesn't spend money; marking it paid spends it once.
group('Pendientes');get(app.button,'Guardar pendiente').click().run();check();assert app.error
get(app.text_input,'¿Qué te falta pagar? *').set_value('Pendiente rápido QA')
get(app.text_input,'Monto pendiente *').set_value('2.500')
before=balances_df(LIVE_DB).set_index('id').loc[1,'saldo']
get(app.button,'Guardar pendiente').click().run();check()
assert get(app.text_input,'Monto pendiente *').value==''
assert balances_df(LIVE_DB).set_index('id').loc[1,'saldo']==before
with con(LIVE_DB) as c:c.execute("update movimientos set importado=1 where descripcion='Pendiente rápido QA'")
app.run();source('¿De dónde salió? *','QA cuenta');get(app.button,'Registrar pago del pendiente').click().run();check()
assert balances_df(LIVE_DB).set_index('id').loc[1,'saldo']==before-2500
paid=query("select tipo,importado,subtipo from movimientos where descripcion='Pendiente rápido QA'").iloc[0]
assert paid.tolist()==['Gasto',0,'Pago de pendiente']
# Inline rate editing updates estimation immediately and preserves rate when switched off.
group('Más');app.button(key='detail_more_Cuentas').click().run();check()
app.toggle(key='yield_on_1').set_value(True).run();check()
app.text_input(key='yield_rate_1').set_value('36,1234').run();check()
assert query('select tasa_anual from cuentas where id=1').iloc[0,0]==36.1234
expected=yield_snapshot(LIVE_DB,30)['estimated_yield'];assert expected>0
app.selectbox(key='yield_type_1').select('TEA').run();check();assert yield_snapshot(LIVE_DB,30)['estimated_yield']<expected
app.toggle(key='yield_on_1').set_value(False).run();check()
assert query('select tasa_anual from cuentas where id=1').iloc[0,0]==36.1234 and yield_snapshot(LIVE_DB,30)['estimated_yield']==0
app.text_input(key='yield_rate_1').set_value('nan').run();check();assert app.error and query('select tasa_anual from cuentas where id=1').iloc[0,0]==36.1234
app.text_input(key='yield_rate_1').set_value('40.5').run();check()
# Delta writes from another session don't overwrite a recently changed rate.
update_rate_field(LIVE_DB,1,'rate','45,5');app.toggle(key='yield_on_1').set_value(True).run();check()
assert query('select tasa_anual from cuentas where id=1').iloc[0,0]==45.5
# Blur/rate, toggle and type may be submitted in the same rerun.
app.toggle(key='yield_on_1').set_value(False).run();check()
app.toggle(key='yield_on_1').set_value(True)
app.text_input(key='yield_rate_1').set_value('42,3456')
app.selectbox(key='yield_type_1').select('TNA')
app.run();check()
assert query('select genera_rendimiento,tasa_anual,tipo_tasa from cuentas where id=1').iloc[0].tolist()==[1,42.3456,'TNA']
assert parse_rate('36,12345') is None and parse_rate('inf') is None and parse_rate('35,5%')==35.5
assert query('pragma integrity_check').iloc[0,0]=='ok'
# Reload starts on current month and retains rates.
again=AppTest.from_file(str(ROOT/'app.py')).run();assert not again.exception
assert again.session_state['period_month']==date.today().month
print('PASS cargas rápidas, validaciones, propia/tercero, fecha actual/backdate, limpieza al guardar, tasa instantánea/TNA/TEA/inválidos, alternancia sin perder tasa, edición concurrente, persistencia y navegación de cinco grupos')
