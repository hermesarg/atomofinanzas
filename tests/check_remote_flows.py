"""Toda la batería de formularios, ahora con transacciones libSQL reales."""
import os, runpy, secrets
from pathlib import Path
from remote_server import remote_server
with remote_server():
    os.environ['ATOMO_SETUP_TOKEN']=secrets.token_urlsafe(40)
    runpy.run_path(str(Path(__file__).with_name('check_flows.py')),run_name='__main__')
