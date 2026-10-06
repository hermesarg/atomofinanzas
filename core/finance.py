from core.clock import today as local_today, local_now
import math
import re
from datetime import date
from datetime import timedelta
import calendar
import pandas as pd
import streamlit as st
from core.config import DISCRETIONARY
from core.database import accounts_df, balances_df, debts_df, dfq, get_config, institutions_df, movements_df, positions_df

def add_months(d, months):
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)

def money(n, currency="ARS", decimals=False):
    if n is None or pd.isna(n):
        return "Corroborar"
    n = float(n or 0)
    dec = 2 if decimals or currency != "ARS" or n != round(n) else 0
    s = f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}" if currency == "ARS" else f"{currency} {s}"


def parse_amount(value):
    if value is None:
        return None
    raw = re.sub(r"^(?:ARS|USDT|USD|EUR|\$)\s*", "", str(value).strip())
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?", raw):
        return None
    try:
        amount = float(raw.replace(".", "").replace(",", "."))
        return amount if math.isfinite(amount) and abs(amount) <= 1e15 else None
    except ValueError:
        return None


def amount_input(label, value="", key=None, help=None, placeholder="Ej.: 125000 o 125.000,50"):
    raw = st.text_input(label, value=value, key=key, help=help, placeholder=placeholder)
    amt = parse_amount(raw)
    return amt, raw


def fmt_day(value):
    if value in (None, "", 0):
        return "—"
    try:
        iv = int(value)
        return str(iv)
    except Exception:
        return "—"

def account_map(db=None):
    acc = accounts_df(db)
    mp = {}
    for _, r in acc.iterrows():
        if r["tipo_cuenta"] in ["Cuenta por cobrar", "Prepago"]:
            continue
        lab = f"{r['nombre']} · {r['moneda']} · #{r['id']}"
        mp[lab] = int(r["id"])
    return mp

def institution_map(types=None, db=None):
    d = institutions_df(db)
    if types:
        d = d[d["tipo"].isin(types)]
    return {f"{r['nombre']} [{r['tipo']}]": int(r["id"]) for _, r in d.iterrows()}

def period_summary(period, db=None):
    m = movements_df(period, db)
    all_moves = m
    if m.empty:
        return {"ingresos":0., "gastos":0., "compromisos":0., "transferencias":0., "discrecional":0.}, m
    m = m[m["moneda"].fillna("ARS") == "ARS"]
    return {
        "ingresos": float(m.loc[m.tipo=="Ingreso","monto"].sum()),
        "gastos": float(m.loc[m.tipo=="Gasto","monto"].sum()),
        "compromisos": float(m.loc[m.tipo=="Compromiso","monto"].sum()),
        "transferencias": float(m.loc[m.tipo=="Transferencia","monto"].sum()),
        "discrecional": float(m.loc[(m.tipo=="Gasto") & (m.categoria.isin(DISCRETIONARY)),"monto"].sum()),
    }, all_moves

def commitments_next(days=45, db=None):
    end = local_today() + timedelta(days=days)
    d = dfq("""
    SELECT * FROM movimientos
    WHERE tipo='Compromiso'
      AND COALESCE(estado,'activo')='activo'
      AND date(fecha)<=date(?)
    ORDER BY fecha
    """, (end.isoformat(),), db=db)
    return d

# =========================================================
# ELECTRO FINANCIERO (100% DETERMINISTA)
# =========================================================

def _band(score):
    score = float(score)
    if score < 25:
        return "Ajustado"
    if score < 45:
        return "A vigilar"
    if score < 65:
        return "Estable"
    if score < 85:
        return "Firme"
    return "Muy firme"

def _piecewise_coverage(ratio):
    ratio = max(0.0, float(ratio))
    if ratio < .5:
        return 30 * ratio / .5
    if ratio < 1.0:
        return 30 + 35 * (ratio - .5) / .5
    if ratio < 1.5:
        return 65 + 20 * (ratio - 1.0) / .5
    if ratio < 2.0:
        return 85 + 15 * (ratio - 1.5) / .5
    return 100.0

