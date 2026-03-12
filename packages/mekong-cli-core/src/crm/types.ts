import { z } from 'zod';

/** Lead — potential customer */
export const LeadSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
  company: z.string().optional(),
  source: z.enum(['website', 'referral', 'social', 'cold_outreach', 'inbound', 'other']),
  status: z.enum(['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']),
  score: z.number().min(0).max(100).default(0),
  notes: z.array(z.object({
    content: z.string(),
    createdAt: z.string(),
  })).default([]),
  tags: z.array(z.string()).default([]),
  estimatedValue: z.number().optional(),           // USD
  nextFollowUp: z.string().optional(),             // ISO date
  assignedAgent: z.string().default('sales-agent'),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type Lead = z.infer<typeof LeadSchema>;

/** Customer — converted lead */
export const CustomerSchema = z.object({
  id: z.string(),
  leadId: z.string().optional(),                   // link to original lead
  name: z.string(),
  email: z.string().email(),
  company: z.string().optional(),
  plan: z.enum(['free', 'pro', 'team', 'enterprise']).default('free'),
  mrr: z.number().default(0),                      // monthly recurring revenue
  status: z.enum(['active', 'churned', 'paused', 'trial']),
  onboardedAt: z.string().optional(),
  churnedAt: z.string().optional(),
  healthScore: z.number().min(0).max(100).default(50),
  tags: z.array(z.string()).default([]),
  notes: z.array(z.object({
    content: z.string(),
    createdAt: z.string(),
  })).default([]),
  metadata: z.record(z.unknown()).default({}),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type Customer = z.infer<typeof CustomerSchema>;

/** Support Ticket */
export const TicketSchema = z.object({
  id: z.string(),
  customerId: z.string(),
  subject: z.string(),
  description: z.string(),
  status: z.enum(['open', 'in_progress', 'waiting_customer', 'resolved', 'closed']),
  priority: z.enum(['low', 'normal', 'high', 'critical']),
  category: z.enum(['bug', 'feature_request', 'question', 'billing', 'other']),
  messages: z.array(z.object({
    from: z.enum(['customer', 'agent', 'system']),
    content: z.string(),
    createdAt: z.string(),
  })).default([]),
  resolution: z.string().optional(),
  slaDeadline: z.string().optional(),              // ISO date
  createdAt: z.string(),
  updatedAt: z.string(),
  resolvedAt: z.string().optional(),
});

export type Ticket = z.infer<typeof TicketSchema>;

/** Sales Pipeline Stage */
export interface PipelineStage {
  name: string;
  leads: Lead[];
  totalValue: number;
  conversionRate: number;          // percentage to next stage
}

/** CRM Summary — for dashboard */
export interface CrmSummary {
  totalLeads: number;
  newLeadsThisWeek: number;
  totalCustomers: number;
  activeCustomers: number;
  churnedThisMonth: number;
  openTickets: number;
  avgResolutionTimeHours: number;
  pipeline: PipelineStage[];
  mrr: number;
  mrrGrowthPercent: number;
}
