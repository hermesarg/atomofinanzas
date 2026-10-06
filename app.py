import sqlite3
import os
import re
from datetime import date
import streamlit as st
import importlib
from core.config import ATOMO_AVATAR, ATOMO_LOGO, BACKUP_DIR, DEMO_DB, LIVE_DB, PAGES, PAGE_ICONS, _PAGE_ICON
from core.database import backup_live_once, current_db, init_db, reset_demo
from core.navigation import go, period_selector, GROUPS, MAIN_ICONS, menu_widget, detail_widget, group_for_page
from core.styles import apply_styles




st.set_page_config(
    page_title="Átomo Finanzas",
    page_icon=_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="auto",
)

apply_styles()

from core.security import require_private_access, web_private, logout
try:
    require_private_access()
except (OSError, sqlite3.Error):
    st.error("No pude verificar el acceso privado. Los datos permanecen bloqueados.")
    st.stop()

# El modo de prueba usa una base separada y no migra ni escribe la base real.
st.session_state.demo_mode = os.getenv("ATOMO_DEMO", "0") == "1"
try:
    if st.session_state.demo_mode:
        if not DEMO_DB.exists():
            reset_demo()
        else:
            init_db(DEMO_DB)
    else:
        backup_live_once()
        init_db(LIVE_DB)
        if web_private():
            from core.storage import daily_backup
            daily_backup(LIVE_DB, BACKUP_DIR)
except (OSError, sqlite3.Error):
    st.error("No pude abrir tu base de datos. Revisá la conexión o la configuración del guardado; los datos permanecen protegidos.")
    st.stop()

def render_workspace():
    if st.session_state.get("page") not in PAGES:
        st.session_state.page = "Inicio"
    
    with st.sidebar:
        if ATOMO_LOGO.exists():
            st.image(str(ATOMO_LOGO), width=90)
        st.markdown('<div class="atomo-brand">Átomo Finanzas</div>', unsafe_allow_html=True)
        st.caption("Las cuentas las hago yo. Las decisiones, vos.")
        menu_widget("sidebar_group", "Secciones")
        period = period_selector(current_db())
        st.caption("Tus datos se guardan en tu espacio privado." if web_private() else "Tus datos se guardan en esta PC.")
        if web_private():
            st.button("Cerrar sesión", key="private_logout", on_click=logout)
    
    # Header
    with st.container(key="brand_header"):
        hlogo, htitle = st.columns([0.65, 10], vertical_alignment="center")
        with hlogo:
            if ATOMO_LOGO.exists():
                st.image(str(ATOMO_LOGO), width=64)
            elif ATOMO_AVATAR.exists():
                st.image(str(ATOMO_AVATAR), width=64)
        with htitle:
            st.title("Átomo Finanzas")
            st.caption("Las cuentas las hago yo. Las decisiones, vos.")
        
    
    with st.container(key="topnav_stable"):
        for col, group in zip(st.columns(len(GROUPS)), GROUPS):
            with col:
                if st.button(f"{MAIN_ICONS[group]} {group}", key="main_" + group,
                             width="stretch", type="primary" if group_for_page(st.session_state.page) == group else "secondary"):
                    go(GROUPS[group][0][0])
    with st.container(key="mobile_nav_stable"):
        menu_widget("mobile_group")
    detail_widget()
    
    page = st.session_state.page
    db = current_db()
    
    # =========================================================
    # PAGE: INICIO
    # =========================================================
    
    SCREENS = {'Pagos': 'quick_payments', 'Ingresos': 'quick_income', 'Pendientes': 'pending', 'Inicio': 'home', 'Cuentas': 'accounts', 'Tarjetas y cuotas': 'cards', 'Movimientos': 'movements', 'Deudas': 'debts', 'Inversiones': 'investments', 'Comparar rendimientos': 'comparison', 'Proyección': 'projection', 'Preguntale a Átomo': 'assistant', 'Instituciones': 'institutions', 'Configuración': 'settings'}
    try:
        if web_private() and page == "Inicio":
            from core.storage import render_initial_import
            if st.session_state.pop("_import_success", False):
                st.success("Tu historial quedó importado. Las próximas cargas se guardan en este espacio.")
            render_initial_import(db)
        importlib.import_module("screens." + SCREENS[page]).render(period, db)
    except sqlite3.Error:
        st.error("No pude confirmar la operación. Revisá la conexión y el historial antes de volver a cargarla.")
        st.stop()
    
    st.markdown("---")
    st.caption("Datos ficticios de prueba" if st.session_state.demo_mode else ("Tus datos se guardan en tu espacio privado. Vos decidís cada operación." if web_private() else "Tus datos se guardan localmente. Vos decidís cada operación."))

try:
    render_workspace()
except sqlite3.Error:
    st.error("No pude confirmar la operación. Revisá la conexión y el historial antes de volver a cargarla.")
    st.stop()
except PermissionError:
    st.session_state.pop('_private_access', None)
    st.rerun()
