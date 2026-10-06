"""Snapshots SQLite consistentes e importación inicial del espacio privado."""
import os
import sqlite3
import tempfile
from pathlib import Path
from core.clock import local_now
from core.database import DB_LOCK, con, init_db

TABLES = {'movimientos','saldos_iniciales','periodos_financieros','instituciones','cuentas','tarjetas','deudas','posiciones','alternativas_rendimiento','config','referencias_importadas'}
RECORD_TABLES = TABLES - {'instituciones','config','periodos_financieros'}
MAX_DATABASE_BYTES = 32 * 1024 * 1024
_REMOTE_BACKUP_CHECKED = set()


def snapshot(db):
    """No copiar el archivo mientras SQLite escribe: usar su API de backup."""
    with DB_LOCK, tempfile.TemporaryDirectory(prefix='atomo-snapshot-') as folder:
        target = Path(folder)/'finanzas.db'
        with con(db) as source, sqlite3.connect(target) as dest:
            from core.backend import remote_target
            if remote_target(db):
                # Una transacción remota consistente; exportar solo tablas financieras.
                schemas = dict(source.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall())
                for table in sorted(TABLES):
                    sql = schemas[table]
                    dest.execute(sql)
                    cursor = source.execute(f'SELECT * FROM "{table}"')
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    marks = ','.join('?' for _ in columns)
                    dest.executemany(f'INSERT INTO "{table}" VALUES ({marks})', rows)
                names = tuple(sorted(TABLES))
                marks = ','.join('?' for _ in names)
                dest.execute('DELETE FROM sqlite_sequence')
                dest.executemany('INSERT INTO sqlite_sequence(name,seq) VALUES (?,?)', source.execute(f'SELECT name,seq FROM sqlite_sequence WHERE name IN ({marks})', names).fetchall())
            else:
                source.backup(dest)
        return target.read_bytes()


def daily_backup(db, backup_dir, force=False):
    db, backup_dir = Path(db), Path(backup_dir)
    from core.backend import remote_target
    if remote_target(db):
        return _remote_daily_backup(db, force)
    if not db.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    name = 'finanzas_diario_' + local_now().strftime('%Y%m%d') + '.db'
    target = backup_dir/name
    with DB_LOCK:
        if target.exists() and not force:
            return target
        content = snapshot(db)
        fd, path = tempfile.mkstemp(prefix='.backup-', dir=backup_dir)
        try:
            with os.fdopen(fd,'wb') as file:
                file.write(content)
            os.replace(path, target)
        finally:
            Path(path).unlink(missing_ok=True)
        for old in sorted(backup_dir.glob('finanzas_diario_*.db'), reverse=True)[30:]:
            old.unlink()
    return target


def _remote_daily_backup(db, force=False):
    """Respaldos remotos: como máximo una comprobación por proceso y por día."""
    stamp = local_now().strftime('%Y%m%d')
    from core.backend import remote_settings
    key = (remote_settings()[0], stamp)
    if not force and key in _REMOTE_BACKUP_CHECKED:
        return stamp

    with con(db) as c:
        c.execute('CREATE TABLE IF NOT EXISTS atomo_backups(fecha TEXT, parte INTEGER, contenido BLOB NOT NULL, PRIMARY KEY(fecha,parte))')
        if not force and c.execute('SELECT 1 FROM atomo_backups WHERE fecha=? LIMIT 1', (stamp,)).fetchone():
            _REMOTE_BACKUP_CHECKED.add(key)
            return stamp
    content = snapshot(db)
    with con(db) as c:
        c.execute('DELETE FROM atomo_backups WHERE fecha=?', (stamp,))
        for part, start in enumerate(range(0, len(content), 256*1024)):
            c.execute('INSERT INTO atomo_backups VALUES (?,?,?)', (stamp, part, content[start:start+256*1024]))
        c.execute('DELETE FROM atomo_backups WHERE fecha NOT IN (SELECT DISTINCT fecha FROM atomo_backups ORDER BY fecha DESC LIMIT 30)')
    _REMOTE_BACKUP_CHECKED.add(key)
    return stamp


