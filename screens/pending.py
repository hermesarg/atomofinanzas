from core.clock import today as local_today, local_now
import streamlit as st
from core.quick import pending_rows, pay_pending
from core.finance import money


def render(period, db):
    st.header('📅 Pendientes')
    if 'pending_paid' in st.session_state:
        st.success(st.session_state.pop('pending_paid'))
    if st.session_state.pop("new_pending_reset", False):
        from datetime import date
        st.session_state.new_pending_concept = ""
        st.session_state.new_pending_amount = ""
        st.session_state.new_pending_date = local_today()
    rows = pending_rows(db)
    with st.expander("Agregar un pendiente"):
        with st.form("new_pending_form"):
            concept = st.text_input("¿Qué te falta pagar? *", key="new_pending_concept")
            raw = st.text_input("Monto pendiente *", key="new_pending_amount", placeholder="Ej.: 25.000,50")
            when = st.date_input("¿Cuándo vence? *", key="new_pending_date")
            with st.expander("Otros detalles (opcional)"):
                from core.config import MONEDAS
                currency = st.selectbox("Moneda del pendiente", MONEDAS)
                notes = st.text_input("Detalle del pendiente")
            if st.form_submit_button("Guardar pendiente", width="stretch"):
                from core.finance import parse_amount
                from core.database import insert_movement
                amount = parse_amount(raw)
                if not concept.strip() or amount is None or amount <= 0:
                    st.error("Completá qué falta pagar y un monto positivo.")
                else:
                    insert_movement(when, "Compromiso", concept.strip(), "Otros", amount, None, None, currency, notes, db=db)
                    st.session_state.new_pending_reset = True
                    st.session_state.pending_created = "Pendiente guardado. Tu saldo no cambia hasta que registres el pago."
                    st.rerun()
    if "pending_created" in st.session_state:
        st.success(st.session_state.pop("pending_created"))
    if rows.empty:
        st.info('No tenés pagos pendientes cargados.')
    else:
        view = rows.copy()
        view['Monto'] = view.apply(lambda r: money(r.monto,r.moneda,True),axis=1)
        view['Cuándo'] = view.apply(lambda r: r.fecha[:7] + ' · día por confirmar' if r.fecha_precision == 'mes' else r.fecha,axis=1)
        st.dataframe(view[['descripcion','Monto','Cuándo']].rename(columns={'descripcion':'Pago pendiente'}),hide_index=True,width='stretch')
        if rows.fecha_precision.eq('mes').any():
            st.caption('Tenés pendientes sin día exacto: elegí la fecha real cuando los pagues. Los presupuestos estimados siguen sujetos a confirmación.')
    with st.expander('Ya pagué uno de estos pendientes'):
        pay_pending(db)
    st.caption('Tarjetas, cuotas y préstamos están en el desplegable Dentro de pendientes.')
