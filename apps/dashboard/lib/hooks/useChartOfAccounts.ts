'use client'

import { useState, useCallback, useMemo } from 'react'
import { logger } from '@/lib/utils/logger'
import {
  type AccountType,
  type AccountSubtype,
  type Account,
  type JournalEntry,
  type JournalLine,
  type AccountingPeriod,
  type FinancialSummary,
  buildAccountTree,
  computeFinancialSummary,
  getDefaultAccounts,
} from './chart-of-accounts-helpers'

export type {
  AccountType,
  AccountSubtype,
  Account,
  JournalEntry,
  JournalLine,
  AccountingPeriod,
  FinancialSummary,
}

/**
 * Chart of Accounts Hook
 * Hierarchical account structure for full double-entry bookkeeping
 */
export function useChartOfAccounts() {
  const [accounts, setAccounts] = useState<Account[]>(getDefaultAccounts())
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [loading] = useState(false)

  const accountTree = useMemo(() => buildAccountTree(accounts), [accounts])

  const getByType = useCallback(
    (type: AccountType) => accounts.filter(a => a.type === type),
    [accounts]
  )

  const createJournalEntry = useCallback(
    (date: string, description: string, lines: Omit<JournalLine, 'id'>[]): JournalEntry | null => {
      const totalDebits = lines.reduce((sum, l) => sum + l.debit, 0)
      const totalCredits = lines.reduce((sum, l) => sum + l.credit, 0)

      if (Math.abs(totalDebits - totalCredits) > 0.01) {
        logger.error('Debits must equal credits')
        return null
      }

      const entry: JournalEntry = {
        id: crypto.randomUUID(),
        date,
        description,
        lines: lines.map(l => ({ ...l, id: crypto.randomUUID() })),
        status: 'draft',
        createdAt: new Date().toISOString(),
      }

      setEntries(prev => [entry, ...prev])
      return entry
    },
    []
  )

  const postEntry = useCallback(
    (entryId: string) => {
      const entry = entries.find(e => e.id === entryId)
      if (!entry || entry.status !== 'draft') return

      setAccounts(prev =>
        prev.map(acc => {
          const line = entry.lines.find(l => l.accountId === acc.id)
          if (!line) return acc

          const balanceChange = ['asset', 'expense'].includes(acc.type)
            ? line.debit - line.credit
            : line.credit - line.debit

          return { ...acc, balance: acc.balance + balanceChange }
        })
      )

      setEntries(prev => prev.map(e => (e.id === entryId ? { ...e, status: 'posted' } : e)))
    },
    [entries]
  )

  const summary: FinancialSummary = useMemo(() => computeFinancialSummary(accounts), [accounts])

  const trialBalance = useMemo(
    () =>
      accounts.map(acc => ({
        ...acc,
        debit: acc.balance > 0 && ['asset', 'expense'].includes(acc.type) ? acc.balance : 0,
        credit:
          acc.balance > 0 && ['liability', 'equity', 'income'].includes(acc.type)
            ? acc.balance
            : 0,
      })),
    [accounts]
  )

  return {
    accounts,
    accountTree,
    entries,
    summary,
    trialBalance,
    loading,
    getByType,
    createJournalEntry,
    postEntry,
  }
}

export default useChartOfAccounts
