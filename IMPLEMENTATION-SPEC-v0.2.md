# MEKONG-CLI v0.2.0 IMPLEMENTATION SPEC
# Upgrade từ v0.1.0. Đọc xong → code từng module theo thứ tự.
# QUAN TRỌNG: Giữ nguyên toàn bộ code v0.1.0. Chỉ THÊM modules mới.

---

## 0. PREREQUISITE

v0.1.0 phải đã hoàn thành và pass `pnpm build && pnpm test`.
Nếu chưa, STOP và hoàn thành v0.1.0 trước.

Verify:
```bash
pnpm build    # phải pass
pnpm test     # phải pass  
mekong --help # phải hiện command list
```

---

## 1. NEW DEPENDENCIES

```bash
pnpm add nodemailer googleapis stripe handlebars date-fns cron markdown-table csv-parse csv-stringify
pnpm add -D @types/nodemailer @types/cron
```

Bump version trong package.json:
```json
{ "version": "0.2.0" }
```

---

## 2. NEW DIRECTORY STRUCTURE (thêm vào cây v0.1.0)

```
src/
  # ... giữ nguyên v0.1.0 ...

  # === MỚI v0.2.0 ===
  integrations/
  │   ├── index.ts                    # Integration registry
  │   ├── types.ts                    # Shared integration types
  │   ├── stripe/
  │   │   ├── client.ts               # Stripe API wrapper
  │   │   ├── invoices.ts             # Create/send/track invoices
  │   │   ├── payments.ts             # Payment tracking
  │   │   └── types.ts                # Stripe-specific types
  │   ├── email/
  │   │   ├── sender.ts               # SMTP email sender
  │   │   ├── templates.ts            # Handlebars email templates
  │   │   ├── inbox.ts                # IMAP inbox reader (basic)
  │   │   └── types.ts
  │   ├── calendar/
  │   │   ├── google.ts               # Google Calendar API
  │   │   ├── scheduler.ts            # Smart scheduling
  │   │   └── types.ts
  │   └── notifications/
  │       ├── slack.ts                # Slack webhook sender
  │       ├── telegram.ts             # Telegram bot sender
  │       ├── dispatcher.ts           # Multi-channel notification router
  │       └── types.ts
  │
  ├── crm/
  │   ├── types.ts                    # CRM domain types
  │   ├── leads.ts                    # Lead management
  │   ├── customers.ts                # Customer lifecycle
  │   ├── support.ts                  # Support ticket system
  │   ├── pipeline.ts                 # Sales pipeline tracker
  │   └── store.ts                    # CRM data persistence (JSON files)
  │
  ├── finance/
  │   ├── types.ts                    # Finance domain types
  │   ├── invoicing.ts                # Invoice generation & tracking
  │   ├── expenses.ts                 # Expense logging & categorization
  │   ├── revenue.ts                  # Revenue tracking & MRR calc
  │   ├── reports.ts                  # Financial reports generator
  │   └── store.ts                    # Finance data persistence (JSON files)
  │
  ├── dashboard/
  │   ├── types.ts                    # Dashboard types
  │   ├── daily-standup.ts            # Auto-generate daily standup
  │   ├── weekly-digest.ts            # Weekly business summary
  │   ├── metrics-aggregator.ts       # Collect metrics across all modules
  │   └── renderer.ts                 # CLI dashboard rendering
  │
  ├── agents/definitions/             # THÊM vào folder có sẵn
  │   ├── finance-agent.yaml          # NEW
  │   ├── sales-agent.yaml            # NEW
  │   ├── support-agent.yaml          # NEW
  │   └── scheduler-agent.yaml        # NEW
  │
  ├── sops/templates/                 # THÊM vào folder có sẵn
  │   ├── invoice-send.yaml           # NEW
  │   ├── expense-log.yaml            # NEW
  │   ├── monthly-close.yaml          # NEW
  │   ├── lead-qualify.yaml           # NEW
  │   ├── customer-onboard.yaml       # NEW
  │   ├── support-triage.yaml         # NEW
  │   ├── weekly-report.yaml          # NEW
  │   ├── daily-standup.yaml          # NEW
  │   ├── email-campaign.yaml         # NEW
  │   └── payment-followup.yaml       # NEW
  │
  └── cli/commands/                   # THÊM vào folder có sẵn
      ├── crm.ts                      # `mekong crm <subcommand>` NEW
      ├── finance.ts                  # `mekong finance <subcommand>` NEW
      └── dashboard.ts               # `mekong dashboard` NEW
```

---

## 3. NEW TYPES

### 3.1 src/integrations/types.ts
```typescript
import type { Result } from '../types/common.js';

/** Base interface for all integrations */
export interface Integration {
  name: string;
  connected: boolean;
  connect(credentials: IntegrationCredentials): Promise<Result<void>>;
  disconnect(): Promise<void>;
  healthCheck(): Promise<boolean>;
}

/** Credential types per integration */
export type IntegrationCredentials =
  | { type: 'api_key'; key: string }
  | { type: 'oauth'; clientId: string; clientSecret: string; refreshToken: string }
  | { type: 'smtp'; host: string; port: number; user: string; pass: string; secure: boolean }
  | { type: 'webhook'; url: string; secret?: string };

/** Integration registry entry */
export interface IntegrationEntry {
  integration: Integration;
  credentials?: IntegrationCredentials;
  lastHealthCheck?: string;
  enabled: boolean;
}

/** Notification payload — unified across channels */
export interface NotificationPayload {
  channel: 'slack' | 'telegram' | 'email';
  to: string;                     // channel ID, chat ID, or email
  subject?: string;               // email only
  message: string;                // plain text or markdown
  priority: 'low' | 'normal' | 'high' | 'critical';
  metadata?: Record<string, unknown>;
}
```

### 3.2 src/crm/types.ts
```typescript
import type { Id, Timestamp, Status } from '../types/common.js';
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
```

### 3.3 src/finance/types.ts
```typescript
import type { Id, Timestamp } from '../types/common.js';
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
```

### 3.4 src/dashboard/types.ts
```typescript
import type { CrmSummary } from '../crm/types.js';
import type { FinancialSummary } from '../finance/types.js';

/** Daily Standup Report — auto-generated every morning */
export interface DailyStandup {
  date: string;
  yesterday: {
    tasksCompleted: string[];
    sopRunsCompleted: number;
    codeCommits: number;
    ticketsResolved: number;
    invoicesSent: number;
    revenue: number;
  };
  today: {
    scheduledTasks: string[];
    followUps: Array<{ contact: string; reason: string; priority: string }>;
    deadlines: Array<{ item: string; dueDate: string }>;
    sopScheduled: string[];
  };
  blockers: string[];
  metrics: {
    mrrCurrent: number;
    mrrTarget: number;
    openTickets: number;
    overdueInvoices: number;
    budgetUsedToday: number;
  };
}

/** Weekly Business Digest */
export interface WeeklyDigest {
  week: string;                                     // YYYY-Www
  period: { from: string; to: string };
  financial: FinancialSummary;
  crm: CrmSummary;
  operations: {
    sopRunsTotal: number;
    sopSuccessRate: number;
    avgSopDuration: number;
    topSOPs: Array<{ name: string; runs: number; avgTime: number }>;
    agentTokensUsed: number;
    agentCostTotal: number;
  };
  highlights: string[];                            // AI-generated key insights
  recommendations: string[];                       // AI-generated suggestions
  comparison: {
    revenueVsLastWeek: number;                     // percent change
    expensesVsLastWeek: number;
    customersVsLastWeek: number;
    ticketsVsLastWeek: number;
  };
}

/** Dashboard view for CLI — the Andon Board */
export interface AndonBoard {
  status: 'green' | 'yellow' | 'red';             // overall health
  alerts: Array<{
    level: 'info' | 'warning' | 'critical';
    message: string;
    source: string;
    timestamp: string;
  }>;
  quickStats: {
    mrr: string;
    customers: string;
    openTickets: string;
    todayRevenue: string;
    todayExpenses: string;
    agentBudgetUsed: string;
    nextDeadline: string;
  };
  recentActivity: Array<{
    action: string;
    timestamp: string;
    source: string;
  }>;
}
```

---

## 4. INTEGRATION MODULES

