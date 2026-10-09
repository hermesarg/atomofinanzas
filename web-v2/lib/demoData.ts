import type { FinanceState } from "./types";

export const DEMO_STATE: FinanceState = {
  periodLabel: "Octubre 2026 · desde tu fecha habitual de cobro",
  bufferTarget: 700000,
  accounts: [
    { id: "banco", name: "Cuenta principal", institution: "Banco", currency: "ARS", balance: 2715000, liquid: true },
    { id: "billetera", name: "Billetera", institution: "Billetera", currency: "ARS", balance: 445000, liquid: true },
    { id: "usd", name: "Dólares", institution: "Banco", currency: "USD", balance: 820, liquid: false }
  ],
  debts: [
    { id: "d1", name: "Tarjeta", balance: 840000, nextPayment: 310000, dueDate: "2026-10-20", currency: "ARS" },
    { id: "d2", name: "Préstamo", balance: 1480000, nextPayment: 300000, dueDate: "2026-10-28", currency: "ARS" }
  ],
  movements: [
    { id: "m1", date: "2026-10-09", title: "Sueldo", category: "Sueldo", type: "income", amount: 2480000, currency: "ARS", accountId: "banco" },
    { id: "m2", date: "2026-10-08", title: "Supermercado", category: "Comida", type: "expense", amount: 68450, currency: "ARS", accountId: "banco" },
    { id: "m3", date: "2026-10-08", title: "Transferencia a reserva", category: "Transferencia propia", type: "transfer", amount: 200000, currency: "ARS", accountId: "banco", destinationAccountId: "billetera" },
    { id: "m4", date: "2026-10-07", title: "YPF", category: "Ingreso", type: "income", amount: 45200, currency: "ARS", accountId: "banco" },
    { id: "m5", date: "2026-10-06", title: "Combustible", category: "Transporte", type: "expense", amount: 52000, currency: "ARS", accountId: "banco" },
    { id: "m6", date: "2026-10-05", title: "Internet", category: "Servicios", type: "expense", amount: 31500, currency: "ARS", accountId: "banco" }
  ]
};
