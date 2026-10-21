/**
 * Accounting Financial Reports (Trial Balance & Profit/Loss)
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { AccountType, TrialBalance } from './accounting-types'

export async function getTrialBalanceWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  asOfDate: Date
): Promise<TrialBalance> {
  const { data: accounts } = await supabase
    .from('accounts')
    .select('id, code, name, type, balance')
    .eq('tenant_id', tenantId)
    .eq('is_group', false)
    .order('code')

  const balances = (accounts || []).map(acc => {
    const isDebitNormal = ['asset', 'expense'].includes(acc.type)
    return {
      id: acc.id,
      code: acc.code,
      name: acc.name,
      type: acc.type as AccountType,
      debit:
        isDebitNormal && acc.balance > 0
          ? acc.balance
          : !isDebitNormal && acc.balance < 0
            ? -acc.balance
            : 0,
      credit:
        !isDebitNormal && acc.balance > 0
          ? acc.balance
          : isDebitNormal && acc.balance < 0
            ? -acc.balance
            : 0,
    }
  })

  return {
    accounts: balances,
    totalDebit: balances.reduce((sum, a) => sum + a.debit, 0),
    totalCredit: balances.reduce((sum, a) => sum + a.credit, 0),
    asOfDate,
  }
}

export async function getProfitAndLossWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  fromDate: Date,
  toDate: Date
) {
  const { data: income } = await supabase
    .from('accounts')
    .select('id, code, name, balance')
    .eq('tenant_id', tenantId)
    .eq('type', 'income')
    .eq('is_group', false)

  const { data: expenses } = await supabase
    .from('accounts')
    .select('id, code, name, balance')
    .eq('tenant_id', tenantId)
    .eq('type', 'expense')
    .eq('is_group', false)

  const totalIncome = (income || []).reduce((sum, acc) => sum + Math.abs(acc.balance), 0)
  const totalExpenses = (expenses || []).reduce((sum, acc) => sum + Math.abs(acc.balance), 0)

  return {
    income: income || [],
    expenses: expenses || [],
    totalIncome,
    totalExpenses,
    netProfit: totalIncome - totalExpenses,
    fromDate,
    toDate,
  }
}
