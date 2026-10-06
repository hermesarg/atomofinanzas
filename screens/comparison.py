from core.clock import today as local_today, local_now
from datetime import date
import pandas as pd
import streamlit as st
from core.config import MONEDAS
from core.database import alternatives_df, con
from core.finance import amount_input, electro_financiero, estimated_return, money

def render(period, db):
    st.header("⚖️ Comparar rendimientos")
    p=electro_financiero(period,db)

    if p["overall"] < 55:
        st.info(
            "Tu Electro todavía no marca mucha holgura. Igual podés comparar alternativas, "
            "pero la app no supone que invertir sea la prioridad."
        )
    else:
        st.success(
            "Hay algo de holgura según el Electro. Esta pantalla sirve para comparar, no para elegir por vos."
        )

    st.markdown("""
    <div class="help-card">
    <b>Compará sobre el mismo monto y plazo.</b> Una billetera, un plazo fijo, una letra y un bono
    no tienen el mismo riesgo ni la misma liquidez. El rendimiento solo no alcanza para decidir.
    </div>
    """,unsafe_allow_html=True)

    amount, amount_raw = amount_input("Monto a comparar *", value="1000000")
    if amount is None or amount <= 0:
        st.error("Ingresá un monto válido mayor que cero.")
        amount = 0.0
    amount = float(amount)
    days=st.slider("Horizonte para la estimación",7,365,30)

    compare_currency = st.selectbox("Moneda a comparar", MONEDAS)
    alts=alternatives_df(db)
    alts=alts[alts["moneda"] == compare_currency]
    if alts.empty:
        st.info("Todavía no cargaste alternativas de rendimiento.")
    else:
        if st.session_state.demo_mode:
            st.warning("Las tasas de esta tabla son FICTICIAS y sirven solamente para probar la interfaz.")
        rows=[]
        for _,r in alts.iterrows():
            ret=estimated_return(r["tasa_anual"],r["tipo_tasa"],days,amount)
            rows.append({
                "Categoría":r["categoria"],
                "Institución":r["institucion"],
                "Instrumento":r["instrumento"],
                "Tasa":f"{r['tasa_anual']:.2f}".replace(".", ",") + f"% {r['tipo_tasa']}",
                f"Estimación {days} días":money(ret,r["moneda"]),
                "_estimacion_valor": ret,
                "Liquidez":r["liquidez"],
                "Riesgo orientativo":r["riesgo"],
                "Fuente":r["fuente"] or "",
                "Actualizado":r["actualizado"] or "",
            })
        display_df = pd.DataFrame(rows).drop(columns=["_estimacion_valor"], errors="ignore")
        st.dataframe(display_df,width="stretch",hide_index=True)
        st.caption(
            "Las estimaciones convierten tasas a un horizonte común con fórmulas matemáticas simples. "
            "En bonos/TIR el resultado no está garantizado y el precio puede variar."
        )
        if rows:
            comp_df = pd.DataFrame(rows)
            top_row = comp_df.sort_values(by="_estimacion_valor", ascending=False).iloc[0]
            gain = float(top_row["_estimacion_valor"])
            st.markdown(
                f"**Lectura rápida:** con {money(amount, compare_currency)} durante {days} días, **{top_row['Instrumento']}** estima una "
                f"**ganancia de {money(gain, compare_currency, decimals=True)}** y un **total de {money(amount + gain, compare_currency, decimals=True)}**. "
                "Compará también liquidez y riesgo: mayor rendimiento no significa automáticamente mejor opción."
            )
            if len(comp_df) == 1:
                st.info("Agregá otra alternativa para comparar rendimientos sobre el mismo monto y plazo.")
            else:
                second = comp_df.sort_values(by="_estimacion_valor", ascending=False).iloc[1]
                diff = float(top_row["_estimacion_valor"] - second["_estimacion_valor"])
                st.caption(f"Diferencia estimada entre las dos primeras alternativas: {money(diff, compare_currency, decimals=True)} en {days} días.")

    with st.expander("➕ Cargar o actualizar una alternativa"):
        with st.form("alt_form",clear_on_submit=False):
            a,b=st.columns(2)
            cat=a.selectbox("Categoría de alternativa *",["Billetera virtual","Plazo fijo","Letra","Bono","FCI","Caución","Otro"])
            ins=b.text_input("Institución / mercado")
            instr=st.text_input("Instrumento / nombre específico *", help="Ej.: Plazo fijo 30 días, LECAP, AL30, billetera remunerada")
            a,b,c=st.columns(3)
            tt=a.selectbox("Tipo de tasa",["TNA","TEA","TIR"])
            rate=b.number_input("Tasa anual %",min_value=0.0,step=.1)
            cur=c.selectbox("Moneda",MONEDAS)
            a,b=st.columns(2)
            liq=a.text_input("Liquidez / plazo de salida",placeholder="Ej.: inmediata, 30 días, venta en mercado, T+1")
            risk=b.selectbox("Riesgo orientativo",["Bajo","Bajo/medio","Medio","Medio/alto","Alto"])
            source=st.text_input("Fuente")
            if st.form_submit_button("Agregar alternativa"):
                if instr.strip():
                    with con(db) as cdb:
                        cdb.execute("""
                        INSERT INTO alternativas_rendimiento(categoria,institucion,instrumento,tipo_tasa,tasa_anual,liquidez,riesgo,moneda,fuente,actualizado,demo)
                        VALUES (?,?,?,?,?,?,?,?,?,?,0)
                        """,(cat,ins,instr,tt,rate,liq,risk,cur,source,local_today().isoformat()))
                    st.rerun()

                else:
                    st.error("Falta el instrumento / nombre específico.")

    st.markdown("### Antes de decidir")
    st.write(
        "Usá esto como comparador. Si una alternativa implica riesgo de mercado, duración, impuestos "
        "o condiciones que no entendés, el siguiente paso es **consultar a tu asesor/idóneo**."
    )

# =========================================================
# PAGE: PROYECCIÓN
# =========================================================