def has_records(db):
    with con(db) as c:
        return any(c.execute(f'SELECT EXISTS(SELECT 1 FROM {table})').fetchone()[0] for table in RECORD_TABLES)


def validate_database(content):
    if not (0 < len(content) <= MAX_DATABASE_BYTES) or not content.startswith(b'SQLite format 3\0'):
        raise ValueError('Elegí una base SQLite de Átomo de hasta 32 MB.')
    with tempfile.TemporaryDirectory(prefix='atomo-import-review-') as folder:
        path = Path(folder)/'revision.db'
        path.write_bytes(content)
        try:
            with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
                c.execute('PRAGMA trusted_schema=OFF')
                objects = c.execute('SELECT type,name,sql FROM sqlite_master').fetchall()
                for kind,name,sql in objects:
                    if name.startswith('sqlite_'):
                        continue
                    if kind != 'table' or name not in TABLES or 'virtual' in (sql or '').lower():
                        raise ValueError('La base contiene estructuras ajenas a Átomo. No se importó.')
                existing = {name for kind,name,sql in objects if kind=='table'}
                if not {'movimientos','cuentas','config'} <= existing:
                    raise ValueError('Esta base no corresponde a la versión de Átomo.')
                if c.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                    raise ValueError('La base tiene errores de integridad. No se importó.')
                counts = {table:c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in sorted(existing & TABLES)}
            # Las migraciones se prueban sobre una copia antes de tocar la base real.
            init_db(path)
            with sqlite3.connect(path) as c:
                if c.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                    raise ValueError('No pude validar la base actualizada.')
            return counts
        except sqlite3.Error as e:
            raise ValueError('No pude validar esta base SQLite. No se importó.') from e


def import_available(db):
    from core.security import security_db
    with security_db() as c:
        done = c.execute("SELECT 1 FROM acceso_meta WHERE clave='importacion_inicial'").fetchone()
    return not done and not has_records(db)


def import_initial(content, db):
    """Solo una primera carga; nunca reemplaza movimientos existentes."""
    from core.security import security_db
    validate_database(content)
    from core.backend import remote_target
    if remote_target(db):
        return _remote_import_initial(content, db)
    with DB_LOCK:
        if not import_available(db):
            raise ValueError('Ya hay datos guardados. La importación inicial está bloqueada para conservarlos.')
        with tempfile.TemporaryDirectory(prefix='atomo-import-', dir=Path(db).parent) as folder:
            path = Path(folder)/'finanzas.db'
            path.write_bytes(content)
            init_db(path)
            path.chmod(0o600)
            os.replace(path, db)
        with security_db() as c:
            c.execute("INSERT INTO acceso_meta VALUES ('importacion_inicial',?)", (local_now().isoformat(),))
        from core.config import BACKUP_DIR
        daily_backup(db,BACKUP_DIR,force=True)


