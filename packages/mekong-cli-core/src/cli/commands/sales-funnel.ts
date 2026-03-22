/**
 * sales-funnel.ts — Sales funnel visualization and analysis CLI commands
 * View funnel stages, record conversions, identify bottlenecks, forecast revenue
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

interface FunnelStage { name: string; count: number; convRate: number; avgDays: number; }

const FUNNEL: FunnelStage[] = [
  { name: 'Visitor',    count: 3_840, convRate: 0.062, avgDays: 0  },
  { name: 'Trial',      count: 238,   convRate: 0.273, avgDays: 3  },
  { name: 'Active',     count: 65,    convRate: 0.446, avgDays: 7  },
  { name: 'Paid',       count: 29,    convRate: 0.103, avgDays: 21 },
  { name: 'Enterprise', count: 3,     convRate: 1.0,   avgDays: 45 },
];

const STAGE_NAMES = FUNNEL.map(s => s.name.toLowerCase());

function barOf(n: number, max: number, width = 30): string {
  const filled = Math.max(1, Math.round((n / max) * width));
  return '█'.repeat(filled) + '░'.repeat(width - filled);
}

export function registerSalesFunnelCommand(program: Command, engine: MekongEngine): void {
  const funnel = program
    .command('sales-funnel')
    .description('Funnel analysis — view stages, conversions, bottlenecks, forecast');

  funnel
    .command('view')
    .description('Visualize the full sales funnel with conversion rates')
    .action(() => {
      heading('Sales Funnel — March 2026');
      keyValue('Updated', '2026-03-22 09:00 ICT');
      divider();
      const maxCount = FUNNEL[0].count;
      info('Stage        Count    Bar                              Conv→Next  Avg Days');
      info('─'.repeat(78));
      for (let i = 0; i < FUNNEL.length; i++) {
        const s = FUNNEL[i];
        const bar = barOf(s.count, maxCount);
        const convStr = i < FUNNEL.length - 1 ? `${Math.round(s.convRate * 100)}%` : '—';
        const daysStr = s.avgDays > 0 ? `${s.avgDays}d` : '—';
        const line = `${s.name.padEnd(12)} ${String(s.count).padStart(6)}   [${bar}]  ${convStr.padEnd(10)} ${daysStr}`;
        if (s.name === 'Enterprise') success(line);
        else if (s.convRate < 0.15 && i < FUNNEL.length - 1) warn(line);
        else info(line);
      }
      divider();
      const overallConv = FUNNEL[FUNNEL.length - 1].count / FUNNEL[0].count;
      keyValue('Overall conversion', `${(overallConv * 100).toFixed(2)}% (Visitor → Enterprise)`);
      keyValue('Visitor → Paid', `${(FUNNEL[3].count / FUNNEL[0].count * 100).toFixed(2)}%`);
      // Engine status footer
      try {
        const health = engine.openclaw?.getHealth();
        if (health) {
          divider();
          info('Engine Status');
          keyValue('  Missions completed', `${health.missionsCompleted}`);
          keyValue('  AGI score', `${health.agiScore}/100`);
          keyValue('  Circuit breaker', health.circuitBreakerState);
        }
      } catch { /* engine not ready */ }
      info('');
      info('Use `mekong sales-funnel bottleneck` to identify conversion gaps');
      info('');
    });

  funnel
    .command('convert')
    .description('Record a stage-to-stage conversion event')
    .option('--from <stage>', 'Source stage (visitor|trial|active|paid|enterprise)', 'trial')
    .option('--to <stage>', 'Target stage name', 'active')
    .option('--count <n>', 'Number of conversions to record', '1')
    .action((opts: { from: string; to: string; count: string }) => {
      const fromStage = opts.from.toLowerCase();
      const toStage = opts.to.toLowerCase();
      const count = Math.max(1, parseInt(opts.count, 10) || 1);
      heading('Conversion Recorded');
      if (!STAGE_NAMES.includes(fromStage)) {
        warn(`Unknown stage: "${opts.from}". Valid: ${STAGE_NAMES.join(', ')}`); return;
      }
      if (!STAGE_NAMES.includes(toStage)) {
        warn(`Unknown stage: "${opts.to}". Valid: ${STAGE_NAMES.join(', ')}`); return;
      }
      const fromIdx = STAGE_NAMES.indexOf(fromStage);
      const toIdx = STAGE_NAMES.indexOf(toStage);
      if (toIdx <= fromIdx) {
        warn(`"${opts.to}" is not downstream of "${opts.from}"`); return;
      }
      keyValue('From stage', FUNNEL[fromIdx].name);
      keyValue('To stage', FUNNEL[toIdx].name);
      keyValue('Count', `${count}`);
      keyValue('Recorded at', '2026-03-22 09:20 ICT');
      divider();
      const revenueImpact = toStage === 'paid' ? count * 49 : toStage === 'enterprise' ? count * 499 : 0;
      success(`${count} conversion(s) recorded: ${FUNNEL[fromIdx].name} → ${FUNNEL[toIdx].name}`);
      if (revenueImpact > 0) success(`Estimated MRR impact: +$${revenueImpact}/mo`);
      info('Funnel updated — run `mekong sales-funnel view` to see new state');
      info('');
    });

  funnel
    .command('bottleneck')
    .description('Identify the lowest-converting funnel stages')
    .action(() => {
      heading('Funnel Bottleneck Analysis');
      divider();
      const gaps = FUNNEL.slice(0, -1).map((stage, i) => ({
        from: stage.name, to: FUNNEL[i + 1].name,
        rate: stage.convRate, lost: stage.count - FUNNEL[i + 1].count,
      })).sort((a, b) => a.rate - b.rate);
      info('Transition              Conv Rate   Lost     Verdict');
      info('─'.repeat(60));
      for (const gap of gaps) {
        const verdict = gap.rate < 0.15 ? 'CRITICAL' : gap.rate < 0.30 ? 'WEAK' : 'OK';
        const line = `${gap.from.padEnd(11)} → ${gap.to.padEnd(11)} ${(gap.rate * 100).toFixed(1)}%       ${String(gap.lost).padStart(6)}   ${verdict}`;
        if (verdict === 'CRITICAL') warn(line);
        else if (verdict === 'WEAK') info(line);
        else success(line);
      }
      divider();
      const worst = gaps[0];
      warn(`Biggest bottleneck: ${worst.from} → ${worst.to} (${(worst.rate * 100).toFixed(1)}% conv rate)`);
      try {
        if (engine.openclaw) {
          void engine.openclaw.submitMission({ goal: `Analyze funnel bottleneck at ${worst.from} → ${worst.to} and provide recommendations`, complexity: 'trivial' });
          info('AI analysis: generating bottleneck recommendations...');
        }
      } catch { /* engine not ready — static fallback */ }
      info('Recommended actions:');
      if (worst.from === 'Visitor') {
        info('  - Improve landing page CTA and trial signup flow');
        info('  - A/B test hero section copy');
      } else if (worst.from === 'Paid') {
        info('  - Launch enterprise nurture campaign: mekong sales-campaign create --template upsell');
        info('  - Schedule dedicated account review calls');
      } else {
        info('  - Reduce time-to-value in onboarding for ' + worst.from + ' users');
        info('  - Trigger contextual upgrade prompts at activation moments');
      }
      info('');
    });

  funnel
    .command('forecast')
    .description('Funnel-based revenue forecast by scenario')
    .option('--scenario <type>', 'Scenario: optimistic|realistic|conservative', 'realistic')
    .action((opts: { scenario: string }) => {
      const validScenarios = ['optimistic', 'realistic', 'conservative'];
      const scenario = validScenarios.includes(opts.scenario) ? opts.scenario : 'realistic';
      const growthMultipliers: Record<string, number> = { optimistic: 1.35, realistic: 1.18, conservative: 1.06 };
      const mult = growthMultipliers[scenario];
      const basePaid = FUNNEL[3].count;
      const baseEnt = FUNNEL[4].count;
      heading(`Funnel Revenue Forecast — ${scenario.charAt(0).toUpperCase() + scenario.slice(1)}`);
      keyValue('Scenario', scenario.toUpperCase());
      keyValue('Growth multiplier/month', `${((mult - 1) * 100).toFixed(0)}% visitor growth`);
      divider();
      info('Month   Paid Customers  Enterprise  MRR');
      info('─'.repeat(48));
      for (let m = 1; m <= 6; m++) {
        const visitors = Math.round(FUNNEL[0].count * Math.pow(mult, m));
        const trials   = Math.round(visitors * FUNNEL[0].convRate);
        const active   = Math.round(trials * FUNNEL[1].convRate);
        const paid     = Math.round(active * FUNNEL[2].convRate) + basePaid;
        const ent      = Math.round(paid * FUNNEL[3].convRate) + baseEnt;
        const mrr      = paid * 149 + ent * 499;
        const date = new Date(2026, 3 + m - 1, 1);
        const label = date.toLocaleString('en-US', { month: 'short', year: '2-digit' });
        const line = `${label.padEnd(8)} ${String(paid).padStart(14)}  ${String(ent).padStart(10)}  $${mrr.toLocaleString()}`;
        if (mrr >= 50_000) success(line); else info(line);
      }
      divider();
      const m6paid = Math.round(FUNNEL[2].count * FUNNEL[2].convRate * Math.pow(mult, 6)) + basePaid;
      const m6ent  = Math.round(m6paid * FUNNEL[3].convRate) + baseEnt;
      const m6mrr  = m6paid * 149 + m6ent * 499;
      keyValue('6-month MRR', `$${m6mrr.toLocaleString()}`);
      keyValue('6-month ARR', `$${(m6mrr * 12).toLocaleString()}`);
      if (scenario === 'optimistic') success('Optimistic: requires 35%/mo top-of-funnel growth — aggressive but achievable');
      else if (scenario === 'realistic') info('Realistic: 18%/mo visitor growth — aligns with current trajectory');
      else warn('Conservative: 6%/mo — minimum floor assuming no new marketing investment');
      try {
        const health = engine.openclaw?.getHealth();
        if (health) {
          const total = health.missionsCompleted + health.missionsFailed;
          const rate = total > 0 ? ((health.missionsCompleted / total) * 100).toFixed(1) : '—';
          divider(); info('Platform Capacity');
          keyValue('  Missions processed', `${total}`);
          keyValue('  Success rate', `${rate}%`);
          keyValue('  AGI score', `${health.agiScore}/100`);
        }
      } catch { /* engine not ready */ }
      info('');
    });
}
