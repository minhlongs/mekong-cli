/** Support ticket system — triage, SLA tracking, AI-assisted replies */
import { randomUUID } from 'node:crypto';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { LlmRouter } from '../llm/router.js';
import type { Ticket } from './types.js';
import type { CrmStore } from './store.js';

const SLA_HOURS: Record<Ticket['priority'], number> = { critical: 1, high: 4, normal: 24, low: 72 };
const VALID_CATEGORIES: Ticket['category'][] = ['bug', 'feature_request', 'question', 'billing', 'other'];
const VALID_PRIORITIES: Ticket['priority'][] = ['low', 'normal', 'high', 'critical'];

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
  async create(input: { customerId: string; subject: string; description: string }): Promise<Result<Ticket>> {
    try {
      const now = new Date().toISOString();
      const ticket: Ticket = {
        id: randomUUID(), customerId: input.customerId, subject: input.subject,
        description: input.description, status: 'open', priority: 'normal', category: 'other',
        messages: [{ from: 'customer', content: input.description, createdAt: now }],
        createdAt: now, updatedAt: now,
      };

      const triaged = await this.triage(ticket);
      const finalTicket = triaged.ok ? triaged.value : ticket;
      const deadline = new Date(Date.now() + SLA_HOURS[finalTicket.priority] * 3_600_000).toISOString();
      return this.store.save('tickets', { ...finalTicket, slaDeadline: deadline });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** AI triage: sets category and priority on a ticket (does not save) */
  async triage(ticket: Ticket): Promise<Result<Ticket>> {
    try {
      const response = await this.llm.chat({
        messages: [{
          role: 'user',
          content: `Categorize and prioritize this support ticket.\nSubject: ${ticket.subject}\nDescription: ${ticket.description}\nCategories: bug, feature_request, question, billing, other\nPriorities: low, normal, high, critical\nRespond with JSON only: { "category": string, "priority": string }`,
        }],
        maxTokens: 100,
        temperature: 0.1,
      });

      let category: Ticket['category'] = 'other';
      let priority: Ticket['priority'] = 'normal';
      try {
        const parsed = JSON.parse(response.content) as { category: string; priority: string };
        if (VALID_CATEGORIES.includes(parsed.category as Ticket['category'])) category = parsed.category as Ticket['category'];
        if (VALID_PRIORITIES.includes(parsed.priority as Ticket['priority'])) priority = parsed.priority as Ticket['priority'];
      } catch { /* keep defaults */ }

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
      const history = ticket.messages.slice(-5).map((m) => `${m.from}: ${m.content}`).join('\n');

      const response = await this.llm.chat({
        messages: [{
          role: 'user',
          content: `Draft a support reply for this ticket. Be concise and helpful (max 150 words).\nSubject: ${ticket.subject}\nCategory: ${ticket.category} | Priority: ${ticket.priority}\nRecent messages:\n${history}\nReturn only the reply text.`,
        }],
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
      const now = new Date().toISOString();
      return this.store.save('tickets', {
        ...res.value,
        messages: [...res.value.messages, { from, content, createdAt: now }],
        status: from === 'customer' ? 'open' : 'waiting_customer',
        updatedAt: now,
      });
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
      return this.store.save('tickets', {
        ...res.value, status: 'resolved', resolution, resolvedAt: now, updatedAt: now,
      });
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
      return ok(res.value.filter((t) => {
        if (!t.slaDeadline || t.status === 'resolved' || t.status === 'closed') return false;
        const remaining = new Date(t.slaDeadline).getTime() - now;
        return remaining < SLA_HOURS[t.priority] * 3_600_000 * 0.2 || remaining < 0;
      }));
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
      return ok({
        open: tickets.filter((t) => t.status === 'open').length,
        inProgress: tickets.filter((t) => t.status === 'in_progress').length,
        waitingCustomer: tickets.filter((t) => t.status === 'waiting_customer').length,
        resolved: tickets.filter((t) => t.status === 'resolved' || t.status === 'closed').length,
        slaAtRisk: slaRes.ok ? slaRes.value.length : 0,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
