from core.clock import today as local_today, local_now
from datetime import date
import pandas as pd
import streamlit as st
from core.config import GASTO_CATEGORIAS, MONEDAS, categories_for_type
from core.database import accounts_match_currency, insert_movement, movements_df
from core.finance import account_map, amount_input, money

def render(period, db):
    from core.history import render_history_notice, render_references
    st.header("💸 Historial completo")
    render_history_notice(period, db)
    from core.history import render_cycle_summary
    render_cycle_summary(period, db)
    st.caption(f"Viendo movimientos de {period}. Cada carga conserva su fecha real y también el período financiero asignado.")
    if "movement_saved" in st.session_state:
        st.success(st.session_state.pop("movement_saved"))
    with st.expander("Carga avanzada (opcional)", expanded=False):
        amap = account_map(db)
        typ = st.radio("Tipo *", ["Gasto", "Ingreso", "Transferencia", "Compromiso"], horizontal=True, key="movement_type")
    
        subtype = None
        if typ == "Transferencia":
            subtype = st.radio("¿Qué tipo de transferencia es? *", ["Entre mis cuentas", "A otra persona"], horizontal=True)
        with st.form("mov_form", clear_on_submit=False):
            a, b = st.columns(2)
            d = a.date_input("Fecha *", value=local_today())
            desc = b.text_input("Descripción *")
            a, b, c = st.columns(3)
            category_options = categories_for_type(typ)
            cat = a.selectbox("Categoría *", category_options, index=0)
            amt, amt_raw = amount_input("Monto *", value="0", help="Podés escribir 100000, 100.000 o 100.000,50")
            cur = c.selectbox("Moneda *", MONEDAS)
    
            ori = dst = None
            notes = ""
            if typ == "Gasto":
                s = st.selectbox("Sale de", ["Sin cuenta"] + list(amap.keys()))
                ori = amap.get(s)
                notes = st.text_input("Notas")
            elif typ == "Ingreso":
                s = st.selectbox("Entra a", ["Sin cuenta"] + list(amap.keys()))
                dst = amap.get(s)
                notes = st.text_input("Notas")
            elif typ == "Transferencia":
                if subtype == "Entre mis cuentas":
                    a, b = st.columns(2)
                    so = a.selectbox("Sale de *", ["Sin cuenta"] + list(amap.keys()))
                    sd = b.selectbox("Entra a *", ["Sin cuenta"] + list(amap.keys()))
                    ori, dst = amap.get(so), amap.get(sd)
                    notes = st.text_input("Notas")
                else:
                    a, b = st.columns(2)
                    so = a.selectbox("Sale de *", ["Sin cuenta"] + list(amap.keys()))
                    recipient = b.text_input("Va a / destinatario *", placeholder="Ej.: Juan, alquiler, proveedor")
                    ori = amap.get(so)
                    third_cat = st.selectbox("¿Para qué fue la transferencia? *", GASTO_CATEGORIAS, index=0)
                    notes = st.text_input("Notas")
            else:
                notes = st.text_input("Notas")
    
            st.caption("Los campos con * son obligatorios.")
            if st.form_submit_button("Guardar movimiento"):
                if not desc.strip() or amt is None or amt <= 0:
                    st.error("Falta descripción o monto válido.")
                elif typ == "Transferencia" and subtype == "Entre mis cuentas" and (not ori or not dst or ori == dst):
                    st.error("Elegí una cuenta de salida y otra distinta de entrada.")
                elif typ == "Transferencia" and subtype == "A otra persona" and (not ori or not recipient.strip()):
                    st.error("Elegí de qué cuenta sale la plata y el destinatario.")
                elif not accounts_match_currency([ori, dst], cur, db):
                    st.error("La moneda debe coincidir con las cuentas. No se convierten monedas automáticamente.")
                else:
                    if typ == "Transferencia" and subtype == "A otra persona":
                        detail = notes.strip()
                        if recipient.strip():
                            detail = (f"Destinatario: {recipient.strip()}" + (f" · {detail}" if detail else ""))
                        insert_movement(d, "Gasto", desc, third_cat, amt, ori, None, cur, detail, subtipo="Transferencia a tercero", db=db)
                    elif typ == "Transferencia":
                        insert_movement(d, "Transferencia", desc, "Transferencia", amt, ori, dst, cur, notes, subtipo="Entre mis cuentas", db=db)
                    else:
                        insert_movement(d, typ, desc, cat, amt, ori, dst, cur, notes, db=db)
                    from core.periods import period_for_date
                    saved_period = period_for_date(d, db)
                    st.session_state.pending_period = saved_period
                    st.session_state.movement_saved = f"Guardado: {desc.strip()} · {money(amt,cur,True)}. Ahora estás viendo {saved_period}."
                    st.rerun()
    
    mov = movements_df(period, db)
    if mov.empty:
        st.info("No hay movimientos en este período. Elegí otro mes y año en el menú lateral.")
        available = movements_df(db=db)
        if not available.empty:
            st.caption("Hay registros en: " + ", ".join(sorted(set(available.periodo_registro.fillna(available.fecha.str[:7])))))
    else:
        v = mov.copy()
        v["Monto"] = v.apply(lambda r: money(r["monto"], r["moneda"] or "ARS"), axis=1)
        v["Origen / destino"] = v.apply(
            lambda r: (
                f"{r['institucion_origen'] or ''} · {r['cuenta_origen_nombre'] or ''} → {r['institucion_destino'] or ''} · {r['cuenta_destino_nombre'] or ''}".strip(" ·")
                if r["tipo"] == "Transferencia"
                else (f"Sale de: {(r['institucion_origen'] or '')} · {(r['cuenta_origen_nombre'] or '')}" if pd.notna(r.get("cuenta_origen_nombre")) else (f"Entra a: {(r['institucion_destino'] or '')} · {(r['cuenta_destino_nombre'] or '')}" if pd.notna(r.get("cuenta_destino_nombre")) else "—"))
            ),
            axis=1,
        )
        v['Fecha / período'] = v.apply(lambda r: 'Ciclo ' + str(r['periodo_registro']) + ' · día por corroborar' if r['fecha_precision'] == 'ciclo' else (r['fecha'][:7] + ' · día por corroborar' if r['fecha_precision'] == 'mes' else r['fecha']), axis=1)
        v['Registro'] = v.apply(lambda r: ('Proyección importada · no es un pago' if r['tipo'] == 'Compromiso' else 'Histórico · no modifica saldo actual') if r['importado'] else 'Carga del usuario', axis=1)
        st.dataframe(v[["Fecha / período", "tipo", "subtipo", "descripcion", "categoria", "Origen / destino", "Monto", 'Registro', 'notas']], width="stretch", hide_index=True)
    render_references(['Saldos', 'Conciliación', 'Trading', 'Control'], db, 'Saldos, trading y datos por conciliar del registro original')

# =========================================================
# PAGE: DEUDAS
# =========================================================
