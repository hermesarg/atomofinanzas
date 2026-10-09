"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import ElectroPulse from "./ElectroPulse";
import AnimatedMoney from "./AnimatedMoney";
import ActionFlash from "./ActionFlash";
import { useFinance } from "@/lib/store";
import type { MovementType } from "@/lib/types";

type Tab = "Inicio" | "Movimientos" | "Electro" | "Cuentas" | "Más";
type ActionKind = "income" | "expense" | "transfer" | null;

const pesos = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 0
});

function signedMoney(value: number) {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return sign + " " + pesos.format(Math.abs(value));
}

function movementSymbol(type: MovementType) {
  if (type === "income") return "↙";
  if (type === "expense") return "↗";
  return "⇄";
}

export default function DashboardShell() {
  const { state, electro, level, addMovement, reset } = useFinance();
  const [tab, setTab] = useState<Tab>("Inicio");
  const [action, setAction] = useState<ActionKind>(null);
  const [expanded, setExpanded] = useState(false);
  const [notice, setNotice] = useState("");
  const [flash, setFlash] = useState<"income" | "expense" | "transfer" | null>(null);
  const [query, setQuery] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [showAvailable, setShowAvailable] = useState(true);

  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [accountId, setAccountId] = useState(state.accounts[0]?.id ?? "");
  const [destinationAccountId, setDestinationAccountId] = useState(state.accounts[1]?.id ?? "");

  useEffect(() => {
    const savedTheme = localStorage.getItem("atomo-theme");
    const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const nextTheme = savedTheme === "dark" || savedTheme === "light"
      ? savedTheme
      : (systemDark ? "dark" : "light");
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;

    const savedVisibility = localStorage.getItem("atomo-show-available");
    if (savedVisibility === "false") setShowAvailable(false);
  }, []);

  useEffect(() => {
    if (!notice) return;
    const t = window.setTimeout(() => setNotice(""), 2200);
    return () => window.clearTimeout(t);
  }, [notice]);

  useEffect(() => {
    if (!action) return;
    setTitle("");
    setAmount("");
    setAccountId(state.accounts[0]?.id ?? "");
    setDestinationAccountId(state.accounts.find(a => a.id !== state.accounts[0]?.id && a.currency === state.accounts[0]?.currency)?.id ?? "");
  }, [action, state.accounts]);

  const liquid = electro.liquidArs;
  const available = liquid - electro.nextCommitments;
  const recent = state.movements.slice(0, 5);
  const arsAccounts = state.accounts.filter(a => a.currency === "ARS");

  const filteredMovements = useMemo(() => {
    const q = query.trim().toLocaleLowerCase("es");
    if (!q) return state.movements;
    return state.movements.filter(m =>
      [m.title, m.category, m.type].some(value => value.toLocaleLowerCase("es").includes(q))
    );
  }, [state.movements, query]);

  function openAction(kind: Exclude<ActionKind, null>) {
    setAction(kind);
  }

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    localStorage.setItem("atomo-theme", next);
  }

  function toggleAvailable() {
    setShowAvailable(value => {
      const next = !value;
      localStorage.setItem("atomo-show-available", String(next));
      return next;
    });
  }

  function submitMovement(event: FormEvent) {
    event.preventDefault();
    if (!action) return;

    const numeric = Number(amount.split(".").join("").replace(",", "."));
    if (!Number.isFinite(numeric) || numeric <= 0) {
      setNotice("Revisá el monto");
      return;
    }

    if (action === "transfer") {
      if (!destinationAccountId || destinationAccountId === accountId) {
        setNotice("Elegí otra cuenta de destino");
        return;
      }
      const source = state.accounts.find(a => a.id === accountId);
      const target = state.accounts.find(a => a.id === destinationAccountId);
      if (!source || !target || source.currency !== target.currency) {
        setNotice("Las cuentas deben usar la misma moneda");
        return;
      }
    }

    addMovement({
      type: action,
      title,
      amount: numeric,
      accountId,
      destinationAccountId: action === "transfer" ? destinationAccountId : undefined
    });

    setNotice(action === "income" ? "Dinero agregado" : action === "expense" ? "Salida registrada" : "Transferencia registrada");
    setFlash(action);
    window.setTimeout(() => setFlash(null), 900);
    setAction(null);
  }

  const actionTitle =
    action === "income" ? "Agregar dinero" :
    action === "expense" ? "Registrar salida" :
    action === "transfer" ? "Mover entre mis cuentas" : "";

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="brand-mark" aria-label="Ir al inicio" onClick={() => setTab("Inicio")}>
          <img className="brand-logo" src="/atomo_favicon.png" alt="Átomo Finanzas" />
        </button>
        <div className="brand-copy">
          <strong>Átomo Finanzas</strong>
          <span>Las cuentas las hago yo. Las decisiones, vos.</span>
        </div>

        <nav className="desktop-nav" aria-label="Navegación principal">
          {(["Inicio", "Movimientos", "Electro", "Cuentas", "Más"] as Tab[]).map(item => (
            <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{item}</button>
          ))}
        </nav>

        <div className="top-actions">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Usar modo claro" : "Usar modo oscuro"}
            title={theme === "dark" ? "Modo claro" : "Modo oscuro"}
          >
            <span>{theme === "dark" ? "☀" : "☾"}</span>
          </button>
          <button className="profile-chip" onClick={() => setTab("Más")} aria-label="Perfil">
            <span className="avatar-mini">M</span>
            <span className="profile-copy"><strong>Mi espacio</strong><small>Privado</small></span>
          </button>
        </div>
      </header>

      <div className="workspace">
        {tab === "Inicio" && (
          <Home
            available={available}
            liquid={liquid}
            expanded={expanded}
            setExpanded={setExpanded}
            electro={electro}
            level={level}
            movements={recent}
            onIncome={() => openAction("income")}
            onExpense={() => openAction("expense")}
            onTransfer={() => openAction("transfer")}
            periodLabel={state.periodLabel}
            bufferTarget={state.bufferTarget}
            onGoMovements={() => setTab("Movimientos")}
            onGoElectro={() => setTab("Electro")}
            showAvailable={showAvailable}
            onToggleAvailable={toggleAvailable}
          />
        )}

        {tab === "Movimientos" && (
          <MovementsView
            movements={filteredMovements}
            query={query}
            setQuery={setQuery}
            onIncome={() => openAction("income")}
            onExpense={() => openAction("expense")}
            onTransfer={() => openAction("transfer")}
          />
        )}

        {tab === "Electro" && (
          <ElectroView electro={electro} level={level} />
        )}

        {tab === "Cuentas" && (
          <AccountsView
            accounts={state.accounts}
            onIncome={() => openAction("income")}
            onExpense={() => openAction("expense")}
            onTransfer={() => openAction("transfer")}
          />
        )}

        {tab === "Más" && (
          <MoreView
            debts={state.debts}
            onAccounts={() => setTab("Cuentas")}
            onReset={() => {
              reset();
              setNotice("Prototipo restaurado");
              setTab("Inicio");
            }}
          />
        )}
      </div>

      <nav className="mobile-bottom-nav" aria-label="Navegación móvil">
        {(["Inicio", "Movimientos", "Electro", "Más"] as Tab[]).map(item => (
          <button key={item} className={tab === item || (item === "Más" && tab === "Cuentas") ? "active" : ""} onClick={() => setTab(item)}>
            <span>{item === "Inicio" ? "⌂" : item === "Movimientos" ? "↕" : item === "Electro" ? "⌁" : "•••"}</span>
            <small>{item}</small>
          </button>
        ))}
      </nav>

      <div className={"sheet-backdrop " + (action ? "show" : "")} onClick={() => setAction(null)} />
      <form className={"action-sheet " + (action ? "open" : "") + " " + (action ?? "")} onSubmit={submitMovement} aria-hidden={!action}>
        <div className="sheet-handle" />
        <div className="section-heading">
          <div>
            <span className="eyebrow">{action === "income" ? "ENTRADA" : action === "expense" ? "SALIDA" : "MOVIMIENTO PROPIO"}</span>
            <h2>{actionTitle}</h2>
          </div>
          <button type="button" className="sheet-close" onClick={() => setAction(null)}>×</button>
        </div>

        <label className="amount-field">
          <span>Monto</span>
          <div><span>$</span><input inputMode="decimal" placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} autoFocus /></div>
        </label>

        <label className="field-block">
          <span>¿Qué fue?</span>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder={action === "income" ? "Ej.: Sueldo" : action === "expense" ? "Ej.: Supermercado" : "Ej.: Ahorro"} />
        </label>

        <label className="field-block">
          <span>{action === "income" ? "¿Dónde entra?" : "¿De dónde sale?"}</span>
          <select value={accountId} onChange={e => setAccountId(e.target.value)}>
            {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}
          </select>
        </label>

        {action === "transfer" && (
          <label className="field-block">
            <span>¿A cuál de tus cuentas va?</span>
            <select value={destinationAccountId} onChange={e => setDestinationAccountId(e.target.value)}>
              {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}
            </select>
          </label>
        )}

        <button className="sheet-primary" type="submit">
          {action === "income" ? "Agregar dinero" : action === "expense" ? "Registrar salida" : "Mover dinero"}
        </button>
        <p className="prototype-note">V2 en paralelo · estas pruebas quedan sólo en este navegador.</p>
      </form>

      <ActionFlash kind={flash ?? "transfer"} active={Boolean(flash)} />
      <div className={"toast " + (notice ? "show" : "")} role="status">{notice}</div>
    </main>
  );
}

