"""Períodos financieros configurables sin reescribir el historial."""
import calendar
from datetime import date, timedelta

import streamlit as st

from core.clock import today as local_today, local_now
from core.database import con, get_config, set_config

MODE_LABELS = {
    "calendar": "Mes calendario",
    "salary_fixed": "Desde mi fecha habitual de cobro",
    "salary_business": "Desde un día hábil del mes",
    "salary_manual": "Cuando confirmo que cobré el sueldo",
    "manual": "Yo inicio cada período manualmente",
}


def setup_complete(db):
    return bool(get_config("periodo_modo", "", db))


def _month_shift(year, month, delta):
    serial = year * 12 + (month - 1) + delta
    return serial // 12, serial % 12 + 1


def _fixed_day(year, month, day):
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(max(1, int(day)), last))


def _business_day(year, month, ordinal):
    """N-ésimo lunes-viernes. No intenta adivinar feriados."""
    ordinal = min(max(1, int(ordinal)), 23)
    cursor = date(year, month, 1)
    count = 0
    while cursor.month == month:
        if cursor.weekday() < 5:
            count += 1
            if count == ordinal:
                return cursor
        cursor += timedelta(days=1)
    return _fixed_day(year, month, calendar.monthrange(year, month)[1])


def _period_key(start):
    return start.strftime("%Y-%m")


def _criterion_detail(mode, value=None):
    if mode == "calendar":
        return "Del día 1 al último día del mes."
    if mode == "salary_fixed":
        return f"Comienza alrededor del día {int(value)} de cada mes."
    if mode == "salary_business":
        return f"Comienza el {int(value)}.º día hábil (lunes a viernes; no descuenta feriados)."
    if mode == "salary_manual":
        return "Comienza cuando confirmás que cobraste el sueldo."
    return "Comienza cuando vos lo indicás."


def _insert_period(start, end, mode, detail, db):
    key = _period_key(start)
    with con(db) as c:
        c.execute(
            """INSERT INTO periodos_financieros(periodo,inicio,fin,criterio,detalle,creado_en)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(periodo) DO UPDATE SET
                 inicio=excluded.inicio,
                 fin=COALESCE(periodos_financieros.fin, excluded.fin),
                 criterio=excluded.criterio,
                 detalle=excluded.detalle""",
            (
                key,
                start.isoformat(),
                end.isoformat() if end else None,
                MODE_LABELS.get(mode, mode),
                detail,
                local_now().isoformat(timespec="seconds"),
            ),
        )
    set_config("periodo_activo", key, db)
    return key


def _close_other_periods(new_start, new_key, db):
    with con(db) as c:
        rows = c.execute(
            "SELECT periodo,inicio,fin FROM periodos_financieros WHERE periodo<>? AND inicio<? ORDER BY inicio DESC",
            (new_key, new_start.isoformat()),
        ).fetchall()
        if rows:
            period, start, finish = rows[0]
            if not finish or finish >= new_start.isoformat():
                c.execute(
                    "UPDATE periodos_financieros SET fin=? WHERE periodo=?",
                    ((new_start - timedelta(days=1)).isoformat(), period),
                )


