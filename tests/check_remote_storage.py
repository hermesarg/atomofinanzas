"""QA con libsql 0.1.11 y sqld real por HTTP; no mocks del driver."""
import os
import sys
import secrets
import sqlite3
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from remote_server import remote_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
with remote_server():
    os.environ['ATOMO_DATA_DIR'] = tempfile.mkdtemp(prefix='atomo-free-qa-')
    os.environ['ATOMO_SETUP_TOKEN'] = secrets.token_urlsafe(40)
    from core.config import LIVE_DB, DATA_DIR, BACKUP_DIR
    from core.security import owner, create_owner, authenticate, security_db, security_path
    from core.database import init_db, con, insert_movement, balances_df
    from core.clock import today
    from core.storage import snapshot, import_initial, import_available, daily_backup, validate_database, TABLES
    from core.finance import period_summary
    from core.backend import remote_settings
    assert owner() is None
    result = create_owner(os.environ['ATOMO_SETUP_TOKEN'], 'qauser', 'Contraseña ficticia QA 2026', 'Contraseña ficticia QA 2026')
    assert result[0] == 'qauser'
    assert authenticate('qauser', 'Contraseña ficticia QA 2026')[0] == result
    init_db(LIVE_DB)
    assert not LIVE_DB.exists() and not security_path().exists()
    assert import_available(LIVE_DB)
    fixture = DATA_DIR/'fixture.db'
    init_db(fixture)
    with con(fixture) as c:
        for name in ['Principal QA', 'Reserva QA']:
            c.execute("INSERT INTO cuentas(institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES (6,?,'Otra','ARS',100000,?,?)", (name, today().isoformat(), today().isoformat()))
    insert_movement(today(), 'Compromiso', 'Pendiente QA', 'Otros', 1000, db=fixture)
    source = fixture.read_bytes()
    # Importación fallida a mitad del proceso debe revertir filas y marcador juntos.
    import core.storage as storage
    real_con = storage.con
    from contextlib import contextmanager
    class BrokenImport:
        def __init__(self, connection): self.connection=connection
        def execute(self, sql, params=()):
            return self.connection.execute(sql, params)
        def run_script(self, statements):
            steps=list(statements)
            i=next(i for i,sql in enumerate(steps) if sql.startswith('INSERT INTO "movimientos"'))
            steps.insert(i,'INSERT INTO tabla_inexistente_qa VALUES (1)')
            self.connection.run_script(steps)
    @contextmanager
    def failing_con(db):
        with real_con(db) as c: yield BrokenImport(c)
    storage.con = failing_con
    try:
        import_initial(source, LIVE_DB)
        raise AssertionError('Debe fallar la importación artificial')
    except sqlite3.OperationalError:
        pass
    finally:
        storage.con = real_con
    assert import_available(LIVE_DB)
    import_initial(source, LIVE_DB)
    assert not import_available(LIVE_DB)
    assert owner()[0] == 'qauser'
    for table in sorted(TABLES):
        with con(LIVE_DB) as a, sqlite3.connect(fixture) as b:
            assert a.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall() == b.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall(), table
    try:
        import_initial(source, LIVE_DB)
        raise AssertionError('No debe reemplazar un historial existente')
    except ValueError:
        pass
    print('PASS importación atómica remota, rollback, bloqueo de reemplazo y preservación del propietario')
    insert_movement(today(), 'Ingreso', 'Ingreso QA', 'Otros', 10000, destino=1, db=LIVE_DB)
    insert_movement(today(), 'Gasto', 'Gasto QA', 'Otros', 2000.5, origen=1, db=LIVE_DB)
    insert_movement(today(), 'Transferencia', 'Propia QA', 'Transferencia', 5000, origen=1, destino=2, db=LIVE_DB)
    summary, _ = period_summary(today().strftime('%Y-%m'), LIVE_DB)
    assert summary['gastos']==2000.5 and summary['ingresos']==10000
    assert balances_df(LIVE_DB).saldo.tolist()==[102999.5,105000]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: insert_movement(today(),'Ingreso',f'Concurrente {i}','Otros',1,destino=1,db=LIVE_DB),range(8)))
    assert balances_df(LIVE_DB).saldo.tolist()==[103007.5,105000]
    before=balances_df(LIVE_DB).saldo.tolist()
    try:
        with con(LIVE_DB) as c:
            c.execute('UPDATE cuentas SET saldo_base=0')
            raise ValueError('Rollback QA')
    except ValueError:
        pass
    assert balances_df(LIVE_DB).saldo.tolist()==before
    print('PASS ingresos/gastos/transferencias, simultaneidad y rollback con driver remoto real')
    content=snapshot(LIVE_DB); validate_database(content)
    backup=DATA_DIR/'backup.db';backup.write_bytes(content)
    with sqlite3.connect(backup) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert names == TABLES|{'sqlite_sequence'}
        assert c.execute('SELECT COUNT(*) FROM movimientos').fetchone()[0]==12
    stamp=daily_backup(LIVE_DB,BACKUP_DIR,force=True)
    with con(LIVE_DB) as c:
        persisted=b''.join(r[0] for r in c.execute('SELECT contenido FROM atomo_backups WHERE fecha=? ORDER BY parte',(stamp,)).fetchall())
    assert persisted==snapshot(LIVE_DB)
    # Borrar TODO el almacenamiento del servidor web simula reemplazo de instancia.
    shutil.rmtree(DATA_DIR); DATA_DIR.mkdir(); BACKUP_DIR.mkdir()
    assert owner()[0]=='qauser' and balances_df(LIVE_DB).saldo.tolist()==before
    assert authenticate('qauser','Contraseña ficticia QA 2026')[0]==result
    assert not LIVE_DB.exists() and not security_path().exists()
    print('PASS snapshot SQLite sin accesos, respaldo remoto y eliminación total del disco web sin pérdida')
    original_url=os.environ['TURSO_DATABASE_URL']
    os.environ['TURSO_DATABASE_URL']='http://127.0.0.1:1'
    try:
        with con(LIVE_DB) as c: c.execute('SELECT 1')
        raise AssertionError('No debe usar fallback local')
    except sqlite3.OperationalError as e:
        assert 'synthetic-test-only' not in str(e)
    finally:
        os.environ['TURSO_DATABASE_URL']=original_url
    assert not LIVE_DB.exists()
    os.environ['TURSO_AUTH_TOKEN']=''
    try: remote_settings(); raise AssertionError('Credenciales obligatorias')
    except sqlite3.OperationalError: pass
    print('PASS desconexión bloqueada, ningún fallback local y errores sin secretos')
