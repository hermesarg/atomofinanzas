from core.clock import today as local_today, local_now
import sqlite3
from threading import RLock
DB_LOCK = RLock()
import math
from contextlib import contextmanager
from datetime import date
from datetime import datetime
from datetime import timedelta
import calendar
from pathlib import Path
import secrets
import tempfile
import pandas as pd
import streamlit as st
from core.config import BACKUP_DIR, BASE_INSTITUTIONS, DEMO_DB, LIVE_DB

def current_db():
    if st.session_state.get("demo_mode", False):
        if "_demo_db_path" not in st.session_state:
            token = secrets.token_hex(8)
            path = Path(tempfile.gettempdir()) / f"atomo_demo_{token}.db"
            st.session_state._demo_db_path = str(path)
            reset_demo(path)
        return Path(st.session_state._demo_db_path)
    return LIVE_DB

@contextmanager
def con(db=None):
    """Commit/rollback y cierre garantizado, incluso después de errores."""
    # Los callbacks de widgets se ejecutan antes del cuerpo de app.py.
    # Verificar también acá evita escrituras desde formularios de una sesión vencida.
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    from pathlib import Path
    from core.security import web_private, valid_session
    target = db or current_db()
    if web_private() and get_script_run_ctx(suppress_warning=True) is not None and Path(target).resolve() == LIVE_DB.resolve():
        if not valid_session(st.session_state):
            raise PermissionError('Tu sesión venció. Volvé a entrar a tu espacio privado.')
    DB_LOCK.acquire()
    connection = None
    try:
        from core.backend import connect, remote_target
        connection = connect(target)
        if remote_target(target):
            connection.execute("BEGIN IMMEDIATE")
    except BaseException:
        if connection is not None:
            connection.close()
        DB_LOCK.release()
        raise
    try:
        with connection:
            yield connection
    finally:
        connection.close()
        DB_LOCK.release()

def table_columns(c, table):
    return {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}

def add_col_if_missing(c, table, name, definition):
    if name not in table_columns(c, table):
        c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def backup_live_once():
    from core.backend import remote_mode
    if remote_mode() or not LIVE_DB.exists():
        return
    marker = BACKUP_DIR / ".stable_backup_done"
    if marker.exists():
        return
    stamp = local_now().strftime("%Y%m%d_%H%M%S")
    with con(LIVE_DB) as source, con(BACKUP_DIR / f"finanzas_pre_estabilizacion_{stamp}.db") as target:
        source.backup(target)
    marker.write_text("ok", encoding="utf-8")

_remote_initialized = set()

def init_db(db):
    from core.backend import remote_target, remote_settings
    if remote_target(db):
        with DB_LOCK:
            key = remote_settings()[0]
            if key not in _remote_initialized:
                _initialize_remote_schema(db)
                _remote_initialized.add(key)
        return
    _initialize_schema(db)


