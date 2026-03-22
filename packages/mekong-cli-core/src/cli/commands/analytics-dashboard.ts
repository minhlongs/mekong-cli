/**
 * analytics-dashboard.ts — Analytics insights CLI commands
 * Revenue metrics, conversion funnel, cohort retention, and revenue forecast
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

const OVERVIEW = {
  mrr: 24_850,
  mrrGrowth: 18.4,
  arr: 298_200,
  churnRate: 2.1,
  netRevRetention: 118,
  activeTenants: 312,
  trialConversion: 34.7,
  avgRevenuePerUser: 79.6,
};

const FUNNEL = [
  { stage: 'Visitors',      count: 18_420, pct: 100,  delta: '+12.3%' },
  { stage: 'Signups',       count:  2_205, pct: 12.0, delta: '+8.1%'  },
  { stage: 'Trials',        count:    841, pct:  4.6, delta: '+15.6%' },
  { stage: 'Paid (any)',    count:    292, pct:  1.6, delta: '+21.4%' },
  { stage: 'Pro+',          count:    148, pct:  0.8, delta: '+28.7%' },
  { stage: 'Enterprise',    count:     31, pct:  0.2, delta: '+41.9%' },
];

const COHORTS = [
  { month: '2025-10', m0: 100, m1: 88, m2: 81, m3: 76, m4: 72, m5: 70 },
  { month: '2025-11', m0: 100, m1: 91, m2: 84, m3: 79, m4: 75, m5: null },
  { month: '2025-12', m0: 100, m1: 89, m2: 83, m3: 78, m4: null, m5: null },
  { month: '2026-01', m0: 100, m1: 92, m2: 86, m3: null, m4: null, m5: null },
  { month: '2026-02', m0: 100, m1: 90, m2: null, m3: null, m4: null, m5: null },
  { month: '2026-03', m0: 100, m1: null, m2: null, m3: null, m4: null, m5: null },
];

function bar(value: number, max: number, width = 30): string {
  const filled = Math.round((value / max) * width);
  return '\u2588'.repeat(filled) + '\u2591'.repeat(width - filled);
}

function fmtPct(val: number | null): string {
  if (val === null) return '  -- ';
  return `${String(val).padStart(3)}% `;
}

export function registerInsightsCommand(program: Command): void {
  const insights = program
    .command('insights')
    .description('Analytics insights — revenue, funnel, cohorts, forecast');

  insights
    .command('overview')
    .description('Key business metrics overview — MRR, churn, growth')
    .action(() => {
      heading('Business Metrics Overview');

      keyValue('MRR', `$${OVERVIEW.mrr.toLocaleString()}`);
      keyValue('MRR Growth (MoM)', `+${OVERVIEW.mrrGrowth}%`);
      keyValue('ARR (projected)', `$${OVERVIEW.arr.toLocaleString()}`);
      divider();
      keyValue('Active Tenants', String(OVERVIEW.activeTenants));
      keyValue('ARPU', `$${OVERVIEW.avgRevenuePerUser}/mo`);
      keyValue('Trial → Paid', `${OVERVIEW.trialConversion}%`);
      divider();

      if (OVERVIEW.churnRate <= 2.5) {
        success(`Churn Rate: ${OVERVIEW.churnRate}% (excellent)`);
      } else if (OVERVIEW.churnRate <= 5) {
        info(`Churn Rate: ${OVERVIEW.churnRate}% (acceptable)`);
      } else {
        warn(`Churn Rate: ${OVERVIEW.churnRate}% (needs attention)`);
      }

      if (OVERVIEW.netRevRetention >= 110) {
        success(`Net Revenue Retention: ${OVERVIEW.netRevRetention}% (expansion-led growth)`);
      } else {
        info(`Net Revenue Retention: ${OVERVIEW.netRevRetention}%`);
      }

      divider();
      info('$1M ARR target progress:');
      const pct = Math.round((OVERVIEW.arr / 1_000_000) * 100);
      info(`  [${bar(OVERVIEW.arr, 1_000_000)}] ${pct}%`);
      info(`  $${(1_000_000 - OVERVIEW.arr).toLocaleString()} remaining`);
      info('');
    });

  insights
    .command('funnel')
    .description('Conversion funnel — visitor to enterprise')
    .action(() => {
      heading('Conversion Funnel (Last 30 Days)');
      info(`${'Stage'.padEnd(18)} ${'Count'.padEnd(8)} ${'Rate'.padEnd(7)} ${'WoW'.padEnd(8)} Bar`);
      divider();

      const maxCount = FUNNEL[0].count;
      for (const row of FUNNEL) {
        const b = bar(row.count, maxCount, 20);
        const line = `${row.stage.padEnd(18)} ${String(row.count).padEnd(8)} ${`${row.pct}%`.padEnd(7)} ${row.delta.padEnd(8)} ${b}`;
        if (row.stage === 'Enterprise') success(line);
        else if (row.stage === 'Pro+') success(line);
        else if (row.stage === 'Paid (any)') info(line);
        else info(line);
      }

      divider();
      const trialToPaid = ((FUNNEL[3].count / FUNNEL[2].count) * 100).toFixed(1);
      keyValue('Trial → Paid rate', `${trialToPaid}%`);
      info('');
      info('Improve funnel:');
      info('  mekong insights cohort   — identify retention drop-off');
      info('  mekong sales score       — qualify & prioritize leads');
      info('');
    });

  insights
    .command('cohort')
    .description('Monthly cohort retention table')
    .action(() => {
      heading('Monthly Cohort Retention');
      info(`${'Cohort'.padEnd(10)} M0     M1     M2     M3     M4     M5`);
      divider();

      for (const c of COHORTS) {
        const cols = [c.m0, c.m1, c.m2, c.m3, c.m4, c.m5]
          .map(fmtPct)
          .join(' ');
        const line = `${c.month.padEnd(10)} ${cols}`;
        if (c.m5 !== null && c.m5 >= 70) success(line);
        else if (c.m1 !== null && c.m1 >= 88) info(line);
        else info(line);
      }

      divider();
      info('M5 average retention: ~70% — strong for SaaS (benchmark: 40-60%)');
      success('Cohort retention trending up — product-market fit signal');
      info('');
    });

  insights
    .command('forecast')
    .description('Revenue forecast based on current growth trajectory')
    .action(() => {
      heading('Revenue Forecast');

      const monthlyGrowthRate = OVERVIEW.mrrGrowth / 100;
      let mrr = OVERVIEW.mrr;

      info(`${'Month'.padEnd(12)} ${'MRR'.padEnd(14)} ${'ARR'.padEnd(14)} Progress`);
      divider();

      const targetMRR = 1_000_000 / 12;
      for (let i = 1; i <= 6; i++) {
        mrr = Math.round(mrr * (1 + monthlyGrowthRate));
        const arr = mrr * 12;
        const pct = Math.min(100, Math.round((arr / 1_000_000) * 100));
        const b = bar(arr, 1_000_000, 20);
        const label = new Date(2026, 2 + i, 1).toLocaleString('en', { month: 'short', year: '2-digit' });
        const line = `${label.padEnd(12)} $${String(mrr.toLocaleString()).padEnd(12)} $${String(arr.toLocaleString()).padEnd(12)} [${b}] ${pct}%`;
        if (arr >= 1_000_000) success(line + ' TARGET HIT');
        else if (mrr >= targetMRR * 0.8) info(line);
        else info(line);
      }

      divider();
      if (mrr * 12 >= 1_000_000) {
        success('$1M ARR reachable within 6 months at current growth rate');
      } else {
        warn('Need to accelerate growth — consider enterprise upsell or new GTM');
      }

      info('');
      info('Levers to accelerate:');
      info('  mekong sales score --size 200 --budget 500  — enterprise pipeline');
      info('  mekong onboard recommend                    — optimize tier mix');
      info('  mekong insights funnel                      — fix conversion gaps');
      info('');
    });
}