function Home(props: {
  available: number;
  liquid: number;
  expanded: boolean;
  setExpanded: (value: boolean) => void;
  electro: ReturnType<typeof useFinance>["electro"];
  level: ReturnType<typeof useFinance>["level"];
  movements: ReturnType<typeof useFinance>["state"]["movements"];
  onIncome: () => void;
  onExpense: () => void;
  onTransfer: () => void;
  periodLabel: string;
  bufferTarget: number;
  onGoMovements: () => void;
  onGoElectro: () => void;
  showAvailable: boolean;
  onToggleAvailable: () => void;
}) {
  const { electro, level } = props;

  return (
    <>
      <section className="hero-card entrance entrance-1">
        <div className="hero-top">
          <div className="hero-balance">
            <span className="eyebrow">DISPONIBLE</span>
            <div className="balance-line">
              <h1>
                {props.showAvailable
                  ? <AnimatedMoney value={Math.max(0, props.available)} />
                  : <span className="masked-balance">$ ••••••</span>}
              </h1>
              <button
                className={"eye-button " + (props.showAvailable ? "" : "hidden")}
                onClick={props.onToggleAvailable}
                aria-label={props.showAvailable ? "Ocultar saldo disponible" : "Mostrar saldo disponible"}
                title={props.showAvailable ? "Ocultar saldo" : "Mostrar saldo"}
              >
                <span>{props.showAvailable ? "◉" : "◌"}</span>
              </button>
            </div>
            <p>{props.periodLabel}</p>
          </div>
          <div className="hero-side">
            <img className="mascot-home" src="/atomo_favicon.png" alt="Átomo, mascota de Átomo Finanzas" />
            <div className="period-pill">Período activo</div>
          </div>
        </div>

        <div className="primary-actions">
          <button className="money-action income" onClick={props.onIncome}>
            <span className="action-icon">＋</span>
            <span><strong>Agregar dinero</strong><small>Ingreso, sueldo o cobro</small></span>
          </button>
          <button className="money-action expense" onClick={props.onExpense}>
            <span className="action-icon">−</span>
            <span><strong>Sacar dinero</strong><small>Pago, compra o gasto</small></span>
          </button>
        </div>

        <div className="secondary-action-row">
          <button className="soft-action" onClick={props.onTransfer}>⇄ Mover entre mis cuentas</button>
          <button className="hero-detail-toggle" onClick={() => props.setExpanded(!props.expanded)}>
            {props.expanded ? "Ocultar detalle" : "Ver cómo se compone"} <span>{props.expanded ? "⌃" : "⌄"}</span>
          </button>
        </div>

        <div className={"hero-breakdown " + (props.expanded ? "open" : "")}>
          <div><span>Caja líquida</span><strong>{pesos.format(props.liquid)}</strong></div>
          <div><span>Próximos compromisos</span><strong className="amount-out">− {pesos.format(electro.nextCommitments)}</strong></div>
          <div><span>Colchón objetivo</span><strong>{pesos.format(props.bufferTarget)}</strong></div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="left-column">
          <section className="card entrance entrance-2">
            <div className="section-heading">
              <div><span className="eyebrow">ESTE PERÍODO</span><h2>Tu plata, simple</h2></div>
              <span className="tiny-score">{electro.overall}/100</span>
            </div>
            <div className="summary-strip">
              <div><span>Entró</span><strong className="amount-in"><AnimatedMoney value={electro.income} prefix="+ " /></strong></div>
              <div><span>Salió</span><strong className="amount-out"><AnimatedMoney value={electro.expenses} prefix="− " /></strong></div>
              <div><span>Balance</span><strong className={electro.balance >= 0 ? "amount-in" : "amount-out"}><AnimatedMoney value={Math.abs(electro.balance)} prefix={electro.balance >= 0 ? "+ " : "− "} /></strong></div>
            </div>
          </section>

          <section className="card entrance entrance-3">
            <div className="section-heading">
              <div><span className="eyebrow">ÚLTIMOS MOVIMIENTOS</span><h2>Actividad</h2></div>
              <button className="text-button" onClick={props.onGoMovements}>Ver todo</button>
            </div>
            <MovementList movements={props.movements} />
          </section>
        </div>

        <div className="right-column entrance entrance-2">
          <button className="card-link-wrap" onClick={props.onGoElectro} aria-label="Abrir Electro financiero">
            <ElectroPulse
              state={electro.state}
              liquidity={electro.liquidityLabel}
              solvency={electro.solvencyLabel}
              flow={electro.flowLabel}
            />
          </button>

          <section className="card atom-level-card">
            <div className="mascot-level-wrap">
              <img className="mascot-level" src="/atomo_favicon.png" alt="" aria-hidden="true" />
            </div>
            <div>
              <span className="eyebrow">TU EVOLUCIÓN</span>
              <h2>{level.name}</h2>
              <p>{level.description}</p>
              <div className="progress-track"><span style={{ width: Math.round(level.progress * 100) + "%" }} /></div>
              <small>{level.next ? Math.round(level.progress * 100) + "% hacia " + level.next : "Nivel máximo actual"}</small>
            </div>
          </section>
        </div>
      </section>
    </>
  );
}

