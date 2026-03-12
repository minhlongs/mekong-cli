/** Sales pipeline tracker — overview, conversion rates, weighted forecast */
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { Lead, PipelineStage } from './types.js';
import type { CrmStore } from './store.js';

/** Probability weights per pipeline stage for forecast */
const STAGE_PROBABILITY: Record<Lead['status'], number> = {
  new: 0.05,
  contacted: 0.15,
  qualified: 0.30,
  proposal: 0.50,
  negotiation: 0.75,
  won: 1.0,
  lost: 0.0,
};

export interface ConversionRates {
  stages: Array<{ from: Lead['status']; to: Lead['status']; rate: number }>;
  overallWinRate: number;
}

export interface PipelineForecast {
  weightedValue: number;
  bestCase: number;
  worstCase: number;
  stageBreakdown: Array<{ stage: Lead['status']; value: number; probability: number; weighted: number }>;
}

export class PipelineTracker {
  constructor(private store: CrmStore) {}

  /** Pipeline stages with lead counts and total values */
  async getOverview(): Promise<Result<PipelineStage[]>> {
    try {
      const res = await this.store.getAll('leads');
      if (!res.ok) return res;
      const leads = res.value;

      const stageOrder: Lead['status'][] = [
        'new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost',
      ];

      const grouped = new Map<Lead['status'], Lead[]>();
      for (const s of stageOrder) grouped.set(s, []);
      for (const lead of leads) grouped.get(lead.status)?.push(lead);

      const stages: PipelineStage[] = stageOrder.map((status, i) => {
        const stageLeads = grouped.get(status) ?? [];
        const totalValue = stageLeads.reduce((s, l) => s + (l.estimatedValue ?? 0), 0);
        const nextStatus = stageOrder[i + 1];
        let conversionRate = 0;
        if (nextStatus && stageLeads.length > 0) {
          const nextCount = grouped.get(nextStatus)?.length ?? 0;
          conversionRate = Math.round((nextCount / stageLeads.length) * 100);
        }
        return { name: status, leads: stageLeads, totalValue, conversionRate };
      });

      return ok(stages);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Stage-to-stage conversion rates and overall win rate */
  async getConversionRates(): Promise<Result<ConversionRates>> {
    try {
      const res = await this.store.getAll('leads');
      if (!res.ok) return res;
      const leads = res.value;

      const stageOrder: Lead['status'][] = [
        'new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won',
      ];

      const counts = new Map<Lead['status'], number>();
      for (const s of stageOrder) counts.set(s, 0);
      counts.set('lost', 0);
      for (const lead of leads) {
        counts.set(lead.status, (counts.get(lead.status) ?? 0) + 1);
      }

      const stages: ConversionRates['stages'] = [];
      for (let i = 0; i < stageOrder.length - 1; i++) {
        const from = stageOrder[i]!;
        const to = stageOrder[i + 1]!;
        const fromCount = counts.get(from) ?? 0;
        const toCount = counts.get(to) ?? 0;
        stages.push({
          from,
          to,
          rate: fromCount > 0 ? Math.round((toCount / fromCount) * 100) : 0,
        });
      }

      const totalEntered = counts.get('new') ?? 0;
      const totalWon = counts.get('won') ?? 0;
      const overallWinRate = totalEntered > 0 ? Math.round((totalWon / totalEntered) * 100) : 0;

      return ok({ stages, overallWinRate });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Weighted pipeline value forecast by stage probability */
  async getForecast(): Promise<Result<PipelineForecast>> {
    try {
      const res = await this.store.getAll('leads');
      if (!res.ok) return res;
      const leads = res.value.filter((l) => l.status !== 'lost');

      const stageMap = new Map<Lead['status'], number>();
      for (const lead of leads) {
        const val = lead.estimatedValue ?? 0;
        stageMap.set(lead.status, (stageMap.get(lead.status) ?? 0) + val);
      }

      let weightedValue = 0;
      let bestCase = 0;
      const stageBreakdown: PipelineForecast['stageBreakdown'] = [];

      for (const [stage, value] of stageMap.entries()) {
        const probability = STAGE_PROBABILITY[stage];
        const weighted = value * probability;
        weightedValue += weighted;
        bestCase += value;
        stageBreakdown.push({ stage, value, probability, weighted });
      }

      stageBreakdown.sort((a, b) => b.weighted - a.weighted);

      return ok({
        weightedValue: Math.round(weightedValue),
        bestCase: Math.round(bestCase),
        worstCase: 0,
        stageBreakdown,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
