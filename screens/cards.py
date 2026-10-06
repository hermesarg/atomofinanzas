from core.clock import today as local_today, local_now
import uuid
from datetime import date
from datetime import datetime
import streamlit as st
from core.config import MONEDAS, categories_for_type
from core.database import accounts_match_currency, cards_df, con, dfq
from core.finance import account_map, add_months, amount_input, fmt_day, institution_map, money

def render(period, db):
    from core.history import render_references
    st.header("💳 Tarjetas y cuotas")
    if "card_saved" in st.session_state:
        st.success(st.session_state.pop("card_saved"))
    render_references('Tarjetas', db, 'Tarjetas y pagos recuperados')

    st.markdown("""
    <div class="help-card">
    <b>¿Te faltan cuotas por pagar?</b> Decime cuántas quedan, el monto y el próximo vencimiento:
    la app calcula las fechas futuras. <b>No crea ningún pago real.</b>
    </div>
    """, unsafe_allow_html=True)

    bankmap = institution_map(["Banco / Financiera","Billetera / Fintech"], db)

    with st.expander("➕ Agregar tarjeta"):
        together = st.checkbox("Cargar también sus cuotas pendientes", key="card_with_installments")
        with st.form("card_form", clear_on_submit=False):
            ins = st.selectbox("Emisor *", list(bankmap.keys()) if bankmap else [""])
            name = st.text_input("Nombre de la tarjeta *", placeholder="Ej.: Visa Patagonia")
            a,b,c,d = st.columns(4)
            close = a.selectbox("Día de cierre (opcional)", ["No lo sé"] + list(range(1,32)), index=0)
            due = b.selectbox("Día de vencimiento (opcional)", ["No lo sé"] + list(range(1,32)), index=0)
            with c:
                limit_, limit_raw = amount_input("Límite (opcional)", value="0", help="Opcional")
            cur = d.selectbox("Moneda *", MONEDAS)
            st.caption("Los campos opcionales se pueden completar después. Si no conocés el cierre, no frena la app.")
            if together:
                purchase = st.text_input("Concepto de las cuotas *")
                a, b = st.columns(2)
                count = a.number_input("Cuotas pendientes *", 1, 60, 1)
                first = b.date_input("Próximo resumen *", value=local_today())
                installment, _ = amount_input("Importe de cada cuota *", value="0")
                st.caption("Se guardan la tarjeta y sus cuotas juntas. Esto proyecta vencimientos; no registra pagos.")
            if st.form_submit_button("Guardar tarjeta"):
                if together and (not purchase.strip() or installment is None or installment <= 0):
                    st.error("Completá el concepto y un importe de cuota positivo. No se guardó la tarjeta ni las cuotas.")
                    return
                if name.strip() and bankmap and (limit_ is not None and limit_ >= 0 or not limit_raw.strip()):
                    with con(db) as cdb:
                        cursor = cdb.execute("""
                        INSERT INTO tarjetas(institucion_id,nombre,cierre_dia,vencimiento_dia,limite,moneda,activa,notas,creada_en)
                        VALUES (?,?,?,?,?,?,1,'',?)
                        """, (
                            bankmap[ins], name.strip(),
                            None if close == "No lo sé" else int(close),
                            None if due == "No lo sé" else int(due),
                            float(limit_ or 0), cur,
                            local_now().isoformat(timespec="seconds")
                        ))
                        if together:
                            insert_installments(cdb, purchase.strip(), count, installment, first, "Tarjetas", cur, name.strip())
                    st.session_state.card_saved = "Tarjeta y cuotas guardadas." if together else "Tarjeta guardada."
                    st.success("Tarjeta guardada.")
                    st.rerun()

                else:
                    st.error("Completá el nombre y revisá el límite de la tarjeta.")

    tdf = cards_df(db)
    if not tdf.empty:
        show = tdf[["institucion","nombre","cierre_dia","vencimiento_dia","limite","moneda"]].copy()
        show["cierre_dia"] = show["cierre_dia"].map(lambda x: "No cargado" if fmt_day(x)=="—" else fmt_day(x))
        show["vencimiento_dia"] = show["vencimiento_dia"].map(lambda x: "No cargado" if fmt_day(x)=="—" else fmt_day(x))
        show["limite"] = show.apply(lambda r: money(r["limite"],r["moneda"]),axis=1)
        show = show.rename(columns={"institucion":"Institución","nombre":"Tarjeta","cierre_dia":"Cierre","vencimiento_dia":"Vencimiento","limite":"Límite","moneda":"Moneda"})
        st.dataframe(show,width="stretch",hide_index=True)

        st.subheader("Cargar cuotas pendientes")
        cardmap = {f"{r['institucion']} · {r['nombre']} · #{r['id']}": int(r["id"]) for _,r in tdf.iterrows()}
        with st.form("installment_form", clear_on_submit=False):
            card = st.selectbox("Tarjeta", list(cardmap.keys()))
            desc = st.text_input("Compra / concepto *")
            a,b,c = st.columns(3)
            remaining = a.number_input("Cuotas que faltan *",1,60,3)
            each, each_raw = amount_input("Monto de cada cuota *", value="0")
            first_due = c.date_input("Fecha de la primera cuota / próximo resumen *",value=local_today())
            cat = st.selectbox("Categoría *",categories_for_type("Compromiso"),index=categories_for_type("Compromiso").index("Tarjetas"))
            st.caption("Si pagaste con crédito y querés proyectarlo, decinos cuántas cuotas son y cuándo se verá la primera.")
            if st.form_submit_button("Calcular y agregar cuotas"):
                if desc.strip() and each and each>0:
                    currency = tdf.loc[tdf.id == cardmap[card], "moneda"].iloc[0]
                    with con(db) as cdb:
                        insert_installments(cdb, desc.strip(), remaining, each, first_due, cat, currency, card, db)
                    st.success("Cuotas agregadas. Ahora aparecen en proyección.")
                    st.rerun()
                else:
                    st.error("Completá el concepto y un monto de cuota positivo.")

    st.markdown("---")
    st.markdown("""
    <div class="help-card">
    <b>¿Adelantaste una cuota o pagaste un compromiso antes?</b>
    Marcá cuál fue y desde qué cuenta salió. Recién ahí deja de figurar como pendiente.
    </div>
    """, unsafe_allow_html=True)

    pending = dfq("""
    SELECT * FROM movimientos
    WHERE tipo='Compromiso' AND COALESCE(estado,'activo')='activo'
    ORDER BY fecha
    """, db=db)
    amap = account_map(db)
    if not pending.empty and amap:
        pmap = {f"#{r['id']} · {r['fecha']} · {r['descripcion']} · {money(r['monto'],r['moneda'] or 'ARS')}":int(r["id"]) for _,r in pending.iterrows()}
        a,b = st.columns(2)
        ps = a.selectbox("Compromiso pagado/adelantado",list(pmap.keys()))
        ac = b.selectbox("Salió de *",list(amap.keys()))
        if st.button("Marcar como pagado"):
            currency = pending.loc[pending.id == pmap[ps], "moneda"].iloc[0] or "ARS"
            if not accounts_match_currency([amap[ac]], currency, db):
                st.error("Elegí una cuenta con la misma moneda del compromiso.")
            else:
                from core.periods import period_for_date
                paid_on = local_today()
                period_key = period_for_date(paid_on, db)
                with con(db) as cdb:
                    cdb.execute("""
                    UPDATE movimientos SET tipo='Gasto',cuenta_origen_id=?,fecha=?,impacta_caja=1,importado=0,subtipo='Pago de pendiente',notas='Pago registrado por el usuario. Referencia original: '||COALESCE(notas,''),periodo_registro=?,fecha_precision='dia'
                    WHERE id=? AND tipo='Compromiso' AND COALESCE(estado,'activo')='activo'
                    """,(amap[ac],paid_on.isoformat(),period_key,pmap[ps]))
                st.session_state.pending_period = period_key
                st.success("Actualizado.")
                st.rerun()
    else:
        st.caption("No hay compromisos pendientes o todavía no hay cuentas cargadas.")

# =========================================================
# PAGE: MOVIMIENTOS
# =========================================================


def insert_installments(connection, concept, count, amount, first, category, currency, card, db):
    from core.periods import period_for_date
    group = f"q_{uuid.uuid4().hex}"
    for i in range(int(count)):
        due = add_months(first, i)
        period_key = period_for_date(due, db)
        connection.execute("""
            INSERT INTO movimientos(fecha,tipo,descripcion,categoria,monto,moneda,notas,
                creado_en,grupo_cuotas,cuota_actual,cuotas_total,periodo_registro,estado,impacta_caja)
            VALUES (?,'Compromiso',?,?,?,?,?,?,?,?,?,?,'activo',0)
        """, (due.isoformat(), f"{concept} · cuota pendiente {i+1}/{int(count)} · {card}",
            category, amount, currency, "Cuota generada por el usuario", local_now().isoformat(timespec="seconds"),
            group, i+1, int(count), period_key))
