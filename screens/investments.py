from core.clock import today as local_today, local_now
from datetime import datetime
import streamlit as st
from core.config import MONEDAS, TIPOS_ACTIVO
from core.database import accounts_df, accounts_match_currency, con, positions_df
from core.finance import amount_input, money

def render(period, db):
    from core.history import render_references
    st.header("📈 Inversiones")
    render_references('Inversiones', db, 'Inversiones recuperadas del historial')
    acc=accounts_df(db)
    inv=acc[acc["tipo_cuenta"].isin(["Cuenta comitente","Cuenta de inversión","Cuenta crypto"])] if not acc.empty else acc

    st.markdown("""
    <div class="help-card">
    <b>¿Mandaste dinero a un broker?</b> Primero cargalo como transferencia desde tu banco hacia la cuenta comitente.
    Las posiciones cargadas son una foto del monto invertido y su valor actual: no descuentan caja ni ejecutan compras.
    </div>
    """,unsafe_allow_html=True)

    if inv.empty:
        st.info("Creá primero una cuenta comitente/de inversión en Cuentas.")
    else:
        invmap={f"{r['institucion']} · {r['nombre']} · {r['moneda']} · #{r['id']}":int(r["id"]) for _,r in inv.iterrows()}
        with st.expander("➕ Agregar posición"):
            with st.form("pos_form",clear_on_submit=False):
                account=st.selectbox("Cuenta",list(invmap.keys()))
                a,b=st.columns(2)
                typ=a.selectbox("Activo",TIPOS_ACTIVO)
                ticker=b.text_input("Ticker")
                desc=st.text_input("Descripción *")
                a,b,c=st.columns(3)
                invested, invested_raw = amount_input("Monto invertido *", value="0")
                current_value, current_raw = amount_input("Valor actual *", value="0")
                cur=c.selectbox("Moneda",MONEDAS)
                st.caption("Para simplificar, cargá el monto invertido y el valor actual. La cantidad/unidades queda oculta.")
                if st.form_submit_button("Guardar posición"):
                    if desc.strip() and invested is not None and invested > 0 and current_value is not None and current_value >= 0 and accounts_match_currency([invmap[account]], cur, db):
                        with con(db) as cdb:
                            cdb.execute("""
                            INSERT INTO posiciones(cuenta_id,tipo_activo,ticker,descripcion,cantidad,precio_promedio,precio_actual,moneda,notas,creada_en)
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                            """,(invmap[account],typ,ticker.upper(),desc,1.0,invested,current_value,cur,"",local_now().isoformat(timespec="seconds")))
                        st.rerun()

                    else:
                        st.error("Completá la descripción, el monto invertido positivo y un valor actual válido, en la moneda de la cuenta.")

    pos=positions_df(db)
    if pos.empty:
        st.info("No hay inversiones cargadas.")
    else:
        v=pos.copy()
        v["valor_actual"]=v["cantidad"]*v["precio_actual"]
        v["costo"]=v["cantidad"]*v["precio_promedio"]
        v["resultado"]=v["valor_actual"]-v["costo"]
        v["Monto invertido"] = v.apply(lambda r:money(r["costo"],r["moneda"],True),axis=1)
        v["Valor actual"] = v.apply(lambda r:money(r["valor_actual"],r["moneda"],True),axis=1)
        v["Resultado"] = v.apply(lambda r:money(r["resultado"],r["moneda"],True),axis=1)
        if v['precio_actual'].isna().any():
            st.info('Hay inversiones cuyo costo o valor actual falta corroborar. No se supone ganancia o pérdida ni se incluyen esas valoraciones desconocidas en Solvencia.')
        st.dataframe(v[["institucion","cuenta","tipo_activo","ticker","descripcion","Monto invertido","Valor actual","Resultado", 'notas']],width="stretch",hide_index=True)

# =========================================================
# PAGE: COMPARAR RENDIMIENTOS
# =========================================================
