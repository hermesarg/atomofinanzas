import sqlite3
from core.clock import today as local_today, local_now
from datetime import date
from datetime import datetime
import streamlit as st
from core.config import MONEDAS, TIPOS_CUENTA
from core.database import accounts_df, balances_df, con
from core.finance import account_map, amount_input, estimated_return, institution_map, money
from core.navigation import go

def render(period, db):
    from core.history import render_references
    st.header("🏦 Cuentas")
    with st.expander("¿Cómo registro una transferencia?"):
        st.caption("En Pagos elegí Mover entre mis cuentas. Si pagaste a otra persona, elegí Transferir a otra persona.")
        if st.button("Cargar transferencia →", key="cta_transfer_cuentas"):
            st.session_state["pay_action"] = "Mover entre mis cuentas"
            go("Pagos")

    imap = institution_map(db=db)
    with st.expander("➕ Agregar cuenta", expanded=False):
        if not imap:
            st.warning("Primero agregá una institución.")
        else:
            with st.form("account_form", clear_on_submit=False):
                ins = st.selectbox("Institución *", list(imap.keys()))
                a, b = st.columns(2)
                name = a.text_input("Nombre de la cuenta *", placeholder="Ej.: sueldo, dólares, comitente")
                typ = b.selectbox("Tipo de cuenta *", TIPOS_CUENTA)
                a, b, c = st.columns(3)
                cur = a.selectbox("Moneda *", MONEDAS)
                bal, bal_raw = amount_input("Saldo base *", value="0", help="Podés escribir 125000 o 125.000,50")
                d = c.date_input("Saldo válido desde *", value=local_today())

                st.markdown("#### ¿El saldo genera rendimiento automáticamente?")
                remunera = st.checkbox(
                    "Sí, esta cuenta/billetera remunera el saldo",
                    help="Ej.: una billetera o cuenta remunerada. Si gastás desde acá, baja el saldo que sigue generando rendimiento."
                )
                a, b, c = st.columns(3)
                rate = a.number_input(
                    "Tasa anual % (si corresponde)",
                    min_value=0.0, step=.1, format="%.2f",
                    help="Dejala en 0 si no querés estimar rendimiento."
                )
                rate_type = b.selectbox(
                    "Tipo de tasa", ["TNA","TEA"],
                    help="TNA: tasa nominal anual. TEA: tasa efectiva anual."
                )
                rate_date = c.date_input("Tasa actualizada al", value=local_today())
                rate_source = st.text_input("Fuente de la tasa (opcional)", placeholder="App, web de la entidad, etc.")
                notes = st.text_input("Notas")

                if st.form_submit_button("Guardar cuenta"):
                    if not name.strip():
                        st.error("Falta el nombre.")
                    elif bal is None or bal < 0:
                        st.error("Revisá el saldo base.")
                    else:
                        with con(db) as cdb:
                            cdb.execute("""
                            INSERT INTO cuentas(
                                institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,
                                activa,notas,creada_en,genera_rendimiento,tasa_anual,tipo_tasa,fecha_tasa,fuente_tasa
                            )
                            VALUES (?,?,?,?,?,?,1,?,?,?,?,?,?,?)
                            """, (
                                imap[ins], name.strip(), typ, cur, bal, d.isoformat(),
                                notes, local_now().isoformat(timespec="seconds"),
                                1 if remunera else 0, rate if remunera else 0,
                                rate_type, rate_date.isoformat(), rate_source.strip()
                            ))
                        st.success("Cuenta creada.")
                        st.rerun()

    existing = accounts_df(db)
    if not existing.empty:
        with st.expander("Modificar cuenta"):
            options = account_map(db)
            selected = st.selectbox("Cuenta a modificar", list(options), key="edit_account_selected")
            row = existing.loc[existing.id == options[selected]].iloc[0]
            with st.form(f"edit_account_{row['id']}"):
                edit_name = st.text_input("Nombre actualizado *", value=row["nombre"])
                edit_balance, edit_raw = amount_input("Saldo base actualizado *", value=money(row["saldo_base"], row["moneda"], True).partition(" ")[2], key=f"edit_balance_{row['id']}")
                edit_date = st.date_input("Saldo válido desde *", value=date.fromisoformat(row["fecha_saldo_base"]))
                st.caption("El saldo base se suma a los movimientos desde esa fecha inclusive. Si cargás un saldo actualizado, elegí una fecha posterior a los movimientos que ya incluye.")
                edit_yield = st.checkbox("Remunera el saldo", value=bool(row["genera_rendimiento"]))
                edit_rate = st.number_input("Tasa anual %", min_value=0.0, value=float(row["tasa_anual"] or 0))
                edit_rate_type = st.selectbox("Tipo de tasa", ["TNA", "TEA"], index=1 if row["tipo_tasa"] == "TEA" else 0)
                edit_source = st.text_input("Fuente de la tasa (opcional)", value=row["fuente_tasa"] or "")
                edit_notes = st.text_input("Notas", value=row["notas"] or "")
                if st.form_submit_button("Guardar cambios"):
                    if not edit_name.strip() or edit_balance is None or edit_balance < 0:
                        st.error("Completá el nombre y un saldo base válido.")
                    else:
                        with con(db) as cdb:
                            cdb.execute("""UPDATE cuentas SET nombre=?,saldo_base=?,fecha_saldo_base=?,
                                genera_rendimiento=?,tasa_anual=?,tipo_tasa=?,fuente_tasa=?,fecha_tasa=?,notas=? WHERE id=?""",
                                (edit_name.strip(), edit_balance, edit_date.isoformat(), int(edit_yield),
                                edit_rate, edit_rate_type, edit_source.strip(),
                                local_today().isoformat(), edit_notes, int(row["id"])))
                        st.session_state.pop(f"rate_error_{int(row['id'])}", None)
                        st.session_state[f"yield_on_{int(row['id'])}"] = bool(edit_yield)
                        st.session_state[f"yield_rate_{int(row['id'])}"] = format_rate(edit_rate)
                        st.session_state[f"yield_type_{int(row['id'])}"] = edit_rate_type
                        st.rerun()

    bal = balances_df(db)
    if bal.empty:
        st.info("Todavía no cargaste cuentas.")
    else:
        view = bal.copy()
        view["Saldo"] = view.apply(lambda r: money(r["saldo"], r["moneda"], True), axis=1)
        view["Rendimiento"] = view.apply(
            lambda r: (
                f"{r['tasa_anual']:.2f}% {r['tipo_tasa']}".replace(".", ",")
                if bool(r.get("genera_rendimiento",0)) and float(r.get("tasa_anual",0) or 0)>0
                else "No"
            ),
            axis=1
        )
        view["Estimado 30d"] = view.apply(
            lambda r: (
                money(estimated_return(r["tasa_anual"], r["tipo_tasa"], 30, max(0,float(r["saldo"]))), r["moneda"], True)
                if bool(r.get("genera_rendimiento",0)) and float(r.get("tasa_anual",0) or 0)>0
                else "—"
            ),
            axis=1
        )
        view = view.rename(columns={"institucion":"Institución","cuenta":"Cuenta","tipo":"Tipo","moneda":"Moneda"})
        st.subheader("Tus cuentas")
        st.caption("Activá Rendimiento, escribí la tasa y elegí TNA o TEA. Se guarda al cambiar; la estimación no acredita dinero.")
        for _, account in bal.iterrows():
            aid = int(account["id"])
            with st.container(border=True, key=f"rate_account_{aid}"):
                st.markdown(f"**{account['cuenta']}** · {money(account['saldo'], account['moneda'], True)}")
                st.caption(f"{account['institucion']} · {account['moneda']}")
                if account["tipo"] in ["Cuenta por cobrar", "Prepago"]:
                    st.caption("Pendiente de cobro" if account["tipo"] == "Cuenta por cobrar" else "Saldo prepago para usar")
                    continue
                keys = [f"yield_on_{aid}", f"yield_rate_{aid}", f"yield_type_{aid}"]
                values = [bool(account["genera_rendimiento"]), format_rate(account["tasa_anual"] or 0), account["tipo_tasa"] if account["tipo_tasa"] in ["TNA","TEA"] else "TNA"]
                for key, value in zip(keys, values):
                    if key != keys[1] or not st.session_state.get(f"rate_error_{aid}"):
                        st.session_state[key] = value
                # Every callback runs before the rerender, so all three current values
                # reach SQLite together and the calculation reads the updated rate.
                a, b, c = st.columns([1.3, 1.6, 1])
                a.toggle("Rendimiento", key=keys[0], on_change=save_inline_rate, args=(db,aid,"enabled"))
                b.text_input("Tasa anual %", placeholder="Ej.: 35,50", key=keys[1], on_change=save_inline_rate, args=(db,aid,"rate"))
                c.selectbox("TNA / TEA", ["TNA","TEA"], key=keys[2], on_change=save_inline_rate, args=(db,aid,"type"))
                if st.session_state.get(f"rate_error_{aid}"):
                    st.error(st.session_state[f"rate_error_{aid}"])
                if bool(account["genera_rendimiento"]) and account["tasa_anual"] > 0:
                    st.caption("Estimación 30 días: " + money(estimated_return(account["tasa_anual"],account["tipo_tasa"],30,max(0,float(account["saldo"]))),account["moneda"],True))
                elif account["tasa_anual"] > 0:
                    st.caption("Tasa conservada. Activá Rendimiento para aplicarla a la estimación.")
                else:
                    st.caption("Sin estimación: cargá una tasa si esta cuenta genera rendimiento.")
        if "rate_saved" in st.session_state:
            st.toast(st.session_state.pop("rate_saved"))
        totals = bal.groupby("moneda", as_index=False)["saldo"].sum()
        st.subheader("Totales por moneda")
        cols = st.columns(min(4, len(totals)))
        for i, (_, r) in enumerate(totals.iterrows()):
            cols[i % len(cols)].metric(r["moneda"], money(r["saldo"], r["moneda"], True))
    render_references('Cuentas', db, 'Bancos y cuentas identificados en el historial')