def _remote_import_initial(content, db):
    with DB_LOCK, tempfile.TemporaryDirectory(prefix='atomo-cloud-import-') as folder:
        path = Path(folder)/'finanzas.db'
        path.write_bytes(content)
        init_db(path)
        with sqlite3.connect(path) as src, con(db) as dest:
            done = dest.execute("SELECT 1 FROM acceso_meta WHERE clave='importacion_inicial'").fetchone()
            present = any(dest.execute(f'SELECT EXISTS(SELECT 1 FROM {table})').fetchone()[0] for table in RECORD_TABLES)
            if done or present:
                raise ValueError('Ya hay datos guardados. La importación inicial está bloqueada para conservarlos.')
            def quote(value):
                if isinstance(value, str) and '\x00' in value:
                    # quote() de SQLite corta TEXT en el primer NUL; conservarlo entero.
                    return "CAST(X'"+value.encode('utf-8').hex()+"' AS TEXT)"
                return src.execute('SELECT quote(?)', (value,)).fetchone()[0]
            statements = []
            # Borrar hijos antes de instituciones; libSQL sí aplica claves foráneas.
            for table in sorted(TABLES - {'instituciones'}):
                statements.append(f'DELETE FROM "{table}"')
            statements.append('DELETE FROM instituciones')
            ordered = ['instituciones'] + sorted(TABLES - {'instituciones'})
            for table in ordered:
                cursor = src.execute(f'SELECT * FROM "{table}"')
                columns = [col[0] for col in cursor.description]
                names = ','.join('"'+col.replace('"','""')+'"' for col in columns)
                rows = cursor.fetchall()
                for start in range(0, len(rows), 100):
                    batch = rows[start:start+100]
                    values = ','.join('('+','.join(quote(value) for value in row)+')' for row in batch)
                    statements.append(f'INSERT INTO "{table}" ({names}) VALUES {values}')
            # No importar ni borrar propietario, intentos, metadatos o respaldos.
            for table in sorted(TABLES):
                statements.append(f'DELETE FROM sqlite_sequence WHERE name={quote(table)}')
            for name, seq in src.execute('SELECT name,seq FROM sqlite_sequence').fetchall():
                if name in TABLES:
                    statements.append(f'INSERT INTO sqlite_sequence VALUES ({quote(name)},{quote(seq)})')
            statements.append(f"INSERT INTO acceso_meta VALUES ('importacion_inicial',{quote(local_now().isoformat())})")
            dest.run_script(statements)
    # La importación ya quedó confirmada, aun si el respaldo posterior falla.
    from core.config import BACKUP_DIR
    try:
        daily_backup(db, BACKUP_DIR, force=True)
    except sqlite3.Error:
        pass


def render_initial_import(db):
    import streamlit as st
    if not import_available(db):
        return
    with st.expander('Traer mis datos de la PC', expanded=True):
        st.write('Para continuar tu historial, elegí finanzas.db de la carpeta datos de tu Átomo local. Cerrá primero la aplicación de la PC.')
        upload = st.file_uploader('Tu base de Átomo', type=['db'], max_upload_size=32, key='initial_database')
        if upload:
            try:
                counts = validate_database(upload.getvalue())
                st.write('Encontré: ' + ', '.join(f'{counts.get(name,0)} {name}' for name in ['cuentas','movimientos','tarjetas','deudas','posiciones']) + '.')
                if st.button('Importar mi historial', key='import_initial_confirm', type='primary'):
                    import_initial(upload.getvalue(), db)
                    st.session_state._import_success = True
                    st.rerun()
            except ValueError as e:
                st.error(str(e))
            except sqlite3.Error:
                st.error('No pude confirmar la importación. Revisá la conexión y el historial antes de intentar de nuevo.')


def render_backups(db):
    import streamlit as st
    from core.config import BACKUP_DIR
    with st.expander('Mis respaldos'):
        st.caption('Copia completa de tus cuentas, movimientos, tarjetas e inversiones. Guardala fuera del servidor.')
        if st.button('Preparar copia actual', key='prepare_snapshot'):
            st.session_state._snapshot_bytes = snapshot(db)
            st.session_state._snapshot_stamp = local_now().strftime('%Y-%m-%d_%H-%M-%S')
        if st.session_state.get('_snapshot_bytes'):
            st.download_button('Descargar mi copia', st.session_state._snapshot_bytes, file_name='atomo_'+st.session_state._snapshot_stamp+'.db', mime='application/octet-stream', key='download_snapshot', on_click='ignore')
            st.caption('Esta copia refleja el momento en que presionaste Preparar copia actual.')
        from core.backend import remote_target
        if remote_target(db):
            with con(db) as c:
                last = c.execute('SELECT MAX(fecha) FROM atomo_backups').fetchone()[0]
            if last:
                st.caption('Último respaldo diario: '+last+'. Se conservan hasta 30 días con actividad en la base externa. Descargá también una copia fuera del alojamiento.')
            return
        files = sorted(BACKUP_DIR.glob('finanzas_diario_*.db'),reverse=True)
        if files:
            st.caption('Último respaldo diario: '+files[0].stem.removeprefix('finanzas_diario_')+'. Se conservan hasta 30 días en el disco del servidor.')