def _initialize_remote_schema(db):
    """Preparar el esquema localmente y migrar en un lote breve de red."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='atomo-schema-') as folder:
        path = Path(folder)/'schema.db'
        _initialize_schema(path)
        with sqlite3.connect(path) as desired:
            tables = desired.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            # quote() es de SQLite: también escapa apóstrofes y valores NULL/BLOB.
            def quote(value):
                return desired.execute('SELECT quote(?)', (value,)).fetchone()[0]
            with con(db) as dest:
                existing = {row[0] for row in dest.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                statements = []
                for table, sql in tables:
                    if table not in existing:
                        statements.append(sql)
                        continue
                    actual = table_columns(dest, table)
                    for _, name, kind, mandatory, default, pk in desired.execute(f'PRAGMA table_info("{table}")').fetchall():
                        if name not in actual:
                            if pk:
                                raise sqlite3.OperationalError('La estructura de la base externa no corresponde a Átomo.')
                            definition = kind + (' NOT NULL' if mandatory else '') + (' DEFAULT '+default if default is not None else '')
                            statements.append(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}')
                for tipo, nombre, fuente in BASE_INSTITUTIONS:
                    now = local_now().isoformat(timespec='seconds')
                    values = ','.join(quote(x) for x in (tipo,nombre,fuente,1,now))
                    statements.append(f'INSERT OR IGNORE INTO instituciones(tipo,nombre,fuente,activa,creada_en) SELECT {values} WHERE NOT EXISTS (SELECT 1 FROM instituciones WHERE nombre={quote(nombre)})')
                for key, value in desired.execute('SELECT clave,valor FROM config').fetchall():
                    statements.append(f'INSERT OR IGNORE INTO config VALUES ({quote(key)},{quote(value)})')
                dest.run_script(statements)

def _initialize_schema(db):
    with con(db) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            cuenta TEXT,
            notas TEXT,
            creado_en TEXT NOT NULL
        )""")
        add_col_if_missing(c, "movimientos", "cuenta_origen_id", "INTEGER")
        add_col_if_missing(c, "movimientos", "cuenta_destino_id", "INTEGER")
        add_col_if_missing(c, "movimientos", "moneda", "TEXT DEFAULT 'ARS'")
        add_col_if_missing(c, "movimientos", "impacta_caja", "INTEGER DEFAULT 1")
        add_col_if_missing(c, "movimientos", "grupo_cuotas", "TEXT")
        add_col_if_missing(c, "movimientos", "cuota_actual", "INTEGER")
        add_col_if_missing(c, "movimientos", "cuotas_total", "INTEGER")
        add_col_if_missing(c, "movimientos", "estado", "TEXT DEFAULT 'activo'")
        add_col_if_missing(c, "movimientos", "subtipo", "TEXT")
        add_col_if_missing(c, "movimientos", "importado", "INTEGER DEFAULT 0")
        add_col_if_missing(c, "movimientos", "fecha_precision", "TEXT DEFAULT 'dia'")
        add_col_if_missing(c, "movimientos", "periodo_registro", "TEXT")
        add_col_if_missing(c, "movimientos", "deuda_id", "INTEGER")
        c.execute("""CREATE TABLE IF NOT EXISTS referencias_importadas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave TEXT UNIQUE NOT NULL,
            seccion TEXT NOT NULL,
            concepto TEXT NOT NULL,
            institucion TEXT,
            importe_referencia REAL,
            moneda TEXT DEFAULT 'ARS',
            periodo TEXT,
            estado_fuente TEXT,
            estado_actual TEXT DEFAULT 'Corroborar',
            fuente TEXT,
            notas TEXT
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS saldos_iniciales(
            periodo TEXT PRIMARY KEY,
            monto REAL NOT NULL
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS periodos_financieros(
            periodo TEXT PRIMARY KEY,
            inicio TEXT NOT NULL,
            fin TEXT,
            criterio TEXT NOT NULL,
            detalle TEXT,
            creado_en TEXT NOT NULL
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS instituciones(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL UNIQUE,
            fuente TEXT,
            activa INTEGER NOT NULL DEFAULT 1,
            creada_en TEXT NOT NULL
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS cuentas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institucion_id INTEGER,
            nombre TEXT NOT NULL,
            tipo_cuenta TEXT NOT NULL,
            moneda TEXT NOT NULL,
            saldo_base REAL NOT NULL DEFAULT 0,
            fecha_saldo_base TEXT NOT NULL,
            activa INTEGER NOT NULL DEFAULT 1,
            notas TEXT,
            creada_en TEXT NOT NULL,
            FOREIGN KEY(institucion_id) REFERENCES instituciones(id)
        )""")

        add_col_if_missing(c, "cuentas", "liquidez_operativa", "INTEGER")
        add_col_if_missing(c, "cuentas", "genera_rendimiento", "INTEGER DEFAULT 0")
        add_col_if_missing(c, "cuentas", "tasa_anual", "REAL DEFAULT 0")
        add_col_if_missing(c, "cuentas", "tipo_tasa", "TEXT DEFAULT 'TNA'")
        add_col_if_missing(c, "cuentas", "fecha_tasa", "TEXT")
        add_col_if_missing(c, "cuentas", "fuente_tasa", "TEXT")

        c.execute("""
        CREATE TABLE IF NOT EXISTS tarjetas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institucion_id INTEGER,
            nombre TEXT NOT NULL,
            cierre_dia INTEGER,
            vencimiento_dia INTEGER,
            limite REAL DEFAULT 0,
            moneda TEXT DEFAULT 'ARS',
            activa INTEGER NOT NULL DEFAULT 1,
            notas TEXT,
            creada_en TEXT NOT NULL,
            FOREIGN KEY(institucion_id) REFERENCES instituciones(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS deudas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institucion_id INTEGER,
            nombre TEXT NOT NULL,
            saldo_pendiente REAL NOT NULL DEFAULT 0,
            cuota REAL NOT NULL DEFAULT 0,
            cuotas_restantes INTEGER NOT NULL DEFAULT 0,
            proximo_vencimiento TEXT,
            moneda TEXT DEFAULT 'ARS',
            tasa_info TEXT,
            activa INTEGER NOT NULL DEFAULT 1,
            notas TEXT,
            creada_en TEXT NOT NULL,
            FOREIGN KEY(institucion_id) REFERENCES instituciones(id)
        )""")

        add_col_if_missing(c, "deudas", "saldo_confirmado", "INTEGER DEFAULT 1")
        add_col_if_missing(c, "deudas", "cuotas_confirmadas", "INTEGER DEFAULT 1")
        c.execute("""
        CREATE TABLE IF NOT EXISTS posiciones(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL,
            tipo_activo TEXT NOT NULL,
            ticker TEXT,
            descripcion TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 0,
            precio_promedio REAL NOT NULL DEFAULT 0,
            precio_actual REAL NOT NULL DEFAULT 0,
            moneda TEXT NOT NULL DEFAULT 'USD',
            notas TEXT,
            creada_en TEXT NOT NULL,
            FOREIGN KEY(cuenta_id) REFERENCES cuentas(id)
        )""")
        add_col_if_missing(c, "posiciones", "costo_confirmado", "INTEGER DEFAULT 1")
        add_col_if_missing(c, "posiciones", "valor_actual_confirmado", "INTEGER DEFAULT 1")

        c.execute("""
        CREATE TABLE IF NOT EXISTS alternativas_rendimiento(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            institucion TEXT,
            instrumento TEXT NOT NULL,
            tipo_tasa TEXT NOT NULL,
            tasa_anual REAL NOT NULL,
            liquidez TEXT,
            riesgo TEXT,
            moneda TEXT DEFAULT 'ARS',
            fuente TEXT,
            actualizado TEXT,
            demo INTEGER NOT NULL DEFAULT 0
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS config(
            clave TEXT PRIMARY KEY,
            valor TEXT
        )""")

        now = local_now().isoformat(timespec="seconds")
        for tipo, nombre, fuente in BASE_INSTITUTIONS:
            c.execute(
                "INSERT OR IGNORE INTO instituciones(tipo,nombre,fuente,activa,creada_en) SELECT ?,?,?,1,? WHERE NOT EXISTS (SELECT 1 FROM instituciones WHERE nombre=?)",
                (tipo, nombre, fuente, now, nombre),
            )

        defaults = {
            "colchon_objetivo_ars": "700000",
            "gasto_discrecional_objetivo_pct": "15",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO config(clave,valor) VALUES (?,?)", (k, v))

def reset_demo(db=None):
    db = Path(db or DEMO_DB)
    if db.exists():
        db.unlink()
    init_db(db)
    seed_demo(db)

def get_config(key, default, db=None):
    with con(db) as c:
        row = c.execute("SELECT valor FROM config WHERE clave=?", (key,)).fetchone()
    return row[0] if row else default

def set_config(key, value, db=None):
    with con(db) as c:
        c.execute("""
        INSERT INTO config(clave,valor) VALUES (?,?)
        ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
        """, (key, str(value)))

def dfq(sql, params=(), db=None):
    with con(db) as c:
        # DB-API directo evita avisos de pandas por drivers sin SQLAlchemy.
        cursor = c.execute(sql, params)
        return pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])

