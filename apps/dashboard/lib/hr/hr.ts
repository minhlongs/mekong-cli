/**
 * HR & Payroll Module for AgencyOS
 * ERPNext Parity: Employee Management, Payroll, Leave Management
 */

import { createClient } from '@supabase/supabase-js'
import type {
  Employee,
  EmployeeRow,
  EmployeeStatus,
  EmploymentType,
  LeaveBalance,
  LeaveRequest,
  LeaveStatus,
  LeaveType,
  PayrollItem,
  PayrollRun,
} from './hr-types'
import { mapEmployeeFromDb, mapEmployeeToDb } from './hr-types'
import { SOCIAL_SECURITY_RATES, TAX_BRACKETS } from './hr-seed'
import {
  calculatePayrollByCountry,
  createPayrollRunWithClient,
  getPayrollRunWithClient,
  processPayrollWithClient,
} from './hr-payroll'
import {
  type CreateLeaveRequestInput,
  approveLeaveWithClient,
  calculateWorkDays,
  getLeaveBalanceWithClient,
  requestLeaveWithClient,
} from './hr-leave-attendance'

export * from './hr-types'
export * from './hr-seed'
export * from './hr-payroll'
export * from './hr-leave-attendance'

export class HRService {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async createEmployee(
    tenantId: string,
    employee: Omit<Employee, 'id' | 'tenantId' | 'code' | 'createdAt' | 'updatedAt'>
  ): Promise<Employee> {
    const code = await this.generateEmployeeCode(tenantId)
    const { data, error } = await this.supabase
      .from('employees')
      .insert({ tenant_id: tenantId, code, ...this.mapToDb(employee) })
      .select()
      .single()

    if (error) throw new Error(`Failed to create employee: ${error.message}`)
    return this.mapFromDb(data)
  }

  async getEmployee(tenantId: string, employeeId: string): Promise<Employee | null> {
    const { data } = await this.supabase
      .from('employees')
      .select('*')
      .eq('tenant_id', tenantId)
      .eq('id', employeeId)
      .single()

    return data ? this.mapFromDb(data) : null
  }

  async listEmployees(
    tenantId: string,
    filters?: { status?: EmployeeStatus; department?: string }
  ): Promise<Employee[]> {
    let query = this.supabase
      .from('employees')
      .select('*')
      .eq('tenant_id', tenantId)
      .order('first_name')

    if (filters?.status) query = query.eq('status', filters.status)
    if (filters?.department) query = query.eq('department', filters.department)

    const { data, error } = await query
    if (error) throw new Error(`Failed to list employees: ${error.message}`)
    return (data || []).map(this.mapFromDb)
  }

  async updateEmployee(
    tenantId: string,
    employeeId: string,
    updates: Partial<Employee>
  ): Promise<Employee> {
    const { data, error } = await this.supabase
      .from('employees')
      .update(this.mapToDb(updates))
      .eq('tenant_id', tenantId)
      .eq('id', employeeId)
      .select()
      .single()

    if (error) throw new Error(`Failed to update employee: ${error.message}`)
    return this.mapFromDb(data)
  }

  async createPayrollRun(tenantId: string, period: string, createdBy: string): Promise<PayrollRun> {
    const employees = await this.listEmployees(tenantId, { status: 'active' })
    return createPayrollRunWithClient(this.supabase, tenantId, employees, period, createdBy)
  }

  async getPayrollRun(
    tenantId: string,
    runId: string
  ): Promise<{ run: PayrollRun; items: PayrollItem[] } | null> {
    return getPayrollRunWithClient(this.supabase, tenantId, runId)
  }

  async processPayroll(tenantId: string, runId: string): Promise<void> {
    return processPayrollWithClient(this.supabase, tenantId, runId)
  }

  calculatePayroll(salary: number, countryCode: string = 'VN') {
    return calculatePayrollByCountry(salary, countryCode)
  }

  async requestLeave(tenantId: string, request: CreateLeaveRequestInput): Promise<LeaveRequest> {
    const employee = await this.getEmployee(tenantId, request.employeeId)
    if (!employee) throw new Error('Employee not found')
    return requestLeaveWithClient(this.supabase, tenantId, employee, request)
  }

  async approveLeave(tenantId: string, leaveId: string, approverId: string): Promise<void> {
    return approveLeaveWithClient(this.supabase, tenantId, leaveId, approverId)
  }

  async getLeaveBalance(tenantId: string, employeeId: string): Promise<LeaveBalance> {
    const employee = await this.getEmployee(tenantId, employeeId)
    if (!employee) throw new Error('Employee not found')
    return getLeaveBalanceWithClient(this.supabase, tenantId, employee)
  }

  private async generateEmployeeCode(tenantId: string): Promise<string> {
    const { count } = await this.supabase
      .from('employees')
      .select('*', { count: 'exact', head: true })
      .eq('tenant_id', tenantId)

    return `EMP-${String((count || 0) + 1).padStart(5, '0')}`
  }

  private calculateWorkDays(start: Date, end: Date): number {
    return calculateWorkDays(start, end)
  }

  private mapToDb(emp: Partial<Employee>): Record<string, unknown> {
    return mapEmployeeToDb(emp)
  }

  private mapFromDb(data: EmployeeRow): Employee {
    return mapEmployeeFromDb(data)
  }
}

export function getHRService() {
  return new HRService()
}
