/** Lead management — create, qualify, advance, convert leads */
import { randomUUID } from 'node:crypto';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { LlmRouter } from '../llm/router.js';
import type { Lead, PipelineStage } from './types.js';
import type { CrmStore } from './store.js';

export class LeadManager {
  constructor(
    private store: CrmStore,
    private llm: LlmRouter,
  ) {}

  async create(input: Omit<Lead, 'id' | 'createdAt' | 'updatedAt' | 'score' | 'notes' | 'tags'>): Promise<Result<Lead>> {
    const now = new Date().toISOString();
    const lead: Lead = Object.assign(
      { status: 'new' as Lead['status'], assignedAgent: 'sales-agent' },
      input,
      { id: randomUUID(), score: 0, notes: [], tags: [], createdAt: now, updatedAt: now },
    );
    return this.store.save('leads', lead);
  }

  async getById(id: string): Promise<Result<Lead | null>> {
    return this.store.getById('leads', id);
  }

  async getAll(filter?: Partial<Lead>): Promise<Result<Lead[]>> {
    return this.store.getAll('leads', filter);
  }

  /** Score lead 0-100 using LLM reasoning */
  async qualify(id: string): Promise<Result<Lead>> {
    try {
      const res = await this.store.getById('leads', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Lead ${id} not found`));
      const lead = res.value;

      const response = await this.llm.chat({
        messages: [
          {
            role: 'user',
            content: `Score this sales lead from 0-100 and provide brief reasoning.
Lead: ${JSON.stringify({ name: lead.name, company: lead.company, source: lead.source, estimatedValue: lead.estimatedValue, tags: lead.tags })}
Respond with JSON only: { "score": number, "reasoning": string }`,
          },
        ],
        maxTokens: 200,
        temperature: 0.3,
      });

      let score = lead.score;
      let reasoning = '';
      try {
        const parsed = JSON.parse(response.content) as { score: number; reasoning: string };
        score = Math.max(0, Math.min(100, parsed.score));
        reasoning = parsed.reasoning;
      } catch {
        score = 50;
        reasoning = 'Unable to parse LLM response';
      }

      const updated: Lead = {
        ...lead,
        score,
        notes: [
          ...lead.notes,
          { content: `AI qualification: ${reasoning}`, createdAt: new Date().toISOString() },
        ],
        updatedAt: new Date().toISOString(),
      };
      return this.store.save('leads', updated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Advance lead status and add optional note */
  async advanceStage(id: string, status: Lead['status'], note?: string): Promise<Result<Lead>> {
    try {
      const res = await this.store.getById('leads', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Lead ${id} not found`));
      const lead = res.value;
      const notes = note
        ? [...lead.notes, { content: note, createdAt: new Date().toISOString() }]
        : lead.notes;
      const updated: Lead = { ...lead, status, notes, updatedAt: new Date().toISOString() };
      return this.store.save('leads', updated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Convert won lead to customer — returns customerId */
  async convert(id: string): Promise<Result<string>> {
    try {
      const res = await this.store.getById('leads', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Lead ${id} not found`));
      const lead = res.value;

      const now = new Date().toISOString();
      const customerId = randomUUID();

      // Mark lead as won
      const updatedLead: Lead = { ...lead, status: 'won', updatedAt: now };
      const saveRes = await this.store.save('leads', updatedLead);
      if (!saveRes.ok) return saveRes;

      // Create customer record
      const { CustomerSchema } = await import('./types.js');
      const customer = CustomerSchema.parse({
        id: customerId,
        leadId: lead.id,
        name: lead.name,
        email: lead.email,
        company: lead.company,
        plan: 'free',
        mrr: 0,
        status: 'active',
        healthScore: 50,
        tags: lead.tags,
        notes: lead.notes,
        metadata: {},
        createdAt: now,
        updatedAt: now,
      });
      const custRes = await this.store.save('customers', customer);
      if (!custRes.ok) return custRes;
      return ok(customerId);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Draft follow-up email for a lead using LLM */
  async generateFollowUp(id: string): Promise<Result<string>> {
    try {
      const res = await this.store.getById('leads', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Lead ${id} not found`));
      const lead = res.value;

      const response = await this.llm.chat({
        messages: [
          {
            role: 'user',
            content: `Draft a concise follow-up email for this sales lead. Keep it under 150 words, professional tone.
Lead: name=${lead.name}, company=${lead.company ?? 'unknown'}, source=${lead.source}, status=${lead.status}, score=${lead.score}
Return only the email body text.`,
          },
        ],
        maxTokens: 300,
        temperature: 0.7,
      });
      return ok(response.content);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Get leads with nextFollowUp <= today */
  async getDueFollowUps(): Promise<Result<Lead[]>> {
    try {
      const res = await this.store.getAll('leads');
      if (!res.ok) return res;
      const today = new Date().toISOString();
      const due = res.value.filter(
        (l) => l.nextFollowUp !== undefined && l.nextFollowUp <= today,
      );
      return ok(due);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Group leads by status with value and conversion metrics */
  async getPipeline(): Promise<Result<PipelineStage[]>> {
    try {
      const res = await this.store.getAll('leads');
      if (!res.ok) return res;
      const leads = res.value;

      const stageOrder: Lead['status'][] = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
      const grouped = new Map<Lead['status'], Lead[]>();
      for (const status of stageOrder) grouped.set(status, []);
      for (const lead of leads) {
        grouped.get(lead.status)?.push(lead);
      }

      const stages: PipelineStage[] = stageOrder.map((status, i) => {
        const stageLeads = grouped.get(status) ?? [];
        const totalValue = stageLeads.reduce((s, l) => s + (l.estimatedValue ?? 0), 0);
        const nextStage = stageOrder[i + 1];
        let conversionRate = 0;
        if (nextStage && stageLeads.length > 0) {
          const nextCount = grouped.get(nextStage)?.length ?? 0;
          conversionRate = Math.round((nextCount / stageLeads.length) * 100);
        }
        return { name: status, leads: stageLeads, totalValue, conversionRate };
      });

      return ok(stages);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