# =========================================================
# PAGE: TARJETAS Y CUOTAS
# =========================================================


def format_rate(rate):
    return f"{float(rate):.4f}".rstrip("0").rstrip(".").replace(".", ",")


def save_inline_rate(db, account_id, field):
    from core.security import web_private, valid_session
    try:
        if web_private() and not valid_session(st.session_state):
            st.session_state.pop('_private_access', None)
            return
    except sqlite3.Error:
        st.session_state[f"rate_error_{account_id}"] = "No pude confirmar el cambio. Revisá la conexión y la tasa guardada."
        return
    from core.rates import update_rate_field
    keys = {"enabled":f"yield_on_{account_id}", "rate":f"yield_rate_{account_id}", "type":f"yield_type_{account_id}"}
    try:
        saved = update_rate_field(db, account_id, field, st.session_state[keys[field]])
    except ValueError:
        st.session_state[f"rate_error_{account_id}"] = "Revisá la tasa: usá un número de 0 a 10.000, con hasta cuatro decimales. No se guardó ese cambio."
        return
    except sqlite3.Error:
        st.session_state[f"rate_error_{account_id}"] = "No pude confirmar el cambio. Revisá la conexión y la tasa guardada."
        return
    # Do not overwrite other widget events if blur and toggle arrive together.
    # The next render reads fresh database values for all three controls.
    if saved and field == "rate":
        st.session_state[keys["rate"]] = format_rate(saved[1])
    st.session_state.pop(f"rate_error_{account_id}", None)
    st.session_state.rate_saved = "Rendimiento actualizado."
