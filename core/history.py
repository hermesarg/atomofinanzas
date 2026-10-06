"""Presentación del registro recuperado sin inventar saldos o vencimientos."""
import pandas as pd
import streamlit as st
from core.database import dfq
from core.finance import money


def references(sections, db):
    if isinstance(sections, str):
        sections = [sections]
    marks = ','.join('?' for _ in sections)
    return dfq(f"SELECT * FROM referencias_importadas WHERE seccion IN ({marks}) ORDER BY id", tuple(sections), db=db)


def render_references(sections, db, title):
    rows = references(sections, db)
    if rows.empty:
        return
    with st.expander(f"{title} ({len(rows)} referencias)"):
        st.caption("Recuperado de tus documentos. El importe de referencia no es un saldo pendiente ni una nueva salida de dinero. Lo desconocido queda como Corroborar.")
        view = rows.copy()
        view['Importe de referencia'] = view.apply(lambda r: money(r['importe_referencia'], r['moneda'], True), axis=1)
        view = view.rename(columns={'concepto': 'Concepto', 'institucion': 'Entidad / acreedor', 'periodo': 'Período referido', 'estado_fuente': 'Registro original', 'estado_actual': 'Estado actual', 'fuente': 'Fuente', 'notas': 'Detalle'})
        st.dataframe(view[['Concepto', 'Entidad / acreedor', 'Importe de referencia', 'Período referido', 'Registro original', 'Estado actual', 'Detalle', 'Fuente']], width='stretch', hide_index=True)


def render_history_notice(period, db):
    import json
    from core.database import get_config
    count = dfq("SELECT COUNT(*) AS n FROM movimientos WHERE importado=1 AND COALESCE(periodo_registro,substr(fecha,1,7))=?", (period,), db=db).iloc[0, 0]
    if not count:
        return
    message = f"Tenés {count} registros importados en {period}. Los pagos históricos no se descuentan de nuevo de tus saldos."
    raw = get_config("cierre_martin_pdf_v3", "", db)
    if raw:
        record = json.loads(raw)
        if period == record.get("periodo"):
            message += f" Tu documento abarca {record['ciclo_desde']} a {record['ciclo_hasta']}; los días no informados quedan por confirmar."
    st.info(message)


def render_incomplete_notice(db):
    rows = references(['Deudas', 'Obligaciones'], db)
    if not rows.empty:
        unresolved = rows[rows.estado_actual.fillna("").str.contains("corroborar|estimar|estimado|referencia", case=False)]
        if not unresolved.empty:
            st.warning(f"Tenés {len(unresolved)} referencias de deudas u obligaciones por confirmar. Tu Electro es parcial hasta completarlas. Revisalas en Pendientes.")


def render_cycle_summary(period, db):
    import json
    from pathlib import Path
    from core.database import get_config
    raw = get_config("cierre_martin_pdf_v3", "", db)
    if not raw:
        return
    record = json.loads(raw)
    if period != record["periodo"]:
        return
    st.subheader("Cierre de tu ciclo de septiembre")
    st.caption(f"{record['ciclo_desde']} a {record['ciclo_hasta']} · importes de tu documento. Las salidas incluyen pagos de deuda, ahorro y prepagos; no son consumo puro.")
    a, b, c = st.columns(3)
    a.metric("Ingresos reales del ciclo", money(float(record["ingresos_ars"])))
    b.metric("Salidas ARS del documento", money(float(record["salidas_ars_pdf"]), decimals=True))
    c.metric("Consumos en USD", money(float(record["pagos_usd"]), "USD", True))
    st.caption(f"De tus salidas ARS, {money(float(record.get('salidas_que_no_son_consumo',0)))} corresponden a ahorro y activos/prepagos, separados del consumo. Capital y transferencias propias se muestran aparte.")
    st.caption(f"Activos rastreados en tu documento: {money(float(record['activos_rastreados_pdf']))}. Es una referencia de patrimonio, no una valoración de mercado ni todo efectivo disponible. Reserva aproximada: {money(float(record['reserva_aproximada']))}.")
    datafile = Path(__file__).resolve().parents[1] / "docs" / "cierre_septiembre_datos.json"
    if datafile.exists():
        with st.expander("Ver las 74 salidas originales del PDF"):
            data = json.loads(datafile.read_text(encoding="utf-8"))
            if data.get("control", {}).get("sha256_pdf") != record.get("sha256_pdf"):
                st.caption("El detalle disponible no corresponde a tu documento. Se conservan los totales de tu base.")
                return
            view = pd.DataFrame(data["salidas_confirmadas"])
            view["Monto"] = view.importe.map(lambda x: money(float(x), decimals=True))
            st.dataframe(view[["concepto", "categoria_pdf", "Monto", "pagina"]], hide_index=True, width="stretch")
