import pandas as pd
import streamlit as st
from core.finance import money, period_summary
from core.database import movements_df

def render(period, db):
    from core.history import render_references, render_history_notice
    st.header("🗓️ Proyección")
    render_history_notice(period, db)
    y,m=map(int,period.split("-"))
    rows=[]
    for i in range(6):
        yy=y+(m-1+i)//12
        mm=(m-1+i)%12+1
        pp=f"{yy:04d}-{mm:02d}"
        s,_=period_summary(pp,db)
        rows.append({
            "Mes":pp,
            "Ingresos":s["ingresos"],
            "Gastos pagados":s["gastos"],
            "Compromisos":s["compromisos"],
            "Flujo luego de compromisos":s["ingresos"]-s["gastos"]-s["compromisos"],
        })
    proj=pd.DataFrame(rows)
    show=proj.copy()
    for col in ["Ingresos","Gastos pagados","Compromisos","Flujo luego de compromisos"]:
        show[col]=show[col].map(money)
    st.dataframe(show,width="stretch",hide_index=True)
    st.caption("Proyección en ARS. La proyección usa únicamente lo cargado. No inventa ingresos ni gastos futuros.")
    st.caption("Los compromisos importados de octubre son un presupuesto: hay importes confirmados y otros estimados. Sus días de vencimiento no se informaron; no son pagos realizados. Los USD se muestran aparte sin cambio inventado.")
    usd_rows = movements_df(period, db)
    usd_rows = usd_rows[(usd_rows.tipo == "Compromiso") & (usd_rows.moneda != "ARS")]
    if not usd_rows.empty:
        usd_rows = usd_rows.copy()
        usd_rows["Monto"] = usd_rows.apply(lambda r: money(r.monto, r.moneda, True), axis=1)
        st.dataframe(usd_rows[["descripcion", "Monto", "notas"]], hide_index=True, width="stretch")
    render_references('Obligaciones' , db, 'Obligaciones pendientes de confirmar para la proyección')

# =========================================================
# PAGE: IA
# =========================================================
