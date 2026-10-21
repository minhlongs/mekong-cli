/**
 * openclaw-cost-data.ts — Cost data constants and optimization view for OpenClaw cost CLI.
 */
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

export type Period = 'day' | 'week' | 'month';

export interface MissionCost {
  id: string;
  name: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  date: string;
}

export const MISSION_COSTS: MissionCost[] = [
  { id: 'msn_001', name: 'Deploy landing page', model: 'claude-haiku-3', inputTokens: 18400, outputTokens: 4200, costUsd: 0.031, date: '2026-03-22' },
  { id: 'msn_002', name: 'Scrape competitor data', model: 'claude-sonnet-4', inputTokens: 72300, outputTokens: 18600, costUsd: 0.384, date: '2026-03-22' },
  { id: 'msn_003', name: 'Generate monthly report', model: 'claude-haiku-3', inputTokens: 31200, outputTokens: 9800, costUsd: 0.067, date: '2026-03-21' },
  { id: 'msn_005', name: 'SEO audit & fix', model: 'claude-sonnet-4', inputTokens: 44100, outputTokens: 11300, costUsd: 0.218, date: '2026-03-22' },
  { id: 'msn_006', name: 'Onboarding email sequence', model: 'claude-sonnet-4', inputTokens: 22800, outputTokens: 6400, costUsd: 0.109, date: '2026-03-22' },
];

export const PERIOD_STATS: Record<Period, { totalTokens: number; totalCost: number; missions: number }> = {
  day:   { totalTokens: 188800, totalCost: 0.809, missions: 5 },
  week:  { totalTokens: 891200, totalCost: 3.742, missions: 23 },
  month: { totalTokens: 3_240_000, totalCost: 14.18, missions: 87 },
};

export function renderCostOptimizeView(engine: MekongEngine): void {
  heading('Cost Optimization Recommendations');
  divider();

  try {
    const health = engine.openclaw?.getHealth();
    if (health) {
      const total = health.missionsCompleted + health.missionsFailed;
      const failRate = total > 0 ? ((health.missionsFailed / total) * 100).toFixed(1) : '0.0';
      info('Live engine stats:');
      keyValue('  Failure rate', `${failRate}% (${health.missionsFailed}/${total})`);
      keyValue('  AGI score', `${health.agiScore}/100`);
      if (health.missionsFailed > 0) {
        warn(`  ${health.missionsFailed} failed missions detected — review task complexity settings`);
      }
      if (health.agiScore < 80) {
        warn('  AGI score below 80 — consider reducing concurrent missions');
      } else {
        success('  AGI score healthy — engine performing well');
      }
      if (health.circuitBreakerState !== 'closed') {
        warn(`  Circuit breaker is ${health.circuitBreakerState} — reduce mission load`);
      }
      divider();
    }
  } catch {
    // engine not ready — show demo tips only
  }

  info('General optimization tips (demo):');
  info('');

  warn('1. Model downgrade opportunity (HIGH IMPACT)');
  info('   3 missions used claude-sonnet-4 but had < 30k total tokens.');
  info('   Switching to claude-haiku-3 would save ~$0.52 this week.');
  info('   Affected: msn_005, msn_006 and similar low-complexity tasks.');
  info('');

  warn('2. Prompt caching not enabled (MEDIUM IMPACT)');
  info('   Repeated system prompts detected across missions.');
  info('   Enable prompt caching to reduce input token costs by ~15%.');
  info('   Estimated savings: $0.12/week');
  info('');

  info('3. Off-peak scheduling (LOW IMPACT)');
  info('   Running non-urgent missions 2-6 AM reduces queue wait times.');
  info('   No direct cost saving — improves throughput efficiency.');
  info('');

  divider();
  keyValue('Total estimated savings', '~$0.64/week  (~$2.76/month)');
  success('Apply: set complexity=low missions to use claude-haiku-3 by default');
  info('Docs: https://openclaw.io/docs/cost-optimization');
  info('');
}
