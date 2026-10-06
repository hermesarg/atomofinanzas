"""Acceso de un único propietario. La base financiera nunca es compartida entre usuarios."""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
_SECURITY_INIT_LOCK = RLock()
_SECURITY_INITIALIZED = set()

ITERATIONS = 600_000
SESSION_SECONDS = 12 * 3600


def web_private():
    from core.backend import remote_mode
    return remote_mode() or os.getenv('ATOMO_WEB_PRIVATE') == '1' or os.getenv('RENDER') == 'true'


def security_path():
    from core.config import DATA_DIR
    return DATA_DIR / 'acceso.db'


@contextmanager
def security_db():
    p = security_path()
    from core.backend import connect
    c = connect(p)
    try:
        from core.backend import remote_target, remote_settings
        key = remote_settings()[0] if remote_target(p) else None
        with _SECURITY_INIT_LOCK:
            if key is None or key not in _SECURITY_INITIALIZED:
                c.execute('CREATE TABLE IF NOT EXISTS propietario(id INTEGER PRIMARY KEY CHECK(id=1), usuario TEXT NOT NULL, salt BLOB NOT NULL, digest BLOB NOT NULL, version TEXT NOT NULL)')
                c.execute('CREATE TABLE IF NOT EXISTS intentos(fecha REAL NOT NULL)')
                c.execute('CREATE TABLE IF NOT EXISTS acceso_meta(clave TEXT PRIMARY KEY, valor TEXT NOT NULL)')
                c.commit()
                if key is not None:
                    _SECURITY_INITIALIZED.add(key)
        with c:
            yield c
    finally:
        c.close()
    try:
        p.chmod(0o600)
    except OSError:
        pass


def owner():
    with security_db() as c:
        return c.execute('SELECT usuario, salt, digest, version FROM propietario WHERE id=1').fetchone()


def password_digest(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)


def claim_attempt(c, now):
    """Límite global persistente: otras pestañas no reinician los intentos."""
    c.execute('BEGIN IMMEDIATE')
    c.execute('DELETE FROM intentos WHERE fecha<?', (now-600,))
    short = c.execute('SELECT COUNT(*) FROM intentos WHERE fecha>?', (now-60,)).fetchone()[0]
    long = c.execute('SELECT COUNT(*) FROM intentos').fetchone()[0]
    if short >= 5 or long >= 20:
        return False
    c.execute('INSERT INTO intentos(fecha) VALUES (?)', (now,))
    return True


def create_owner(token, username, password, confirmation):
    expected = os.getenv('ATOMO_SETUP_TOKEN', '')
    if len(expected) < 32:
        raise ValueError('Falta configurar el acceso inicial en el servidor.')
    with security_db() as c:
        if not claim_attempt(c, time.time()):
            raise ValueError('Demasiados intentos. Esperá unos minutos antes de volver a probar.')
        if c.execute('SELECT 1 FROM propietario').fetchone():
            raise ValueError('El acceso ya está configurado.')
        if not hmac.compare_digest(token.encode(), expected.encode()):
            return None
        if not re.fullmatch(r'[A-Za-z0-9_.@-]{3,80}', username):
            raise ValueError('Usá un usuario de 3 a 80 caracteres, sin espacios.')
        if len(password) < 12 or len(password) > 256 or password != confirmation:
            raise ValueError('La contraseña debe tener entre 12 y 256 caracteres y coincidir en ambos campos.')
        salt = secrets.token_bytes(32)
        version = secrets.token_hex(24)
        c.execute('INSERT INTO propietario VALUES (1,?,?,?,?)', (username, salt, password_digest(password, salt), version))
        c.execute('DELETE FROM intentos')
    return username, version


def authenticate(username, password):
    with security_db() as c:
        if not claim_attempt(c, time.time()):
            return None, 'Demasiados intentos. Esperá unos minutos antes de volver a probar.'
        row = c.execute('SELECT usuario,salt,digest,version FROM propietario WHERE id=1').fetchone()
        if not row:
            return None, 'Usuario o contraseña incorrectos.'
        # El cálculo se ejecuta también para un usuario equivocado.
        digest = password_digest(password[:257], row[1])
        ok = hmac.compare_digest(digest, row[2]) and hmac.compare_digest(username.encode(), row[0].encode()) and len(password) <= 256
        if ok:
            c.execute('DELETE FROM intentos')
            return (row[0], row[3]), None
    return None, 'Usuario o contraseña incorrectos.'

def reset_owner_password(recovery_code, username, password, confirmation):
    """Recupera el único acceso usando el código privado del alojamiento."""
    expected = os.getenv('ATOMO_SETUP_TOKEN', '')
    if len(expected) < 32:
        raise ValueError('Falta configurar el código de recuperación en el servidor.')
    if len(password) < 12 or len(password) > 256 or password != confirmation:
        raise ValueError('La contraseña debe tener entre 12 y 256 caracteres y coincidir en ambos campos.')
    with security_db() as c:
        if not claim_attempt(c, time.time()):
            raise ValueError('Demasiados intentos. Esperá unos minutos antes de volver a probar.')
        row = c.execute('SELECT usuario FROM propietario WHERE id=1').fetchone()
        if not row:
            return None
        if not hmac.compare_digest(username.strip().encode(), row[0].encode()):
            return None
        if not hmac.compare_digest(recovery_code.encode(), expected.encode()):
            return None
        salt = secrets.token_bytes(32)
        version = secrets.token_hex(24)
        c.execute(
            'UPDATE propietario SET salt=?,digest=?,version=? WHERE id=1',
            (salt, password_digest(password, salt), version),
        )
        c.execute('DELETE FROM intentos')
    return username.strip(), version


