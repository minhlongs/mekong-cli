/**
 * Accounting Journal Entry Operations
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { JournalEntry, JournalLine } from './accounting-types'

export interface CreateJournalEntryInput {
  date: Date
  reference: string
  description: string
  lines: { accountId: string; debit: number; credit: number; description?: string }[]
}

export async function createJournalEntryWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  entry: CreateJournalEntryInput,
  createdBy: string
): Promise<JournalEntry> {
  // Validate: debits must equal credits
  const totalDebit = entry.lines.reduce((sum, l) => sum + l.debit, 0)
  const totalCredit = entry.lines.reduce((sum, l) => sum + l.credit, 0)

  if (Math.abs(totalDebit - totalCredit) > 0.01) {
    throw new Error(`Journal entry must balance: Debit ${totalDebit} ≠ Credit ${totalCredit}`)
  }

  // Create journal entry
  const { data: journal, error } = await supabase
    .from('journal_entries')
    .insert({
      tenant_id: tenantId,
      date: entry.date.toISOString(),
      reference: entry.reference,
      description: entry.description,
      total_debit: totalDebit,
      total_credit: totalCredit,
      status: 'draft',
      created_by: createdBy,
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to create journal entry: ${error.message}`)

  // Create lines
  const lines: JournalLine[] = []
  for (const line of entry.lines) {
    const { data: lineData } = await supabase
      .from('journal_lines')
      .insert({
        journal_id: journal.id,
        account_id: line.accountId,
        debit: line.debit,
        credit: line.credit,
        description: line.description,
      })
      .select('*, accounts(code, name)')
      .single()

    if (lineData) {
      lines.push({
        id: lineData.id,
        journalId: journal.id,
        accountId: lineData.account_id,
        accountCode: lineData.accounts?.code || '',
        accountName: lineData.accounts?.name || '',
        debit: lineData.debit,
        credit: lineData.credit,
        description: lineData.description,
      })
    }
  }

  return {
    id: journal.id,
    tenantId,
    date: new Date(journal.date),
    reference: journal.reference,
    description: journal.description,
    lines,
    totalDebit,
    totalCredit,
    status: journal.status,
    createdBy: journal.created_by,
    createdAt: new Date(journal.created_at),
  }
}

export async function postJournalEntryWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  journalId: string
): Promise<void> {
  // Get journal with lines
  const { data: journal } = await supabase
    .from('journal_entries')
    .select('*, journal_lines(*)')
    .eq('id', journalId)
    .eq('tenant_id', tenantId)
    .single()

  if (!journal) throw new Error('Journal entry not found')
  if (journal.status !== 'draft') throw new Error('Only draft entries can be posted')

  // Update account balances
  for (const line of journal.journal_lines || []) {
    const adjustment = line.debit - line.credit
    await supabase.rpc('adjust_account_balance', {
      p_account_id: line.account_id,
      p_adjustment: adjustment,
    })
  }

  // Mark as posted
  await supabase.from('journal_entries').update({ status: 'posted' }).eq('id', journalId)
}
