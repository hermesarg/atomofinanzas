from core.clock import today as local_today, local_now
"""Cargas cotidianas: pocas preguntas, cuenta explícita y fecha actual."""
from datetime import date
import pandas as pd
import streamlit as st
from core.config import GASTO_CATEGORIAS, MONEDAS, categories_for_type
from core.database import accounts_df, accounts_match_currency, con, dfq, insert_movement, movements_df
from core.finance import account_map, money, parse_amount

ACTIONS = ['Un gasto o pago', 'Mover entre mis cuentas', 'Transferir a otra persona', 'Pagar un pendiente']


def show_recent(period, db, income=False):
    rows = movements_df(period, db)
    rows = rows[rows.tipo.eq('Ingreso')] if income else rows[rows.tipo.isin(['Gasto', 'Transferencia', 'Financiero'])]
    st.subheader('Ingresos registrados' if income else 'Últimos pagos y movimientos')
    if rows.empty:
        st.caption(f'Todavía no hay registros en {period}.')
        return
    view = rows.head(8).copy()
    view['Monto'] = view.apply(lambda r: money(r.monto, r.moneda, True), axis=1)
    view['Cuándo'] = view.apply(lambda r: 'Ciclo ' + str(r.periodo_registro) if r.fecha_precision == 'ciclo' else (r.fecha[:7] + ' · día por confirmar' if r.fecha_precision == 'mes' else r.fecha), axis=1)
    st.dataframe(view[['Cuándo', 'descripcion', 'tipo', 'Monto']].rename(columns={'descripcion':'Concepto','tipo':'Registro'}), hide_index=True, width='stretch')


def register(income, period, db):
    prefix = 'income' if income else 'pay'
    if st.session_state.pop('reset_' + prefix, False):
        for field in ['description', 'amount', 'notes', 'recipient']:
            st.session_state[prefix + '_' + field] = ''
        st.session_state[prefix + '_date'] = local_today()
    if prefix + '_saved' in st.session_state:
        st.success(st.session_state.pop(prefix + '_saved'))
    action = 'Un ingreso' if income else st.selectbox('¿Qué querés cargar?', ACTIONS, key='pay_action')
    if action == 'Pagar un pendiente':
        pay_pending(db, prefix='quick_pending')
        return
    amap = account_map(db)
    currencies = {int(r.id): r.moneda for _, r in accounts_df(db).iterrows()}
    options = ['Elegí una cuenta'] + list(amap) + ['Solo registrar, sin cuenta']
    own = action == 'Mover entre mis cuentas'
    third = action == 'Transferir a otra persona'
    with st.form(prefix + '_quick_form'):
        raw = st.text_input('Monto *', key=prefix + '_amount', placeholder='Ej.: 12.500 o 12.500,50')
        desc = st.text_input('¿Qué fue? *', key=prefix + '_description', placeholder='Ej.: supermercado, sueldo, alquiler')
        source = st.selectbox('¿Dónde entra? *' if income else '¿De dónde sale? *', options, key=prefix + '_source')
        target = st.selectbox('¿A cuál de tus cuentas va? *', ['Elegí una cuenta'] + list(amap), key='pay_target') if own else None
        recipient = st.text_input('¿A quién? *', key='pay_recipient') if third else ''
        with st.expander('Fecha y otros detalles (opcional)', expanded=False):
            when = st.date_input('Fecha', key=prefix + '_date')
            if not own:
                category = st.selectbox('Categoría (opcional)', categories_for_type('Ingreso') if income else GASTO_CATEGORIAS, key=prefix + '_category', index=(categories_for_type('Ingreso') if income else GASTO_CATEGORIAS).index('Otros'))
            else:
                category = 'Transferencia'
            cur_if_none = st.selectbox('Moneda si registrás sin cuenta', MONEDAS, key=prefix + '_currency')
            notes = st.text_input('Nota (opcional)', key=prefix + '_notes')
            start_with_salary = False
            if income and category == 'Sueldo / ingreso':
                from core.database import get_config
                if get_config('periodo_modo', '', db) == 'salary_manual':
                    start_with_salary = st.checkbox(
                        'Iniciar un nuevo período con este sueldo',
                        value=True,
                        help='El período anterior queda cerrado el día previo. No se modifica ningún período histórico.'
                    )
        st.caption('Fecha inicial: hoy. Para cargar algo anterior, cambiá Fecha en los detalles.')
        submitted = st.form_submit_button('Guardar ingreso' if income else 'Guardar pago', type='primary', width='stretch')
        if submitted:
            amount = parse_amount(raw)
            origin = amap.get(source)
            destination = amap.get(target) if own else (origin if income else None)
            currency = currencies.get(origin, cur_if_none)
            if amount is None or amount <= 0 or not desc.strip():
                st.error('Completá qué fue y un monto positivo. Podés usar puntos de miles y coma decimal.')
            elif source == 'Elegí una cuenta':
                st.error('Elegí una cuenta, o «Solo registrar, sin cuenta» si todavía no sabés cuál.')
            elif (own or third) and not origin:
                st.error('Para transferir elegí la cuenta de salida.')
            elif own and (not destination or destination == origin):
                st.error('Elegí otra cuenta distinta para la entrada.')
            elif third and not recipient.strip():
                st.error('Escribí a quién le transferiste.')
            elif not accounts_match_currency([origin, destination], currency, db):
                st.error('Las dos cuentas deben usar la misma moneda. No se convierten monedas automáticamente.')
            else:
                typ = 'Ingreso' if income else ('Transferencia' if own else 'Gasto')
                detail = notes.strip()
                if third:
                    detail = f'Destinatario: {recipient.strip()}' + (' · ' + detail if detail else '')
                period_key = None
                if income and category == 'Sueldo / ingreso' and start_with_salary:
                    from core.periods import start_period
                    period_key = start_period(
                        when, db, mode='salary_manual',
                        detail='Iniciado al confirmar el cobro de sueldo.'
                    )
                insert_movement(when, typ, desc.strip(), category, amount,
                                None if income else origin, destination, currency, detail,
                                subtipo='Entre mis cuentas' if own else ('Transferencia a tercero' if third else None),
                                db=db, periodo_registro=period_key)
                from core.periods import period_for_date
                st.session_state[prefix + '_saved'] = f'Guardado: {desc.strip()} · {money(amount,currency,True)}.'
                st.session_state['reset_' + prefix] = True
                st.session_state.pending_period = period_for_date(when, db)
                st.rerun()


