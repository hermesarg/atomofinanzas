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
    if group == 'Más':
        st.caption('Dentro de Más')
        for row_start in range(0, len(items), 2):
            cols = st.columns(2)
            for col, (page, label) in zip(cols, items[row_start:row_start + 2]):
                with col:
                    if st.button(
                        label,
                        key='detail_more_' + page,
                        width='stretch',
                        type='primary' if st.session_state.page == page else 'secondary',
                    ):
                        go(page)
        return
    if len(items) > 1:
        st.session_state.section_detail = st.session_state.page
        labels = dict(items)
        st.selectbox('Dentro de ' + group.lower(), list(labels), format_func=labels.get,
                     key='section_detail', on_change=sync_detail)


def period_selector(db):
    from core.periods import active_period
    today = local_today()
    active_info = active_period(db)
    active = active_info["periodo"] if active_info else None
    if active:
        st.session_state._active_period_key = active

    if 'pending_period' in st.session_state:
        pending = st.session_state.pop('pending_period')
        if pending and len(pending) >= 7:
            year, month = map(int, pending[:7].split('-'))
            st.session_state.period_year, st.session_state.period_month = year, month
    elif 'period_year' not in st.session_state or 'period_month' not in st.session_state:
        base = active or today.strftime('%Y-%m')
        year, month = map(int, base[:7].split('-'))
        st.session_state.period_year, st.session_state.period_month = year, month

    years = sorted(set(range(2000, today.year + 11)) | {int(st.session_state.period_year)})
    with st.expander('Ver otro período', expanded=False):
        a, b = st.columns([1.6, 1])
        month = a.selectbox('Período', list(range(1,13)), format_func=lambda m: MONTHS[m-1], key='period_month')
        year = b.selectbox('Año', years, key='period_year')
    return f'{year:04d}-{month:02d}'
