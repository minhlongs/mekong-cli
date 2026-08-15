/** Support ticket system — triage, SLA tracking, AI-assisted replies */
import { randomUUID } from 'node:crypto';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { LlmRouter } from '../llm/router.js';
import type { Ticket } from './types.js';
import type { CrmStore } from './store.js';

const SLA_HOURS: Record<Ticket['priority'], number> = {
  critical: 1,
  high: 4,
  normal: 24,
  low: 72,
};

export interface TicketSummary {
  open: number;
  inProgress: number;
  waitingCustomer: number;
  resolved: number;
  slaAtRisk: number;
}

export class SupportManager {
  constructor(
    private store: CrmStore,
    private llm: LlmRouter,
  ) {}

  async getById(id: string): Promise<Result<Ticket | null>> {
    return this.store.getById('tickets', id);
  }

  async getAll(filter?: Partial<Ticket>): Promise<Result<Ticket[]>> {
    return this.store.getAll('tickets', filter);
  }

  /** Create ticket and run AI triage to set category + priority */
  async create(input: {
    customerId: string;
    subject: string;
    description: string;
  }): Promise<Result<Ticket>> {
    try {
      const now = new Date().toISOString();
      // Default before triage
      const ticket: Ticket = {
        id: randomUUID(),
        customerId: input.customerId,
        subject: input.subject,
        description: input.description,
        status: 'open',
        priority: 'normal',
        category: 'other',
        messages: [
          { from: 'customer', content: input.description, createdAt: now },
        ],
        createdAt: now,
        updatedAt: now,
      };

      // Run AI triage
      const triaged = await this.triage(ticket);
      const finalTicket = triaged.ok ? triaged.value : ticket;

      // Set SLA deadline
      const slaHours = SLA_HOURS[finalTicket.priority];
      const deadline = new Date(Date.now() + slaHours * 3_600_000).toISOString();
      const withSla: Ticket = { ...finalTicket, slaDeadline: deadline };

      return this.store.save('tickets', withSla);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** AI triage: sets category and priority on a ticket (does not save) */
  async triage(ticket: Ticket): Promise<Result<Ticket>> {
    try {
      const response = await this.llm.chat({
        messages: [
          {
            role: 'user',
            content: `Categorize and prioritize this support ticket.
Subject: ${ticket.subject}
Description: ${ticket.description}
Categories: bug, feature_request, question, billing, other
Priorities: low, normal, high, critical
Respond with JSON only: { "category": string, "priority": string }`,
          },
        ],
        maxTokens: 100,
        temperature: 0.1,
      });

      let category: Ticket['category'] = 'other';
      let priority: Ticket['priority'] = 'normal';
      try {
        const parsed = JSON.parse(response.content) as { category: string; priority: string };
        const validCategories: Ticket['category'][] = ['bug', 'feature_request', 'question', 'billing', 'other'];
        const validPriorities: Ticket['priority'][] = ['low', 'normal', 'high', 'critical'];
        if (validCategories.includes(parsed.category as Ticket['category'])) {
          category = parsed.category as Ticket['category'];
        }
        if (validPriorities.includes(parsed.priority as Ticket['priority'])) {
          priority = parsed.priority as Ticket['priority'];
        }
      } catch {
        // keep defaults
      }

      return ok({ ...ticket, category, priority, updatedAt: new Date().toISOString() });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Draft AI reply for a ticket */
  async draftReply(id: string): Promise<Result<string>> {
    try {
      const res = await this.store.getById('tickets', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Ticket ${id} not found`));
      const ticket = res.value;

      const history = ticket.messages
        .slice(-5)
        .map((m) => `${m.from}: ${m.content}`)
        .join('\n');

      const response = await this.llm.chat({
        messages: [
          {
            role: 'user',
            content: `Draft a support reply for this ticket. Be concise and helpful (max 150 words).
Subject: ${ticket.subject}
Category: ${ticket.category} | Priority: ${ticket.priority}
Recent messages:
${history}
Return only the reply text.`,
          },
        ],
        maxTokens: 300,
        temperature: 0.5,
      });

      return ok(response.content);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Append a message to a ticket */
  async addMessage(
    id: string,
    from: Ticket['messages'][number]['from'],
    content: string,
  ): Promise<Result<Ticket>> {
    try {
      const res = await this.store.getById('tickets', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Ticket ${id} not found`));
      const ticket = res.value;
      const now = new Date().toISOString();
      const updated: Ticket = {
        ...ticket,
        messages: [...ticket.messages, { from, content, createdAt: now }],
        status: from === 'customer' ? 'open' : 'waiting_customer',
        updatedAt: now,
      };
      return this.store.save('tickets', updated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Resolve a ticket with resolution text */
  async resolve(id: string, resolution: string): Promise<Result<Ticket>> {
    try {
      const res = await this.store.getById('tickets', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Ticket ${id} not found`));
      const now = new Date().toISOString();
      const updated: Ticket = {
        ...res.value,
        status: 'resolved',
        resolution,
        resolvedAt: now,
        updatedAt: now,
      };
      return this.store.save('tickets', updated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Tickets approaching (within 20%) or past SLA deadline */
  async getSlaAtRisk(): Promise<Result<Ticket[]>> {
    try {
      const res = await this.store.getAll('tickets');
      if (!res.ok) return res;
      const now = Date.now();
      const atRisk = res.value.filter((t) => {
        if (!t.slaDeadline) return false;
        if (t.status === 'resolved' || t.status === 'closed') return false;
        const deadline = new Date(t.slaDeadline).getTime();
        const totalMs = SLA_HOURS[t.priority] * 3_600_000;
        const remaining = deadline - now;
        return remaining < totalMs * 0.2 || remaining < 0;
      });
      return ok(atRisk);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getSummary(): Promise<Result<TicketSummary>> {
    try {
      const res = await this.store.getAll('tickets');
      if (!res.ok) return res;
      const tickets = res.value;
      const slaRes = await this.getSlaAtRisk();
      const slaAtRisk = slaRes.ok ? slaRes.value.length : 0;
      return ok({
        open: tickets.filter((t) => t.status === 'open').length,
        inProgress: tickets.filter((t) => t.status === 'in_progress').length,
        waitingCustomer: tickets.filter((t) => t.status === 'waiting_customer').length,
        resolved: tickets.filter((t) => t.status === 'resolved' || t.status === 'closed').length,
        slaAtRisk,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