def valid_session(state, now=None):
    record = state.get('_private_access')
    if not record:
        return False
    now = time.time() if now is None else now
    if not (record.get('user') and record.get('version') and 0 <= now-record.get('issued', 0) < SESSION_SECONDS):
        return False

    # Turso es remoto: no consultar propietario en cada SELECT de la app.
    # Revalidar contra la base una vez por minuto mantiene revocación razonable
    # sin multiplicar la latencia de cada interacción.
    checked = float(state.get('_private_access_checked_at', 0) or 0)
    if 0 <= now - checked < 60:
        return True
    row = owner()
    ok = bool(row and record.get('user') == row[0] and record.get('version') == row[3])
    if ok:
        state['_private_access_checked_at'] = now
    return ok


def logout():
    import streamlit as st
    for key in list(st.session_state):
        del st.session_state[key]


def require_private_access():
    import streamlit as st
    from core.config import ATOMO_LOGO
    if not web_private():
        return
    if st.session_state.pop('_clear_access_form', False):
        for key in ['access_user','access_password','setup_token','setup_user','setup_password','setup_confirmation','reset_token','reset_user','reset_password','reset_confirmation']:
            st.session_state.pop(key, None)
    if valid_session(st.session_state):
        return
    st.session_state.pop('_private_access', None)
    if ATOMO_LOGO.exists():
        st.image(str(ATOMO_LOGO), width=72)
    st.title('Átomo Finanzas')
    st.caption('Las cuentas las hago yo. Las decisiones, vos.')
    if not owner():
        if len(os.getenv('ATOMO_SETUP_TOKEN', '')) < 32:
            st.error('El acceso privado todavía no está configurado. Los datos permanecen bloqueados.')
            st.stop()
        st.subheader('Activá tu acceso privado')
        st.write('Una sola vez: usá el código de activación del alojamiento y elegí tu usuario y contraseña.')
        with st.form('private_setup'):
            token = st.text_input('Código de activación', type='password', key='setup_token')
            user = st.text_input('Elegí tu usuario', key='setup_user', max_chars=80)
            password = st.text_input('Elegí tu contraseña', type='password', key='setup_password', help='Al menos 12 caracteres.')
            confirm = st.text_input('Repetí tu contraseña', type='password', key='setup_confirmation')
            submit = st.form_submit_button('Crear mi acceso', width='stretch')
        if submit:
            try:
                result = create_owner(token, user.strip(), password, confirm)
                if result is None:
                    st.error('Código de activación incorrecto.')
                else:
                    st.session_state._private_access = {'user':result[0], 'version':result[1], 'issued':time.time()}
                    st.session_state._clear_access_form = True
                    st.rerun()
            except ValueError as e:
                st.error(str(e))
    else:
        st.subheader('Entrá a tu espacio')
        with st.form('private_login'):
            user = st.text_input('Usuario', key='access_user', max_chars=80)
            password = st.text_input('Contraseña', type='password', key='access_password')
            submit = st.form_submit_button('Entrar', width='stretch')
        if submit:
            result, error = authenticate(user.strip(), password)
            if result:
                st.session_state._private_access = {'user':result[0], 'version':result[1], 'issued':time.time()}
                st.session_state._clear_access_form = True
                st.rerun()
            else:
                st.error(error)

        with st.expander('Olvidé mi contraseña'):
            st.caption('Usá el código de recuperación que guardaste en Secrets. Tus datos financieros no se modifican.')
            with st.form('private_reset'):
                recovery = st.text_input('Código de recuperación', type='password', key='reset_token')
                reset_user = st.text_input('Tu usuario', key='reset_user', max_chars=80)
                reset_password = st.text_input('Nueva contraseña', type='password', key='reset_password')
                reset_confirmation = st.text_input('Repetí la nueva contraseña', type='password', key='reset_confirmation')
                reset_submit = st.form_submit_button('Cambiar contraseña', width='stretch')
            if reset_submit:
                try:
                    result = reset_owner_password(recovery, reset_user, reset_password, reset_confirmation)
                    if result is None:
                        st.error('Usuario o código de recuperación incorrectos.')
                    else:
                        now = time.time()
                        st.session_state._private_access = {'user':result[0], 'version':result[1], 'issued':now}
                        st.session_state._private_access_checked_at = now
                        st.session_state._clear_access_form = True
                        st.rerun()
                except ValueError as e:
                    st.error(str(e))
    st.caption('Espacio privado de un único propietario. No hay registro público.')
    st.stop()
