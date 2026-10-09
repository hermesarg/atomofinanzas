export type Currency = "ARS" | "USD" | "USDT";
export type MovementType = "income" | "expense" | "transfer";
export type ElectroBand = "muy-firme" | "firme" | "estable" | "vigilar" | "ajustado";

export type Account = {
  id: string;
  name: string;
  institution: string;
  currency: Currency;
  balance: number;
  liquid: boolean;
};

export type Movement = {
  id: string;
  date: string;
  title: string;
  category: string;
  type: MovementType;
  amount: number;
  currency: Currency;
  accountId?: string;
  destinationAccountId?: string;
  pending?: boolean;
};

export type Debt = {
  id: string;
  name: string;
  balance: number;
  nextPayment: number;
  dueDate?: string;
  currency: Currency;
};

export type FinanceState = {
  accounts: Account[];
  movements: Movement[];
  debts: Debt[];
  periodLabel: string;
  bufferTarget: number;
};

export type ElectroResult = {
  overall: number;
  state: ElectroBand;
  stateLabel: string;
  liquidity: number;
  liquidityLabel: string;
  solvency: number;
  solvencyLabel: string;
  flow: number;
  flowLabel: string;
  liquidArs: number;
  nextCommitments: number;
  income: number;
  expenses: number;
  balance: number;
};

export type AtomoLevel = {
  name: string;
  next?: string;
  progress: number;
  description: string;
};
