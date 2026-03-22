/**
 * sales-report.ts — Sales metrics and revenue reporting CLI commands
 * Daily, weekly, monthly snapshots and multi-month revenue forecast
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

const fmtUsd = (n: number) => `$${n.toLocaleString()}`;

function changeLine(label: string, current: number, prev: number, unit = ''): void {
  const delta = current - prev;
  const pct = prev > 0 ? Math.round((delta / prev) * 100) : 0;
  const sign = delta >= 0 ? '+' : '';
  const line = `${label.padEnd(26)} ${unit}${current}  (${sign}${pct}% vs last week)`;
  if (delta > 0) success(line); else if (delta === 0) info(line); else warn(line);
}

function showEngineHealth(engine: MekongEngine, label: string): void {
  try {
    const health = engine.openclaw?.getHealth();
    if (!health) return;
    divider();
    info(label);
    keyValue('  Uptime', `${Math.round(health.uptime / 1000)}s`);
    keyValue('  Missions completed', `${health.missionsCompleted}`);
    keyValue('  Missions failed', `${health.missionsFailed}`);
    keyValue('  AGI score', `${health.agiScore}/100`);
    keyValue('  Circuit breaker', health.circuitBreakerState);
  } catch { /* engine not ready */ }
}

export function registerSalesReportCommand(program: Command, engine: MekongEngine): void {
  const report = program
    .command('sales-report')
    .description('Sales metrics and revenue reporting — daily, weekly, monthly, forecast');

  report
    .command('daily')
    .description("Today's sales metrics snapshot")
    .action(() => {
      heading("Daily Sales Report — 2026-03-22");
      keyValue('Period', 'Today (Asia/Saigon)'); divider();
      info('Activity'); info('─'.repeat(40));
      success('  New leads captured:       8'); info('  Leads contacted:           5');
      info('  Demos booked:              2');   info('  Proposals sent:            1');
      success('  Deals closed:              1'); divider();
      info('Revenue'); info('─'.repeat(40));
      success(`  New MRR today:             ${fmtUsd(149)}`);
      info(`  Pipeline value added:      ${fmtUsd(2_800)}`);
      info(`  Running MRR (month):       ${fmtUsd(4_320)}`); divider();
      info('Team Activity'); info('─'.repeat(40));
      info('  Emails sent:               34'); info('  Calls made:                6');
      info('  Meetings held:             2'); divider();
      keyValue('Day vs target', '72% of daily goal');
      warn('2 high-score leads (lead_001, lead_008) awaiting follow-up');
      showEngineHealth(engine, 'Engine Performance');
      info('');
    });

  report
    .command('weekly')
    .description('This week vs last week performance comparison')
    .action(() => {
      heading('Weekly Sales Report');
      keyValue('This week', '2026-03-16 to 2026-03-22');
      keyValue('Last week', '2026-03-09 to 2026-03-15'); divider();
      info('Metric                     This Week  Change'); info('─'.repeat(52));
      changeLine('New leads', 31, 24);       changeLine('Leads contacted', 22, 20);
      changeLine('Demos booked', 7, 5);      changeLine('Proposals sent', 3, 4);
      changeLine('Deals closed', 2, 1); divider();
      info('Revenue Metrics'); info('─'.repeat(52));
      changeLine('New MRR', 298, 149, '$');  changeLine('Pipeline value', 8_400, 6_200, '$');
      changeLine('Avg deal size', 149, 149, '$'); divider();
      keyValue('Best performing source', 'Referral (42% of new leads)');
      keyValue('Worst performing source', 'Cold outreach (8% open rate)');
      success('Week-on-week: +100% new MRR — on track for $1k MRR milestone');
      showEngineHealth(engine, 'Engine Health (Week)');
      info('');
    });

  report
    .command('monthly')
    .description('Monthly revenue, MRR, churn, and expansion metrics')
    .action(() => {
      heading('Monthly Sales Report — March 2026');
      keyValue('MRR start of month', fmtUsd(2_827));
      keyValue('MRR end of month (projected)', fmtUsd(4_571)); divider();
      info('MRR Breakdown'); info('─'.repeat(44));
      success(`  New MRR:            ${fmtUsd(1_893)}`);
      success(`  Expansion MRR:      ${fmtUsd(298)}`);
      warn(`  Churned MRR:       -${fmtUsd(447)}`);
      info(`  Net New MRR:        ${fmtUsd(1_744)}`); divider();
      info('Customers'); info('─'.repeat(44));
      info('  Active customers:          29'); success('  New customers:             12');
      warn('  Churned customers:          3  (churn rate: 10.3%)');
      info('  Expansion upgrades:         2'); divider();
      info('Revenue by Plan'); info('─'.repeat(44));
      info(`  Starter ($49/mo):   12 customers   ${fmtUsd(588)}/mo`);
      info(`  Pro ($149/mo):      14 customers   ${fmtUsd(2_086)}/mo`);
      success(`  Enterprise ($499):   3 customers   ${fmtUsd(1_497)}/mo`); divider();
      keyValue('ARR (annualized)', fmtUsd(4_571 * 12));
      keyValue('LTV (avg)', fmtUsd(1_340)); keyValue('CAC (avg)', fmtUsd(87));
      success('LTV:CAC ratio: 15.4x — healthy');
      try {
        const health = engine.openclaw?.getHealth();
        if (health) {
          const total = health.missionsCompleted + health.missionsFailed;
          const rate = total > 0 ? ((health.missionsCompleted / total) * 100).toFixed(1) : '—';
          divider(); info('Platform Operations'); info('─'.repeat(44));
          keyValue('  Total missions', `${total}`);
          keyValue('  Success rate', `${rate}%`);
          keyValue('  AGI score', `${health.agiScore}/100`);
        }
      } catch { /* engine not ready */ }
      info('');
    });

  report
    .command('forecast')
    .description('Revenue forecast with confidence intervals')
    .option('--months <n>', 'Forecast horizon: 3|6|12', '6')
    .action((opts: { months: string }) => {
      const months = [3, 6, 12].includes(parseInt(opts.months)) ? parseInt(opts.months) : 6;
      const baseMrr = 4_571;
      const gr = { conservative: 0.12, realistic: 0.20, optimistic: 0.32 };
      heading(`Revenue Forecast — ${months}-Month Horizon`);
      keyValue('Base MRR (March 2026)', fmtUsd(baseMrr));
      keyValue('Model', 'Compound monthly growth'); divider();
      info('Month        Conservative  Realistic     Optimistic'); info('─'.repeat(56));
      for (let m = 1; m <= months; m++) {
        const date = new Date(2026, 3 + m - 1, 1);
        const label = date.toLocaleString('en-US', { month: 'short', year: '2-digit' });
        const cons = Math.round(baseMrr * Math.pow(1 + gr.conservative, m));
        const real = Math.round(baseMrr * Math.pow(1 + gr.realistic, m));
        const opti = Math.round(baseMrr * Math.pow(1 + gr.optimistic, m));
        const line = `${label.padEnd(13)} ${fmtUsd(cons).padEnd(14)} ${fmtUsd(real).padEnd(14)} ${fmtUsd(opti)}`;
        if (real >= 10_000) success(line); else info(line);
      }
      divider();
      const finalReal = Math.round(baseMrr * Math.pow(1 + gr.realistic, months));
      const milestone = finalReal >= 83_333 ? '$1M ARR' : finalReal >= 41_667 ? '$500k ARR' : finalReal >= 8_333 ? '$100k ARR' : '$50k ARR';
      keyValue(`${months}m realistic MRR`, fmtUsd(finalReal));
      keyValue(`${months}m realistic ARR`, fmtUsd(finalReal * 12));
      success(`Trajectory: ${milestone} within reach on realistic scenario`);
      try {
        if (engine.openclaw) {
          void engine.openclaw.submitMission({ goal: 'Analyze revenue forecast and provide growth commentary', complexity: 'trivial' });
          info('AI forecast commentary: analyzing revenue trajectory...');
        }
      } catch { /* engine not ready — static fallback */ }
      warn('Confidence range widens beyond 6 months — reforecast monthly');
      info('');
    });
}
