/**
 * HR Payroll Calculations and Persistence Operations
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Employee, PayrollItem, PayrollRun } from './hr-types'
import { SOCIAL_SECURITY_RATES, TAX_BRACKETS } from './hr-seed'

export function calculatePayrollByCountry(salary: number, countryCode: string = 'VN') {
  const ssRates = SOCIAL_SECURITY_RATES[countryCode] || SOCIAL_SECURITY_RATES.VN
  const taxBrackets = TAX_BRACKETS[countryCode] || TAX_BRACKETS.VN

  const socialSecurity = salary * ssRates.employee
  const taxableIncome = salary - socialSecurity

  let tax = 0
  let remaining = taxableIncome
  for (const bracket of taxBrackets) {
    if (remaining <= 0) break
    const taxable = Math.min(remaining, bracket.max - bracket.min)
    tax += taxable * bracket.rate
    remaining -= taxable
  }

  const deductions = socialSecurity + tax
  const netPay = salary - deductions
  return { grossSalary: salary, socialSecurity, tax, deductions, netPay }
}

export async function createPayrollRunWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  employees: Employee[],
  period: string,
  createdBy: string
): Promise<PayrollRun> {
  const { data: run, error } = await supabase
    .from('payroll_runs')
    .insert({
      tenant_id: tenantId, period, run_date: new Date().toISOString(), status: 'draft',
      total_gross: 0, total_deductions: 0, total_net: 0, employee_count: employees.length, created_by: createdBy,
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to create payroll run: ${error.message}`)

  let totalGross = 0
  let totalDeductions = 0
  let totalNet = 0

  for (const emp of employees) {
    const calculation = calculatePayrollByCountry(emp.salary, emp.currency)
    await supabase.from('payroll_items').insert({
      payroll_run_id: run.id, employee_id: emp.id, employee_name: `${emp.firstName} ${emp.lastName}`,
      base_salary: emp.salary, allowances: 0, deductions: calculation.deductions,
      tax_amount: calculation.tax, social_security: calculation.socialSecurity, net_pay: calculation.netPay,
      work_days: 22, status: 'pending',
    })
    totalGross += emp.salary
    totalDeductions += calculation.deductions
    totalNet += calculation.netPay
  }

  await supabase
    .from('payroll_runs')
    .update({ total_gross: totalGross, total_deductions: totalDeductions, total_net: totalNet })
    .eq('id', run.id)

  return {
    id: run.id, tenantId, period, runDate: new Date(run.run_date), status: 'draft',
    totalGross, totalDeductions, totalNet, employeeCount: employees.length, createdBy, createdAt: new Date(run.created_at),
  }
}

interface PayrollItemRow {
  id: string
  payroll_run_id: string
  employee_id: string
  employee_name: string
  base_salary: number
  allowances: number
  deductions: number
  tax_amount: number
  social_security: number
  net_pay: number
  work_days: number
  status: 'pending' | 'paid'
}

export async function getPayrollRunWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  runId: string
): Promise<{ run: PayrollRun; items: PayrollItem[] } | null> {
  const { data: run } = await supabase.from('payroll_runs').select('*').eq('tenant_id', tenantId).eq('id', runId).single()
  if (!run) return null

  const { data: items } = await supabase.from('payroll_items').select('*').eq('payroll_run_id', runId)

  return {
    run: {
      id: run.id, tenantId: run.tenant_id, period: run.period, runDate: new Date(run.run_date), status: run.status,
      totalGross: run.total_gross, totalDeductions: run.total_deductions, totalNet: run.total_net,
      employeeCount: run.employee_count, createdBy: run.created_by, createdAt: new Date(run.created_at),
    },
    items: (items || []).map((i: PayrollItemRow) => ({
      id: i.id, payrollRunId: i.payroll_run_id, employeeId: i.employee_id, employeeName: i.employee_name,
      baseSalary: i.base_salary, allowances: i.allowances, deductions: i.deductions, taxAmount: i.tax_amount,
      socialSecurity: i.social_security, netPay: i.net_pay, workDays: i.work_days, status: i.status,
    })),
  }
}

export async function processPayrollWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  runId: string
): Promise<void> {
  await supabase.from('payroll_runs').update({ status: 'completed' }).eq('tenant_id', tenantId).eq('id', runId)
  await supabase.from('payroll_items').update({ status: 'paid' }).eq('payroll_run_id', runId)
}
