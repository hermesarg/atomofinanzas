"""Servidor libSQL oficial aislado para QA; nunca se conecta a datos personales."""
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def remote_server():
    binary = os.getenv('SQLD_QA_BINARY') or shutil.which('sqld')
    if not binary:
        raise RuntimeError('Indicá SQLD_QA_BINARY con el ejecutable oficial sqld para correr el QA remoto.')
    with tempfile.TemporaryDirectory(prefix='atomo-sqld-qa-') as folder:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        log = open(Path(folder)/'server.log', 'w')
        process = subprocess.Popen([binary, '--db-path', folder+'/external', '--http-listen-addr', f'127.0.0.1:{port}', '--no-welcome'], stdout=log, stderr=subprocess.STDOUT)
        os.environ.update(ATOMO_STORAGE='turso', ATOMO_WEB_PRIVATE='1', ATOMO_TEST_HTTP='1', TURSO_DATABASE_URL=f'http://127.0.0.1:{port}', TURSO_AUTH_TOKEN='synthetic-test-only')
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('No inició sqld de prueba.')
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=.2)
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Timeout de inicio de sqld.')
            yield process
        finally:
            process.terminate()
            process.wait(timeout=15)
            log.close()