### 4.1 src/integrations/index.ts — Integration Registry
```typescript
/**
 * Integration Registry — discover, connect, manage third-party services.
 * 
 * Usage:
 *   const registry = new IntegrationRegistry(config);
 *   await registry.connect('stripe', { type: 'api_key', key: 'sk_...' });
 *   const stripe = registry.get('stripe') as StripeIntegration;
 *   await stripe.createInvoice({...});
 *
 * All integrations are LAZY — only initialized when first used.
 * Credentials stored in ~/.mekong/credentials.json (gitignored).
 */

import type { Integration, IntegrationCredentials, IntegrationEntry } from './types.js';
import type { MekongConfig } from '../types/config.js';

export class IntegrationRegistry {
  private entries: Map<string, IntegrationEntry> = new Map();

  constructor(private config: MekongConfig) {}

  /** Register an integration (called during startup) */
  register(name: string, integration: Integration): void { /* ... */ }

  /** Connect integration with credentials */
  async connect(name: string, credentials: IntegrationCredentials): Promise<void> { /* ... */ }

  /** Get connected integration — throws if not connected */
  get<T extends Integration>(name: string): T { /* ... */ throw new Error('Not implemented'); }

  /** Check if integration is available and healthy */
  async isHealthy(name: string): Promise<boolean> { /* ... */ return false; }

  /** List all registered integrations and their status */
  list(): Array<{ name: string; connected: boolean; healthy: boolean }> { /* ... */ return []; }

  /** Save credentials to ~/.mekong/credentials.json */
  private async saveCredentials(): Promise<void> { /* ... */ }

  /** Load credentials from ~/.mekong/credentials.json */
  private async loadCredentials(): Promise<void> { /* ... */ }
}
```

### 4.2 src/integrations/stripe/client.ts
```typescript
/**
 * Stripe API wrapper — invoicing, payments, subscriptions.
 * Uses stripe npm package.
 * 
 * Requires: STRIPE_SECRET_KEY in env or mekong.yaml
 * 
 * Features:
 * - Create and send invoices
 * - Track payment status
 * - List transactions
 * - Subscription management
 * - Revenue reporting
 *
 * Security: Level 2 (requires first-time approval)
 * Financial operations (refund, cancel): Level 3 (always ask)
 */

import Stripe from 'stripe';
import type { Integration, IntegrationCredentials } from '../types.js';
import type { Invoice, RevenueEntry } from '../../finance/types.js';
import type { Result } from '../../types/common.js';

export class StripeIntegration implements Integration {
  name = 'stripe';
  connected = false;
  private client: Stripe | null = null;

  async connect(credentials: IntegrationCredentials): Promise<Result<void>> {
    if (credentials.type !== 'api_key') {
      return { ok: false, error: new Error('Stripe requires api_key credentials') };
    }
    this.client = new Stripe(credentials.key);
    this.connected = true;
    return { ok: true, value: undefined };
  }

  async disconnect(): Promise<void> {
    this.client = null;
    this.connected = false;
  }

  async healthCheck(): Promise<boolean> {
    if (!this.client) return false;
    try {
      await this.client.balance.retrieve();
      return true;
    } catch { return false; }
  }

  /** Create a Stripe invoice from our Invoice type */
  async createInvoice(invoice: Omit<Invoice, 'id' | 'stripeInvoiceId' | 'createdAt' | 'updatedAt'>): Promise<Result<string>> {
    // 1. Find or create Stripe customer by email
    // 2. Create invoice with line items
    // 3. Return Stripe invoice ID
    throw new Error('Not implemented');
  }

  /** Send invoice to customer via Stripe */
  async sendInvoice(stripeInvoiceId: string): Promise<Result<void>> {
    throw new Error('Not implemented');
  }

  /** Get payment status for an invoice */
  async getPaymentStatus(stripeInvoiceId: string): Promise<Result<'draft' | 'open' | 'paid' | 'void' | 'uncollectible'>> {
    throw new Error('Not implemented');
  }

  /** List recent payments for revenue tracking */
  async listRecentPayments(days: number): Promise<Result<RevenueEntry[]>> {
    throw new Error('Not implemented');
  }

  /** Get balance overview */
  async getBalance(): Promise<Result<{ available: number; pending: number; currency: string }>> {
    throw new Error('Not implemented');
  }
}
```

### 4.3 src/integrations/email/sender.ts
```typescript
/**
 * Email sender via SMTP (nodemailer).
 * 
 * Supports:
 * - Send plain text or HTML emails
 * - Handlebars templates for invoices, notifications, follow-ups
 * - CC/BCC
 * - Attachments (invoice PDFs)
 * - Rate limiting (avoid spam flags)
 *
 * Requires SMTP config in mekong.yaml:
 *   integrations.email.host: smtp.gmail.com
 *   integrations.email.port: 587
 *   integrations.email.user: you@gmail.com
 *   integrations.email.pass_env: SMTP_PASSWORD
 *
 * Security: Level 2 (ask first time, remember preference)
 */

import nodemailer from 'nodemailer';
import type { Integration, IntegrationCredentials } from '../types.js';
import type { Result } from '../../types/common.js';

export interface EmailMessage {
  to: string | string[];
  cc?: string | string[];
  bcc?: string | string[];
  subject: string;
  text?: string;
  html?: string;
  templateName?: string;           // Handlebars template key
  templateData?: Record<string, unknown>;
  attachments?: Array<{
    filename: string;
    path: string;
  }>;
  replyTo?: string;
}

export class EmailIntegration implements Integration {
  name = 'email';
  connected = false;
  private transporter: nodemailer.Transporter | null = null;
  private sendCount = 0;
  private lastResetTime = Date.now();
  private readonly RATE_LIMIT = 20;                // max emails per hour
  private readonly RATE_WINDOW = 3600000;          // 1 hour in ms

  async connect(credentials: IntegrationCredentials): Promise<Result<void>> {
    if (credentials.type !== 'smtp') {
      return { ok: false, error: new Error('Email requires smtp credentials') };
    }
    this.transporter = nodemailer.createTransport({
      host: credentials.host,
      port: credentials.port,
      secure: credentials.secure,
      auth: { user: credentials.user, pass: credentials.pass },
    });
    this.connected = true;
    return { ok: true, value: undefined };
  }

  async disconnect(): Promise<void> {
    this.transporter?.close();
    this.transporter = null;
    this.connected = false;
  }

  async healthCheck(): Promise<boolean> {
    if (!this.transporter) return false;
    try { await this.transporter.verify(); return true; }
    catch { return false; }
  }

  /** Send email with rate limiting */
  async send(message: EmailMessage): Promise<Result<{ messageId: string }>> {
    // 1. Check rate limit
    // 2. If template, render with Handlebars
    // 3. Send via transporter
    // 4. Return messageId
    throw new Error('Not implemented');
  }

  /** Check rate limit — Poka-yoke against accidental spam */
  private checkRateLimit(): boolean {
    if (Date.now() - this.lastResetTime > this.RATE_WINDOW) {
      this.sendCount = 0;
      this.lastResetTime = Date.now();
    }
    return this.sendCount < this.RATE_LIMIT;
  }
}
```

### 4.4 src/integrations/email/templates.ts
```typescript
/**
 * Email templates using Handlebars.
 * 
 * Built-in templates:
 * - invoice_send: Invoice email to customer
 * - payment_received: Payment confirmation
 * - payment_overdue: Overdue reminder
 * - welcome: Customer onboarding welcome
 * - follow_up: Lead follow-up
 * - support_reply: Support ticket response
 * - weekly_digest: Weekly summary to self
 *
 * Custom templates: place .hbs files in ~/.mekong/templates/email/
 */

import Handlebars from 'handlebars';

/** Template definitions — compiled once, reused */
const TEMPLATES: Record<string, string> = {
  invoice_send: `
Subject: Invoice {{invoiceNumber}} from {{companyName}}

Hi {{customerName}},

Please find your invoice {{invoiceNumber}} for {{currency}} {{total}}.

