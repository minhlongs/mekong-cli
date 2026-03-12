import { z } from 'zod';

/** Invoice */
export const InvoiceSchema = z.object({
  id: z.string(),
  number: z.string(),                              // INV-2026-001
  customerId: z.string(),
  customerName: z.string(),
  customerEmail: z.string().email(),
  items: z.array(z.object({
    description: z.string(),
    quantity: z.number(),
    unitPrice: z.number(),                         // USD
    total: z.number(),
  })),
  subtotal: z.number(),
  tax: z.number().default(0),
  taxRate: z.number().default(0),                  // percentage
  total: z.number(),
  currency: z.string().default('USD'),
  status: z.enum(['draft', 'sent', 'viewed', 'paid', 'overdue', 'cancelled']),
  dueDate: z.string(),                             // ISO date
  paidAt: z.string().optional(),
  stripeInvoiceId: z.string().optional(),
  notes: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type Invoice = z.infer<typeof InvoiceSchema>;

/** Expense */
export const ExpenseSchema = z.object({
  id: z.string(),
  description: z.string(),
  amount: z.number(),
  currency: z.string().default('USD'),
  category: z.enum([
    'infrastructure',    // hosting, domains, servers
    'tools',             // SaaS subscriptions
    'ai_api',            // LLM API costs
    'marketing',         // ads, content
    'legal',             // contracts, compliance
    'office',            // equipment, supplies
    'travel',
    'contractor',        // freelancer payments
    'other',
  ]),
  vendor: z.string(),
  receiptPath: z.string().optional(),              // file path
  recurring: z.boolean().default(false),
  recurringInterval: z.enum(['monthly', 'yearly', 'weekly']).optional(),
  date: z.string(),                                // ISO date
  tags: z.array(z.string()).default([]),
  createdAt: z.string(),
});

export type Expense = z.infer<typeof ExpenseSchema>;

/** Revenue entry — from payments received */
export const RevenueEntrySchema = z.object({
  id: z.string(),
  invoiceId: z.string().optional(),
  customerId: z.string(),
  amount: z.number(),
  currency: z.string().default('USD'),
  type: z.enum(['subscription', 'one_time', 'template_sale', 'consulting', 'other']),
  description: z.string(),
  date: z.string(),
  stripePaymentId: z.string().optional(),
  createdAt: z.string(),
});

export type RevenueEntry = z.infer<typeof RevenueEntrySchema>;

/** Financial Summary — for dashboard and reports */
export interface FinancialSummary {
  period: { from: string; to: string };
  revenue: {
    total: number;
    byType: Record<string, number>;
    mrr: number;
    arr: number;                                   // annual recurring revenue
    mrrGrowth: number;                             // percent vs last period
  };
  expenses: {
    total: number;
    byCategory: Record<string, number>;
    topVendors: Array<{ vendor: string; amount: number }>;
  };
  profit: {
    gross: number;
    margin: number;                                // percentage
  };
  runway: {
    months: number;                                // at current burn rate
    burnRate: number;                              // monthly
  };
  customers: {
    total: number;
    new: number;
    churned: number;
    arpu: number;                                  // average revenue per user
    ltv: number;                                   // lifetime value estimate
  };
  aiCosts: {
    total: number;
    byProvider: Record<string, number>;
    byModel: Record<string, number>;
    percentOfRevenue: number;
  };
}

/** Monthly Close Report */
export interface MonthlyCloseReport {
  month: string;                                   // YYYY-MM
  summary: FinancialSummary;
  invoicesSent: number;
  invoicesPaid: number;
  invoicesOverdue: number;
  newSubscriptions: number;
  cancelledSubscriptions: number;
  notes: string[];
  generatedAt: string;
}
