import sqlite3
import os
import re
from datetime import date
import streamlit as st
import importlib
from core.config import ATOMO_AVATAR, ATOMO_LOGO, BACKUP_DIR, DEMO_DB, LIVE_DB, PAGES, PAGE_ICONS, _PAGE_ICON
from core.database import backup_live_once, current_db, init_db
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

# El modo demo usa una base temporal aislada por sesión.
st.session_state.demo_mode = os.getenv("ATOMO_DEMO", "0") == "1"
try:
    db_boot = current_db()
    if st.session_state.demo_mode:
        init_db(db_boot)
    else:
        backup_live_once()
        init_db(db_boot)
        if web_private():
            from core.storage import daily_backup
            daily_backup(db_boot, BACKUP_DIR)
except (OSError, sqlite3.Error):
    st.error("No pude abrir tu base de datos. Revisá la conexión o la configuración del guardado; los datos permanecen protegidos.")
    st.stop()

def render_workspace():
    if st.session_state.get("page") not in PAGES:
        st.session_state.page = "Inicio"

    db = current_db()
    if not st.session_state.demo_mode:
        from core.periods import setup_complete, render_setup, save_preference
        if not setup_complete(db):
            if web_private():
                render_setup(db)
                return
            # La app local conserva el comportamiento histórico: mes calendario.
            save_preference("calendar", None, db)

    if st.session_state.demo_mode:
        st.markdown('<div class="demo-banner">🧪 <b>Átomo Demo</b> · datos ficticios y espacio temporal. Podés probar sin tocar información real.</div>', unsafe_allow_html=True)
        if not st.session_state.get("demo_intro_dismissed", False):
            with st.container(key="demo_welcome"):
                st.markdown("### Probalo sin miedo")
                st.write(
                    "No necesitás registrarte. Todo lo que ves es ficticio y tu prueba queda aislada "
                    "de la de otras personas. Podés cargar, editar y explorar."
                )
                a, b, d = st.columns(3)
                with a:
                    if st.button("💸 Registrar un pago", key="demo_start_payment", width="stretch"):
                        st.session_state.demo_intro_dismissed = True
                        go("Pagos")
                with b:
                    if st.button("⚡ Ver Electro", key="demo_start_electro", width="stretch"):
                        st.session_state.demo_intro_dismissed = True
                        go("Electro")
                with d:
                    if st.button("🏦 Explorar cuentas", key="demo_start_accounts", width="stretch"):
                        st.session_state.demo_intro_dismissed = True
                        go("Cuentas")
                if st.button("Seguir mirando", key="demo_intro_close"):
                    st.session_state.demo_intro_dismissed = True
                    st.rerun()

    with st.sidebar:
        if ATOMO_LOGO.exists():
            st.image(str(ATOMO_LOGO), width=90)
        st.markdown('<div class="atomo-brand">Átomo Finanzas</div>', unsafe_allow_html=True)
        st.caption("Las cuentas las hago yo. Las decisiones, vos.")
        menu_widget("sidebar_group", "Secciones")
        period = period_selector(db)
        st.caption("Tus datos se guardan en tu espacio privado." if web_private() else ("Demo temporal: se reinicia en una nueva sesión." if st.session_state.demo_mode else "Tus datos se guardan en esta PC."))
        if web_private():
            st.button("Cerrar sesión", key="private_logout", on_click=logout)
        elif st.session_state.demo_mode:
            if st.button("Reiniciar demo", key="reset_public_demo"):
                from core.database import reset_demo
                reset_demo(db)
                st.rerun()
    
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

    from core.periods import render_status
    render_status(db, compact=True)

    page = st.session_state.page
    
    # =========================================================
    # PAGE: INICIO
    # =========================================================
    
    SCREENS = {'Pagos': 'quick_payments', 'Ingresos': 'quick_income', 'Pendientes': 'pending', 'Inicio': 'home', 'Electro': 'electro', 'Cuentas': 'accounts', 'Tarjetas y cuotas': 'cards', 'Movimientos': 'movements', 'Deudas': 'debts', 'Inversiones': 'investments', 'Comparar rendimientos': 'comparison', 'Proyección': 'projection', 'Preguntale a Átomo': 'assistant', 'Instituciones': 'institutions', 'Configuración': 'settings'}
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