def electro_financiero(period, db=None):
    summary, _ = period_summary(period, db)
    balances = balances_df(db)
    debts = debts_df(db)
    positions = positions_df(db)
    commitments_45 = commitments_next(45, db)
    all_commitments = dfq("""
        SELECT monto,moneda,deuda_id FROM movimientos
        WHERE tipo='Compromiso' AND COALESCE(estado,'activo')='activo'
    """, db=db)

    # ---------- LIQUIDEZ ----------
    liquid_ars = 0.0
    if not balances.empty:
        liquid_mask = (
            (balances["moneda"] == "ARS") &
            (~balances["tipo"].isin(["Cuenta comitente","Cuenta de inversión","Cuenta crypto"]))
        )
        explicit = balances["liquidez_operativa"]
        liquid_mask = liquid_mask.where(explicit.isna(), (balances["moneda"] == "ARS") & (explicit == 1))
        liquid_ars = float(balances.loc[liquid_mask, "saldo"].sum())

    commitment_45_ars = 0.0
    if not commitments_45.empty:
        mask = commitments_45["moneda"].fillna("ARS") == "ARS"
        commitment_45_ars = float(commitments_45.loc[mask, "monto"].sum())

    if not debts.empty:
        end = (local_today() + timedelta(days=45)).isoformat()
        scheduled = debts[(debts["moneda"].fillna("ARS") == "ARS") &
            debts["proximo_vencimiento"].notna() & (debts["proximo_vencimiento"] <= end)]
        linked = set(commitments_45["deuda_id"].dropna())
        scheduled = scheduled[~scheduled["id"].isin(linked)]
        commitment_45_ars += float(scheduled["cuota"].sum())

    buffer_target = float(get_config("colchon_objetivo_ars", 700000, db))
    liquidity_need = max(commitment_45_ars + buffer_target, 1.0)
    liquidity_ratio = liquid_ars / liquidity_need
    liquidity_score = max(0, min(100, _piecewise_coverage(liquidity_ratio)))

    # ---------- SOLVENCIA ----------
    # Patrimonio conocido: saldos de cuentas (incluida reserva y prepagos)
    # más posiciones valoradas. El fondo YPF sin desglose queda como referencia
    # y no se inventa valoración ni se duplica como cuenta y posición.
    investment_value_ars = 0.0
    if not positions.empty:
        pos_ars = positions[positions["moneda"] == "ARS"].copy()
        if not pos_ars.empty:
            investment_value_ars = float((pos_ars["cantidad"] * pos_ars["precio_actual"]).sum())

    accounts_ars = float(balances.loc[balances["moneda"] == "ARS", "saldo"].sum()) if not balances.empty else 0
    assets_known = max(accounts_ars, 0) + max(investment_value_ars, 0)

    debt_balance_ars = 0.0
    if not debts.empty:
        debt_balance_ars = float(
            debts.loc[debts["moneda"].fillna("ARS")=="ARS", "saldo_pendiente"].sum()
        )

    future_commitments_ars = 0.0
    if not all_commitments.empty:
        known_debts = set(debts.loc[debts["saldo_pendiente"].notna(), "id"]) if not debts.empty else set()
        mask = (all_commitments["moneda"].fillna("ARS") == "ARS") & ~all_commitments["deuda_id"].isin(known_debts)
        future_commitments_ars = float(all_commitments.loc[mask, "monto"].sum())

    liabilities_known = max(0.0, debt_balance_ars + future_commitments_ars)

    if liabilities_known <= 0:
        solvency_ratio = float("inf") if assets_known > 0 else 1.0
        solvency_score = 100.0 if assets_known > 0 else 60.0
    else:
        solvency_ratio = assets_known / liabilities_known
        if solvency_ratio < .5:
            solvency_score = 15 * solvency_ratio / .5
        elif solvency_ratio < 1:
            solvency_score = 15 + 35 * (solvency_ratio - .5) / .5
        elif solvency_ratio < 2:
            solvency_score = 50 + 30 * (solvency_ratio - 1)
        elif solvency_ratio < 4:
            solvency_score = 80 + 20 * (solvency_ratio - 2) / 2
        else:
            solvency_score = 100.0
        solvency_score = max(0, min(100, solvency_score))

    # ---------- FLUJO ----------
    income = float(summary["ingresos"])
    expenses = float(summary["gastos"])
    period_commitments = float(summary["compromisos"])
    if income > 0:
        net_after = income - expenses - period_commitments
        net_ratio = net_after / income
        # -20% -> 0 | 0% -> 33 | +20% -> 67 | +40% -> 100
        flow_score = 100 * (net_ratio + .20) / .60
        flow_score = max(0, min(100, flow_score))
    else:
        net_after = -expenses - period_commitments
        net_ratio = 0.0
        flow_score = 50.0 if (expenses + period_commitments) == 0 else 20.0

    # El estado general no reemplaza a los tres canales.
    # La señal se vuelve más errática si alguno de ellos queda muy rezagado.
    overall_score = round(
        liquidity_score * .40 +
        solvency_score * .35 +
        flow_score * .25
    )

    dispersion = max(liquidity_score, solvency_score, flow_score) - min(
        liquidity_score, solvency_score, flow_score
    )
    tension = min(100.0, (100 - overall_score) * .78 + dispersion * .35)

    free_after = liquid_ars - commitment_45_ars - buffer_target

    return {
        "overall": int(max(0, min(100, overall_score))),
        "state": _band(overall_score),
        "tension": tension,
        "liquidity": round(liquidity_score, 1),
        "liquidity_state": _band(liquidity_score),
        "liquid_ars": liquid_ars,
        "commitment_45_ars": commitment_45_ars,
        "buffer_target": buffer_target,
        "free_after": free_after,
        "solvency": round(solvency_score, 1),
        "solvency_state": _band(solvency_score),
        "assets_known": assets_known,
        "liabilities_known": liabilities_known,
        "solvency_ratio": solvency_ratio,
        "flow": round(flow_score, 1),
        "flow_state": _band(flow_score),
        "income": income,
        "expenses": expenses,
        "period_commitments": period_commitments,
        "net_after": net_after,
        "net_ratio": net_ratio,
        "flexible_spend": float(summary["discrecional"]),
        "_balances": balances,
        "_summary": summary,
    }

