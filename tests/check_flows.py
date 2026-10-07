import os, sys, tempfile, sqlite3
from pathlib import Path
from datetime import date, timedelta
ROOT=Path(__file__).resolve().parents[1]
os.environ['ATOMO_DATA_DIR']=tempfile.mkdtemp(prefix='atomo-tests-')
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from core.config import PAGES, LIVE_DB
from core.navigation import GROUPS, group_for_page
from core.database import dfq, con, balances_df
from core.finance import period_summary, atomo_profile, parse_amount, money, add_months
from core.clock import today as local_today

def get(elements,label):
    items=[x for x in elements if x.label==label]
    assert len(items)==1, (label,[(x.label,x.value) for x in elements])
    return items[0]
def check(app): assert not app.exception,[e.message for e in app.exception]
def page(app,title):
    group=group_for_page(title)
    app.selectbox(key='sidebar_group').select(group).run(); check(app)
    if app.session_state['page'] != title:
        if group == 'Pagos':
            if title == 'Movimientos':app.button(key='pay_history').click().run()
            else:app.button(key='main_Pagos').click().run()
        elif group == 'Más':
            app.button(key='detail_more_'+title).click().run()
        else:app.selectbox(key='section_detail').select(title).run()
        check(app)
def text(app,label,value): get(app.text_input,label).set_value(value)
def pick(app,label,value): get(app.selectbox,label).select(value)
def click(app,label): get(app.button,label).click().run(); check(app)
def query(sql): return dfq(sql,db=LIVE_DB)
def new_app():
    app=AppTest.from_file(str(ROOT/'app.py'))
    from core.backend import remote_mode
    if remote_mode():
        import time
        from core.security import owner, create_owner
        record=owner()
        if not record:
            result=create_owner(os.environ['ATOMO_SETUP_TOKEN'],'qauser','Contraseña ficticia QA 2026','Contraseña ficticia QA 2026')
        else:
            result=(record[0],record[3])
        app.session_state['_private_access']={'user':result[0],'version':result[1],'issued':time.time()}
    return app.run()
app=new_app(); check(app)
for title in PAGES:
    page(app,title); assert app.session_state['page']==title
for group in GROUPS:
    app.selectbox(key='mobile_group').select(group).run(); check(app)
    assert group_for_page(app.session_state['page'])==group
    app.button(key='main_'+group).click().run();check(app)
print('PASS secciones internas y cinco grupos de navegación: lateral, superior y móvil')
page(app,'Cuentas'); click(app,'Guardar cuenta'); assert app.error
for name,kind,currency,balance in [('Banco QA','Caja de ahorro ARS','ARS','100.000,50'),('Billetera QA','Billetera','ARS','50.000'),('USD QA','Caja de ahorro USD','USD','100'),('Broker QA','Cuenta comitente','ARS','0')]:
    text(app,'Nombre de la cuenta *',name); text(app,'Saldo base *',balance)
    pick(app,'Tipo de cuenta *',kind); pick(app,'Moneda *',currency)
    click(app,'Guardar cuenta')
assert len(query('select * from cuentas'))==4
pick(app,'Cuenta a modificar',next(x for x in get(app.selectbox,'Cuenta a modificar').options if 'Banco QA' in x)); app.run()
# Duplicate labels occur in separate account forms: use edit keys/name index
text(app,'Nombre actualizado *','Banco QA editado')
edit_bal=next(x for x in app.text_input if x.key and x.key.startswith('edit_balance_'))
edit_bal.set_value('120.000,50'); click(app,'Guardar cambios')
assert query('select saldo_base from cuentas where id=1').iloc[0,0]==120000.5
click(app,'Cargar transferencia →'); assert app.session_state['page']=='Pagos'; page(app,'Movimientos')
print('PASS cuentas: altas, modificación, persistencia y botón interno')
def choose_account(label, fragment):
    box=get(app.selectbox,label); box.select(next(x for x in box.options if fragment in x))
def movement(typ,desc,amount,account_label=None,fragment=None):
    get(app.radio,'Tipo *').set_value(typ); app.run(); check(app)
    text(app,'Descripción *',desc); text(app,'Monto *',amount)
    if account_label: choose_account(account_label,fragment)
    click(app,'Guardar movimiento')
movement('Ingreso','Sueldo QA','20.000','Entra a','Banco QA')
movement('Gasto','Gasto QA','5.000,50','Sale de','Banco QA')
get(app.radio,'Tipo *').set_value('Transferencia'); app.run()
text(app,'Descripción *','Propia QA'); text(app,'Monto *','10.000'); choose_account('Sale de *','Banco QA'); choose_account('Entra a *','Billetera QA'); click(app,'Guardar movimiento')
s,_=period_summary(date.today().strftime('%Y-%m'),LIVE_DB); assert s['gastos']==5000.5 and s['transferencias']==10000
get(app.radio,'¿Qué tipo de transferencia es? *').set_value('A otra persona'); app.run()
text(app,'Descripción *','Tercero QA'); text(app,'Monto *','1.000'); choose_account('Sale de *','Banco QA')
click(app,'Guardar movimiento'); assert app.error
text(app,'Va a / destinatario *','Persona ficticia'); click(app,'Guardar movimiento')
s,_=period_summary(date.today().strftime('%Y-%m'),LIVE_DB); assert s['gastos']==6000.5
text(app,'Descripción *','Moneda incorrecta'); text(app,'Monto *','100'); choose_account('Sale de *','USD QA'); click(app,'Guardar movimiento'); assert app.error
for raw in ('nan','inf','-50','1.2','1,2,3','USDT nan'):
    text(app,'Monto *',raw); click(app,'Guardar movimiento'); assert app.error
