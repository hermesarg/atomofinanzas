"""Entrada de producción: acceso obligatorio, disco comprobado y backups periódicos."""
import os
import subprocess
import sys
import threading
from pathlib import Path
from zoneinfo import ZoneInfo


def persistent_mount(path):
    path = Path(path).resolve()
    if os.path.ismount(path):
        return True
    info = Path('/proc/self/mountinfo')
    return info.exists() and any(line.split()[4].replace('\\040',' ') == str(path) for line in info.read_text().splitlines())


def validate_environment():
    if os.getenv('ATOMO_WEB_PRIVATE') != '1':
        raise ValueError('El servidor requiere ATOMO_WEB_PRIVATE=1.')
    data = Path(os.getenv('ATOMO_DATA_DIR',''))
    if not os.getenv('ATOMO_DATA_DIR') or not data.is_absolute():
        raise ValueError('Configurá ATOMO_DATA_DIR con una ruta absoluta del disco persistente.')
    ZoneInfo(os.getenv('ATOMO_TIMEZONE','America/Argentina/Buenos_Aires'))
    if os.getenv('RENDER') == 'true' and not persistent_mount(data):
        raise ValueError('El disco persistente no está montado. El inicio se detuvo para proteger los datos.')
    data.mkdir(parents=True,exist_ok=True)
    if not (data/'acceso.db').exists() and len(os.getenv('ATOMO_SETUP_TOKEN','')) < 32:
        raise ValueError('Configurá un ATOMO_SETUP_TOKEN aleatorio de al menos 32 caracteres.')
    port = int(os.getenv('PORT','8501'))
    if not 1 <= port <= 65535:
        raise ValueError('Puerto inválido.')
    return port


def main():
    os.umask(0o077)
    try:
        port = validate_environment()
    except (ValueError, OSError) as e:
        print('No pude iniciar Átomo: '+str(e),file=sys.stderr)
        return 1
    from core.config import LIVE_DB,BACKUP_DIR
    from core.storage import daily_backup
    stop = threading.Event()
    def backups():
        while not stop.is_set():
            try:
                daily_backup(LIVE_DB,BACKUP_DIR)
            except Exception:
                # No imprimir datos, claves ni contenido de la base.
                print('Átomo: no pude completar el respaldo diario; revisá el disco.',file=sys.stderr)
            stop.wait(3600)
    thread = threading.Thread(target=backups,daemon=True)
    thread.start()
    try:
        return subprocess.call([sys.executable,'-m','streamlit','run',str(Path(__file__).with_name('app.py')),
            '--server.address','0.0.0.0','--server.port',str(port),
            '--server.headless','true','--server.fileWatcherType','none',
            '--server.enableStaticServing','false','--browser.gatherUsageStats','false'])
    finally:
        stop.set()


if __name__ == '__main__':
    raise SystemExit(main())