def deterministic_suggestions(period, db=None, electro=None):
    e = electro if electro is not None else electro_financiero(period, db)
    suggestions = []
    watch = []

    if e["commitment_45_ars"] > 0:
        reserve = min(e["liquid_ars"], e["commitment_45_ars"])
        suggestions.append(
            f"Reservar {money(reserve)} para compromisos de los próximos 45 días antes de asignar ese saldo a otra cosa."
        )

    if e["free_after"] < 0:
        suggestions.append(
            f"Faltan aproximadamente {money(abs(e['free_after']))} para cubrir próximos compromisos más tu colchón objetivo."
        )
    elif e["liquidity"] >= 65 and e["free_after"] > 0:
        suggestions.append(
            f"Después de próximos compromisos y colchón quedan aproximadamente {money(e['free_after'])} líquidos para que decidas su destino."
        )

    if e["solvency"] < 45:
        suggestions.append(
            "La solvencia cargada está más exigida que la liquidez. Antes de sumar deuda, revisá saldo pendiente y compromisos futuros."
        )

    if e["flow"] < 45:
        suggestions.append(
            "El flujo del período merece atención: ingresos menos gastos y compromisos está dejando poco margen."
        )

    if e["income"] > 0:
        flexible_ratio = e["flexible_spend"] / e["income"]
        target = float(get_config("gasto_discrecional_objetivo_pct", 15, db))/100
        if flexible_ratio > target:
            watch.append(
                f"Los gastos flexibles van en {flexible_ratio*100:.1f}% del ingreso, por encima de tu referencia de {target*100:.0f}%.".replace(".", ",", 1)
            )

    if not suggestions:
        suggestions.append("Con los datos cargados no aparece una acción matemática prioritaria. Podés revisar objetivos o alternativas para el excedente.")
    if not watch and min(e["liquidity"], e["solvency"], e["flow"]) < 45:
        watch.append("Uno de los canales está ajustado. Revisá por separado liquidez, solvencia y flujo, y los datos que faltan.")
    if not watch:
        watch.append("No aparece una tensión fuerte en los datos cargados. Revisá igualmente si faltan cuotas, deudas o vencimientos.")

    return suggestions[:4], watch[0]

