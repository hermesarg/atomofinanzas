import pandas as pd
import streamlit as st
from core.finance import atomo_profile, deterministic_suggestions, electro_financiero, money, period_summary, render_atomo_profile, render_electro, yield_snapshot

def render(period, db):
    from core.navigation import go
    st.header("🏠 Inicio")
    st.subheader("¿Qué querés hacer?")
    actions = [("Registrar un pago", "Pagos"), ("Registrar un ingreso", "Ingresos"),
               ("Ver mis pendientes", "Pendientes"), ("Mis cuentas", "Cuentas")]
    for col, (label, target) in zip(st.columns(2) * 2, actions):
        with col:
            if st.button(label, key="home_" + target, width="stretch"):
                go(target)
    from core.database import balances_df
    from core.finance import electro_financiero
    st.metric("Dinero disponible para usar", money(electro_financiero(period, db)["liquid_ars"]))
    st.caption("La reserva, inversiones y dinero por cobrar se muestran en Mis cuentas.")
    with st.expander("Ver mi resumen y Electro", expanded=False):
        from core.history import render_history_notice, render_incomplete_notice
        render_history_notice(period, db)
        from core.history import render_cycle_summary
        render_cycle_summary(period, db)
        render_incomplete_notice(db)
        e = electro_financiero(period, db)
        suggestions, watch = deterministic_suggestions(period, db)
        yld = yield_snapshot(db, 30)
        profile = atomo_profile(period, db)
    
        render_electro(e)
        render_atomo_profile(profile)
        st.caption("El nivel de Átomo mide progreso y orden relativo, no riqueza absoluta. Las escalas internas quedan ocultas.")
    
        with st.expander("¿Qué está mirando el Electro?"):
            st.write(
                "No lo decide la IA. El dibujo cambia según tres cálculos separados: "
                "**Liquidez**, **Solvencia** y **Flujo**. Una señal más irregular significa "
                "que uno o más de esos canales tienen menos margen con los datos cargados."
            )
            detail = pd.DataFrame([
                {
                    "Canal":"Liquidez",
                    "Estado":e["liquidity_state"],
                    "Índice interno":f"{e['liquidity']:.1f}/100",
                    "Lectura":f"{money(e['liquid_ars'])} líquidos vs. {money(e['commitment_45_ars'])} de compromisos próximos + colchón.",
                },
                {
                    "Canal":"Solvencia",
                    "Estado":e["solvency_state"],
                    "Índice interno":f"{e['solvency']:.1f}/100",
                    "Lectura":f"{money(e['assets_known'])} de activos conocidos vs. {money(e['liabilities_known'])} de pasivos cargados.",
                },
                {
                    "Canal":"Flujo",
                    "Estado":e["flow_state"],
                    "Índice interno":f"{e['flow']:.1f}/100",
                    "Lectura":f"{money(e['income'])} de ingresos y {money(e['expenses'] + e['period_commitments'])} entre gastos/compromisos.",
                },
            ])
            st.dataframe(detail, width="stretch", hide_index=True)
            st.caption(
                "El Electro se calcula en ARS, sin convertir otras monedas. Solvencia es una estimación con lo que cargaste. Si faltan inversiones, deudas o cuotas, cambia la lectura."
            )
    
        left, right = st.columns([1.25, 1])
    
        with left:
            st.subheader("Qué podrías hacer ahora")
            st.caption("Opciones para que vos decidas. La app no ejecuta ninguna.")
            for i, s in enumerate(suggestions, 1):
                st.markdown(f"**{i}.** {s}")
            st.markdown("#### Una cosa para vigilar")
            st.info(watch)
    
        with right:
            st.subheader("Caja que genera rendimiento")
            c1, c2 = st.columns(2)
            c1.metric("Saldo remunerado", money(yld["remunerated_balance"]))
            c2.metric("Estimación próximos 30 días", money(yld["estimated_yield"], decimals=True))
            st.caption(
                "Estimación hacia adelante con el saldo y la tasa cargados hoy. "
                "No es rendimiento histórico ni garantizado."
            )
    
            if yld["unremunerated_liquid"] > 0:
                st.markdown(
                    f"**{money(yld['unremunerated_liquid'])}** de la liquidez cargada está en cuentas "
                    "marcadas como no remuneradas."
                )
            st.markdown(
                "💡 Si registrás un gasto desde una billetera remunerada, ese saldo baja y "
                "esta estimación de rendimiento baja automáticamente."
            )
    
        if not yld["rows"].empty:
            with st.expander("Ver detalle de cuentas remuneradas / no remuneradas"):
                yd = yld["rows"].copy()
                yd["Saldo"] = yd["Saldo"].map(lambda x: money(x))
                yd["Rend. estimado 30d"] = yd["Rend. estimado 30d"].map(lambda x: money(x, decimals=True))
                st.dataframe(yd, width="stretch", hide_index=True)
    
        st.markdown("---")
        st.subheader("Resumen rápido")
        summary, _ = period_summary(period, db)
        st.caption("Resumen en ARS. Otras monedas se muestran por separado en sus cuentas.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", money(summary["ingresos"]))
        c2.metric("Gastos pagados", money(summary["gastos"]))
        c3.metric("Compromisos", money(summary["compromisos"]))
        c4.metric("Gastos flexibles", money(summary["discrecional"]))
    
    # =========================================================
    # PAGE: CUENTAS
    # =========================================================
