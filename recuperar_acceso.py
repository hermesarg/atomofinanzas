"""Recuperación desde la consola privada del servidor; nunca desde un enlace público."""
import getpass
import secrets
from core.security import owner,security_db,password_digest

def main():
    row=owner()
    if not row:
        raise SystemExit('Todavía no hay un propietario configurado.')
    password=getpass.getpass('Nueva contraseña (al menos 12 caracteres): ')
    confirm=getpass.getpass('Repetir contraseña: ')
    if password != confirm or not 12 <= len(password) <= 256:
        raise SystemExit('Las contraseñas no coinciden o su longitud no es válida.')
    salt=secrets.token_bytes(32)
    with security_db() as c:
        c.execute('UPDATE propietario SET salt=?,digest=?,version=? WHERE id=1',(salt,password_digest(password,salt),secrets.token_hex(24)))
        c.execute('DELETE FROM intentos')
    print('Acceso actualizado. Las sesiones anteriores quedaron revocadas.')

if __name__=='__main__':main()