def pending_rows(db):
    return dfq("SELECT * FROM movimientos WHERE tipo='Compromiso' AND COALESCE(estado,'activo')='activo' ORDER BY fecha,id", db=db)


def pay_pending(db, prefix='pending'):
    pending = pending_rows(db)
    amap = account_map(db)
    if pending.empty:
        st.info('No tenés pendientes cargados.')
        return
    if not amap:
        st.info('Agregá una cuenta en Más → Cuentas y rendimientos para registrar desde dónde pagaste.')
        return
    options = {f"{r.descripcion} · {money(r.monto,r.moneda,True)}": int(r.id) for _, r in pending.iterrows()}
    # IDs only disambiguate identical concepts, never hide or merge a payment.
    if len(options) != len(pending):
        options = {f"{r.descripcion} · {money(r.monto,r.moneda,True)} · #{r.id}": int(r.id) for _, r in pending.iterrows()}
    with st.form(prefix + '_form'):
        selected = st.selectbox('¿Qué pagaste? *', list(options), key=prefix + '_selected')
        source = st.selectbox('¿De dónde salió? *', ['Elegí una cuenta'] + list(amap), key=prefix + '_source')
        when = st.date_input('Fecha del pago', value=local_today(), key=prefix + '_date')
        if st.form_submit_button('Registrar pago del pendiente', type='primary', width='stretch'):
            row = pending.loc[pending.id == options[selected]].iloc[0]
            if source not in amap:
                st.error('Elegí la cuenta desde la que pagaste.')
            elif not accounts_match_currency([amap[source]], row.moneda or 'ARS', db):
                st.error('Elegí una cuenta que use la misma moneda que este pendiente.')
            else:
                from core.periods import period_for_date
                period_key = period_for_date(when, db)
                with con(db) as connection:
                    connection.execute("UPDATE movimientos SET tipo='Gasto',cuenta_origen_id=?,fecha=?,impacta_caja=1,importado=0,subtipo='Pago de pendiente',notas='Pago registrado por el usuario. Referencia original: '||COALESCE(notas,''),periodo_registro=?,fecha_precision='dia' WHERE id=? AND tipo='Compromiso' AND COALESCE(estado,'activo')='activo'", (amap[source],when.isoformat(),period_key,int(row.id)))
                st.session_state.pending_paid = f'Pago registrado: {row.descripcion}.'
                st.session_state.pending_period = period_key
                st.rerun()