def _ecg_points(score, width=760, height=105):
    """Devuelve una polilínea determinista. Menor score => más irregularidad."""
    score = max(0.0, min(100.0, float(score)))
    irr = (100.0 - score) / 100.0
    base = height * .56
    points = [(0, base)]
    beats = 6
    beat_w = width / beats

    for i in range(beats):
        x0 = i * beat_w
        shift = math.sin((i+1)*2.17) * 9 * irr
        amp = 18 + 25 * irr + (i % 2) * 4 * irr
        wobble = 2 + 9 * irr

        pts = [
            (x0 + 8, base + math.sin(i*1.7)*wobble),
            (x0 + 28 + shift, base + math.cos(i*1.3)*wobble*.55),
            (x0 + 38 + shift, base - 4 - wobble*.25),
            (x0 + 46 + shift, base + 7 + wobble*.55),
            (x0 + 55 + shift, base - amp),
            (x0 + 65 + shift, base + amp*.62),
            (x0 + 76 + shift, base - amp*.28),
            (x0 + 92, base + math.sin(i*2.0)*wobble*.65),
            (x0 + beat_w - 3, base + math.cos(i*1.8)*wobble*.35),
        ]

        if irr > .55:
            pts.insert(2, (x0 + 33 + shift, base - 10*irr))
            pts.insert(8, (x0 + 84 + shift, base + 11*irr))

        points.extend(pts)

    return " ".join(f"{max(0,min(width,x)):.1f},{max(5,min(height-5,y)):.1f}" for x,y in points)

