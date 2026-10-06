import streamlit as st
from core.database import con, get_config
from core.finance import amount_input, money

def render(period, db):
    st.header("⚙️ Configuración")
    st.caption("Configuración personal. El modo de prueba quedó oculto para no mezclarse con tus datos reales.")
    st.write("Estos valores afectan el Electro. No cambian movimientos ni ejecutan operaciones.")

    buffer=float(get_config("colchon_objetivo_ars",700000,db))
    disc=float(get_config("gasto_discrecional_objetivo_pct",15,db))

    a,b=st.columns(2)
    with a:
        new_buffer, buffer_raw = amount_input("Colchón objetivo ARS *", value=money(buffer, "ARS", True).partition(" ")[2])
    new_disc=b.number_input("Referencia de gastos flexibles (% del ingreso)",min_value=0.0,max_value=100.0,value=disc,step=1.0, help="Antes figuraba como gasto discrecional. Acá hablamos de gastos flexibles: salidas, ropa, ocio, etc.")

    if st.button("Guardar configuración"):
        if new_buffer is None or new_buffer < 0:
            st.error("Ingresá un colchón válido, sin valores negativos.")
            return
        with con(db) as connection:
            connection.executemany("INSERT INTO config(clave,valor) VALUES (?,?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", [("colchon_objetivo_ars", str(new_buffer)), ("gasto_discrecional_objetivo_pct", str(new_disc))])
        st.success("Guardado.")
        st.rerun()

    from core.periods import render_settings as render_period_settings
    render_period_settings(db)

    from core.security import web_private
    if web_private():
        from core.storage import render_backups
        render_backups(db)

    st.markdown("### Principios de la app")
    st.markdown(
        "- Los cálculos matemáticos pueden actualizarse automáticamente.\n"
        "- Ninguna deuda se adelanta, inversión se compra o gasto se autoriza automáticamente.\n"
        "- Las sugerencias presentan opciones; la persona elige.\n"
        "- La IA es complementaria: la app debe seguir siendo útil aunque la IA no esté disponible.\n"
        "- Todo indicador importante debe poder explicar de dónde salió.\n- Liquidez, solvencia y flujo se muestran por separado antes de resumirse en el Electro."
    )