get(app.radio,'Tipo *').set_value('Ingreso'); app.run(); text(app,'Descripción *','Ingreso USD'); text(app,'Monto *','10'); pick(app,'Moneda *','USD'); choose_account('Entra a','USD QA'); click(app,'Guardar movimiento')
s,_=period_summary(date.today().strftime('%Y-%m'),LIVE_DB); assert s['ingresos']==20000
assert balances_df(LIVE_DB).loc[lambda x:x.id==1,'saldo'].iloc[0]==124000
print('PASS movimientos: ingreso/gasto, transferencia propia/tercero, monedas, inválidos y saldos')
page(app,'Tarjetas y cuotas'); click(app,'Guardar tarjeta'); assert app.error
text(app,'Nombre de la tarjeta *','Visa QA'); text(app,'Límite (opcional)','abc'); click(app,'Guardar tarjeta'); assert app.error
text(app,'Límite (opcional)',''); pick(app,'Moneda *','USD'); click(app,'Guardar tarjeta')
assert query('select * from tarjetas').iloc[0].cierre_dia is None
text(app,'Compra / concepto *','Compra USD QA'); text(app,'Monto de cada cuota *','10'); click(app,'Calcular y agregar cuotas')
qs=query("select * from movimientos where tipo='Compromiso'"); assert len(qs)==3 and set(qs.moneda)=={'USD'}
choose_account('Salió de *','Banco QA'); click(app,'Marcar como pagado'); assert app.error
choose_account('Salió de *','USD QA'); click(app,'Marcar como pagado'); assert len(query("select * from movimientos where tipo='Compromiso'"))==2
row=query("select * from movimientos where grupo_cuotas is not null and tipo='Gasto'").iloc[0]; assert row.fecha==local_today().isoformat()
print('PASS tarjetas: cierre opcional, cuotas atómicas y en moneda correcta, pago y fecha efectiva')
page(app,'Deudas'); text(app,'Nombre de la deuda *','Deuda QA'); text(app,'Cuota','oops'); click(app,'Guardar deuda'); assert app.error
text(app,'Saldo pendiente *','10.000'); text(app,'Cuota','1.000'); click(app,'Guardar deuda'); assert len(query('select * from deudas'))==1
snapshot=query('select * from movimientos').to_json(); text(app,'Monto a adelantar','1.000'); app.run(); assert query('select * from movimientos').to_json()==snapshot
print('PASS deuda válida, inválida y simulación sin operaciones')
page(app,'Inversiones'); text(app,'Descripción *','Activo QA'); text(app,'Monto invertido *','1.000'); text(app,'Valor actual *','1.200'); click(app,'Guardar posición'); assert len(query('select * from posiciones'))==1
text(app,'Valor actual *','-1'); click(app,'Guardar posición'); assert app.error
print('PASS posición y validación')
page(app,'Comparar rendimientos'); click(app,'Agregar alternativa'); assert app.error
for instrument,currency,rate in [('Alternativa ARS A','ARS',30.0),('Alternativa ARS B','ARS',40.0),('Alternativa USD','USD',100.0)]:
    text(app,'Instrumento / nombre específico *',instrument); pick(app,'Moneda',currency); get(app.number_input,'Tasa anual %').set_value(rate); click(app,'Agregar alternativa')
assert len(query('select * from alternativas_rendimiento'))==3
shown=app.dataframe[0].value; assert len(shown)==2 and 'Alternativa USD' not in set(shown.Instrumento)
print('PASS comparador: tasas, mismo monto/plazo y monedas separadas')
page(app,'Instituciones'); text(app,'Buscar','['); app.run(); check(app)
text(app,'Nombre *','Institución QA'); click(app,'Agregar'); click(app,'Agregar'); assert app.warning
page(app,'Configuración'); text(app,'Colchón objetivo ARS *','123.456'); click(app,'Guardar configuración')
assert query("select valor from config where clave='colchon_objetivo_ars'").iloc[0,0]=='123456.0'
page(app,'Proyección'); pick(app,'Período',1); pick(app,'Año',2025); app.run(); check(app)
pick(app,'Período',date.today().month); pick(app,'Año',date.today().year); app.run(); check(app)
# New Streamlit session, same SQLite data
again=new_app(); check(again); assert len(query('select * from cuentas'))==4
assert parse_amount('1.234.567,89')==1234567.89 and money(1234.56,'ARS',True)=='$ 1.234,56'
assert add_months(date(2024,1,31),1)==date(2024,2,29)
# Scaling every financial magnitude cannot buy a better level.
period=date.today().strftime('%Y-%m'); profile=atomo_profile(period,LIVE_DB)
with con(LIVE_DB) as c:
    for table,cols in [('movimientos',['monto']),('cuentas',['saldo_base']),('deudas',['saldo_pendiente','cuota']),('posiciones',['precio_actual','precio_promedio'])]:
        for col in cols: c.execute(f'update {table} set {col}={col}*100')
assert atomo_profile(period,LIVE_DB)['score']==profile['score']
assert query('PRAGMA integrity_check').iloc[0,0]=='ok'
print('PASS instituciones, configuración, período, reinicio, números ARS, calendario, nivel independiente de riqueza e integridad SQLite')
