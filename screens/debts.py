from core.clock import today as local_today, local_now
from datetime import date
from datetime import datetime
import streamlit as st
import pandas as pd
from core.config import MONEDAS
from core.database import con, debts_df
from core.finance import amount_input, electro_financiero, institution_map, money

def render(period, db):
    from core.history import render_references
    st.header("🧾 Deudas y préstamos")
    st.markdown("""
    <div class="help-card">
    <b>¿Querés adelantar una deuda?</b> Primero simulala. La app puede mostrar cómo cambia tu liquidez y tu Electro,
    y no registra pagos. Cargar un gasto en Movimientos no actualiza automáticamente el saldo de esta deuda.
    </div>
    """,unsafe_allow_html=True)

    imap=institution_map(db=db)
    render_references(['Deudas', 'Obligaciones'], db, 'Préstamos y obligaciones recuperados')
    with st.expander("➕ Agregar deuda"):
        with st.form("debt_form",clear_on_submit=False):
            ins=st.selectbox("Institución / acreedor *",list(imap.keys()) if imap else [""])
            name=st.text_input("Nombre de la deuda *")
            a,b,c=st.columns(3)
            bal, bal_raw = amount_input("Saldo pendiente *", value="0")
            q, q_raw = amount_input("Cuota", value="0")
            rem=c.number_input("Cuotas restantes",0,360,0)
            a,b=st.columns(2)
            due=a.date_input("Próximo vencimiento",value=local_today())
            cur=b.selectbox("Moneda",MONEDAS)
            rate=st.text_input("Tasa / referencia")
            if st.form_submit_button("Guardar deuda"):
                if name.strip() and imap and bal is not None and bal >= 0 and q is not None and q >= 0:
                    with con(db) as cdb:
                        cdb.execute("""
                        INSERT INTO deudas(institucion_id,nombre,saldo_pendiente,cuota,cuotas_restantes,proximo_vencimiento,moneda,tasa_info,activa,notas,creada_en)
                        VALUES (?,?,?,?,?,?,?,?,1,'',?)
                        """,(imap[ins],name,bal,q,rem,due.isoformat(),cur,rate,local_now().isoformat(timespec="seconds")))
                    st.rerun()

                else:
                    st.error("Completá el nombre y revisá saldo y cuota: deben ser números válidos, sin valores negativos.")

    debt=debts_df(db)
    if debt.empty:
        st.info("No hay saldos pendientes vigentes confirmados cargados. Los pagos históricos y las referencias por corroborar se muestran arriba.")
    else:
        v=debt.copy()
        v["cuotas_restantes"] = v["cuotas_restantes"].map(lambda x: "Corroborar" if pd.isna(x) else str(int(x)))
        v["proximo_vencimiento"] = v["proximo_vencimiento"].fillna("Corroborar")
        v["Saldo"]=v.apply(lambda r:money(r["saldo_pendiente"],r["moneda"]),axis=1)
        v["Cuota"]=v.apply(lambda r:money(r["cuota"],r["moneda"]),axis=1)
        st.dataframe(v[["institucion","nombre","Saldo","Cuota","cuotas_restantes","proximo_vencimiento","tasa_info","notas"]],width="stretch",hide_index=True)

        st.caption("Corroborar significa saldo total desconocido, no deuda cero. Las cuotas estimadas se identifican en las notas; el presupuesto está en Proyección.")
        st.subheader("Simular un adelanto")
        dmap={f"{r['institucion']} · {r['nombre']} · #{r['id']}":int(r["id"]) for _,r in debt.iterrows()}
        ds=st.selectbox("Deuda",list(dmap.keys()))
        debt_currency=debt.loc[debt.id == dmap[ds], "moneda"].iloc[0]
        if debt_currency != "ARS":
            st.info("Esta simulación de liquidez trabaja en ARS. No se convierten deudas de otras monedas.")
            st.stop()
        adel, adel_raw = amount_input("Monto a adelantar", value="0")
        p=electro_financiero(period,db)
        if adel is None or adel < 0:
            st.error("Ingresá un monto de adelanto válido, sin valores negativos.")
            return
        adel = float(adel)
        after=p["liquid_ars"]-adel
        free_after=after-p["commitment_45_ars"]-p["buffer_target"]
        c1,c2=st.columns(2)
        c1.metric("Liquidez estimada después",money(after))
        c2.metric("Margen después de compromisos/colchón",money(free_after))
        st.caption("Simulación solamente. No registra ningún pago.")

# =========================================================
# PAGE: INVERSIONES
# =========================================================
