"use client";

import { useMemo, useState } from "react";
import ElectroPulse from "./ElectroPulse";

type ActionKind = "income" | "expense" | null;
type MobileTab = "Inicio" | "Movimientos" | "Electro" | "Más";

const transactions = [
  { title: "Sueldo", meta: "Hoy · Banco", amount: 2480000, type: "income" },
  { title: "Supermercado", meta: "Ayer · Mastercard", amount: -68450, type: "expense" },
  { title: "Transferencia a reserva", meta: "Ayer · Movimiento propio", amount: -200000, type: "transfer" },
  { title: "YPF", meta: "07 oct · Ingreso", amount: 45200, type: "income" }
] as const;

const pesos = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 0
});

export default function DashboardShell() {
  const [action, setAction] = useState<ActionKind>(null);
  const [mobileTab, setMobileTab] = useState<MobileTab>("Inicio");
  const [expanded, setExpanded] = useState(false);

  const actionTitle = useMemo(
    () => action === "income" ? "Agregar dinero" : "Registrar salida",
    [action]
  );

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true"><span>Á</span></div>
        <div className="brand-copy">
          <strong>Átomo Finanzas</strong>
          <span>Las cuentas las hago yo. Las decisiones, vos.</span>
        </div>

        <nav className="desktop-nav" aria-label="Navegación principal">
          {["Inicio", "Movimientos", "Electro", "Cuentas", "Más"].map((item, index) => (
            <button key={item} className={index === 0 ? "active" : ""}>{item}</button>
          ))}
        </nav>

        <button className="profile-chip" aria-label="Perfil">
          <span className="avatar-mini">M</span>
          <span className="profile-copy"><strong>Mi espacio</strong><small>Privado</small></span>
        </button>
      </header>

      <div className="workspace">
        <section className="hero-card entrance entrance-1">
          <div className="hero-top">
            <div>
              <span className="eyebrow">DISPONIBLE</span>
              <h1>{pesos.format(2550000)}</h1>
              <p>Octubre · desde tu fecha habitual de cobro</p>
            </div>
            <button className="eye-button" aria-label="Ocultar saldo">◉</button>
          </div>

          <div className="primary-actions">
            <button className="money-action income" onClick={() => setAction("income")}>
              <span className="action-icon">＋</span>
              <span><strong>Agregar dinero</strong><small>Ingreso, sueldo o cobro</small></span>
            </button>
            <button className="money-action expense" onClick={() => setAction("expense")}>
              <span className="action-icon">−</span>
              <span><strong>Sacar dinero</strong><small>Pago, compra o transferencia</small></span>
            </button>
          </div>

          <button className="hero-detail-toggle" onClick={() => setExpanded(v => !v)}>
            {expanded ? "Ocultar detalle" : "Ver cómo se compone"} <span>{expanded ? "⌃" : "⌄"}</span>
          </button>

          <div className={"hero-breakdown " + (expanded ? "open" : "")}>
            <div><span>Caja líquida</span><strong>{pesos.format(3160000)}</strong></div>
            <div><span>Próximos compromisos</span><strong className="amount-out">− {pesos.format(610000)}</strong></div>
            <div><span>Colchón objetivo</span><strong>{pesos.format(700000)}</strong></div>
          </div>
        </section>

        <section className="dashboard-grid">
          <div className="left-column">
            <section className="card entrance entrance-2">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">HOY</span>
                  <h2>Tu plata, simple</h2>
                </div>
                <button className="text-button">Ver todo</button>
              </div>
              <div className="summary-strip">
                <div><span>Entró</span><strong className="amount-in">+ {pesos.format(2525200)}</strong></div>
                <div><span>Salió</span><strong className="amount-out">− {pesos.format(413450)}</strong></div>
                <div><span>Balance</span><strong>+ {pesos.format(2111750)}</strong></div>
              </div>
            </section>

            <section className="card entrance entrance-3">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">ÚLTIMOS MOVIMIENTOS</span>
                  <h2>Actividad</h2>
                </div>
                <button className="text-button">Todos</button>
              </div>
              <div className="transaction-list">
                {transactions.map((t, index) => (
                  <button className="transaction-row" key={t.title + index}>
                    <span className={"tx-icon " + t.type}>
                      {t.type === "income" ? "↙" : t.type === "expense" ? "↗" : "⇄"}
                    </span>
                    <span className="tx-copy"><strong>{t.title}</strong><small>{t.meta}</small></span>
                    <span className={t.amount > 0 ? "tx-amount amount-in" : "tx-amount amount-out"}>
                      {t.amount > 0 ? "+" : "−"} {pesos.format(Math.abs(t.amount))}
                    </span>
                  </button>
                ))}
              </div>
            </section>
          </div>

          <div className="right-column entrance entrance-2">
            <ElectroPulse state="firme" />

            <section className="card atom-level-card">
              <div className="atom-orbit" aria-hidden="true">
                <span className="nucleus">Á</span>
                <i className="orbit orbit-a"><b /></i>
                <i className="orbit orbit-b"><b /></i>
              </div>
              <div>
                <span className="eyebrow">TU EVOLUCIÓN</span>
                <h2>Átomo</h2>
                <p>El punto de partida. Tu nivel mejora por orden y hábitos, no por tener más plata.</p>
                <div className="progress-track"><span style={{ width: "46%" }} /></div>
                <small>46% hacia Agua</small>
              </div>
            </section>
          </div>
        </section>
      </div>

      <nav className="mobile-bottom-nav" aria-label="Navegación móvil">
        {(["Inicio", "Movimientos", "Electro", "Más"] as MobileTab[]).map(tab => (
          <button
            key={tab}
            className={mobileTab === tab ? "active" : ""}
            onClick={() => setMobileTab(tab)}
          >
            <span>{tab === "Inicio" ? "⌂" : tab === "Movimientos" ? "↕" : tab === "Electro" ? "⌁" : "•••"}</span>
            <small>{tab}</small>
          </button>
        ))}
      </nav>

      <div className={"sheet-backdrop " + (action ? "show" : "")} onClick={() => setAction(null)} />
      <section className={"action-sheet " + (action ? "open" : "") + " " + (action ?? "")} aria-hidden={!action}>
        <div className="sheet-handle" />
        <div className="section-heading">
          <div>
            <span className="eyebrow">{action === "income" ? "ENTRADA" : "SALIDA"}</span>
            <h2>{actionTitle}</h2>
          </div>
          <button className="sheet-close" onClick={() => setAction(null)}>×</button>
        </div>
        <label className="amount-field">
          <span>Monto</span>
          <div><span>$</span><input inputMode="decimal" placeholder="0" aria-label="Monto" /></div>
        </label>
        <button className="sheet-row"><span>Concepto</span><strong>Elegir ›</strong></button>
        <button className="sheet-row"><span>{action === "income" ? "¿Dónde entra?" : "¿De dónde sale?"}</span><strong>Elegir ›</strong></button>
        <button className="sheet-primary">{action === "income" ? "Agregar" : "Registrar salida"}</button>
        <p className="prototype-note">Prototipo visual V2 · todavía no escribe en la base real.</p>
      </section>
    </main>
  );
}
