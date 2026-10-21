/**
 * Accounting Module for AgencyOS
 * ERPNext Parity: Chart of Accounts, Journal Entries, Ledgers
 */

import { createClient } from '@supabase/supabase-js'
import type {
  Account,
  AccountRow,
  AccountType,
  JournalEntry,
  JournalLine,
  TrialBalance,
} from './accounting-types'
import { mapToAccount } from './accounting-types'
import { DEFAULT_CHART_OF_ACCOUNTS } from './accounting-seed'
import {
  type CreateJournalEntryInput,
  createJournalEntryWithClient,
  postJournalEntryWithClient,
} from './accounting-journal'
import { getProfitAndLossWithClient, getTrialBalanceWithClient } from './accounting-reports'

export type {
  Account,
  AccountRow,
  AccountType,
  CreateJournalEntryInput,
  JournalEntry,
  JournalLine,
  TrialBalance,
}
export {
  DEFAULT_CHART_OF_ACCOUNTS,
  createJournalEntryWithClient,
  getProfitAndLossWithClient,
  getTrialBalanceWithClient,
  mapToAccount,
  postJournalEntryWithClient,
}

export class AccountingService {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async getChartOfAccounts(tenantId: string): Promise<Account[]> {
    const { data, error } = await this.supabase
      .from('accounts')
      .select('*')
      .eq('tenant_id', tenantId)
      .order('code')

    if (error) throw new Error(`Failed to get chart of accounts: ${error.message}`)
    return (data || []).map(this.mapToAccount)
  }

  async createAccount(
    tenantId: string,
    account: Omit<Account, 'id' | 'tenantId' | 'balance' | 'createdAt' | 'updatedAt'>
  ): Promise<Account> {
    const { data, error } = await this.supabase
      .from('accounts')
      .insert({
        tenant_id: tenantId,
        code: account.code,
        name: account.name,
        type: account.type,
        parent_id: account.parentId,
        is_group: account.isGroup,
        currency: account.currency,
        balance: 0,
      })
      .select()
      .single()

    if (error) throw new Error(`Failed to create account: ${error.message}`)
    return this.mapToAccount(data)
  }

  async initializeChartOfAccounts(tenantId: string): Promise<void> {
    const existing = await this.getChartOfAccounts(tenantId)
    if (existing.length > 0) return

    for (const account of DEFAULT_CHART_OF_ACCOUNTS) {
      await this.createAccount(tenantId, account)
    }
  }

  async getAccountBalance(tenantId: string, accountId: string): Promise<number> {
    const { data } = await this.supabase
      .from('accounts')
      .select('balance')
      .eq('tenant_id', tenantId)
      .eq('id', accountId)
      .single()

    return data?.balance || 0
  }

  async createJournalEntry(
    tenantId: string,
    entry: CreateJournalEntryInput,
    createdBy: string
  ): Promise<JournalEntry> {
    return createJournalEntryWithClient(this.supabase, tenantId, entry, createdBy)
  }

  async postJournalEntry(tenantId: string, journalId: string): Promise<void> {
    return postJournalEntryWithClient(this.supabase, tenantId, journalId)
  }

  async getTrialBalance(tenantId: string, asOfDate: Date): Promise<TrialBalance> {
    return getTrialBalanceWithClient(this.supabase, tenantId, asOfDate)
  }

  async getProfitAndLoss(tenantId: string, fromDate: Date, toDate: Date) {
    return getProfitAndLossWithClient(this.supabase, tenantId, fromDate, toDate)
  }

  private mapToAccount(data: AccountRow): Account {
    return mapToAccount(data)
  }
}

export function getAccountingService() {
  return new AccountingService()
}
