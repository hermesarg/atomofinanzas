import streamlit as st
from core.quick import register, show_recent


def render(period, db):
    st.header('💸 Pagos')
    st.caption('Registrá lo que pagaste o moviste. Las transferencias entre tus cuentas no son gastos.')
    if 'pending_paid' in st.session_state:
        st.success(st.session_state.pop('pending_paid'))
    register(False, period, db)
    show_recent(period, db)

    from core.navigation import go
    if st.button('Ver historial completo', key='pay_history'):
        go('Movimientos')
