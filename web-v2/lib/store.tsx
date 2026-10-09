"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { DEMO_STATE } from "./demoData";
import { calculateAtomoLevel, calculateElectro } from "./finance";
import type { FinanceState, Movement, MovementType } from "./types";

type AddMovementInput = {
  type: MovementType;
  title: string;
  amount: number;
  accountId: string;
  destinationAccountId?: string;
};

type FinanceStore = {
  state: FinanceState;
  electro: ReturnType<typeof calculateElectro>;
  level: ReturnType<typeof calculateAtomoLevel>;
  addMovement: (input: AddMovementInput) => void;
  reset: () => void;
};

const KEY = "atomo-v2-prototype";
const Ctx = createContext<FinanceStore | null>(null);

function cloneDemo(): FinanceState {
  return JSON.parse(JSON.stringify(DEMO_STATE));
}

export function FinanceProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<FinanceState>(cloneDemo);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY);
      if (saved) setState(JSON.parse(saved));
    } catch {}
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(KEY, JSON.stringify(state));
  }, [state, hydrated]);

  const addMovement = (input: AddMovementInput) => {
    if (!Number.isFinite(input.amount) || input.amount <= 0) return;

    setState(prev => {
      const accounts = prev.accounts.map(a => ({ ...a }));
      const source = accounts.find(a => a.id === input.accountId);
      const target = input.destinationAccountId
        ? accounts.find(a => a.id === input.destinationAccountId)
        : undefined;

      if (input.type === "income" && source) source.balance += input.amount;
      if (input.type === "expense" && source) source.balance -= input.amount;
      if (input.type === "transfer" && source && target && source.currency === target.currency) {
        source.balance -= input.amount;
        target.balance += input.amount;
      }

      const movement: Movement = {
        id: crypto.randomUUID(),
        date: new Date().toISOString().slice(0, 10),
        title: input.title.trim() || (input.type === "income" ? "Ingreso" : input.type === "expense" ? "Salida" : "Transferencia"),
        category: input.type === "transfer" ? "Transferencia propia" : input.type === "income" ? "Ingreso" : "Gasto",
        type: input.type,
        amount: input.amount,
        currency: source?.currency ?? "ARS",
        accountId: input.accountId,
        destinationAccountId: input.destinationAccountId
      };

      return { ...prev, accounts, movements: [movement, ...prev.movements] };
    });
  };

  const reset = () => setState(cloneDemo());
  const electro = useMemo(() => calculateElectro(state), [state]);
  const level = useMemo(() => calculateAtomoLevel(state, electro), [state, electro]);

  return <Ctx.Provider value={{ state, electro, level, addMovement, reset }}>{children}</Ctx.Provider>;
}

export function useFinance() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useFinance debe usarse dentro de FinanceProvider");
  return value;
}