function MovementsView(props: {
  movements: ReturnType<typeof useFinance>["state"]["movements"];
  query: string;
  setQuery: (value: string) => void;
  onIncome: () => void;
  onExpense: () => void;
  onTransfer: () => void;
}) {
  return (
    <section className="page-stack entrance entrance-1">
      <div className="page-title-row">
        <div><span className="eyebrow">MOVIMIENTOS</span><h1>Todo lo que pasó</h1><p>Buscá, cargá o revisá sin perderte entre formularios.</p></div>
        <div className="desktop-quick-actions">
          <button className="mini-action income" onClick={props.onIncome}>＋ Entrada</button>
          <button className="mini-action expense" onClick={props.onExpense}>− Salida</button>
          <button className="mini-action neutral" onClick={props.onTransfer}>⇄ Mover</button>
        </div>
      </div>

      <section className="card">
        <div className="search-row">
          <input value={props.query} onChange={e => props.setQuery(e.target.value)} placeholder="Buscar movimiento..." />
          <span>{props.movements.length} registros</span>
        </div>
        <MovementList movements={props.movements} large />
      </section>

      <div className="mobile-floating-actions">
        <button className="income" onClick={props.onIncome}>＋</button>
        <button className="expense" onClick={props.onExpense}>−</button>
        <button className="neutral" onClick={props.onTransfer}>⇄</button>
      </div>
    </section>
  );
}

