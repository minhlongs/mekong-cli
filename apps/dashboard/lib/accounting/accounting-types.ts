/**
 * Accounting Types & Mappers for AgencyOS
 * ERPNext Parity: Chart of Accounts, Journal Entries, Ledgers
 */

export type AccountType = 'asset' | 'liability' | 'equity' | 'income' | 'expense'

export interface Account {
  id: string
  tenantId: string
  code: string
  name: string
  type: AccountType
  parentId: string | null
  isGroup: boolean
  currency: string
  balance: number
  createdAt: Date
  updatedAt: Date
}

export interface JournalEntry {
  id: string
  tenantId: string
  date: Date
  reference: string
  description: string
  lines: JournalLine[]
  totalDebit: number
  totalCredit: number
  status: 'draft' | 'posted' | 'cancelled'
  createdBy: string
  createdAt: Date
}

export interface JournalLine {
  id: string
  journalId: string
  accountId: string
  accountCode: string
  accountName: string
  debit: number
  credit: number
  description?: string
}

export interface TrialBalance {
  accounts: {
    id: string
    code: string
    name: string
    type: AccountType
    debit: number
    credit: number
  }[]
  totalDebit: number
  totalCredit: number
  asOfDate: Date
}

export interface AccountRow {
  id: string
  tenant_id: string
  code: string
  name: string
  type: AccountType
  parent_id: string | null
  is_group: boolean
  currency: string
  balance?: number
  created_at: string
  updated_at: string
}

export function mapToAccount(data: AccountRow): Account {
  return {
    id: data.id,
    tenantId: data.tenant_id,
    code: data.code,
    name: data.name,
    type: data.type,
    parentId: data.parent_id,
    isGroup: data.is_group,
    currency: data.currency,
    balance: data.balance || 0,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}