def render_electro(e):
    pts = _ecg_points(100 - e["tension"])

    if min(e["liquidity"], e["solvency"], e["flow"]) >= 65:
        explanation = "La señal es relativamente regular: los tres canales cargados están razonablemente sostenidos."
    elif e["overall"] >= 45:
        explanation = "La señal muestra algunas variaciones: hay equilibrio general, pero al menos un canal tiene menos margen."
    else:
        explanation = "La señal se vuelve más irregular cuando liquidez, solvencia o flujo requieren más atención. No es una alarma: indica dónde mirar."

    st.markdown(
        f"""
        <div class="electro-card">
          <div class="at-muted">ELECTRO FINANCIERO</div>
          <div class="electro-title">{e['state']}</div>
          <div class="electro-state">{explanation}</div>
          <svg class="electro-svg" viewBox="0 0 760 105" preserveAspectRatio="none" aria-label="Electro financiero">
            <defs>
              <linearGradient id="atomoElectroGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff8a1f"/>
                <stop offset="52%" stop-color="#ffad55"/>
                <stop offset="100%" stop-color="#ffd08b"/>
              </linearGradient>
            </defs>
            <line class="electro-baseline" x1="0" y1="59" x2="760" y2="59" stroke-width="1"/>
            <polyline class="electro-wave" points="{pts}" fill="none" stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round"/>
          </svg>
          <div class="electro-grid">
            <div class="electro-mini">
              <div class="electro-mini-title">Liquidez</div>
              <div class="electro-mini-value">{e['liquidity_state']}</div>
              <div class="electro-note">Caja disponible frente a vencimientos próximos y colchón.</div>
            </div>
            <div class="electro-mini">
              <div class="electro-mini-title">Solvencia</div>
              <div class="electro-mini-value">{e['solvency_state']}</div>
              <div class="electro-note">Activos conocidos frente a deudas y compromisos cargados.</div>
            </div>
            <div class="electro-mini">
              <div class="electro-mini-title">Flujo</div>
              <div class="electro-mini-value">{e['flow_state']}</div>
              <div class="electro-note">Ingresos frente a gastos pagados y compromisos del período.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def yield_snapshot(db=None, days=30, balances=None):
    balances = balances if balances is not None else balances_df(db)
    if balances.empty:
        return {
            "remunerated_balance":0.0,
            "unremunerated_liquid":0.0,
            "estimated_yield":0.0,
            "rows":pd.DataFrame(),
        }

    rows = []
    remunerated_balance = 0.0
    unremunerated_liquid = 0.0
    estimated_total = 0.0

    for _, r in balances.iterrows():
        if r["moneda"] != "ARS":
            continue
        # Las cuentas de inversión se muestran en su módulo, no como caja remunerada cotidiana.
        if r["tipo"] in ["Cuenta comitente","Cuenta de inversión","Cuenta crypto"]:
            continue

        bal = max(0.0, float(r["saldo"]))
        remunerates = bool(r.get("genera_rendimiento", 0))
        rate = float(r.get("tasa_anual", 0) or 0)
        rate_type = r.get("tipo_tasa", "TNA") or "TNA"

        est = 0.0
        if remunerates and rate > 0 and bal > 0:
            est = estimated_return(rate, rate_type, days, bal)
            remunerated_balance += bal
            estimated_total += est
        else:
            unremunerated_liquid += bal

        rows.append({
            "Institución": r["institucion"],
            "Cuenta": r["cuenta"],
            "Saldo": bal,
            "Remunera": "Sí" if remunerates else "No",
            "Tasa": f"{rate:.2f}% {rate_type}".replace(".", ",") if remunerates and rate > 0 else "—",
            f"Rend. estimado {days}d": est,
            "Fuente": r.get("fuente_tasa", "") or "",
            "Actualizado": r.get("fecha_tasa", "") or "",
        })

    return {
        "remunerated_balance":remunerated_balance,
        "unremunerated_liquid":unremunerated_liquid,
        "estimated_yield":estimated_total,
        "rows":pd.DataFrame(rows),
    }


# =========================================================
# PERFIL / EVOLUCIÓN
# =========================================================

LEVELS = [
    ("Partícula", "Todavía falta estructura o faltan datos clave."),
    ("Átomo", "Ya hay una base mínima de orden financiero."),
    ("Agua", "Estado base: estabilidad razonable y manejo cotidiano sano."),
    ("Carbono", "Empezás a construir una estructura más flexible y útil."),
    ("Cadena", "Se nota continuidad y mejores hábitos."),
    ("Hidrocarburo", "Hay más capacidad, previsión y sostén."),
    ("Polímero", "Tu sistema financiero es más robusto y repetible."),
    ("Proteína", "La estructura ya es compleja y funcional."),
    ("ADN", "Nivel alto de organización, consistencia y criterio."),
]

_LEVEL_THRESHOLDS = [18, 30, 42, 54, 65, 74, 82, 90, 101]


def atomo_profile(period, db=None, electro=None):
    e = electro if electro is not None else electro_financiero(period, db)
    history = movements_df(db=db)

    if history.empty:
        incomes = 0.0
        flex_ratio = 0.0
        habit_scores = []
    else:
        history = history[history["importado"].fillna(0) == 0].copy()
        history = history[history["moneda"].fillna("ARS") == "ARS"].copy()
        history["_period"] = history["periodo_registro"].fillna(history["fecha"].str[:7])
        periods = sorted(set(history["_period"].dropna()))
        periods = [p for p in periods if p <= period][-6:]
        habit_scores = []

        current = history[history["_period"] == period]
        incomes = float(current.loc[current["tipo"] == "Ingreso", "monto"].sum()) if not current.empty else 0.0
        flex = float(current.loc[(current["tipo"] == "Gasto") & (current["categoria"].isin(DISCRETIONARY)), "monto"].sum()) if not current.empty else 0.0
        flex_ratio = flex / incomes if incomes > 0 else 0.0

        for p in periods:
            records = history[history["_period"] == p]
            inc = float(records.loc[records["tipo"] == "Ingreso", "monto"].sum())
            out = float(records.loc[records["tipo"].isin(["Gasto", "Compromiso"]), "monto"].sum())
            flexible_amount = float(records.loc[(records["tipo"] == "Gasto") & (records["categoria"].isin(DISCRETIONARY)), "monto"].sum())
            flow = max(0, min(1, (inc - out) / inc + 0.5)) if inc > 0 else 0.5
            flexible = max(0, 1 - flexible_amount / inc / 0.35) if inc > 0 else 0.5
            organized = records["cuenta_origen_id"].notna() | records["cuenta_destino_id"].notna() | (records["tipo"] == "Compromiso")
            overdue = records[(records["tipo"] == "Compromiso") & (records["fecha"] < local_today().isoformat())]
            completion = 1 - len(overdue) / max(1, len(records))
            habit_scores.append(100 * (0.4 * flow + 0.2 * flexible + 0.2 * organized.mean() + 0.2 * completion))

    score = sum(habit_scores) / len(habit_scores) if habit_scores else 0.0
    score *= min(1.0, 0.4 + 0.1 * len(habit_scores))

    idx = 0
    for i, th in enumerate(_LEVEL_THRESHOLDS):
        if score < th:
            idx = i
            break
    level_name, level_desc = LEVELS[idx]
    prev_th = 0 if idx == 0 else _LEVEL_THRESHOLDS[idx - 1]
    next_th = _LEVEL_THRESHOLDS[idx]
    progress = 1.0 if idx == len(LEVELS) - 1 else max(0.0, min(1.0, (score - prev_th) / max(1, next_th - prev_th)))
    next_name = None if idx == len(LEVELS) - 1 else LEVELS[idx + 1][0]

    hints = []
    if e["liquidity"] < 60:
        hints.append("mejorar liquidez")
    if e["solvency"] < 60:
        hints.append("ordenar deudas / solvencia")
    if e["flow"] < 60:
        hints.append("cuidar flujo mensual")
    if incomes > 0 and flex_ratio > float(get_config("gasto_discrecional_objetivo_pct", 15, db)) / 100:
        hints.append("reducir gastos flexibles")
    if not hints:
        hints.append("mantener la constancia")

    return {
        "score": score,
        "level": level_name,
        "desc": level_desc,
        "progress": progress,
        "next_level": next_name,
        "hints": hints[:2],
    }

def render_atomo_profile(profile):
    pct = round(profile["progress"] * 100)
    next_line = "Nivel máximo actual" if not profile["next_level"] else f"Próxima evolución: {profile['next_level']}"
    hint = " · ".join(profile["hints"])
    st.markdown(
        f"""
        <div class="help-card" style="border-radius:16px; border:1px solid rgba(120,120,120,.22);">
          <div class="at-muted">PERFIL DE ÁTOMO</div>
          <div class="at-brand" style="font-size:2rem; margin:.1rem 0 .2rem 0;">{profile['level']}</div>
          <div style="font-size:1rem; margin-bottom:.55rem;">{profile['desc']}</div>
          <div style="height:12px; background:rgba(120,120,120,.15); border-radius:999px; overflow:hidden; margin:.35rem 0 .5rem 0;">
            <div style="width:{pct}%; height:12px; background:linear-gradient(90deg,#ff8a1f,#ffc27a);"></div>
          </div>
          <div class="at-muted">{next_line}</div>
          <div class="at-muted" style="margin-top:.2rem;">Pistas actuales: {hint}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# YIELD COMPARISON
# =========================================================

def estimated_return(rate, rate_type, days=30, amount=1_000_000):
    rate = float(rate)/100
    if rate_type == "TNA":
        return amount * rate * days / 365
    if rate_type in ("TEA", "TIR"):
        return amount * ((1 + rate) ** (days/365) - 1)
    return amount * rate * days / 365

# =========================================================
# AI CONTEXT
# =========================================================

def ai_context(period, db=None):
    p = electro_financiero(period, db)
    summary, moves = period_summary(period, db)
    bal = balances_df(db)
    debt = debts_df(db)
    pos = positions_df(db)

    lines = [
        f"PERIODO {period}",
        f"ELECTRO DETERMINISTA: liquidez {p['liquidity_state']}, solvencia {p['solvency_state']}, flujo {p['flow_state']}",
        f"Ingresos: {summary['ingresos']:.2f}",
        f"Gastos pagados: {summary['gastos']:.2f}",
        f"Compromisos del período: {summary['compromisos']:.2f}",
        f"Liquidez ARS estimada: {p['liquid_ars']:.2f}",
        f"Compromisos próximos 45 días: {p['commitment_45_ars']:.2f}",
        f"Colchón objetivo: {p['buffer_target']:.2f}",
        f"Margen después de compromisos y colchón: {p['free_after']:.2f}",
        "",
        "CUENTAS:",
    ]
    if bal.empty:
        lines.append("- Sin cuentas")
    else:
        for _, r in bal.iterrows():
            lines.append(f"- {r['institucion']} | {r['cuenta']} | {r['moneda']} | {r['saldo']:.2f}")

    lines.append("\nDEUDAS:")
    if debt.empty:
        lines.append("- Sin saldos de deuda vigentes confirmados. Esto no acredita ausencia de deuda.")
    else:
        for _, r in debt.iterrows():
            lines.append(f"- {r['institucion']} | {r['nombre']} | saldo {money(r['saldo_pendiente'],r['moneda'],True)} | cuota {r['cuota']:.2f} | restantes {fmt_day(r['cuotas_restantes'])} | notas {r['notas'] or ''}")

    lines.append("\nINVERSIONES:")
    if pos.empty:
        lines.append("- Sin posiciones")
    else:
        for _, r in pos.iterrows():
            cost = r['cantidad'] * r['precio_promedio'] if pd.notna(r['precio_promedio']) else None
            value = r['cantidad'] * r['precio_actual'] if pd.notna(r['precio_actual']) else None
            lines.append(f"- {r['institucion']} | {r['tipo_activo']} | {r['ticker'] or r['descripcion']} | costo {money(cost,r['moneda'],True)} | valor actual {money(value,r['moneda'],True)} | notas: {r['notas'] or ''}")

    recovered = dfq("SELECT seccion,concepto,importe_referencia,moneda,estado_fuente,estado_actual,notas FROM referencias_importadas ORDER BY id", db=db)
    if not recovered.empty:
        lines.append("\nREFERENCIAS IMPORTADAS: importes de referencia, no saldos vigentes ni nuevas obligaciones. Liquidez y Solvencia parciales cuando hay datos por corroborar.")
        for _, r in recovered.iterrows():
            lines.append(f"- {r['seccion']} | {r['concepto']} | referencia {money(r['importe_referencia'],r['moneda'],True)} | fuente: {r['estado_fuente']} | actual: {r['estado_actual']} | {r['notas'] or ''}")

    lines.append("\nMOVIMIENTOS DEL MES:")
    for _, r in moves.head(100).iterrows():
        when = 'ciclo ' + str(r['periodo_registro']) + ' (04/09–03/10, día desconocido)' if r['fecha_precision'] == 'ciclo' else (r['fecha'][:7] + ' (día desconocido)' if r['fecha_precision'] == 'mes' else r['fecha'])
        lines.append(f"- {when} | {r['tipo']} | {r['descripcion']} | {r['categoria']} | {r['monto']:.2f} {r['moneda'] or 'ARS'} | {r['notas'] or ''}")

    return "\n".join(lines)