function ElectroView(props: {
  electro: ReturnType<typeof useFinance>["electro"];
  level: ReturnType<typeof useFinance>["level"];
}) {
  const e = props.electro;
  return (
    <section className="page-stack entrance entrance-1">
      <div className="page-title-row">
        <div><span className="eyebrow">SALUD FINANCIERA</span><h1>Electro</h1><p>No decide por vos: te muestra dónde hay margen y dónde conviene mirar.</p></div>
        <div className="score-orb"><strong>{e.overall}</strong><span>/100</span></div>
      </div>

      <ElectroPulse state={e.state} liquidity={e.liquidityLabel} solvency={e.solvencyLabel} flow={e.flowLabel} large />

      <div className="metric-grid">
        <MetricCard title="Liquidez" value={e.liquidity} label={e.liquidityLabel} detail={"Caja líquida: " + pesos.format(e.liquidArs)} />
        <MetricCard title="Solvencia" value={e.solvency} label={e.solvencyLabel} detail="Activos conocidos frente a deudas cargadas." />
        <MetricCard title="Flujo" value={e.flow} label={e.flowLabel} detail={"Balance del período: " + signedMoney(e.balance)} />
      </div>

      <section className="card evolution-wide">
        <div className="mascot-level-wrap large">
          <img className="mascot-level" src="/atomo_favicon.png" alt="Átomo, mascota de Átomo Finanzas" />
        </div>
        <div className="evolution-copy">
          <span className="eyebrow">EVOLUCIÓN</span>
          <h2>{props.level.name}</h2>
          <p>{props.level.description} El nivel mide orden y hábitos, nunca riqueza absoluta.</p>
          <div className="progress-track"><span style={{ width: Math.round(props.level.progress * 100) + "%" }} /></div>
          <small>{props.level.next ? "Próxima evolución: " + props.level.next : "Nivel máximo actual"}</small>
        </div>
      </section>
    </section>
  );
}

