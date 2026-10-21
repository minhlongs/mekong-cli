export type AccountType = 'asset' | 'liability' | 'equity' | 'income' | 'expense'
export type AccountSubtype =
  | 'cash'
  | 'bank'
  | 'receivable'
  | 'inventory'
  | 'fixed_asset'
  | 'other_asset'
  | 'payable'
  | 'credit_card'
  | 'tax_payable'
  | 'other_liability'
  | 'retained_earnings'
  | 'owner_equity'
  | 'revenue'
  | 'other_income'
  | 'cost_of_goods'
  | 'operating_expense'
  | 'payroll'
  | 'other_expense'

export interface Account {
  id: string
  code: string
  name: string
  type: AccountType
  subtype: AccountSubtype
  parentId?: string
  balance: number
  currency: string
  isActive: boolean
  description?: string
  children?: Account[]
}

export interface JournalEntry {
  id: string
  date: string
  description: string
  lines: JournalLine[]
  status: 'draft' | 'posted' | 'void'
  createdAt: string
}

export interface JournalLine {
  id: string
  accountId: string
  accountName: string
  debit: number
  credit: number
  memo?: string
}

export interface AccountingPeriod {
  startDate: string
  endDate: string
  isClosed: boolean
}

export interface FinancialSummary {
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
  totalIncome: number
  totalExpenses: number
  netIncome: number
  accountsReceivable: number
  accountsPayable: number
  cashBalance: number
}

export function buildAccountTree(accounts: Account[]): Account[] {
  const map = new Map<string, Account>()
  const roots: Account[] = []
  accounts.forEach(acc => map.set(acc.id, { ...acc, children: [] }))
  accounts.forEach(acc => {
    if (acc.parentId) {
      const parent = map.get(acc.parentId)
      const node = map.get(acc.id)
      if (parent && node) parent.children?.push(node)
    } else {
      const node = map.get(acc.id)
      if (node) roots.push(node)
    }
  })
  return roots
}

export function computeFinancialSummary(accounts: Account[]): FinancialSummary {
  const byType = (type: AccountType) =>
    accounts.filter(a => a.type === type).reduce((sum, a) => sum + a.balance, 0)
  const totalAssets = byType('asset')
  const totalLiabilities = byType('liability')
  const totalEquity = byType('equity')
  const totalIncome = byType('income')
  const totalExpenses = byType('expense')
  const sumSubtype = (...subtypes: AccountSubtype[]) =>
    accounts.filter(a => subtypes.includes(a.subtype)).reduce((sum, a) => sum + a.balance, 0)

  return {
    totalAssets,
    totalLiabilities,
    totalEquity,
    totalIncome,
    totalExpenses,
    netIncome: totalIncome - totalExpenses,
    accountsReceivable: sumSubtype('receivable'),
    accountsPayable: sumSubtype('payable'),
    cashBalance: sumSubtype('cash', 'bank'),
  }
}

export function getDefaultAccounts(): Account[] {
  const mk = (
    code: string,
    name: string,
    type: AccountType,
    subtype: AccountSubtype,
    balance: number
  ): Account => ({ id: code, code, name, type, subtype, balance, currency: 'USD', isActive: true })
  return [
    mk('1000', 'Cash', 'asset', 'cash', 45000),
    mk('1010', 'Operating Bank Account', 'asset', 'bank', 125000),
    mk('1100', 'Accounts Receivable', 'asset', 'receivable', 68000),
    mk('1500', 'Equipment', 'asset', 'fixed_asset', 35000),
    mk('2000', 'Accounts Payable', 'liability', 'payable', 12500),
    mk('2100', 'Credit Card', 'liability', 'credit_card', 3200),
    mk('2200', 'Sales Tax Payable', 'liability', 'tax_payable', 4800),
    mk('3000', 'Owner Equity', 'equity', 'owner_equity', 200000),
    mk('3100', 'Retained Earnings', 'equity', 'retained_earnings', 52500),
    mk('4000', 'Service Revenue', 'income', 'revenue', 285000),
    mk('4100', 'Consulting Income', 'income', 'revenue', 45000),
    mk('5000', 'Payroll Expense', 'expense', 'payroll', 95000),
    mk('5100', 'Rent Expense', 'expense', 'operating_expense', 24000),
    mk('5200', 'Software & Subscriptions', 'expense', 'operating_expense', 8500),
    mk('5300', 'Marketing Expense', 'expense', 'operating_expense', 15000),
  ]
}
