"""Entrada pública de demostración: datos ficticios y base temporal por sesión."""
import os
from pathlib import Path

os.environ["ATOMO_DEMO"] = "1"
os.environ["ATOMO_WEB_PRIVATE"] = "0"
os.environ["ATOMO_STORAGE"] = "sqlite"
os.environ["ATOMO_TIMEZONE"] = "America/Argentina/Buenos_Aires"

source = Path(__file__).with_name("app.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