function AccountsView(props: {
  accounts: ReturnType<typeof useFinance>["state"]["accounts"];
  onIncome: () => void;
  onExpense: () => void;
  onTransfer: () => void;
}) {
  return (
    <section className="page-stack entrance entrance-1">
      <div className="page-title-row">
        <div><span className="eyebrow">CUENTAS</span><h1>Tu plata por lugar</h1><p>Lo esencial primero. Los ajustes avanzados quedan atrás.</p></div>
        <button className="mini-action neutral" onClick={props.onTransfer}>⇄ Mover entre cuentas</button>
      </div>

      <div className="account-grid">
        {props.accounts.map(account => (
          <article className="account-card" key={account.id}>
            <div className="account-logo">{account.name.slice(0,1).toUpperCase()}</div>
            <div className="account-main">
              <span>{account.institution}</span>
              <h2>{account.name}</h2>
              <strong>{account.currency === "ARS" ? pesos.format(account.balance) : account.currency + " " + account.balance.toLocaleString("es-AR")}</strong>
            </div>
            <div className="account-status">{account.liquid ? "Disponible" : "Reserva"}</div>
          </article>
        ))}
      </div>

      <section className="card quick-center">
        <button className="mini-action income" onClick={props.onIncome}>＋ Agregar dinero</button>
        <button className="mini-action expense" onClick={props.onExpense}>− Registrar salida</button>
      </section>
    </section>
  );
}

function MoreView(props: {
  debts: ReturnType<typeof useFinance>["state"]["debts"];
  onAccounts: () => void;
  onReset: () => void;
}) {
  return (
    <section className="page-stack entrance entrance-1">
      <div className="page-title-row">
        <div><span className="eyebrow">MÁS</span><h1>Todo lo demás, sin ruido</h1><p>Lo menos frecuente vive acá para que Inicio siga simple.</p></div>
      </div>

      <div className="more-grid">
        <button className="more-card" onClick={props.onAccounts}><span>🏦</span><div><strong>Cuentas</strong><small>Saldos, instituciones y movimientos propios</small></div><b>›</b></button>
        <button className="more-card"><span>💳</span><div><strong>Tarjetas y cuotas</strong><small>Cierres, vencimientos y compras</small></div><b>›</b></button>
        <button className="more-card"><span>📈</span><div><strong>Inversiones</strong><small>Posiciones y comparaciones</small></div><b>›</b></button>
        <button className="more-card"><span>⚙️</span><div><strong>Configuración</strong><small>Período, objetivos y preferencias</small></div><b>›</b></button>
      </div>

      <section className="card">
        <div className="section-heading"><div><span className="eyebrow">PRÓXIMOS COMPROMISOS</span><h2>Deudas cargadas</h2></div></div>
        <div className="debt-list">
          {props.debts.map(debt => (
            <div key={debt.id}><span><strong>{debt.name}</strong><small>{debt.dueDate ? "Vence " + debt.dueDate.split("-").reverse().join("/") : "Sin fecha"}</small></span><b>{pesos.format(debt.nextPayment)}</b></div>
          ))}
        </div>
      </section>

      <button className="reset-prototype" onClick={props.onReset}>Restaurar datos de prueba de V2</button>
    </section>
  );
}

function MetricCard(props: { title: string; value: number; label: string; detail: string }) {
  return (
    <article className="metric-card">
      <span className="eyebrow">{props.title.toUpperCase()}</span>
      <div className="metric-number"><strong>{props.value}</strong><small>/100</small></div>
      <h3>{props.label}</h3>
      <p>{props.detail}</p>
      <div className="metric-bar"><span style={{ width: props.value + "%" }} /></div>
    </article>
  );
}

function MovementList(props: { movements: ReturnType<typeof useFinance>["state"]["movements"]; large?: boolean }) {
  if (!props.movements.length) return <div className="empty-state">No hay movimientos para mostrar.</div>;

  return (
    <div className={"transaction-list " + (props.large ? "large" : "")}>
      {props.movements.map(t => (
        <button className="transaction-row" key={t.id}>
          <span className={"tx-icon " + t.type}>{movementSymbol(t.type)}</span>
          <span className="tx-copy">
            <strong>{t.title}</strong>
            <small>{t.date.split("-").reverse().join("/")} · {t.category}</small>
          </span>
          <span className={t.type === "income" ? "tx-amount amount-in" : t.type === "expense" ? "tx-amount amount-out" : "tx-amount"}>
            {t.type === "income" ? "+ " : t.type === "expense" ? "− " : ""}{t.currency === "ARS" ? pesos.format(t.amount) : t.currency + " " + t.amount.toLocaleString("es-AR")}
          </span>
        </button>
      ))}
    </div>
  );
}