def inst_id(name, db=None):
    with con(db) as c:
        row = c.execute("SELECT id FROM instituciones WHERE nombre=?", (name,)).fetchone()
    return row[0] if row else None

def seed_demo(db=None):
    from .finance import add_months
    db = Path(db or DEMO_DB)
    today = local_today()
    period = today.strftime("%Y-%m")
    first = today.replace(day=1)
    now = local_now().isoformat(timespec="seconds")

    with con(db) as c:
        # cuentas
        demo_accounts = [
            ("Banco Provincia del Neuquén", "Cuenta sueldo", "Caja de ahorro ARS", "ARS", 2450000),
            ("Banco Macro", "Caja ahorro", "Caja de ahorro ARS", "ARS", 620000),
            ("Mercado Pago", "Billetera diaria", "Billetera", "ARS", 315000),
            ("Brubank", "Dólares", "Caja de ahorro USD", "USD", 780),
            ("InvertirOnline (IOL)", "Comitente", "Cuenta comitente", "ARS", 1450000),
            ("Cocos Capital", "Inversiones", "Cuenta de inversión", "ARS", 480000),
        ]
        for institution, name, t, cur, bal in demo_accounts:
            iid = inst_id(institution, db)
            c.execute("""
            INSERT INTO cuentas(institucion_id,nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,activa,notas,creada_en)
            VALUES (?,?,?,?,?,?,1,?,?)
            """, (iid, name, t, cur, bal, first.isoformat(), "Dato ficticio del modo demo", now))

        # La billetera demo remunera el saldo. La tasa es FICTICIA.
        c.execute("""
        UPDATE cuentas
        SET genera_rendimiento=1, tasa_anual=28.0, tipo_tasa='TNA',
            fecha_tasa=?, fuente_tasa='Tasa ficticia del modo demo'
        WHERE nombre='Billetera diaria'
        """, (today.isoformat(),))

        # tarjetas
        for institution, name, close, due, limit_ in [
            ("Banco Patagonia", "Visa Patagonia", 20, 8, 2500000),
            ("Banco Macro", "Visa Macro", 24, 10, 1800000),
            ("Mercado Pago", "Crédito MP", 18, 5, 900000),
        ]:
            c.execute("""
            INSERT INTO tarjetas(institucion_id,nombre,cierre_dia,vencimiento_dia,limite,moneda,activa,notas,creada_en)
            VALUES (?,?,?,?,?,'ARS',1,?,?)
            """, (inst_id(institution, db), name, close, due, limit_, "Demo", now))

    accounts = accounts_df(db)
    amap = {r["nombre"]: int(r["id"]) for _, r in accounts.iterrows()}

    # movimientos del mes demo
    demo_moves = [
        (2, "Ingreso", "Sueldo", "Sueldo / ingreso", 5100000, None, amap["Cuenta sueldo"]),
        (3, "Gasto", "Alquiler", "Vivienda / alquiler", 1200000, amap["Cuenta sueldo"], None),
        (5, "Gasto", "Compra supermercado", "Supermercado / compra del mes", 310000, amap["Cuenta sueldo"], None),
        (7, "Gasto", "Combustible", "Combustible / transporte", 125000, amap["Billetera diaria"], None),
        (9, "Gasto", "Cena", "Comida afuera", 72000, amap["Billetera diaria"], None),
        (11, "Gasto", "Café y kiosco", "Gasto hormiga", 38000, amap["Billetera diaria"], None),
        (13, "Gasto", "Internet + celular", "Servicios", 89000, amap["Cuenta sueldo"], None),
        (15, "Gasto", "Gimnasio", "Salud", 65000, amap["Cuenta sueldo"], None),
        (16, "Transferencia", "Transferencia a IOL", "Transferencia", 450000, amap["Cuenta sueldo"], amap["Comitente"]),
        (19, "Gasto", "Ropa", "Ropa", 125000, amap["Caja ahorro"], None),
    ]
    for day, typ, desc, cat, amt, ori, dst in demo_moves:
        d = first.replace(day=min(day, calendar.monthrange(first.year, first.month)[1]))
        insert_movement(d, typ, desc, cat, amt, ori, dst, "ARS", "Dato de demostración", db=db)

    # compromisos futuros
    for offset, desc, amount in [
        (3, "Resumen Visa Patagonia", 540000),
        (7, "Crédito MP", 210000),
        (10, "Visa Macro", 185000),
    ]:
        d = today + timedelta(days=offset)
        insert_movement(d, "Compromiso", desc, "Tarjetas", amount, None, None, "ARS", "Demo", db=db)

    # deuda
    with con(db) as c:
        c.execute("""
        INSERT INTO deudas(institucion_id,nombre,saldo_pendiente,cuota,cuotas_restantes,proximo_vencimiento,moneda,tasa_info,activa,notas,creada_en)
        VALUES (?,?,?,?,?,?,? ,?,1,?,?)
        """, (
            inst_id("Banco Macro", db), "Préstamo personal", 2380000, 395000, 7,
            (today + timedelta(days=12)).isoformat(), "ARS", "Tasa fija", "Ejemplo", now
        ))

    # inversiones
    acc = accounts_df(db)
    iol = int(acc.loc[acc["nombre"]=="Comitente","id"].iloc[0])
    cocos = int(acc.loc[acc["nombre"]=="Inversiones","id"].iloc[0])
    with con(db) as c:
        positions = [
            (iol, "CEDEAR", "KO", "Coca-Cola", 12, 31800, 33200, "ARS"),
            (iol, "Bono soberano", "AL30", "Bonar 2030", 850, 820, 865, "ARS"),
            (cocos, "Acción argentina", "YPFD", "YPF", 18, 54200, 56800, "ARS"),
        ]
        for row in positions:
            c.execute("""
            INSERT INTO posiciones(cuenta_id,tipo_activo,ticker,descripcion,cantidad,precio_promedio,precio_actual,moneda,notas,creada_en)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (*row, "Precios ficticios del modo demo", now))

        # Comparación de rendimiento: deliberadamente ficticia.
        alternatives = [
            ("Billetera virtual", "Billetera Ejemplo", "Cuenta remunerada", "TNA", 25.0, "Inmediata", "Bajo", "ARS"),
            ("Plazo fijo", "Banco Ejemplo", "Plazo fijo 30 días", "TNA", 30.0, "30 días", "Bajo", "ARS"),
            ("Letra", "Mercado", "LECAP ejemplo", "TEA", 35.0, "Mercado / vencimiento", "Medio", "ARS"),
            ("Bono", "Mercado", "Bono ejemplo", "TIR", 40.0, "Mercado", "Medio/alto", "ARS"),
        ]
        for cat, ins, instr, tt, rate, liq, risk, cur in alternatives:
            c.execute("""
            INSERT INTO alternativas_rendimiento(categoria,institucion,instrumento,tipo_tasa,tasa_anual,liquidez,riesgo,moneda,fuente,actualizado,demo)
            VALUES (?,?,?,?,?,?,?,?,?,?,1)
            """, (cat, ins, instr, tt, rate, liq, risk, cur, "Dato ficticio", today.isoformat()))

        c.execute("INSERT OR REPLACE INTO config(clave,valor) VALUES ('periodo_modo','calendar')")
        c.execute("INSERT OR REPLACE INTO config(clave,valor) VALUES ('periodo_activo',?)", (period,))
        last = calendar.monthrange(today.year, today.month)[1]
        c.execute(
            "INSERT OR REPLACE INTO periodos_financieros(periodo,inicio,fin,criterio,detalle,creado_en) VALUES (?,?,?,?,?,?)",
            (period, first.isoformat(), first.replace(day=last).isoformat(), "Mes calendario", "Dato ficticio del modo demo para períodos.", now),
        )

# =========================================================
# DATA HELPERS
# =========================================================

def institutions_df(db=None):
    return dfq("SELECT * FROM instituciones WHERE activa=1 ORDER BY tipo,nombre", db=db)

def accounts_df(db=None):
    return dfq("""
    SELECT c.*, i.nombre AS institucion, i.tipo AS tipo_institucion
    FROM cuentas c
    LEFT JOIN instituciones i ON i.id=c.institucion_id
    WHERE c.activa=1
    ORDER BY i.nombre,c.nombre
    """, db=db)

def cards_df(db=None):
    return dfq("""
    SELECT t.*,i.nombre AS institucion
    FROM tarjetas t
    LEFT JOIN instituciones i ON i.id=t.institucion_id
    WHERE t.activa=1
    ORDER BY i.nombre,t.nombre
    """, db=db)

def debts_df(db=None):
    result = dfq("""
    SELECT d.*, CASE WHEN COALESCE(d.cuotas_confirmadas,1)=1 THEN d.cuotas_restantes ELSE NULL END AS cuotas_visibles, CASE WHEN COALESCE(d.saldo_confirmado,1)=1 THEN d.saldo_pendiente ELSE NULL END AS saldo_visible, i.nombre AS institucion
    FROM deudas d
    LEFT JOIN instituciones i ON i.id=d.institucion_id
    WHERE d.activa=1
    ORDER BY d.proximo_vencimiento
    """, db=db)
    result["saldo_pendiente"] = result["saldo_visible"]
    result["cuotas_restantes"] = result["cuotas_visibles"]
    return result.drop(columns=["saldo_visible", "cuotas_visibles"])

def positions_df(db=None):
    return dfq("""
    SELECT p.id,p.cuenta_id,p.tipo_activo,p.ticker,p.descripcion,p.cantidad,
           CASE WHEN COALESCE(p.costo_confirmado,1)=1 THEN p.precio_promedio ELSE NULL END AS precio_promedio,
           CASE WHEN COALESCE(p.valor_actual_confirmado,1)=1 THEN p.precio_actual ELSE NULL END AS precio_actual,
           p.moneda,p.notas,p.creada_en,p.valor_actual_confirmado,c.nombre AS cuenta,i.nombre AS institucion
    FROM posiciones p
    JOIN cuentas c ON c.id=p.cuenta_id
    LEFT JOIN instituciones i ON i.id=c.institucion_id
    ORDER BY i.nombre,p.tipo_activo,p.ticker
    """, db=db)

def alternatives_df(db=None):
    return dfq("""
    SELECT * FROM alternativas_rendimiento
    ORDER BY categoria,instrumento
    """, db=db)

def movements_df(period=None, db=None):
    sql = """
    SELECT m.*,
           co.nombre AS cuenta_origen_nombre,
           io.nombre AS institucion_origen,
           cd.nombre AS cuenta_destino_nombre,
           idst.nombre AS institucion_destino
    FROM movimientos m
    LEFT JOIN cuentas co ON co.id=m.cuenta_origen_id
    LEFT JOIN instituciones io ON io.id=co.institucion_id
    LEFT JOIN cuentas cd ON cd.id=m.cuenta_destino_id
    LEFT JOIN instituciones idst ON idst.id=cd.institucion_id
    WHERE COALESCE(m.estado,'activo')='activo'
    """
    params = []
    if period:
        sql += " AND COALESCE(m.periodo_registro,substr(m.fecha,1,7))=?"
        params.append(period)
    sql += " ORDER BY m.fecha DESC,m.id DESC"
    return dfq(sql, tuple(params), db=db)

def account_balance(row, db=None):
    aid = int(row["id"])
    base = float(row["saldo_base"] or 0)
    since = row["fecha_saldo_base"]
    moves = dfq("""
    SELECT tipo,monto,cuenta_origen_id,cuenta_destino_id
    FROM movimientos
    WHERE fecha>=? AND fecha<=date('now','localtime')
      AND COALESCE(estado,'activo')='activo'
      AND (COALESCE(importado,0)=0 OR COALESCE(impacta_caja,1)=1)
      AND (cuenta_origen_id=? OR cuenta_destino_id=?)
    """, (since, aid, aid), db=db)
    bal = base
    for _, m in moves.iterrows():
        amt = float(m["monto"])
        if m["tipo"] == "Ingreso" and m["cuenta_destino_id"] == aid:
            bal += amt
        elif m["tipo"] == "Gasto" and m["cuenta_origen_id"] == aid:
            bal -= amt
        elif m["tipo"] == "Transferencia":
            if m["cuenta_origen_id"] == aid:
                bal -= amt
            if m["cuenta_destino_id"] == aid:
                bal += amt
    return bal

def balances_df(db=None):
    """Saldos de todas las cuentas con una sola lectura de movimientos."""
    acc = accounts_df(db)
    if acc.empty:
        return pd.DataFrame(columns=["id","institucion","cuenta","tipo","moneda","saldo","liquidez_operativa","genera_rendimiento","tasa_anual","tipo_tasa","fecha_tasa","fuente_tasa"])
    earliest = min(str(x) for x in acc["fecha_saldo_base"] if x)
    moves = dfq("""
        SELECT fecha,tipo,monto,cuenta_origen_id,cuenta_destino_id
        FROM movimientos
        WHERE fecha>=? AND fecha<=date('now','localtime')
          AND COALESCE(estado,'activo')='activo'
          AND (COALESCE(importado,0)=0 OR COALESCE(impacta_caja,1)=1)
          AND (cuenta_origen_id IS NOT NULL OR cuenta_destino_id IS NOT NULL)
    """, (earliest,), db=db)
    rows = []
    for _, r in acc.iterrows():
        aid = int(r["id"])
        base = float(r["saldo_base"] or 0)
        since = str(r["fecha_saldo_base"])
        saldo = base
        if not moves.empty:
            relevant = moves[(moves["fecha"] >= since) & ((moves["cuenta_origen_id"] == aid) | (moves["cuenta_destino_id"] == aid))]
            for _, m in relevant.iterrows():
                amt = float(m["monto"])
                if m["tipo"] == "Ingreso" and m["cuenta_destino_id"] == aid:
                    saldo += amt
                elif m["tipo"] == "Gasto" and m["cuenta_origen_id"] == aid:
                    saldo -= amt
                elif m["tipo"] == "Transferencia":
                    if m["cuenta_origen_id"] == aid:
                        saldo -= amt
                    if m["cuenta_destino_id"] == aid:
                        saldo += amt
        rows.append({
            "id": aid,
            "institucion": r["institucion"],
            "cuenta": r["nombre"],
            "tipo": r["tipo_cuenta"],
            "moneda": r["moneda"],
            "saldo": saldo,
            "liquidez_operativa": r.get("liquidez_operativa"),
            "genera_rendimiento": int(r.get("genera_rendimiento", 0) or 0),
            "tasa_anual": float(r.get("tasa_anual", 0) or 0),
            "tipo_tasa": r.get("tipo_tasa", "TNA") or "TNA",
            "fecha_tasa": r.get("fecha_tasa", None),
            "fuente_tasa": r.get("fuente_tasa", None),
        })
    return pd.DataFrame(rows)

def insert_movement(fecha, tipo, descripcion, categoria, monto,
                    origen=None, destino=None, moneda="ARS", notas="",
                    grupo_cuotas=None, cuota_actual=None, cuotas_total=None,
                    subtipo=None, db=None, periodo_registro=None):
    if not descripcion.strip() or not math.isfinite(float(monto)) or float(monto) <= 0:
        raise ValueError("Descripción y monto positivo son obligatorios.")
    if tipo == "Transferencia" and (not origen or not destino or origen == destino):
        raise ValueError("Una transferencia propia requiere dos cuentas distintas.")
    if not accounts_match_currency([origen, destino], moneda, db):
        raise ValueError("La moneda del movimiento debe coincidir con sus cuentas.")
    fecha_texto = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
    if periodo_registro is None:
        try:
            from core.periods import period_for_date
            periodo_registro = period_for_date(fecha_texto, db)
        except (sqlite3.Error, ValueError):
            periodo_registro = fecha_texto[:7]
    with con(db) as c:
        c.execute("""
        INSERT INTO movimientos(
            fecha,tipo,descripcion,categoria,monto,cuenta,notas,creado_en,
            cuenta_origen_id,cuenta_destino_id,moneda,impacta_caja,
            grupo_cuotas,cuota_actual,cuotas_total,periodo_registro,estado,subtipo
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'activo',?)
        """, (
            fecha_texto,
            tipo, descripcion.strip(), categoria, float(monto), None, notas.strip(),
            local_now().isoformat(timespec="seconds"),
            origen, destino, moneda, 0 if tipo == "Transferencia" else 1,
            grupo_cuotas, cuota_actual, cuotas_total, periodo_registro, subtipo,
        ))


def accounts_match_currency(ids, currency, db=None):
    for aid in ids:
        if aid is not None:
            row = dfq("SELECT moneda FROM cuentas WHERE id=? AND activa=1", (aid,), db)
            if row.empty or row.iloc[0]["moneda"] != currency:
                return False
    return True
