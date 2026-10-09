import type { AtomoLevel, ElectroBand, ElectroResult, FinanceState } from "./types";

const clamp = (n: number) => Math.max(0, Math.min(100, n));

export function band(score: number): ElectroBand {
  if (score < 25) return "ajustado";
  if (score < 45) return "vigilar";
  if (score < 65) return "estable";
  if (score < 85) return "firme";
  return "muy-firme";
}

export function bandLabel(value: ElectroBand) {
  return {
    "ajustado": "Ajustado",
    "vigilar": "A vigilar",
    "estable": "Estable",
    "firme": "Firme",
    "muy-firme": "Muy firme"
  }[value];
}

function coverage(ratio: number) {
  const r = Math.max(0, ratio);
  if (r < .5) return 30 * r / .5;
  if (r < 1) return 30 + 35 * (r - .5) / .5;
  if (r < 1.5) return 65 + 20 * (r - 1) / .5;
  if (r < 2) return 85 + 15 * (r - 1.5) / .5;
  return 100;
}

export function calculateElectro(state: FinanceState): ElectroResult {
  const liquidArs = state.accounts
    .filter(a => a.currency === "ARS" && a.liquid)
    .reduce((sum, a) => sum + a.balance, 0);

  const nextCommitments = state.debts
    .filter(d => d.currency === "ARS")
    .reduce((sum, d) => sum + d.nextPayment, 0);

  const liquidityScore = clamp(coverage(liquidArs / Math.max(1, nextCommitments + state.bufferTarget)));

  const assets = state.accounts
    .filter(a => a.currency === "ARS")
    .reduce((sum, a) => sum + Math.max(0, a.balance), 0);

  const liabilities = state.debts
    .filter(d => d.currency === "ARS")
    .reduce((sum, d) => sum + Math.max(0, d.balance), 0);

  let solvencyScore = 60;
  if (liabilities <= 0) {
    solvencyScore = assets > 0 ? 100 : 60;
  } else {
    const ratio = assets / liabilities;
    if (ratio < .5) solvencyScore = 15 * ratio / .5;
    else if (ratio < 1) solvencyScore = 15 + 35 * (ratio - .5) / .5;
    else if (ratio < 2) solvencyScore = 50 + 30 * (ratio - 1);
    else if (ratio < 4) solvencyScore = 80 + 20 * (ratio - 2) / 2;
    else solvencyScore = 100;
  }
  solvencyScore = clamp(solvencyScore);

  const ars = state.movements.filter(m => m.currency === "ARS" && !m.pending);
  const income = ars.filter(m => m.type === "income").reduce((s,m) => s + m.amount, 0);
  const expenses = ars.filter(m => m.type === "expense").reduce((s,m) => s + m.amount, 0);
  const balance = income - expenses;

  let flowScore = 50;
  if (income > 0) {
    const netRatio = balance / income;
    flowScore = clamp(100 * (netRatio + .20) / .60);
  } else if (expenses > 0) {
    flowScore = 20;
  }

  const overall = Math.round(liquidityScore * .40 + solvencyScore * .35 + flowScore * .25);
  const stateBand = band(overall);

  return {
    overall,
    state: stateBand,
    stateLabel: bandLabel(stateBand),
    liquidity: Math.round(liquidityScore),
    liquidityLabel: bandLabel(band(liquidityScore)),
    solvency: Math.round(solvencyScore),
    solvencyLabel: bandLabel(band(solvencyScore)),
    flow: Math.round(flowScore),
    flowLabel: bandLabel(band(flowScore)),
    liquidArs,
    nextCommitments,
    income,
    expenses,
    balance
  };
}

const LEVELS = [
  ["Átomo", "Agua", "Punto de partida: empezás a ordenar y darle estructura a tus finanzas."],
  ["Agua", "Carbono", "Tu manejo cotidiano empieza a sostenerse con mayor regularidad."],
  ["Carbono", "Cadena", "Construís una estructura más flexible y útil."],
  ["Cadena", "Hidrocarburo", "Se nota continuidad y mejores hábitos."],
  ["Hidrocarburo", "Polímero", "Hay más capacidad de previsión y sostén."],
  ["Polímero", "Proteína", "Tu sistema financiero es más robusto y repetible."],
  ["Proteína", "ADN", "La estructura ya es compleja y funcional."],
  ["ADN", "", "Nivel alto de organización, consistencia y criterio."]
] as const;

export function calculateAtomoLevel(state: FinanceState, electro: ElectroResult): AtomoLevel {
  const completed = state.movements.filter(m => !m.pending).length;
  const dataDepth = Math.min(1, completed / 24);
  const habitScore = clamp((electro.liquidity + electro.solvency + electro.flow) / 3);
  const score = habitScore * (.45 + dataDepth * .55);

  const thresholds = [30, 42, 54, 65, 74, 82, 90, 101];
  let idx = thresholds.findIndex(t => score < t);
  if (idx < 0) idx = LEVELS.length - 1;

  const prev = idx === 0 ? 0 : thresholds[idx - 1];
  const nextThreshold = thresholds[idx];
  const progress = idx === LEVELS.length - 1 ? 1 : clamp((score - prev) / Math.max(1, nextThreshold - prev)) / 100;

  return {
    name: LEVELS[idx][0],
    next: LEVELS[idx][1] || undefined,
    description: LEVELS[idx][2],
    progress
  };
}
