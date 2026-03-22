/**
 * raas-demo.ts — Sales demo and ROI calculator CLI commands
 * Used for enterprise pitches and ProductHunt demos
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, info, warn } from '../ui/output.js';

const TIERS = {
  starter: { price: 49, credits: 200, margin: 0.82 },
  pro: { price: 149, credits: 1000, margin: 0.85 },
  enterprise: { price: 499, credits: -1, margin: 0.88 },
} as const;

export function registerRaasDemoCommand(program: Command, engine: MekongEngine): void {
  const demo = program
    .command('demo')
    .description('Sales demo — showcase RaaS platform capabilities');

  demo
    .command('roi [teamSize] [hoursPerWeek]')
    .description('Calculate ROI for prospect — show cost savings')
    .action((_teamSize?: string, _hoursPerWeek?: string) => {
      const teamSize = parseInt(_teamSize ?? '5', 10);
      const hours = parseInt(_hoursPerWeek ?? '20', 10);
      const hourlyRate = 50; // avg dev hourly rate USD

      const currentCost = teamSize * hours * hourlyRate * 4; // monthly
      const withMekong = TIERS.pro.price; // Pro tier covers most teams
      const savings = currentCost - withMekong;
      const roiPercent = Math.round((savings / withMekong) * 100);
      const breakEvenWeeks = Math.ceil(withMekong / (savings / 4));

      info('');
      info('═══════════════════════════════════════════');
      info('   MEKONG CLI — ROI CALCULATOR');
      info('═══════════════════════════════════════════');
      info(`   Team size:        ${teamSize} developers`);
      info(`   Hours automated:  ${hours}h/week`);
      info(`   Avg hourly rate:  $${hourlyRate}/hr`);
      info('───────────────────────────────────────────');
      info(`   Current cost:     $${currentCost.toLocaleString()}/month`);
      info(`   With Mekong Pro:  $${withMekong}/month`);
      success(`   Monthly savings:  $${savings.toLocaleString()}/month`);
      success(`   ROI:              ${roiPercent}%`);
      info(`   Break-even:       Week ${breakEvenWeeks}`);
      info(`   Annual savings:   $${(savings * 12).toLocaleString()}`);
      info('═══════════════════════════════════════════');
      info('');
    });

  demo
    .command('pitch')
    .description('Generate enterprise sales pitch with live stats')
    .action(() => {
      const status = engine.getStatus();
      const openclawInfo = status.openclaw;

      info('');
      info('═══════════════════════════════════════════');
      info('   MEKONG CLI — ENTERPRISE PITCH');
      info('═══════════════════════════════════════════');
      info('');
      info('   "Describe your goal. AI delivers results."');
      info('');
      info('   WHAT WE DO:');
      info('   319 commands across 5 business layers');
      info('   AI plans → executes → verifies → delivers');
      info('');
      info('   PRICING (RaaS Credits):');
      for (const [name, tier] of Object.entries(TIERS)) {
        const credits = tier.credits === -1 ? 'Unlimited' : `${tier.credits}`;
        info(`   ${name.padEnd(12)} $${tier.price}/mo — ${credits} credits`);
      }
      info('');
      info('   TECH STACK:');
      info('   OpenClaw Engine — mission orchestration + circuit breaker');
      info('   PEV Bridge — Plan → Execute → Verify loop');
      info('   Universal LLM — any provider (OpenRouter/Ollama/DeepSeek)');
      if (openclawInfo) {
        info('');
        info('   LIVE ENGINE STATS:');
        info(`   Missions completed: ${openclawInfo.missionsCompleted}`);
        info(`   AGI Score: ${openclawInfo.agiScore}/100`);
        info(`   Circuit breaker: ${openclawInfo.circuitBreaker}`);
      }
      info('');
      info('   COMPETITIVE EDGE:');
      info('   vs Cursor/Copilot: Full business stack, not just code');
      info('   vs Custom AI: 10x faster setup, battle-tested');
      info('   vs Agencies: $149/mo vs $10k/mo retainer');
      info('');
      info('═══════════════════════════════════════════');
      info('');
    });

  demo
    .command('walkthrough')
    .description('Interactive demo — simulate a mission lifecycle')
    .action(async () => {
      info('');
      info('═══════════════════════════════════════════');
      info('   MEKONG CLI — LIVE DEMO');
      info('═══════════════════════════════════════════');

      // Step 1: Classify
      const goal = 'Build a REST API with auth and deploy to Cloudflare';
      info('');
      info('   Step 1: CLASSIFY complexity');
      info(`   Goal: "${goal}"`);
      const complexity = engine.openclaw.classifyComplexity(goal);
      success(`   Complexity: ${complexity}`);

      // Step 2: Submit mission
      info('');
      info('   Step 2: SUBMIT to OpenClaw Engine');
      const mission = await engine.openclaw.submitMission({ goal, complexity });
      success(`   Mission ID: ${mission.id}`);
      success(`   Status: ${mission.status}`);
      info(`   Credits used: ${mission.creditsUsed} MCU`);

      // Step 3: Health check
      info('');
      info('   Step 3: ENGINE HEALTH');
      const health = engine.openclaw.getHealth();
      info(`   Uptime: ${Math.round(health.uptime / 1000)}s`);
      info(`   AGI Score: ${health.agiScore}/100`);
      info(`   Circuit Breaker: ${health.circuitBreakerState}`);

      // Step 4: RaaS modules
      info('');
      info('   Step 4: RaaS MODULE ACCESS');
      const modules = engine.openclaw.modules;
      const raasHealth = await modules.raas.checkHealth();
      info(`   RaaS Status: ${raasHealth.status} (v${raasHealth.version})`);

      info('');
      success('   Demo complete. Ready for production.');
      info('═══════════════════════════════════════════');
      info('');
    });

  demo
    .command('tiers')
    .description('Show pricing comparison table')
    .action(() => {
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
    });

  demo
    .command('pricing-calc [customers] [distribution]')
    .description('Revenue projection calculator — model different customer mixes')
    .option('--churn <percent>', 'Monthly churn rate', '5')
    .option('--months <n>', 'Projection months', '12')
    .action((_customers?: string, _dist?: string, opts?: { churn: string; months: string }) => {
      const totalCustomers = parseInt(_customers ?? '100', 10);
      const churn = parseInt(opts?.churn ?? '5', 10) / 100;
      const months = parseInt(opts?.months ?? '12', 10);
      // distribution format: "20/60/20" for starter/pro/enterprise
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
          const bar = '\u2588'.repeat(Math.min(Math.round(mrr / 500), 40));
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
    });
}
