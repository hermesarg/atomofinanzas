"""Navegador real del servidor privado: setup, importación, cargas, backups y reinicio."""
import os,sys,tempfile,subprocess,time,sqlite3,json,secrets,shutil,atexit
from remote_server import remote_server
_remote=remote_server();_remote.__enter__();atexit.register(_remote.__exit__,None,None,None)
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1];DATA=Path(tempfile.mkdtemp(prefix='atomo-web-browser-'))
os.environ['ATOMO_DATA_DIR']=str(DATA);os.environ['ATOMO_WEB_PRIVATE']='1'
TOKEN=secrets.token_urlsafe(40);PASSWORD='Contraseña ficticia de QA 2026'
os.environ['ATOMO_SETUP_TOKEN']=TOKEN;os.environ['PORT']='8523'
sys.path.insert(0,str(ROOT))
from core.database import init_db,con,insert_movement,balances_df
from core.clock import today
from core.config import LIVE_DB
OUT=ROOT/'docs/qa_gratis';OUT.mkdir(parents=True,exist_ok=True)
fixture=DATA/'fixture.db';init_db(fixture)
with con(fixture) as c:
 for name in ['Cuenta principal QA','Reserva QA']:
  c.execute("INSERT INTO cuentas(institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES (6,?,'Otra','ARS',100000,?,?)",(name,today().isoformat(),today().isoformat()))
insert_movement(today(),'Compromiso','Pendiente privado QA','Otros',1000,db=fixture)
log=open(OUT/'servidor.log','w');server=None;results=[]
def start():
 global server
 server=subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT/'app_cloud.py'),'--server.address','127.0.0.1','--server.port','8523','--server.fileWatcherType','none','--browser.gatherUsageStats','false'],cwd=ROOT,env=dict(os.environ),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 import urllib.request
 for _ in range(150):
  if server.poll() is not None:raise AssertionError('No inició el servidor')
  try:urllib.request.urlopen('http://127.0.0.1:8523/_stcore/health');return
  except Exception:time.sleep(.1)
 raise AssertionError('Timeout de inicio')
def stop():
 import signal
 if server and server.poll() is None:
  os.killpg(server.pid,signal.SIGTERM)
  server.wait(timeout=15)
