import streamlit as st

from core.database import balances_df
from core.finance import money, period_summary


def _liquid_ars(db):
    balances = balances_df(db)
    if balances.empty:
        return 0.0
    mask = (
        (balances["moneda"] == "ARS")
        & (~balances["tipo"].isin(["Cuenta comitente", "Cuenta de inversión", "Cuenta crypto"]))
    )
    explicit = balances["liquidez_operativa"]
    mask = mask.where(explicit.isna(), (balances["moneda"] == "ARS") & (explicit == 1))
    return float(balances.loc[mask, "saldo"].sum())


def render(period, db):
    from core.navigation import go

    st.header("🏠 Inicio")
    st.subheader("¿Qué querés hacer?")

    actions = [
        ("Registrar un pago", "Pagos"),
        ("Registrar un ingreso", "Ingresos"),
        ("Ver mis pendientes", "Pendientes"),
        ("Mis cuentas", "Cuentas"),
    ]
    for col, (label, target) in zip(st.columns(2) * 2, actions):
        with col:
            if st.button(label, key="home_" + target, width="stretch"):
                go(target)

    st.metric("Dinero disponible para usar", money(_liquid_ars(db)))
    st.caption("La reserva, inversiones y dinero por cobrar se muestran en Mis cuentas.")

    with st.container(key="home_electro_card"):
        st.markdown("### ⚡ Electro financiero")
        st.write("La lectura completa de liquidez, solvencia y flujo quedó en una sección propia para que Inicio cargue más rápido.")
        if st.button("Abrir Electro", key="home_open_electro", type="primary"):
            go("Electro")

    st.markdown("### Resumen del período")
    summary, _ = period_summary(period, db)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", money(summary["ingresos"]))
    c2.metric("Gastos pagados", money(summary["gastos"]))
    c3.metric("Compromisos", money(summary["compromisos"]))
    c4.metric("Gastos flexibles", money(summary["discrecional"]))

    if not any(summary.values()):
        st.caption("Todavía no hay movimientos en este período. Podés empezar con un ingreso o un pago.")
