from core.clock import today as local_today, local_now
from datetime import date
import streamlit as st
from core.config import PAGES

GROUPS = {
    'Inicio': [('Inicio', 'Inicio')],
    'Pagos': [('Pagos', 'Registrar pago'), ('Movimientos', 'Ver historial completo')],
    'Ingresos': [('Ingresos', 'Registrar ingreso')],
    'Pendientes': [('Pendientes', 'Próximos pagos'), ('Tarjetas y cuotas', 'Tarjetas y cuotas'), ('Deudas', 'Deudas'), ('Proyección', 'Ver proyección')],
    'Electro': [('Electro', 'Electro financiero')],
    'Más': [('Cuentas', 'Cuentas y rendimientos'), ('Inversiones', 'Inversiones'), ('Comparar rendimientos', 'Comparar rendimientos'), ('Preguntale a Átomo', 'Preguntale a Átomo'), ('Instituciones', 'Bancos y otras entidades'), ('Configuración', 'Ajustes')],
}
MAIN_ICONS = {'Inicio':'🏠', 'Pagos':'💸', 'Ingresos':'💰', 'Pendientes':'📅', 'Electro':'⚡', 'Más':'☰'}
MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def group_for_page(page):
    return next((group for group, items in GROUPS.items() if any(p == page for p, _ in items)), 'Inicio')


def activate(page):
    st.session_state.page = page
    if page in ['Pagos', 'Ingresos']:
        st.session_state.pending_period = st.session_state.get('_active_period_key', local_today().strftime('%Y-%m'))
        st.session_state['reset_' + ('pay' if page == 'Pagos' else 'income')] = True


def go(page_name):
    if page_name in PAGES:
        activate(page_name)
        st.rerun()


def sync_group(key):
    activate(GROUPS[st.session_state[key]][0][0])


def sync_detail():
    activate(st.session_state.section_detail)


def menu_widget(key, label='Menú'):
    st.session_state[key] = group_for_page(st.session_state.page)
    return st.selectbox(label, list(GROUPS), key=key, on_change=sync_group, args=(key,))


def detail_widget():
    group = group_for_page(st.session_state.page)
    items = GROUPS[group]
    if group == 'Pagos':
        if st.session_state.page == 'Movimientos' and st.button('Volver a registrar un pago', key='back_to_payments'):
            go('Pagos')
        return
    if len(items) > 1:
        st.session_state.section_detail = st.session_state.page
        labels = dict(items)
        st.selectbox('Dentro de ' + group.lower(), list(labels), format_func=labels.get,
                     key='section_detail', on_change=sync_detail)


def period_selector(db):
    from core.database import dfq
    today = local_today()
    if 'pending_period' in st.session_state:
        year, month = map(int, st.session_state.pop('pending_period').split('-'))
        st.session_state.period_year, st.session_state.period_month = year, month
    st.session_state.setdefault('period_year', today.year)
    st.session_state.setdefault('period_month', today.month)
    years = list(range(2000, today.year + 11))
    recorded = dfq('SELECT DISTINCT CAST(substr(COALESCE(periodo_registro,fecha),1,4) AS INTEGER) AS y FROM movimientos', db=db)
    years = sorted(set(years + [int(y) for y in recorded.y if y and 1 <= y <= 9999] + [st.session_state.period_year]))
    with st.expander('Ver otro mes', expanded=False):
        a, b = st.columns([1.6, 1])
        month = a.selectbox('Mes', list(range(1,13)), format_func=lambda m: MONTHS[m-1], key='period_month')
        year = b.selectbox('Año', years, key='period_year')
    return f'{year:04d}-{month:02d}'
