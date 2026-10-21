/**
 * HR Leave & Attendance Management Operations
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Employee, LeaveBalance, LeaveRequest, LeaveType } from './hr-types'

export interface CreateLeaveRequestInput {
  employeeId: string
  leaveType: LeaveType
  startDate: Date
  endDate: Date
  reason?: string
}

export function calculateWorkDays(start: Date, end: Date): number {
  let count = 0
  const current = new Date(start)
  while (current <= end) {
    const day = current.getDay()
    if (day !== 0 && day !== 6) count++
    current.setDate(current.getDate() + 1)
  }
  return count
}

export async function requestLeaveWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  employee: Employee,
  request: CreateLeaveRequestInput
): Promise<LeaveRequest> {
  const days = calculateWorkDays(request.startDate, request.endDate)

  const { data, error } = await supabase
    .from('leave_requests')
    .insert({
      tenant_id: tenantId,
      employee_id: request.employeeId,
      employee_name: `${employee.firstName} ${employee.lastName}`,
      leave_type: request.leaveType,
      start_date: request.startDate.toISOString(),
      end_date: request.endDate.toISOString(),
      days,
      reason: request.reason,
      status: 'pending',
    })
    .select()
    .single()

  if (error) throw new Error(`Failed to create leave request: ${error.message}`)

  return {
    id: data.id,
    tenantId: data.tenant_id,
    employeeId: data.employee_id,
    employeeName: data.employee_name,
    leaveType: data.leave_type,
    startDate: new Date(data.start_date),
    endDate: new Date(data.end_date),
    days: data.days,
    reason: data.reason,
    status: data.status,
    createdAt: new Date(data.created_at),
  }
}

export async function approveLeaveWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  leaveId: string,
  approverId: string
): Promise<void> {
  await supabase
    .from('leave_requests')
    .update({
      status: 'approved',
      approved_by: approverId,
      approved_at: new Date().toISOString(),
    })
    .eq('tenant_id', tenantId)
    .eq('id', leaveId)
}

export async function getLeaveBalanceWithClient(
  supabase: SupabaseClient,
  tenantId: string,
  employee: Employee
): Promise<LeaveBalance> {
  const yearsOfService = Math.floor(
    (Date.now() - employee.hireDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
  )

  const annualTotal = Math.min(12 + yearsOfService, 20)
  const sickTotal = 30
  const personalTotal = 3

  const { data: leaves } = await supabase
    .from('leave_requests')
    .select('leave_type, days')
    .eq('tenant_id', tenantId)
    .eq('employee_id', employee.id)
    .eq('status', 'approved')
    .gte('start_date', new Date(new Date().getFullYear(), 0, 1).toISOString())

  let annualUsed = 0
  let sickUsed = 0
  let personalUsed = 0

  for (const leave of leaves || []) {
    if (leave.leave_type === 'annual') annualUsed += leave.days
    else if (leave.leave_type === 'sick') sickUsed += leave.days
    else if (leave.leave_type === 'personal') personalUsed += leave.days
  }

  return {
    employeeId: employee.id,
    annual: { total: annualTotal, used: annualUsed, remaining: annualTotal - annualUsed },
    sick: { total: sickTotal, used: sickUsed, remaining: sickTotal - sickUsed },
    personal: {
      total: personalTotal,
      used: personalUsed,
      remaining: personalTotal - personalUsed,
    },
  }
}
