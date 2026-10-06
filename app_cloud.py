"""Entrada exclusiva para la beta gratuita: acceso y guardado remoto obligatorios."""
import os
from pathlib import Path
import streamlit as st

# Leer secrets antes de importar core.config. Nunca imprimir sus valores.
for name in ['TURSO_DATABASE_URL', 'TURSO_AUTH_TOKEN', 'ATOMO_SETUP_TOKEN']:
    try:
        value = st.secrets.get(name)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        value = None
    if value:
        os.environ[name] = str(value)
os.environ['ATOMO_STORAGE'] = 'turso'
os.environ['ATOMO_WEB_PRIVATE'] = '1'
os.environ['ATOMO_TIMEZONE'] = 'America/Argentina/Buenos_Aires'
os.environ['ATOMO_DEMO'] = '0'

source = Path(__file__).with_name('app.py')
exec(compile(source.read_text(encoding='utf-8'), str(source), 'exec'))