try:
 start()
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True);p=context.new_page()
  p.goto('http://127.0.0.1:8523')
  def settle():
   p.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').wait_for()
   p.wait_for_timeout(180);assert not p.get_by_test_id('stException').count()
  def fill(label,value):p.get_by_role('textbox',name=label,exact=True).fill(value)
  def click(label):p.get_by_role('button',name=label,exact=True).click();settle()
  def select(label,value):
   box=p.get_by_role('combobox',name=label,exact=True);box.click();box.fill(value)
   p.get_by_role('option').filter(has_text=value).first.click();settle()
  def login():
   p.get_by_role('textbox',name='Usuario',exact=True).wait_for();fill('Usuario','qauser');fill('Contraseña',PASSWORD);click('Entrar')
   p.get_by_role('heading',name='🏠 Inicio',exact=True).wait_for()
  p.get_by_role('heading',name='Activá tu acceso privado').wait_for();settle()
  assert not LIVE_DB.exists()
  assert 'Cuenta principal QA' not in p.locator('body').inner_text()
  fill('Código de activación','incorrecto');fill('Elegí tu usuario','qauser');fill('Elegí tu contraseña',PASSWORD);fill('Repetí tu contraseña',PASSWORD);click('Crear mi acceso')
  expect(p.get_by_text('Código de activación incorrecto.',exact=True)).to_be_visible()
  fill('Código de activación',TOKEN);click('Crear mi acceso');p.get_by_role('heading',name='🏠 Inicio',exact=True).wait_for();settle()
  assert TOKEN not in p.locator('body').inner_text();results.append('Alta privada con token válido; inválido bloqueado; sin SQLite financiero antes de autenticar')
  p.locator('input[type=file]').set_input_files(str(fixture));settle()
  expect(p.get_by_text('Encontré:',exact=False)).to_be_visible();click('Importar mi historial')
  expect(p.get_by_text('Tu historial quedó importado.',exact=False)).to_be_visible(timeout=10000)
  assert not p.locator('input[type=file]').count();results.append('Importación inicial revisada; no se vuelve a ofrecer después de importar')
  guest=browser.new_context(viewport={'width':360,'height':800});g=guest.new_page();g.goto('http://127.0.0.1:8523/?page=Cuentas')
  g.get_by_role('textbox',name='Contraseña',exact=True).wait_for()
  assert 'Cuenta principal QA' not in g.locator('body').inner_text()
  assert not g.get_by_role('combobox',name='Menú',exact=True).count();results.append('Navegador anónimo no ve cuentas, menú, pendientes ni importación')
  p.set_viewport_size({'width':1440,'height':1000});settle()
  for theme in ['Light','Dark']:
   p.emulate_media(color_scheme=theme.lower());settle()
   for group in ['Inicio','Pagos','Ingresos','Pendientes','Más']:
    p.get_by_role('button',name={'Inicio':'🏠 Inicio','Pagos':'💸 Pagos','Ingresos':'💰 Ingresos','Pendientes':'📅 Pendientes','Más':'☰ Más'}[group],exact=True).click();settle()
   for title in ['Cuentas y rendimientos','Inversiones','Comparar rendimientos','Preguntale a Átomo','Bancos y otras entidades','Ajustes']:
    select('Dentro de más',title)
   p.get_by_role('button',name='📅 Pendientes',exact=True).click();settle()
   for title in ['Próximos pagos','Tarjetas y cuotas','Deudas','Ver proyección']:
    select('Dentro de pendientes',title)
   p.get_by_role('button',name='💸 Pagos',exact=True).click();settle();click('Ver historial completo')
   results.append(theme+': todas las pantallas recorridas en Chromium con base externa real')
  p.set_viewport_size({'width':390,'height':844});settle();select('Menú','Ingresos')
  for theme in ['Light','Dark']:
   # En producción se oculta el menú general; cambiar tema mediante preferencias del navegador.
   p.emulate_media(color_scheme=theme.lower());settle()
   select('Menú','Pagos');fill('Monto *','1.200,50');fill('¿Qué fue? *','Pago privado '+theme)
   select('¿De dónde sale? *','Cuenta principal QA');click('Guardar pago')
   expect(p.get_by_text('Guardado: Pago privado '+theme,exact=False)).to_be_visible()
   assert not p.evaluate('document.documentElement.scrollWidth > window.innerWidth')
   p.screenshot(path=str(OUT/(theme+'_pago_privado.png')),full_page=True)
   select('Menú','Ingresos');fill('Monto *','3.000');fill('¿Qué fue? *','Ingreso privado '+theme);select('¿Dónde entra? *','Cuenta principal QA');click('Guardar ingreso')
   select('Menú','Más');select('Dentro de más','Cuentas y rendimientos')
   card=p.locator('.st-key-rate_account_1');card.get_by_role('textbox',name='Tasa anual %',exact=True).fill('36,5');card.get_by_role('textbox',name='Tasa anual %',exact=True).press('Enter');settle()
   with con(LIVE_DB) as c:assert c.execute('SELECT tasa_anual FROM cuentas WHERE id=1').fetchone()[0]==36.5
   results.append(theme+': pago, ingreso y tasa desde celular con persistencia')
  p.set_viewport_size({'width':360,'height':800});settle();assert not p.evaluate('document.documentElement.scrollWidth > window.innerWidth')
  select('Dentro de más','Ajustes');p.get_by_text('Mis respaldos',exact=True).click();click('Preparar copia actual')
  with p.expect_download() as download:p.get_by_role('button',name='Descargar mi copia',exact=True).click()
  saved=DATA/'descarga.db';download.value.save_as(str(saved))
  with sqlite3.connect(saved) as c:
   assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
   assert c.execute('SELECT COUNT(*) FROM movimientos').fetchone()[0]==5
   assert not c.execute("SELECT 1 FROM sqlite_master WHERE name='propietario'").fetchone()
  results.append('Backup descargable íntegro con todos los movimientos y sin datos de acceso')
  # Recarga y reinicio real del proceso: mismas cuentas y movimientos, acceso vuelve a cerrarse.
  before=balances_df(LIVE_DB).saldo.tolist();p.reload();login()
  assert balances_df(LIVE_DB).saldo.tolist()==before
  stop();shutil.rmtree(DATA);DATA.mkdir();(DATA/'backups').mkdir();start();p.reload();login();assert balances_df(LIVE_DB).saldo.tolist()==before
  assert not LIVE_DB.exists();results.append('Eliminación total del disco del servidor web: acceso e historial conservados en la base externa')
  with con(LIVE_DB) as c:assert c.execute('SELECT COUNT(*) FROM movimientos').fetchone()[0]==5
  results.append('Recarga y reinicio del servidor conservan propietario, saldos, movimientos y tasa')
  p.set_viewport_size({'width':1440,'height':1000});settle()
  p.get_by_role('button',name='Cerrar sesión',exact=True).click()
  p.get_by_role('textbox',name='Contraseña',exact=True).wait_for();assert 'Cuenta principal QA' not in p.locator('body').inner_text()
  results.append('Cerrar sesión bloquea de nuevo todas las pantallas')
  browser.close()
 print('PASS '+str(len(results))+' escenarios reales de acceso privado, celular, importación, cargas, backup, recarga y reinicio')
finally:
 stop();log.close();(OUT/'resultados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