def start_period(start, db, mode=None, detail=None):
    if not isinstance(start, date):
        start = date.fromisoformat(str(start))
    mode = mode or get_config("periodo_modo", "manual", db)
    key = _period_key(start)

    if mode == "calendar":
        end = _fixed_day(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
    elif mode == "salary_fixed":
        day = int(get_config("periodo_dia", start.day, db))
        ny, nm = _month_shift(start.year, start.month, 1)
        end = _fixed_day(ny, nm, day) - timedelta(days=1)
    elif mode == "salary_business":
        ordinal = int(get_config("periodo_dia", 1, db))
        ny, nm = _month_shift(start.year, start.month, 1)
        end = _business_day(ny, nm, ordinal) - timedelta(days=1)
    else:
        end = None

    detail = detail or _criterion_detail(mode, get_config("periodo_dia", "", db) or None)
    _close_other_periods(start, key, db)
    return _insert_period(start, end, mode, detail, db)


def _expected_start(today, mode, value):
    if mode == "calendar":
        return today.replace(day=1)
    if mode == "salary_fixed":
        candidate = _fixed_day(today.year, today.month, value)
        if today >= candidate:
            return candidate
        py, pm = _month_shift(today.year, today.month, -1)
        return _fixed_day(py, pm, value)
    if mode == "salary_business":
        candidate = _business_day(today.year, today.month, value)
        if today >= candidate:
            return candidate
        py, pm = _month_shift(today.year, today.month, -1)
        return _business_day(py, pm, value)
    return None


def ensure_active_period(db, today=None):
    if not setup_complete(db):
        return None
    today = today or local_today()
    mode = get_config("periodo_modo", "calendar", db)
    active = get_config("periodo_activo", "", db)

    if mode in {"calendar", "salary_fixed", "salary_business"}:
        value = int(get_config("periodo_dia", 1, db) or 1)
        start = _expected_start(today, mode, value)
        expected = _period_key(start)
        if active != expected:
            active = start_period(start, db, mode=mode)
    elif not active:
        return None
    return active


def active_period(db):
    key = ensure_active_period(db)
    if not key:
        return None
    with con(db) as c:
        row = c.execute(
            "SELECT periodo,inicio,fin,criterio,detalle FROM periodos_financieros WHERE periodo=?",
            (key,),
        ).fetchone()
    if not row:
        return None
    return {
        "periodo": row[0],
        "inicio": row[1],
        "fin": row[2],
        "criterio": row[3],
        "detalle": row[4],
    }


def period_for_date(value, db):
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    value = str(value)[:10]
    with con(db) as c:
        row = c.execute(
            """SELECT periodo FROM periodos_financieros
               WHERE inicio<=? AND (fin IS NULL OR fin>=?)
               ORDER BY inicio DESC LIMIT 1""",
            (value, value),
        ).fetchone()
    if row:
        return row[0]
    return value[:7]


def save_preference(mode, value, db):
    if mode not in MODE_LABELS:
        raise ValueError("Elegí un criterio de período válido.")
    if mode in {"salary_fixed", "salary_business"}:
        value = int(value)
        max_value = 31 if mode == "salary_fixed" else 23
        if value < 1 or value > max_value:
            raise ValueError("El día elegido no es válido.")
        set_config("periodo_dia", value, db)
    else:
        set_config("periodo_dia", "", db)
    set_config("periodo_modo", mode, db)

    # Los cambios de criterio no reescriben períodos anteriores.
    if mode in {"calendar", "salary_fixed", "salary_business"}:
        start = _expected_start(local_today(), mode, int(value or 1))
        start_period(start, db, mode=mode)
    elif not get_config("periodo_activo", "", db):
        start_period(local_today(), db, mode=mode)


def render_setup(db):
    st.title("🗓️ ¿Cómo querés organizar tus meses?")
    st.write(
        "Átomo guarda la fecha real de cada movimiento, pero además puede agruparlos "
        "según tu ciclo financiero. Esta elección se puede cambiar después sin modificar períodos anteriores."
    )

    choice = st.radio(
        "Elegí el criterio inicial",
        [
            "Mes calendario",
            "Desde mi sueldo",
            "Manual",
        ],
        captions=[
            "Del 1 al último día del mes.",
            "El ciclo empieza alrededor de tu cobro.",
            "Vos decidís cuándo empieza cada período.",
        ],
    )

    mode = "calendar"
    value = None
    if choice == "Desde mi sueldo":
        subtype = st.radio(
            "¿Cómo querés indicar el cobro?",
            ["Día fijo del mes", "Día hábil", "Lo confirmo cuando cobro"],
            horizontal=True,
        )
        if subtype == "Día fijo del mes":
            mode = "salary_fixed"
            value = st.number_input("¿Qué día cobrás normalmente?", min_value=1, max_value=31, value=8, step=1)
        elif subtype == "Día hábil":
            mode = "salary_business"
            value = st.number_input("¿Qué número de día hábil?", min_value=1, max_value=23, value=5, step=1)
            st.caption("Por ahora cuenta lunes a viernes; no descuenta feriados nacionales.")
        else:
            mode = "salary_manual"
            st.caption("Cuando registres o confirmes el sueldo, vas a poder iniciar el nuevo período.")
    elif choice == "Manual":
        mode = "manual"

    if st.button("Guardar y empezar", type="primary", width="stretch"):
        save_preference(mode, value, db)
        st.session_state.pending_period = get_config("periodo_activo", local_today().strftime("%Y-%m"), db)
        st.rerun()


def render_status(db, compact=False):
    info = active_period(db)
    if not info:
        st.warning("Todavía no hay un período activo.")
        if st.button("Iniciar período hoy", type="primary", key="start_period_now"):
            start_period(local_today(), db)
            st.rerun()
        return

    start = date.fromisoformat(info["inicio"]).strftime("%d/%m/%Y")
    finish = date.fromisoformat(info["fin"]).strftime("%d/%m/%Y") if info["fin"] else "hasta que inicies el próximo"
    text = f"**{info['periodo']}** · {start} → {finish} · {info['criterio']}"
    if compact:
        st.caption(text)
    else:
        st.markdown(f'<div class="period-card">🗓️ {text}</div>', unsafe_allow_html=True)


def render_settings(db):
    st.markdown("### 🗓️ Períodos financieros")
    mode = get_config("periodo_modo", "calendar", db)
    current_label = MODE_LABELS.get(mode, mode)
    st.caption(f"Criterio actual: {current_label}. Los cambios se aplican hacia adelante; no se reescribe el historial.")

    labels = {
        "Mes calendario": "calendar",
        "Cobro: día fijo": "salary_fixed",
        "Cobro: día hábil": "salary_business",
        "Cobro: confirmo cuando cobro": "salary_manual",
        "Manual": "manual",
    }
    reverse = {v: k for k, v in labels.items()}
    selected = st.selectbox("Criterio para próximos períodos", list(labels), index=list(labels).index(reverse.get(mode, "Mes calendario")))
    new_mode = labels[selected]
    value = None
    if new_mode == "salary_fixed":
        value = st.number_input("Día habitual de cobro", 1, 31, int(get_config("periodo_dia", 8, db) or 8))
    elif new_mode == "salary_business":
        value = st.number_input("Número de día hábil", 1, 23, int(get_config("periodo_dia", 5, db) or 5))
        st.caption("Cuenta lunes a viernes; no descuenta feriados.")

    if st.button("Guardar criterio para próximos períodos", key="save_period_pref"):
        save_preference(new_mode, value, db)
        st.success("Criterio guardado. Los períodos anteriores conservaron su definición.")
        st.rerun()

    if new_mode in {"manual", "salary_manual"}:
        with st.expander("Iniciar un nuevo período ahora"):
            start = st.date_input("Fecha de inicio", value=local_today(), key="manual_period_start")
            if st.button("Iniciar período", key="manual_period_button", type="primary"):
                detail = "Iniciado al confirmar cobro de sueldo." if new_mode == "salary_manual" else "Iniciado manualmente."
                start_period(start, db, mode=new_mode, detail=detail)
                st.session_state.pending_period = start.strftime("%Y-%m")
                st.rerun()
