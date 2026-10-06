"""SQLite local o libSQL remoto. Nunca usar una copia local como fallback remoto."""
import os
import sqlite3
import secrets
from pathlib import Path
from urllib.parse import urlsplit


def remote_mode():
    return os.getenv('ATOMO_STORAGE', 'sqlite') == 'turso'


def remote_target(path):
    from core.config import LIVE_DB
    from core.security import security_path
    return remote_mode() and Path(path).resolve() in {LIVE_DB.resolve(), security_path().resolve()}


def remote_settings():
    url = os.getenv('TURSO_DATABASE_URL', '')
    token = os.getenv('TURSO_AUTH_TOKEN', '')
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise sqlite3.OperationalError('La dirección de la base externa no es válida.') from None
    test_http = os.getenv('ATOMO_TEST_HTTP') == '1' and parsed.hostname in {'127.0.0.1', 'localhost'}
    if not url or not token or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise sqlite3.OperationalError('Falta configurar el guardado privado externo.')
    if parsed.scheme not in {'libsql', 'https'} and not (test_http and parsed.scheme == 'http'):
        raise sqlite3.OperationalError('La base externa requiere una conexión segura.')
    if not parsed.hostname or port == 0:
        raise sqlite3.OperationalError('Falta configurar el guardado privado externo.')
    return url, token


def _call(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except (ValueError, RuntimeError) as e:
        # libsql 0.1.11 informa errores de SQL/red mediante ValueError.
        # No filtrar URLs, tokens ni consultas con datos personales a la UI/log.
        if any(word in str(e).lower() for word in ['unique constraint', 'foreign key constraint', 'not null constraint', 'check constraint']):
            raise sqlite3.IntegrityError('El registro no cumple las restricciones de la base.') from None
        raise sqlite3.OperationalError('No pude confirmar la operación en la base externa. Revisá la conexión y el historial antes de volver a cargarla.') from None


class RemoteCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, *args, **kwargs):
        _call(self._cursor.execute, *args, **kwargs)
        return self

    def executemany(self, *args, **kwargs):
        _call(self._cursor.executemany, *args, **kwargs)
        return self

    def fetchone(self):
        return _call(self._cursor.fetchone)

    def fetchall(self):
        return _call(self._cursor.fetchall)

    def fetchmany(self, *args):
        return _call(self._cursor.fetchmany, *args)

    def close(self):
        return _call(self._cursor.close)


class RemoteConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, *args, **kwargs):
        return RemoteCursor(_call(self._connection.execute, *args, **kwargs))

    def executemany(self, *args, **kwargs):
        return RemoteCursor(_call(self._connection.executemany, *args, **kwargs))

    def cursor(self):
        return RemoteCursor(_call(self._connection.cursor))

    def run_script(self, statements):
        """Una ida de red para un lote, con verificación explícita antes del commit.

        libsql 0.1.11 executescript descarta errores del lote. Un marcador final
        permite detectarlos; el contexto revierte toda la transacción al fallar.
        El código llamador debe haber abierto BEGIN IMMEDIATE previamente.
        """
        marker = secrets.token_hex(24)
        self.execute('CREATE TABLE IF NOT EXISTS atomo_batch_marker(id TEXT PRIMARY KEY)')
        script = ';\n'.join(statements) + f";\nINSERT INTO atomo_batch_marker VALUES ('{marker}');"
        _call(self._connection.executescript, script)
        if not self.execute('SELECT 1 FROM atomo_batch_marker WHERE id=?', (marker,)).fetchone():
            raise sqlite3.OperationalError('No pude completar la operación en la base externa. Se revirtió el lote.')
        self.execute('DELETE FROM atomo_batch_marker WHERE id=?', (marker,))

    def commit(self):
        return _call(self._connection.commit)

    def rollback(self):
        return _call(self._connection.rollback)

    def close(self):
        return _call(self._connection.close)

    def __enter__(self):
        return self

    def __exit__(self, kind, error, tb):
        if kind is None:
            self.commit()
        else:
            try:
                self.rollback()
            except sqlite3.Error:
                pass


def connect(path):
    if not remote_target(path):
        return sqlite3.connect(path, timeout=15)
    import libsql
    url, token = remote_settings()
    return RemoteConnection(_call(libsql.connect, database=url, auth_token=token, timeout=15))
