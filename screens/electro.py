import pandas as pd
import streamlit as st

from core.finance import (
    atomo_profile,
    deterministic_suggestions,
    electro_financiero,
    money,
    period_summary,
    render_atomo_profile,
    render_electro,
    yield_snapshot,
)


def render(period, db):
    st.header("⚡ Electro financiero")
    st.caption("Una lectura rápida de liquidez, solvencia y flujo. No toma decisiones por vos.")

    with st.spinner("Leyendo tus datos financieros…"):
        e = electro_financiero(period, db)

    if e.get("_unresolved_refs", 0):
        st.warning(
            f"Tenés {e['_unresolved_refs']} referencias de deudas u obligaciones por confirmar. "
            "El Electro es parcial hasta completarlas en Pendientes."
        )

    render_electro(e)

    st.markdown("### Perfil de Átomo")
    profile = atomo_profile(period, db, electro=e)
    render_atomo_profile(profile)
    st.caption("El nivel mide progreso y orden relativo, no riqueza absoluta.")

    with st.expander("¿Qué está mirando el Electro?"):
        st.write(
            "El cálculo es determinista: combina tres canales separados. "
            "**Liquidez** mira caja disponible frente a vencimientos y colchón; "
            "**Solvencia** compara activos conocidos con deudas y compromisos; "
            "**Flujo** compara ingresos con gastos y compromisos del período."
        )
        detail = pd.DataFrame([
            {
                "Canal": "Liquidez",
                "Estado": e["liquidity_state"],
                "Índice interno": f"{e['liquidity']:.1f}/100",
                "Lectura": f"{money(e['liquid_ars'])} líquidos vs. {money(e['commitment_45_ars'])} de compromisos próximos + colchón.",
            },
            {
                "Canal": "Solvencia",
                "Estado": e["solvency_state"],
                "Índice interno": f"{e['solvency']:.1f}/100",
                "Lectura": f"{money(e['assets_known'])} de activos conocidos vs. {money(e['liabilities_known'])} de pasivos cargados.",
            },
            {
                "Canal": "Flujo",
                "Estado": e["flow_state"],
                "Índice interno": f"{e['flow']:.1f}/100",
                "Lectura": f"{money(e['income'])} de ingresos y {money(e['expenses'] + e['period_commitments'])} entre gastos/compromisos.",
            },
        ])
        st.dataframe(detail, width="stretch", hide_index=True)
        st.caption("Se calcula en ARS y con los datos efectivamente cargados.")

    suggestions, watch = deterministic_suggestions(period, db, electro=e)
    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("Qué podrías hacer ahora")
        st.caption("Opciones para que vos decidas. La app no ejecuta ninguna.")
        for i, suggestion in enumerate(suggestions, 1):
            st.markdown(f"**{i}.** {suggestion}")
        st.markdown("#### Una cosa para vigilar")
        st.info(watch)

    with right:
        yld = yield_snapshot(db, 30, balances=e.get("_balances"))
        st.subheader("Caja que genera rendimiento")
        c1, c2 = st.columns(2)
        c1.metric("Saldo remunerado", money(yld["remunerated_balance"]))
        c2.metric("Estimación próximos 30 días", money(yld["estimated_yield"], decimals=True))
        if yld["unremunerated_liquid"] > 0:
            st.caption(f"{money(yld['unremunerated_liquid'])} de liquidez está en cuentas marcadas como no remuneradas.")

    st.markdown("---")
    st.subheader("Resumen rápido")
    summary = e.get("_summary") or period_summary(period, db)[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", money(summary["ingresos"]))
    c2.metric("Gastos pagados", money(summary["gastos"]))
    c3.metric("Compromisos", money(summary["compromisos"]))
    c4.metric("Gastos flexibles", money(summary["discrecional"]))
