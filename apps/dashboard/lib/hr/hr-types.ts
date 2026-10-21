/**
 * HR & Payroll Types and Mappers for AgencyOS
 * ERPNext Parity: Employee Management, Payroll, Leave Management
 */

export type EmploymentType = 'full_time' | 'part_time' | 'contractor' | 'intern'
export type EmployeeStatus = 'active' | 'on_leave' | 'terminated' | 'resigned'
export type LeaveType = 'annual' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'unpaid'
export type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled'

export interface Employee {
  id: string
  tenantId: string
  userId?: string
  code: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  dateOfBirth?: Date
  hireDate: Date
  terminationDate?: Date
  department: string
  position: string
  reportsTo?: string
  employmentType: EmploymentType
  status: EmployeeStatus
  salary: number
  currency: string
  bankAccount?: string
  taxId?: string
  createdAt: Date
  updatedAt: Date
}

export interface PayrollRun {
  id: string
  tenantId: string
  period: string // YYYY-MM
  runDate: Date
  status: 'draft' | 'processing' | 'completed' | 'cancelled'
  totalGross: number
  totalDeductions: number
  totalNet: number
  employeeCount: number
  createdBy: string
  createdAt: Date
}

export interface PayrollItem {
  id: string
  payrollRunId: string
  employeeId: string
  employeeName: string
  baseSalary: number
  allowances: number
  deductions: number
  taxAmount: number
  socialSecurity: number
  netPay: number
  workDays: number
  status: 'pending' | 'paid'
}

export interface LeaveRequest {
  id: string
  tenantId: string
  employeeId: string
  employeeName: string
  leaveType: LeaveType
  startDate: Date
  endDate: Date
  days: number
  reason?: string
  status: LeaveStatus
  approvedBy?: string
  approvedAt?: Date
  createdAt: Date
}

export interface LeaveBalance {
  employeeId: string
  annual: { total: number; used: number; remaining: number }
  sick: { total: number; used: number; remaining: number }
  personal: { total: number; used: number; remaining: number }
}

export interface EmployeeRow {
  id: string
  tenant_id: string
  user_id?: string
  code: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  date_of_birth?: string
  hire_date: string
  termination_date?: string
  department: string
  position: string
  reports_to?: string
  employment_type: EmploymentType
  status: EmployeeStatus
  salary: number
  currency: string
  bank_account?: string
  tax_id?: string
  created_at: string
  updated_at: string
}

export function mapEmployeeToDb(emp: Partial<Employee>): Record<string, unknown> {
  return {
    user_id: emp.userId,
    first_name: emp.firstName,
    last_name: emp.lastName,
    email: emp.email,
    phone: emp.phone,
    date_of_birth: emp.dateOfBirth?.toISOString(),
    hire_date: emp.hireDate?.toISOString(),
    termination_date: emp.terminationDate?.toISOString(),
    department: emp.department,
    position: emp.position,
    reports_to: emp.reportsTo,
    employment_type: emp.employmentType,
    status: emp.status,
    salary: emp.salary,
    currency: emp.currency,
    bank_account: emp.bankAccount,
    tax_id: emp.taxId,
  }
}

export function mapEmployeeFromDb(data: EmployeeRow): Employee {
  return {
    id: data.id,
    tenantId: data.tenant_id,
    userId: data.user_id,
    code: data.code,
    firstName: data.first_name,
    lastName: data.last_name,
    email: data.email,
    phone: data.phone,
    dateOfBirth: data.date_of_birth ? new Date(data.date_of_birth) : undefined,
    hireDate: new Date(data.hire_date),
    terminationDate: data.termination_date ? new Date(data.termination_date) : undefined,
    department: data.department,
    position: data.position,
    reportsTo: data.reports_to,
    employmentType: data.employment_type,
    status: data.status,
    salary: data.salary,
    currency: data.currency,
    bankAccount: data.bank_account,
    taxId: data.tax_id,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}
