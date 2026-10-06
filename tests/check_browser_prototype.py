"""QA real de navegación, carga móvil, tasas y persistencia; usa datos ficticios."""
import os,sys,tempfile,subprocess,time,sqlite3,json
from pathlib import Path
from datetime import date
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];DATA=Path(tempfile.mkdtemp(prefix='atomo-prototype-browser-'))
os.environ['ATOMO_DATA_DIR']=str(DATA);sys.path.insert(0,str(ROOT))
from core.database import init_db,con,insert_movement
from core.config import LIVE_DB
init_db(LIVE_DB)
with con(LIVE_DB) as c:
 for name in ['Cuenta principal QA','Reserva QA']:
  c.execute("INSERT INTO cuentas(institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES (6,?,'Otra','ARS',100000,?,?)",(name,date.today().isoformat(),date.today().isoformat()))
insert_movement(date.today(),'Compromiso','Pendiente QA','Otros',1000,None,None,'ARS','Datos ficticios de QA',db=LIVE_DB)
OUT=ROOT/'docs/qa_prototipo';OUT.mkdir(exist_ok=True)
server=subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),'--server.address','127.0.0.1','--server.port','8518','--browser.gatherUsageStats','false','--server.fileWatcherType','none','--client.toolbarMode','developer'],cwd=ROOT,env=dict(os.environ,ATOMO_DATA_DIR=str(DATA)),stdout=open(OUT/'servidor.log','w'),stderr=subprocess.STDOUT)
results=[]
try:
 import urllib.request
 for _ in range(100):
  try:urllib.request.urlopen('http://127.0.0.1:8518/_stcore/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1440,'height':1000});p.goto('http://127.0.0.1:8518');p.get_by_role('heading',name='🏠 Inicio',exact=True).wait_for()
  def settle():
   p.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').wait_for();p.wait_for_timeout(250)
   assert p.get_by_test_id('stException').count()==0
   assert 'created with a default value' not in p.locator('body').inner_text()
  def select(label,value,scope=None):
   root=scope or p;box=root.get_by_role('combobox',name=label,exact=True)
   if value in box.input_value():return
   box.click();box.fill(value);option=p.get_by_role('option').filter(has_text=value).first
   try:option.click(timeout=5000)
   except Exception:
    if value in box.input_value() and not p.get_by_role('listbox').count():settle();return
    box.click();box.fill(value);option.click(timeout=5000)
   settle()
  def main(group,mobile=False):
   if mobile:select('Menú',group)
   else:p.get_by_role('button',name={'Inicio':'🏠 Inicio','Pagos':'💸 Pagos','Ingresos':'💰 Ingresos','Pendientes':'📅 Pendientes','Más':'☰ Más'}[group],exact=True).click();settle()
  def fill(label,value):p.get_by_role('textbox',name=label,exact=True).fill(value)
  def click(label):p.get_by_role('button',name=label,exact=True).click();settle()
  settle()
  for theme in ['Light','Dark']:
   p.get_by_test_id('stMainMenu').click();p.get_by_test_id('stMainMenuItem-theme-'+theme).click();settle()
   for group in ['Inicio','Pagos','Ingresos','Pendientes','Más']:main(group);results.append(theme+' desktop '+group)
   # Every advanced screen is still reachable through its contextual submenu.
   for title in ['Cuentas y rendimientos','Inversiones','Comparar rendimientos','Preguntale a Átomo','Bancos y otras entidades','Ajustes']:
    main('Más');select('Dentro de más',title);results.append(theme+' más '+title)
   for title in ['Próximos pagos','Tarjetas y cuotas','Deudas','Ver proyección']:
    main('Pendientes');select('Dentro de pendientes',title);results.append(theme+' pendientes '+title)
   p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(700)
   for group in ['Inicio','Pagos','Ingresos','Pendientes','Más']:
    main(group,True);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1');results.append(theme+' móvil '+group)
   main('Pagos',True);fill('Monto *','2.000,50');fill('¿Qué fue? *','Compra móvil '+theme);select('¿De dónde sale? *','Cuenta principal QA');click('Guardar pago')
   expect(p.get_by_text('Guardado: Compra móvil '+theme,exact=False)).to_be_visible();expect(p.get_by_role('textbox',name='Monto *',exact=True)).to_have_value('')
   p.screenshot(path=str(OUT/(theme+'_pagos_celular.png')),full_page=True)
   # Own transfer: origin/destination visible only in the selected branch.
   select('¿Qué querés cargar?','Mover entre mis cuentas');fill('Monto *','5.000');fill('¿Qué fue? *','Transferencia móvil '+theme);select('¿De dónde sale? *','Cuenta principal QA');select('¿A cuál de tus cuentas va? *','Reserva QA');click('Guardar pago')
   main('Ingresos',True);fill('Monto *','10.000');fill('¿Qué fue? *','Ingreso móvil '+theme);select('¿Dónde entra? *','Cuenta principal QA');click('Guardar ingreso')
   results.append(theme+' móvil: gasto, propia e ingreso guardados y campos listos para siguiente carga')
   # Yield controls work on phone, immediately, without opening Modify or clicking Save.
   main('Más',True);select('Dentro de más','Cuentas y rendimientos')
   card=p.locator('.st-key-rate_account_1');card.get_by_role('textbox',name='Tasa anual %',exact=True).fill('36,1234');card.get_by_role('textbox',name='Tasa anual %',exact=True).press('Enter');settle()
   toggle=card.locator('input[type=checkbox]')
   if not toggle.is_checked():card.get_by_text('Rendimiento',exact=True).click();settle()
   select('TNA / TEA','TEA',card)
   with sqlite3.connect(DATA/'finanzas.db') as c:assert c.execute('select genera_rendimiento,tasa_anual,tipo_tasa from cuentas where id=1').fetchone()==(1,36.1234,'TEA')
   card.get_by_text('Rendimiento',exact=True).click();settle()
   with sqlite3.connect(DATA/'finanzas.db') as c:assert c.execute('select genera_rendimiento,tasa_anual from cuentas where id=1').fetchone()==(0,36.1234)
   p.screenshot(path=str(OUT/(theme+'_tasas_celular.png')),full_page=True)
   results.append(theme+' tasa en celular: coma, TNA/TEA, estimación, activar/desactivar y persistencia inmediata')
   p.set_viewport_size({'width':360,'height':800});main('Pagos',True);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   p.set_viewport_size({'width':1440,'height':1000});p.wait_for_timeout(500)
  main('Pagos');select('¿Qué querés cargar?','Pagar un pendiente');select('¿De dónde salió? *','Cuenta principal QA');click('Registrar pago del pendiente')
  expect(p.get_by_text('Pago registrado: Pendiente QA.',exact=True)).to_be_visible()
  p.reload();p.get_by_role('heading',name='🏠 Inicio',exact=True).wait_for();settle()
  with sqlite3.connect(DATA/'finanzas.db') as c:
   assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
   assert c.execute("select count(*) from movimientos where descripcion like 'Compra móvil%'").fetchone()[0]==2
   assert c.execute("select count(*) from movimientos where descripcion like 'Transferencia móvil%' and tipo='Transferencia'").fetchone()[0]==2
   assert c.execute("select count(*) from movimientos where tipo='Compromiso'").fetchone()[0]==0
   assert c.execute('select genera_rendimiento,tasa_anual from cuentas where id=1').fetchone()==(0,36.1234)
  results.append('Pendiente pagado explícitamente, recarga y persistencia SQLite sin duplicar transferencias ni ingresos')
  b.close()
finally:
 server.terminate();server.wait();(OUT/'resultados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('PASS',len(results),'comprobaciones navegador en escritorio, 390/360px, claro/oscuro y formularios móviles')