{{#each items}}
- {{description}}: {{currency}} {{total}}
{{/each}}

Subtotal: {{currency}} {{subtotal}}
{{#if tax}}Tax ({{taxRate}}%): {{currency}} {{tax}}{{/if}}
Total: {{currency}} {{total}}

Due date: {{dueDate}}

{{#if paymentLink}}
Pay online: {{paymentLink}}
{{/if}}

Thank you for your business!
{{companyName}}
  `.trim(),

  payment_received: `
Subject: Payment received — Thank you!

Hi {{customerName}},

We've received your payment of {{currency}} {{amount}} for invoice {{invoiceNumber}}.

Thank you for your prompt payment!

Best,
{{companyName}}
  `.trim(),

  payment_overdue: `
Subject: Reminder: Invoice {{invoiceNumber}} is overdue

Hi {{customerName}},

This is a friendly reminder that invoice {{invoiceNumber}} for {{currency}} {{total}} was due on {{dueDate}}.

{{#if paymentLink}}
You can pay online: {{paymentLink}}
{{/if}}

If you've already sent payment, please disregard this message.

Best,
{{companyName}}
  `.trim(),

  welcome: `
Subject: Welcome to {{companyName}}!

Hi {{customerName}},

Welcome aboard! We're excited to have you.

Here's what to do next:
{{#each onboardingSteps}}
{{@index}}. {{this}}
{{/each}}

If you have any questions, reply to this email.

Best,
{{companyName}}
  `.trim(),

  follow_up: `
Subject: Following up — {{subject}}

Hi {{leadName}},

{{body}}

Would love to hear your thoughts. 
Feel free to reply or book a call: {{calendarLink}}

Best,
{{senderName}}
  `.trim(),

  support_reply: `
Subject: Re: {{ticketSubject}} [#{{ticketId}}]

Hi {{customerName}},

{{body}}

{{#if resolved}}
This ticket has been marked as resolved. If you need further help, just reply.
{{else}}
We'll keep you updated on the progress.
{{/if}}

Best,
{{companyName}} Support
  `.trim(),
};

export class EmailTemplateEngine {
  private compiled: Map<string, HandlebarsTemplateDelegate> = new Map();

  constructor() {
    for (const [name, source] of Object.entries(TEMPLATES)) {
      this.compiled.set(name, Handlebars.compile(source));
    }
  }

  /** Render template with data */
  render(templateName: string, data: Record<string, unknown>): { subject: string; body: string } {
    const template = this.compiled.get(templateName);
    if (!template) {
      throw new Error(`Email template "${templateName}" not found`);
    }
    const rendered = template(data);
    // Extract subject from first line (format: "Subject: xxx")
    const lines = rendered.split('\n');
    const subjectLine = lines[0]?.startsWith('Subject:') ? lines[0].slice(9).trim() : templateName;
    const body = lines.slice(lines[0]?.startsWith('Subject:') ? 2 : 0).join('\n').trim();
    return { subject: subjectLine, body };
  }

  /** Register custom template */
  registerTemplate(name: string, source: string): void {
    this.compiled.set(name, Handlebars.compile(source));
  }

  /** List available templates */
  listTemplates(): string[] {
    return Array.from(this.compiled.keys());
  }
}
```

### 4.5 src/integrations/calendar/google.ts
```typescript
/**
 * Google Calendar integration.
 * 
 * Features:
 * - List upcoming events
 * - Create events (meetings, deadlines, follow-ups)
 * - Find free slots for scheduling
 * - Set reminders
 *
 * Auth: OAuth2 via googleapis. Token stored in ~/.mekong/credentials.json
 * Security: Level 1 (read), Level 2 (create/modify)
 */

import { google, type calendar_v3 } from 'googleapis';
import type { Integration, IntegrationCredentials } from '../types.js';
import type { Result } from '../../types/common.js';

export interface CalendarEvent {
  summary: string;
  description?: string;
  startTime: string;               // ISO datetime
  endTime: string;                 // ISO datetime
  attendees?: string[];            // email addresses
  location?: string;
  reminders?: Array<{ method: 'email' | 'popup'; minutes: number }>;
}

export class GoogleCalendarIntegration implements Integration {
  name = 'google_calendar';
  connected = false;
  private calendar: calendar_v3.Calendar | null = null;

  async connect(credentials: IntegrationCredentials): Promise<Result<void>> {
    // OAuth2 setup with googleapis
    throw new Error('Not implemented');
  }

  async disconnect(): Promise<void> { this.calendar = null; this.connected = false; }
  async healthCheck(): Promise<boolean> { return this.connected && this.calendar !== null; }

  /** List events in date range */
  async listEvents(from: string, to: string): Promise<Result<CalendarEvent[]>> {
    throw new Error('Not implemented');
  }

  /** Create a new event */
  async createEvent(event: CalendarEvent): Promise<Result<string>> {
    // Returns event ID
    throw new Error('Not implemented');
  }

  /** Find free slots between two dates */
  async findFreeSlots(from: string, to: string, durationMinutes: number): Promise<Result<Array<{ start: string; end: string }>>> {
    throw new Error('Not implemented');
  }

  /** Get today's agenda */
  async todayAgenda(): Promise<Result<CalendarEvent[]>> {
    const now = new Date();
    const endOfDay = new Date(now);
    endOfDay.setHours(23, 59, 59);
    return this.listEvents(now.toISOString(), endOfDay.toISOString());
  }
}
```

### 4.6 src/integrations/notifications/dispatcher.ts
```typescript
/**
 * Multi-channel notification dispatcher.
 * Routes notifications to Slack, Telegram, Email based on config.
 *
 * Priority routing:
 * - critical → all channels simultaneously
 * - high → primary channel + email
 * - normal → primary channel only
 * - low → batch and send in daily digest
 *
 * Usage:
 *   const dispatcher = new NotificationDispatcher(config, integrations);
 *   await dispatcher.send({
 *     channel: 'slack',
 *     to: '#general',
 *     message: 'Deploy complete!',
 *     priority: 'normal',
 *   });
 */

import type { NotificationPayload } from '../types.js';
import type { IntegrationRegistry } from '../index.js';
import type { Result } from '../../types/common.js';

export class NotificationDispatcher {
  private queue: NotificationPayload[] = [];       // for batching low-priority
  private primaryChannel: string = 'slack';

  constructor(
    private integrations: IntegrationRegistry,
    private config: { primaryChannel: string; batchInterval: number }
  ) {
    this.primaryChannel = config.primaryChannel;
  }

  /** Send notification with priority-based routing */
  async send(payload: NotificationPayload): Promise<Result<void>> {
    // critical → send to ALL connected channels
    // high → primary + email
    // normal → primary only
    // low → add to queue, batch send later
    throw new Error('Not implemented');
  }

  /** Flush low-priority queue (called by scheduler) */
  async flushQueue(): Promise<void> {
    // Combine all queued messages into one digest
    // Send via primary channel
    throw new Error('Not implemented');
  }

  /** Send to specific channel */
  private async sendToChannel(channel: string, payload: NotificationPayload): Promise<Result<void>> {
    throw new Error('Not implemented');
  }
}
```

---

## 5. CRM MODULES

### 5.1 src/crm/store.ts
```typescript
/**
 * CRM data persistence — JSON files in ~/.mekong/crm/
 * 
 * File structure:
 *   ~/.mekong/crm/
 *     leads.json       — all leads
 *     customers.json   — all customers
 *     tickets.json     — all support tickets
 *     pipeline.json    — pipeline stage config
 *
 * Design decisions:
 * - JSON files (not SQLite) for simplicity and git-friendliness
 * - Atomic writes (write to temp, rename) to prevent corruption
 * - Auto-backup before destructive operations
 * - Max 10,000 records per file (sufficient for solo company)
 */

import type { Lead, Customer, Ticket } from './types.js';
import type { Result } from '../types/common.js';

export class CrmStore {
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;  // ~/.mekong/crm/
  }

  // --- LEADS ---
  async getLeads(filter?: Partial<Pick<Lead, 'status' | 'source'>>): Promise<Lead[]> { throw new Error('Not implemented'); }
  async getLead(id: string): Promise<Lead | null> { throw new Error('Not implemented'); }
  async saveLead(lead: Lead): Promise<Result<Lead>> { throw new Error('Not implemented'); }
  async updateLead(id: string, updates: Partial<Lead>): Promise<Result<Lead>> { throw new Error('Not implemented'); }
  async deleteLead(id: string): Promise<Result<void>> { throw new Error('Not implemented'); }

  // --- CUSTOMERS ---
  async getCustomers(filter?: Partial<Pick<Customer, 'status' | 'plan'>>): Promise<Customer[]> { throw new Error('Not implemented'); }
  async getCustomer(id: string): Promise<Customer | null> { throw new Error('Not implemented'); }
  async saveCustomer(customer: Customer): Promise<Result<Customer>> { throw new Error('Not implemented'); }
  async updateCustomer(id: string, updates: Partial<Customer>): Promise<Result<Customer>> { throw new Error('Not implemented'); }

  // --- TICKETS ---
  async getTickets(filter?: Partial<Pick<Ticket, 'status' | 'priority' | 'customerId'>>): Promise<Ticket[]> { throw new Error('Not implemented'); }
  async getTicket(id: string): Promise<Ticket | null> { throw new Error('Not implemented'); }
  async saveTicket(ticket: Ticket): Promise<Result<Ticket>> { throw new Error('Not implemented'); }
  async updateTicket(id: string, updates: Partial<Ticket>): Promise<Result<Ticket>> { throw new Error('Not implemented'); }

  // --- GENERIC ---
  /** Atomic write: write to .tmp, then rename */
  private async atomicWrite(filename: string, data: unknown): Promise<void> { throw new Error('Not implemented'); }
  /** Backup file before destructive operation */
  private async backup(filename: string): Promise<void> { throw new Error('Not implemented'); }
}
```

### 5.2 src/crm/leads.ts
```typescript
/**
 * Lead Management — track potential customers from first contact to conversion.
 *
 * Features:
 * - Add leads from multiple sources (manual, webhook, email parse)
 * - Auto-score leads based on engagement signals
 * - Move leads through pipeline stages
 * - Schedule follow-ups (integrates with calendar)
 * - Convert lead → customer when deal closes
 *
 * AI capabilities:
 * - Qualify leads using LLM (analyze email/message for intent signals)
 * - Generate personalized follow-up messages
 * - Predict conversion probability
 */

import type { Lead, PipelineStage } from './types.js';
import type { CrmStore } from './store.js';
import type { LlmRouter } from '../llm/router.js';
import type { Result } from '../types/common.js';

export class LeadManager {
  constructor(
    private store: CrmStore,
    private llm: LlmRouter,
  ) {}

  /** Create new lead */
  async create(input: {
    name: string;
    email: string;
    company?: string;
    source: Lead['source'];
    notes?: string;
    estimatedValue?: number;
  }): Promise<Result<Lead>> {
    // Generate ID, set defaults, validate, save
    throw new Error('Not implemented');
  }

  /** AI-powered lead qualification */
  async qualify(leadId: string): Promise<Result<{ score: number; reasoning: string; suggestedAction: string }>> {
    // 1. Get lead data + all notes/interactions
    // 2. Call LLM: "Score this lead 0-100, explain why, suggest next action"
    // 3. Update lead score
    // 4. Return analysis
    throw new Error('Not implemented');
  }

  /** Move lead to next pipeline stage */
  async advanceStage(leadId: string, newStatus: Lead['status'], note?: string): Promise<Result<Lead>> {
    throw new Error('Not implemented');
  }

  /** Convert lead to customer */
  async convert(leadId: string, plan: string): Promise<Result<{ leadId: string; customerId: string }>> {
    // 1. Get lead data
    // 2. Create customer from lead
    // 3. Update lead status to 'won'
    // 4. Return both IDs
    throw new Error('Not implemented');
  }

  /** Generate AI follow-up message */
  async generateFollowUp(leadId: string, context?: string): Promise<Result<{ subject: string; body: string }>> {
    // Call LLM with lead history, generate personalized follow-up
    throw new Error('Not implemented');
  }

  /** Get leads needing follow-up today */
  async getDueFollowUps(): Promise<Lead[]> {
    throw new Error('Not implemented');
  }

  /** Get pipeline overview */
  async getPipeline(): Promise<PipelineStage[]> {
    throw new Error('Not implemented');
  }
}
```

### 5.3 src/crm/support.ts
```typescript
/**
 * Support Ticket System — handle customer issues.
 *
 * Features:
 * - Create tickets from email, CLI, or webhook
 * - AI-powered triage: auto-categorize + set priority
 * - AI-assisted responses: draft replies based on knowledge base
 * - SLA tracking: warn before deadline
 * - Auto-resolve: close tickets after customer confirmation
 *
 * SLA defaults (configurable):
 * - P0 (critical): respond in 1 hour
 * - P1 (high): respond in 4 hours
 * - P2 (normal): respond in 24 hours
 * - P3 (low): respond in 72 hours
 */

import type { Ticket, Customer } from './types.js';
import type { CrmStore } from './store.js';
import type { LlmRouter } from '../llm/router.js';
import type { Result } from '../types/common.js';

export class SupportManager {
  private slaHours: Record<string, number> = {
    critical: 1,
    high: 4,
    normal: 24,
    low: 72,
  };

  constructor(
    private store: CrmStore,
    private llm: LlmRouter,
  ) {}

  /** Create ticket with AI triage */
  async create(input: {
    customerId: string;
    subject: string;
    description: string;
  }): Promise<Result<Ticket>> {
    // 1. Create ticket
    // 2. AI triage: determine category + priority
    // 3. Set SLA deadline based on priority
    // 4. Save and return
    throw new Error('Not implemented');
  }

  /** AI triage — auto-categorize and set priority */
  async triage(ticketId: string): Promise<Result<{ category: Ticket['category']; priority: Ticket['priority']; reasoning: string }>> {
    // Call LLM with ticket subject + description
    // Determine category (bug, feature_request, question, billing, other)
    // Determine priority based on urgency signals
    throw new Error('Not implemented');
  }

  /** AI-assisted reply draft */
  async draftReply(ticketId: string, instructions?: string): Promise<Result<string>> {
    // 1. Get ticket + all messages
    // 2. Get customer context
    // 3. Call LLM: generate helpful, empathetic reply
    // 4. Return draft (user reviews before sending)
    throw new Error('Not implemented');
  }

  /** Add message to ticket */
  async addMessage(ticketId: string, from: 'customer' | 'agent', content: string): Promise<Result<Ticket>> {
    throw new Error('Not implemented');
  }

  /** Resolve ticket */
  async resolve(ticketId: string, resolution: string): Promise<Result<Ticket>> {
    throw new Error('Not implemented');
  }

  /** Get tickets approaching SLA deadline */
  async getSlaAtRisk(): Promise<Ticket[]> {
    // Tickets where (now + 1 hour) > slaDeadline and status not resolved/closed
    throw new Error('Not implemented');
  }

  /** Get support summary stats */
  async getSummary(): Promise<{
    open: number;
    inProgress: number;
    waitingCustomer: number;
    resolvedThisWeek: number;
    avgResolutionHours: number;
    slaCompliancePercent: number;
  }> {
    throw new Error('Not implemented');
  }
}
```

---

## 6. FINANCE MODULES

### 6.1 src/finance/store.ts
```typescript
/**
 * Finance data persistence — JSON files in ~/.mekong/finance/
 * 
 * Files:
 *   invoices.json, expenses.json, revenue.json, settings.json
 *
 * Same atomic write pattern as CRM store.
 */

import type { Invoice, Expense, RevenueEntry } from './types.js';
import type { Result } from '../types/common.js';

export class FinanceStore {
  constructor(private basePath: string) {}

  // --- INVOICES ---
  async getInvoices(filter?: { status?: Invoice['status']; customerId?: string }): Promise<Invoice[]> { throw new Error('Not implemented'); }
  async getInvoice(id: string): Promise<Invoice | null> { throw new Error('Not implemented'); }
  async saveInvoice(invoice: Invoice): Promise<Result<Invoice>> { throw new Error('Not implemented'); }
  async updateInvoice(id: string, updates: Partial<Invoice>): Promise<Result<Invoice>> { throw new Error('Not implemented'); }

  // --- EXPENSES ---
  async getExpenses(filter?: { category?: Expense['category']; from?: string; to?: string }): Promise<Expense[]> { throw new Error('Not implemented'); }
  async saveExpense(expense: Expense): Promise<Result<Expense>> { throw new Error('Not implemented'); }

  // --- REVENUE ---
  async getRevenue(filter?: { from?: string; to?: string; type?: RevenueEntry['type'] }): Promise<RevenueEntry[]> { throw new Error('Not implemented'); }
  async saveRevenue(entry: RevenueEntry): Promise<Result<RevenueEntry>> { throw new Error('Not implemented'); }

  // --- HELPERS ---
  /** Generate next invoice number: INV-2026-001 */
  async nextInvoiceNumber(): Promise<string> { throw new Error('Not implemented'); }

  private async atomicWrite(filename: string, data: unknown): Promise<void> { throw new Error('Not implemented'); }
}
```

### 6.2 src/finance/invoicing.ts
```typescript
/**
 * Invoice Management — create, send, track invoices.
 *
 * Flow:
 * 1. Create invoice (draft)
 * 2. Review (user approves)
 * 3. Send via Stripe and/or Email
 * 4. Track payment status
 * 5. Send reminders for overdue
 * 6. Record revenue when paid
 *
 * Integrates with: Stripe (payment), Email (delivery), CRM (customer data)
 */

import type { Invoice } from './types.js';
import type { FinanceStore } from './store.js';
import type { StripeIntegration } from '../integrations/stripe/client.js';
import type { EmailIntegration } from '../integrations/email/sender.js';
import type { CrmStore } from '../crm/store.js';
import type { Result } from '../types/common.js';

export class InvoiceManager {
  constructor(
    private store: FinanceStore,
    private crm: CrmStore,
    private stripe?: StripeIntegration,
    private email?: EmailIntegration,
  ) {}

  /** Create invoice draft */
  async create(input: {
    customerId: string;
    items: Array<{ description: string; quantity: number; unitPrice: number }>;
    dueDate: string;
    notes?: string;
    taxRate?: number;
  }): Promise<Result<Invoice>> {
    // 1. Get customer data from CRM
    // 2. Calculate subtotal, tax, total
    // 3. Generate invoice number
    // 4. Save as draft
    throw new Error('Not implemented');
  }

  /** Send invoice — via Stripe (preferred) or Email (fallback) */
  async send(invoiceId: string): Promise<Result<void>> {
    // 1. Get invoice
    // 2. If Stripe connected: create Stripe invoice + send
    // 3. If email connected: render template + send
    // 4. Update status to 'sent'
    throw new Error('Not implemented');
  }

  /** Check and update payment status from Stripe */
  async syncPaymentStatus(invoiceId: string): Promise<Result<Invoice['status']>> {
    throw new Error('Not implemented');
  }

  /** Send overdue reminders */
  async sendOverdueReminders(): Promise<Result<{ sent: number; failed: number }>> {
    // Get all invoices where status=sent and dueDate < now
    // Send reminder email for each
    throw new Error('Not implemented');
  }

  /** Get invoicing summary */
  async getSummary(period: { from: string; to: string }): Promise<{
    sent: number;
    paid: number;
    overdue: number;
    totalBilled: number;
    totalCollected: number;
    totalOutstanding: number;
  }> {
    throw new Error('Not implemented');
  }
}
```

### 6.3 src/finance/revenue.ts
```typescript
/**
 * Revenue Tracking — MRR, ARR, growth, and unit economics.
 *
 * Tracks:
 * - Subscription revenue (MRR)
 * - One-time revenue (template sales, consulting)
 * - Revenue by customer, by type, by period
 * - MRR growth rate
 * - ARPU (Average Revenue Per User)
 * - LTV estimate (ARPU / churn rate)
 *
 * Data sources: Stripe (auto-sync), manual entries
 */

import type { RevenueEntry, FinancialSummary } from './types.js';
import type { FinanceStore } from './store.js';
import type { CrmStore } from '../crm/store.js';
import type { Result } from '../types/common.js';

export class RevenueTracker {
  constructor(
    private financeStore: FinanceStore,
    private crmStore: CrmStore,
  ) {}

  /** Record revenue entry */
  async record(input: Omit<RevenueEntry, 'id' | 'createdAt'>): Promise<Result<RevenueEntry>> {
    throw new Error('Not implemented');
  }

  /** Calculate MRR from active subscriptions */
  async calculateMrr(): Promise<number> {
    // Sum all active customer MRR values from CRM
    throw new Error('Not implemented');
  }

  /** Calculate full financial summary for a period */
  async generateSummary(period: { from: string; to: string }): Promise<FinancialSummary> {
    // 1. Get all revenue in period
    // 2. Get all expenses in period
    // 3. Get customer data from CRM
    // 4. Get AI costs from budget tracker
    // 5. Calculate all metrics
    throw new Error('Not implemented');
  }

  /** Calculate runway (months of cash at current burn rate) */
  async calculateRunway(cashOnHand: number): Promise<{ months: number; burnRate: number }> {
    throw new Error('Not implemented');
  }
}
```

### 6.4 src/finance/reports.ts
```typescript
/**
 * Financial Report Generator — monthly close, P&L, summaries.
 *
 * Output formats:
 * - CLI table (for `mekong finance report`)
 * - Markdown (for saving/sharing)
 * - JSON (for programmatic use)
 *
 * Reports:
 * - Monthly Close: revenue, expenses, profit, key metrics
 * - P&L Summary: revenue breakdown, expense breakdown, margins
 * - AI Cost Report: token usage, cost by provider, % of revenue
 * - Runway Report: cash position, burn rate, months left
 */

import type { MonthlyCloseReport, FinancialSummary } from './types.js';
import type { RevenueTracker } from './revenue.js';
import type { FinanceStore } from './store.js';
import type { Result } from '../types/common.js';

export class FinancialReporter {
  constructor(
    private revenueTracker: RevenueTracker,
    private store: FinanceStore,
  ) {}

  /** Generate monthly close report */
  async monthlyClose(month: string): Promise<Result<MonthlyCloseReport>> {
    // month format: YYYY-MM
    throw new Error('Not implemented');
  }

  /** Render report as CLI table */
  renderCliTable(summary: FinancialSummary): string {
    // Use markdown-table to render
    throw new Error('Not implemented');
  }

  /** Render report as Markdown */
  renderMarkdown(report: MonthlyCloseReport): string {
    throw new Error('Not implemented');
  }

  /** Export report as CSV */
  async exportCsv(period: { from: string; to: string }, outputPath: string): Promise<Result<string>> {
    throw new Error('Not implemented');
  }
}
```

---

## 7. DASHBOARD MODULES

### 7.1 src/dashboard/daily-standup.ts
```typescript
/**
 * Auto-generated Daily Standup Report.
 *
 * Runs every morning (configured time) via heartbeat scheduler.
 * Collects data from all modules:
 * - SOP runs from yesterday
 * - Git commits
 * - Tickets resolved
 * - Invoices sent/paid
 * - Revenue collected
 * - Today's calendar events
 * - Follow-ups due today
 * - Upcoming deadlines
 *
 * Output: CLI display + optional Slack/email notification
 */

import type { DailyStandup } from './types.js';
import type { CrmStore } from '../crm/store.js';
import type { FinanceStore } from '../finance/store.js';
import type { Result } from '../types/common.js';

export class DailyStandupGenerator {
  constructor(
    private crmStore: CrmStore,
    private financeStore: FinanceStore,
    private sopMetricsPath: string,
  ) {}

  /** Generate today's standup report */
  async generate(): Promise<Result<DailyStandup>> {
    // 1. Query yesterday's activity across all modules
    // 2. Query today's scheduled items
    // 3. Identify blockers (overdue invoices, SLA-at-risk tickets, etc)
    // 4. Calculate quick metrics
    // 5. Return structured report
    throw new Error('Not implemented');
  }

  /** Render standup as CLI output */
  renderCli(standup: DailyStandup): string {
    // Render with chalk colors:
    //   Green: completed items
    //   Yellow: pending items
    //   Red: blockers/overdue
    throw new Error('Not implemented');
  }
}
```

### 7.2 src/dashboard/weekly-digest.ts
```typescript
/**
 * Weekly Business Digest — comprehensive weekly summary.
 *
 * Generated every Sunday evening (configurable).
 * Includes AI-powered insights and recommendations.
 *
 * Sections:
 * 1. Financial overview (revenue, expenses, profit, MRR trend)
 * 2. CRM overview (leads, customers, tickets)
 * 3. Operations (SOP runs, agent performance)
 * 4. Week-over-week comparison
 * 5. AI insights: "Here's what stood out this week..."
 * 6. AI recommendations: "Consider doing X next week..."
 */

import type { WeeklyDigest } from './types.js';
import type { RevenueTracker } from '../finance/revenue.js';
import type { CrmStore } from '../crm/store.js';
import type { LlmRouter } from '../llm/router.js';
import type { Result } from '../types/common.js';

export class WeeklyDigestGenerator {
  constructor(
    private revenueTracker: RevenueTracker,
    private crmStore: CrmStore,
    private llm: LlmRouter,
    private sopMetricsPath: string,
  ) {}

  /** Generate this week's digest */
  async generate(): Promise<Result<WeeklyDigest>> {
    // 1. Calculate period (Monday to Sunday)
    // 2. Get financial summary for period
    // 3. Get CRM summary
    // 4. Get SOP metrics
    // 5. Get last week's digest for comparison
    // 6. Call LLM for highlights + recommendations
    // 7. Return complete digest
    throw new Error('Not implemented');
  }

  /** Generate AI insights from weekly data */
  private async generateInsights(digest: Partial<WeeklyDigest>): Promise<{ highlights: string[]; recommendations: string[] }> {
    // Prompt LLM with all weekly data
    // Ask for 3-5 key highlights and 2-3 actionable recommendations
    throw new Error('Not implemented');
  }

  /** Render as Markdown report */
  renderMarkdown(digest: WeeklyDigest): string {
    throw new Error('Not implemented');
  }

  /** Render as CLI output */
  renderCli(digest: WeeklyDigest): string {
    throw new Error('Not implemented');
  }
}
```

### 7.3 src/dashboard/renderer.ts
```typescript
/**
 * Andon Board CLI Renderer — visual dashboard for terminal.
 *
 * Shows overall system health at a glance:
 * 
 *   ┌─ MEKONG STATUS ──────────────────────────┐
 *   │  Status: 🟢 GREEN                         │
 *   │                                            │
 *   │  MRR: $4,200   Customers: 28              │
 *   │  Open Tickets: 3   Today Revenue: $150    │
 *   │  AI Budget: $2.40 / $5.00 (48%)           │
 *   │  Next Deadline: Invoice #42 due tomorrow   │
 *   │                                            │
 *   │  Alerts:                                   │
 *   │  ⚠️  2 invoices overdue                    │
 *   │  ⚠️  Ticket #15 SLA expires in 2 hours    │
 *   │                                            │
 *   │  Recent:                                   │
 *   │  14:30 SOP deploy completed (staging)      │
 *   │  14:15 Ticket #18 resolved                 │
 *   │  13:00 Invoice INV-2026-042 sent           │
 *   └───────────────────────────────────────────┘
 *
 * Colors: Green (all OK), Yellow (warnings), Red (critical alerts)
 */

import type { AndonBoard } from './types.js';
import chalk from 'chalk';

export class DashboardRenderer {
  /** Build AndonBoard data from all modules */
  async buildBoard(deps: {
    crmStore: any;
    financeStore: any;
    budgetTracker: any;
    sopMetrics: any;
  }): Promise<AndonBoard> {
    throw new Error('Not implemented');
  }

  /** Render AndonBoard to terminal string */
  render(board: AndonBoard): string {
    const statusColor = board.status === 'green' ? chalk.green
      : board.status === 'yellow' ? chalk.yellow
      : chalk.red;

    const statusEmoji = board.status === 'green' ? '🟢'
      : board.status === 'yellow' ? '🟡'
      : '🔴';

    let output = '';
    output += chalk.bold(`\n  MEKONG STATUS  ${statusColor(`${statusEmoji} ${board.status.toUpperCase()}`)}\n\n`);

    // Quick stats
    const s = board.quickStats;
    output += `  MRR: ${chalk.green(s.mrr)}   Customers: ${s.customers}\n`;
    output += `  Open Tickets: ${s.openTickets}   Today Revenue: ${chalk.green(s.todayRevenue)}\n`;
    output += `  AI Budget: ${s.agentBudgetUsed}\n`;
    output += `  Next Deadline: ${s.nextDeadline}\n\n`;

    // Alerts
    if (board.alerts.length > 0) {
      output += chalk.bold('  Alerts:\n');
      for (const alert of board.alerts) {
        const icon = alert.level === 'critical' ? chalk.red('🔴')
          : alert.level === 'warning' ? chalk.yellow('⚠️')
          : chalk.blue('ℹ️');
        output += `  ${icon}  ${alert.message}\n`;
      }
      output += '\n';
    }

    // Recent activity
    if (board.recentActivity.length > 0) {
      output += chalk.bold('  Recent:\n');
      for (const activity of board.recentActivity.slice(0, 5)) {
        output += chalk.dim(`  ${activity.timestamp}`) + ` ${activity.action}\n`;
      }
    }

    return output;
  }
}
```

---

## 8. NEW AGENT DEFINITIONS

### 8.1 src/agents/definitions/finance-agent.yaml
```yaml
agent:
  name: finance
  role: "CFO / Financial Controller"
  goal: "Manage invoicing, expense tracking, revenue analysis, and financial reporting"
  backstory: "Meticulous financial manager with experience in startup finance and SaaS metrics"
  tools:
    - file_ops
    - http_client
    - shell
    - ask_user
  constraints:
    max_iterations: 8
    max_tokens_per_turn: 4096
    require_tests: false
    sandbox: true
  model:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.2
  memory:
    type: persistent
    max_context: 50000
```

### 8.2 src/agents/definitions/sales-agent.yaml
```yaml
agent:
  name: sales
  role: "Sales & Business Development"
  goal: "Qualify leads, manage pipeline, generate follow-ups, close deals"
  backstory: "Experienced SaaS sales professional who understands developer tools market"
  tools:
    - file_ops
    - http_client
    - ask_user
  constraints:
    max_iterations: 6
    max_tokens_per_turn: 2048
    require_tests: false
    sandbox: true
  model:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.5
  memory:
    type: persistent
    max_context: 50000
```

### 8.3 src/agents/definitions/support-agent.yaml
```yaml
agent:
  name: support
  role: "Customer Support Specialist"
  goal: "Triage tickets, draft helpful replies, resolve customer issues quickly"
  backstory: "Empathetic support specialist with deep product knowledge"
  tools:
    - file_ops
    - http_client
    - ask_user
  constraints:
    max_iterations: 5
    max_tokens_per_turn: 2048
    require_tests: false
    sandbox: true
  model:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.4
  memory:
    type: persistent
    max_context: 30000
```

### 8.4 src/agents/definitions/scheduler-agent.yaml
```yaml
agent:
  name: scheduler
  role: "Operations Scheduler & Daily Planner"
  goal: "Generate daily standups, weekly digests, and manage heartbeat tasks"
  backstory: "Organized operations manager who keeps the solo founder on track"
  tools:
    - file_ops
    - shell
  constraints:
    max_iterations: 5
    max_tokens_per_turn: 4096
    require_tests: false
    sandbox: true
  model:
    provider: deepseek
    model: deepseek-chat
    temperature: 0.3
  memory:
    type: session
    max_context: 30000
```

---

## 9. NEW SOP TEMPLATES (10 templates)

### 9.1 templates/invoice-send.yaml
```yaml
sop:
  name: "Send Invoice"
  version: "1.0.0"
  category: finance
  estimated_time: "2min"
  inputs:
    - name: customer_id
      type: string
      required: true
    - name: items
      type: string
      required: true
      description: "JSON array of {description, quantity, unitPrice}"
    - name: due_days
      type: number
      default: 30
  steps:
    - id: create
      name: "Create invoice"
      agent: finance
      action: llm
      config:
        prompt: |
          Create an invoice for customer {customer_id}.
          Items: {items}
          Due in {due_days} days from today.
          Use the InvoiceManager.create() method.
    - id: review
      name: "Review invoice"
      action: prompt
      config:
        message: "Review invoice above. Send? (y/n)"
      depends_on: [create]
    - id: send
      name: "Send invoice"
      agent: finance
      action: llm
      config:
        prompt: "Send the invoice using InvoiceManager.send()"
      depends_on: [review]
      requires_approval: "true"
    - id: notify
      name: "Log and notify"
      agent: ops
      action: shell
      command: "echo 'Invoice sent to customer {customer_id}'"
      depends_on: [send]
```

### 9.2 templates/expense-log.yaml
```yaml
sop:
  name: "Log Expense"
  version: "1.0.0"
  category: finance
  estimated_time: "1min"
  inputs:
    - name: description
      type: string
      required: true
    - name: amount
      type: number
      required: true
    - name: category
      type: enum
      options: [infrastructure, tools, ai_api, marketing, legal, office, travel, contractor, other]
      required: true
    - name: vendor
      type: string
      required: true
  steps:
    - id: log
      name: "Record expense"
      agent: finance
      action: llm
      config:
        prompt: |
          Log expense: {description}
          Amount: ${amount}
          Category: {category}
          Vendor: {vendor}
          Save using FinanceStore.saveExpense()
    - id: confirm
      name: "Confirm saved"
      action: shell
      command: "echo 'Expense logged: {description} - ${amount}'"
      depends_on: [log]
```

### 9.3 templates/monthly-close.yaml
```yaml
sop:
  name: "Monthly Financial Close"
  version: "1.0.0"
  category: finance
  estimated_time: "10min"
  inputs:
    - name: month
      type: string
      required: true
      description: "Format: YYYY-MM"
  steps:
    - id: sync_payments
      name: "Sync payment status from Stripe"
      agent: finance
      action: llm
      config:
        prompt: "Sync all invoice payment statuses from Stripe for {month}"
    - id: check_overdue
      name: "Identify overdue invoices"
      agent: finance
      action: llm
      config:
        prompt: "List all overdue invoices for {month}. Send reminders if needed."
      depends_on: [sync_payments]
    - id: calculate
      name: "Calculate monthly figures"
      agent: finance
      action: llm
      config:
        prompt: |
          Generate monthly close report for {month}:
          - Total revenue, expenses, profit
          - MRR, MRR growth
          - Top expense categories
          - AI cost as % of revenue
      depends_on: [check_overdue]
    - id: report
      name: "Generate and save report"
      agent: finance
      action: llm
      config:
        prompt: "Save monthly close report as Markdown to ./reports/{month}-close.md"
      depends_on: [calculate]
    - id: review
      name: "Owner review"
      action: prompt
      config:
        message: "Monthly close for {month} complete. Review report above."
      depends_on: [report]
```

### 9.4 templates/lead-qualify.yaml
```yaml
sop:
  name: "Qualify Lead"
  version: "1.0.0"
  category: sales
  estimated_time: "3min"
  inputs:
    - name: lead_id
      type: string
      required: true
  steps:
    - id: gather
      name: "Gather lead info"
      agent: sales
      action: llm
      config:
        prompt: "Get all data for lead {lead_id} from CRM"
    - id: qualify
      name: "AI qualification"
      agent: sales
      action: llm
      config:
        prompt: |
          Score this lead 0-100 based on:
          - Company size/type fit
          - Budget signals
          - Timeline urgency
          - Technical fit
          Explain your reasoning. Suggest next action.
        input_from: "step.gather.output"
      depends_on: [gather]
    - id: update
      name: "Update lead score"
      agent: sales
      action: llm
      config:
        prompt: "Update lead {lead_id} with new score and notes from qualification"
      depends_on: [qualify]
    - id: action
      name: "Execute next action"
      agent: sales
      action: llm
      config:
        prompt: |
          Based on qualification: {step.qualify.output}
          If score > 70: Draft follow-up email and schedule call
          If score 40-70: Add to nurture sequence
          If score < 40: Mark as low priority
      depends_on: [update]
```

### 9.5 templates/customer-onboard.yaml
```yaml
sop:
  name: "Customer Onboarding"
  version: "1.0.0"
  category: sales
  estimated_time: "5min"
  inputs:
    - name: customer_id
      type: string
      required: true
    - name: plan
      type: enum
      options: [free, pro, team, enterprise]
      required: true
  steps:
    - id: setup
      name: "Setup customer account"
      agent: ops
      action: llm
      config:
        prompt: "Create account setup for customer {customer_id} on {plan} plan"
    - id: welcome
      name: "Send welcome email"
      agent: sales
      action: llm
      config:
        prompt: |
          Send welcome email to customer {customer_id}.
          Include: getting started steps, documentation links, support info.
          Use 'welcome' email template.
      depends_on: [setup]
    - id: calendar
      name: "Schedule onboarding call"
      agent: scheduler
      action: llm
      config:
        prompt: "Find a free 30-min slot this week and create calendar event for onboarding call with customer {customer_id}"
      depends_on: [welcome]
      condition: "plan != free"
    - id: checklist
      name: "Create onboarding checklist"
      agent: ops
      action: file
      config:
        path: "./onboarding/{customer_id}-checklist.md"
        content_from: "step.setup.output"
      depends_on: [setup]
```

### 9.6 templates/support-triage.yaml
```yaml
sop:
  name: "Support Ticket Triage"
  version: "1.0.0"
  category: support
  estimated_time: "2min"
  inputs:
    - name: ticket_id
      type: string
      required: true
  steps:
    - id: load
      name: "Load ticket"
      agent: support
      action: llm
      config:
        prompt: "Load ticket {ticket_id} with full customer context"
    - id: triage
      name: "AI triage"
      agent: support
      action: llm
      config:
        prompt: |
          Analyze this ticket:
          {step.load.output}
          
          Determine: category, priority, estimated effort.
          If similar ticket resolved before, reference the resolution.
      depends_on: [load]
    - id: draft
      name: "Draft initial reply"
      agent: support
      action: llm
      config:
        prompt: |
          Draft a helpful, empathetic first response.
          Acknowledge the issue, provide immediate help if possible.
          If bug: ask for reproduction steps.
          If question: answer if known, escalate if not.
      depends_on: [triage]
    - id: review
      name: "Review and send"
      action: prompt
      config:
        message: "Review draft reply above. Send to customer? (y/n)"
      depends_on: [draft]
```

### 9.7 templates/weekly-report.yaml
```yaml
sop:
  name: "Weekly Business Report"
  version: "1.0.0"
  category: business
  estimated_time: "5min"
  steps:
    - id: digest
      name: "Generate weekly digest"
      agent: scheduler
      action: llm
      config:
        prompt: "Generate this week's business digest using WeeklyDigestGenerator"
    - id: insights
      name: "AI analysis"
      agent: scheduler
      action: llm
      config:
        prompt: |
          Analyze the weekly data: {step.digest.output}
          
          Provide:
          1. Top 3 highlights (what went well)
          2. Top 3 concerns (what needs attention)
          3. Top 3 recommendations for next week
          Be specific, use numbers.
      depends_on: [digest]
    - id: save
      name: "Save report"
      action: file
      config:
        path: "./reports/weekly-{week}.md"
        content_from: "step.insights.output"
      depends_on: [insights]
    - id: notify
      name: "Send to self"
      agent: ops
      action: llm
      config:
        prompt: "Send weekly digest via primary notification channel"
      depends_on: [save]
```

### 9.8 templates/daily-standup.yaml
```yaml
sop:
  name: "Daily Standup"
  version: "1.0.0"
  category: business
  estimated_time: "1min"
  steps:
    - id: generate
      name: "Generate standup report"
      agent: scheduler
      action: llm
      config:
        prompt: "Generate today's standup using DailyStandupGenerator"
    - id: display
      name: "Display standup"
      action: shell
      command: "echo '{step.generate.output}'"
      depends_on: [generate]
```

### 9.9 templates/email-campaign.yaml
```yaml
sop:
  name: "Email Campaign"
  version: "1.0.0"
  category: marketing
  estimated_time: "15min"
  inputs:
    - name: subject
      type: string
      required: true
    - name: target
      type: enum
      options: [all_customers, active_customers, churned, leads, trial]
      required: true
    - name: goal
      type: string
      required: true
      description: "What should this email achieve?"
  steps:
    - id: audience
      name: "Build recipient list"
      agent: sales
      action: llm
      config:
        prompt: "Get all contacts matching target: {target} from CRM"
    - id: draft
      name: "Draft email"
      agent: sales
      action: llm
      config:
        prompt: |
          Write email campaign:
          Subject: {subject}
          Goal: {goal}
          Audience: {target} ({step.audience.output})
          
          Write compelling, concise email. Include clear CTA.
      depends_on: [audience]
    - id: review
      name: "Review before sending"
      action: prompt
      config:
        message: "Review email draft. Approve to send to all recipients? (y/n)"
      depends_on: [draft]
    - id: send
      name: "Send to all recipients"
      agent: ops
      action: llm
      config:
        prompt: "Send email to all recipients. Use rate limiting (max 20/hour)."
      depends_on: [review]
      requires_approval: "true"
```

### 9.10 templates/payment-followup.yaml
```yaml
sop:
  name: "Payment Follow-up"
  version: "1.0.0"
  category: finance
  estimated_time: "3min"
  steps:
    - id: check
      name: "Find overdue invoices"
      agent: finance
      action: llm
      config:
        prompt: "List all invoices with status 'sent' where dueDate < today"
    - id: categorize
      name: "Categorize by age"
      agent: finance
      action: llm
      config:
        prompt: |
          Categorize overdue invoices:
          - 1-7 days: gentle reminder
          - 8-30 days: firm reminder
          - 30+ days: final notice
          List each with customer name, amount, days overdue.
      depends_on: [check]
    - id: generate
      name: "Generate follow-up emails"
      agent: finance
      action: llm
      config:
        prompt: |
          For each overdue invoice, generate appropriate follow-up email.
          Use templates: payment_overdue for gentle/firm, custom for final notice.
          Show all drafts for review.
      depends_on: [categorize]
    - id: approve
      name: "Review and approve"
      action: prompt
      config:
        message: "Review follow-up emails above. Send all? (y/n/edit)"
      depends_on: [generate]
    - id: send
      name: "Send follow-ups"
      agent: ops
      action: llm
      config:
        prompt: "Send all approved follow-up emails"
      depends_on: [approve]
      requires_approval: "true"
```

---

## 10. CONFIG UPDATES — thêm vào mekong.yaml

```yaml
# THÊM section này vào mekong.yaml (giữ nguyên config v0.1.0)

integrations:
  stripe:
    api_key_env: STRIPE_SECRET_KEY     # env var name
    
  email:
    host: smtp.gmail.com
    port: 587
    user_env: SMTP_USER                 # env var name
    pass_env: SMTP_PASSWORD             # env var name
    secure: false
    from_name: "Your Company"
    from_email_env: SMTP_USER
    
  google_calendar:
    credentials_path: ~/.mekong/google-credentials.json
    
  notifications:
    primary_channel: slack
    slack_webhook_env: SLACK_WEBHOOK_URL
    telegram_bot_token_env: TELEGRAM_BOT_TOKEN
    telegram_chat_id_env: TELEGRAM_CHAT_ID
    batch_interval_minutes: 60

crm:
  data_dir: ~/.mekong/crm
  sla_hours:
    critical: 1
    high: 4
    normal: 24
    low: 72
  lead_scoring:
    auto_qualify: true
    qualify_model: deepseek-chat       # cheaper model for lead scoring

finance:
  data_dir: ~/.mekong/finance
  currency: USD
  tax_rate: 0                          # default tax rate %
  invoice_prefix: INV
  company_name: "Your Company"
  company_email_env: SMTP_USER

dashboard:
  daily_standup:
    enabled: true
    time: "08:00"                       # local time
    notify: true
  weekly_digest:
    enabled: true
    day: sunday
    time: "18:00"
    notify: true

heartbeat:
  enabled: true                         # upgrade from false in v0.1.0
  interval_minutes: 30
  checklist_file: HEARTBEAT.md
  scheduled_sops:                       # NEW: auto-run SOPs on schedule
    - name: daily-standup
      cron: "0 8 * * *"                # 8 AM daily
    - name: payment-followup
      cron: "0 10 * * 1"               # Monday 10 AM
    - name: weekly-report
      cron: "0 18 * * 0"               # Sunday 6 PM
```

---

## 11. NEW CLI COMMANDS

### 11.1 src/cli/commands/crm.ts
```typescript
/**
 * `mekong crm` — Customer Relationship Management commands.
 *
 * Subcommands:
 *   mekong crm lead add <name> <email>           Add new lead
 *   mekong crm lead list [--status=new]           List leads
 *   mekong crm lead qualify <id>                  AI-qualify a lead
 *   mekong crm lead followup <id>                 Generate follow-up
 *   mekong crm customer list [--status=active]    List customers
 *   mekong crm customer onboard <id> <plan>       Run onboarding SOP
 *   mekong crm ticket create <customer_id>        Create support ticket
 *   mekong crm ticket list [--status=open]        List tickets
 *   mekong crm ticket triage <id>                 AI-triage ticket
 *   mekong crm pipeline                           Show sales pipeline
 *   mekong crm summary                            CRM dashboard
 */
```

### 11.2 src/cli/commands/finance.ts
```typescript
/**
 * `mekong finance` — Financial operations commands.
 *
 * Subcommands:
 *   mekong finance invoice create <customer_id>   Create invoice
 *   mekong finance invoice send <id>              Send invoice
 *   mekong finance invoice list [--status=sent]   List invoices
 *   mekong finance expense add                    Log expense (interactive)
 *   mekong finance expense list [--month=YYYY-MM] List expenses
 *   mekong finance revenue                        Revenue summary
 *   mekong finance report [--month=YYYY-MM]       Monthly close report
 *   mekong finance report --weekly                Weekly report
 *   mekong finance runway <cash>                  Calculate runway
 *   mekong finance export <period> <path>         Export CSV
 */
```

### 11.3 src/cli/commands/dashboard.ts
```typescript
/**
 * `mekong dashboard` — Andon Board & reports.
 *
 * Subcommands:
 *   mekong dashboard                              Show Andon board
 *   mekong dashboard standup                      Today's daily standup
 *   mekong dashboard weekly                       This week's digest
 *   mekong dashboard --watch                      Live-updating dashboard
 */
```

### 11.4 Update src/cli/index.ts — add new commands
```typescript
// Add these to existing Commander setup:

import { crmCommand } from './commands/crm.js';
import { financeCommand } from './commands/finance.js';
import { dashboardCommand } from './commands/dashboard.js';

program.addCommand(crmCommand);
program.addCommand(financeCommand);
program.addCommand(dashboardCommand);
```

---

## 12. MODULE IMPLEMENTATION ORDER — v0.2.0

```
LAYER A: New Types (no deps beyond v0.1.0 types)
  ├── src/integrations/types.ts
  ├── src/crm/types.ts
  ├── src/finance/types.ts
  └── src/dashboard/types.ts

LAYER B: Data Stores (depends on types)
  ├── src/crm/store.ts
  └── src/finance/store.ts

LAYER C: Integrations (depends on types + v0.1.0 config)
  ├── src/integrations/index.ts
  ├── src/integrations/stripe/client.ts
  ├── src/integrations/email/sender.ts
  ├── src/integrations/email/templates.ts
  ├── src/integrations/calendar/google.ts
  ├── src/integrations/notifications/slack.ts
  ├── src/integrations/notifications/telegram.ts
  └── src/integrations/notifications/dispatcher.ts

LAYER D: Business Logic (depends on stores + integrations + v0.1.0 llm)
  ├── src/crm/leads.ts
  ├── src/crm/customers.ts
  ├── src/crm/support.ts
  ├── src/crm/pipeline.ts
  ├── src/finance/invoicing.ts
  ├── src/finance/expenses.ts
  ├── src/finance/revenue.ts
  └── src/finance/reports.ts

LAYER E: Dashboard (depends on business logic)
  ├── src/dashboard/daily-standup.ts
  ├── src/dashboard/weekly-digest.ts
  ├── src/dashboard/metrics-aggregator.ts
  └── src/dashboard/renderer.ts

LAYER F: Agent Definitions + SOP Templates (YAML files, no code)
  ├── src/agents/definitions/finance-agent.yaml
  ├── src/agents/definitions/sales-agent.yaml
  ├── src/agents/definitions/support-agent.yaml
  ├── src/agents/definitions/scheduler-agent.yaml
  └── src/sops/templates/*.yaml (10 new templates)

LAYER G: CLI Commands (thin wrappers, depends on everything)
  ├── src/cli/commands/crm.ts
  ├── src/cli/commands/finance.ts
  ├── src/cli/commands/dashboard.ts
  └── src/cli/index.ts (update)

LAYER H: Config Update + Heartbeat Enhancement
  ├── Update src/config/schema.ts (add new config sections)
  ├── Update src/core/scheduler.ts (add scheduled_sops support)
  └── Update mekong.yaml default
```

---

## 13. IMPLEMENTATION NOTES CHO OPUS

1. **Verify v0.1.0 first**: Run `pnpm build && pnpm test`. If fails, fix v0.1.0 first.
2. **Code types FIRST**: Layer A trước tất cả.
3. **Stores trước logic**: CrmStore + FinanceStore phải xong trước Leads/Invoicing.
4. **Integrations có thể stubbed**: Stripe/Email/Calendar connect() có thể return mock data nếu chưa có API key — đừng block trên credentials.
5. **YAML templates chỉ copy**: Không cần code gì, chỉ tạo file.
6. **Test mỗi store**: Viết test cho CrmStore + FinanceStore trước khi code business logic.
7. **Dashboard renderer code cuối cùng**: Vì nó cần data từ tất cả modules.
8. **Cẩn thận config schema update**: Dùng `.extend()` hoặc `.merge()` trong Zod, ĐỪNG replace ConfigSchema cũ.
9. **KHÔNG refactor engine.ts**: Chỉ register thêm modules mới vào existing engine.
10. **Email rate limit là HARD constraint**: 20/hour, KHÔNG cho override — Poka-yoke.
