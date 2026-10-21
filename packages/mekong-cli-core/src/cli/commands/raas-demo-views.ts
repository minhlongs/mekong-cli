/**
 * raas-demo-views.ts — Pricing tiers and revenue projection views for RaaS demo CLI.
 */
import { success, info, warn } from '../ui/output.js';

export const TIERS = {
  starter: { price: 49, credits: 200, margin: 0.82 },
  pro: { price: 149, credits: 1000, margin: 0.85 },
  enterprise: { price: 499, credits: -1, margin: 0.88 },
} as const;

export function renderDemoTiersView(): void {
  info('');
  info('┌─────────────┬────────┬──────────┬────────┐');
  info('│ Tier        │ Price  │ Credits  │ Margin │');
  info('├─────────────┼────────┼──────────┼────────┤');
  for (const [name, tier] of Object.entries(TIERS)) {
    const credits = tier.credits === -1 ? '∞' : String(tier.credits);
    const margin = `${Math.round(tier.margin * 100)}%`;
    info(`│ ${name.padEnd(11)} │ $${String(tier.price).padEnd(4)}  │ ${credits.padEnd(8)} │ ${margin.padEnd(6)} │`);
  }
  info('└─────────────┴────────┴──────────┴────────┘');
  info('');
  info('Revenue projection @ 100 customers:');
  const revenue = 20 * TIERS.starter.price + 60 * TIERS.pro.price + 20 * TIERS.enterprise.price;
  info(`  $${revenue.toLocaleString()}/month = $${(revenue * 12).toLocaleString()}/year`);
  warn('  Target: $1M ARR = ~83 enterprise customers');
  info('');
}

export function renderPricingCalcView(
  _customers?: string,
  _dist?: string,
  opts?: { churn: string; months: string },
): void {
  const totalCustomers = parseInt(_customers ?? '100', 10);
  const churn = parseInt(opts?.churn ?? '5', 10) / 100;
  const months = parseInt(opts?.months ?? '12', 10);
  const [s, p, e] = (_dist ?? '20/60/20').split('/').map(Number);
  const sum = s + p + e;
  const dist = { starter: s / sum, pro: p / sum, enterprise: e / sum };

  info('');
  info('═══════════════════════════════════════════════════════');
  info('   MEKONG CLI — REVENUE PROJECTION CALCULATOR');
  info('═══════════════════════════════════════════════════════');
  info(`   Customers: ${totalCustomers}  |  Churn: ${(churn * 100).toFixed(0)}%/mo  |  Months: ${months}`);
  info(`   Mix: ${Math.round(dist.starter * 100)}% Starter / ${Math.round(dist.pro * 100)}% Pro / ${Math.round(dist.enterprise * 100)}% Enterprise`);
  info('───────────────────────────────────────────────────────');

  let cumRevenue = 0;
  let active = totalCustomers;

  for (let m = 1; m <= months; m++) {
    const starterRev = Math.round(active * dist.starter) * TIERS.starter.price;
    const proRev = Math.round(active * dist.pro) * TIERS.pro.price;
    const entRev = Math.round(active * dist.enterprise) * TIERS.enterprise.price;
    const mrr = starterRev + proRev + entRev;
    cumRevenue += mrr;

    if (m <= 3 || m === 6 || m === months) {
      const bar = '█'.repeat(Math.min(Math.round(mrr / 500), 40));
      info(`   M${String(m).padStart(2)}  ${bar} $${mrr.toLocaleString()} MRR  (${Math.round(active)} active)`);
    }

    active = Math.max(1, active * (1 - churn));
  }

  info('───────────────────────────────────────────────────────');
  const avgMRR = Math.round(cumRevenue / months);
  const arr = avgMRR * 12;
  success(`   Total ${months}-month revenue: $${cumRevenue.toLocaleString()}`);
  success(`   Average MRR:            $${avgMRR.toLocaleString()}`);
  success(`   Projected ARR:          $${arr.toLocaleString()}`);

  if (arr >= 1_000_000) {
    success('   STATUS: $1M ARR TARGET ACHIEVABLE');
  } else {
    const needed = Math.ceil(1_000_000 / 12 / (avgMRR / totalCustomers));
    warn(`   Need ~${needed} customers for $1M ARR`);
  }

  info('');
  info('   Try: mekong demo pricing-calc 200 10/50/40 --churn 3');
  info('═══════════════════════════════════════════════════════');
  info('');
}
