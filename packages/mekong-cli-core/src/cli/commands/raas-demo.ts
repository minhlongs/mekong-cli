/**
 * raas-demo.ts — Sales demo and ROI calculator CLI commands
 * Used for enterprise pitches and ProductHunt demos
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, info } from '../ui/output.js';
import { TIERS, renderDemoTiersView, renderPricingCalcView } from './raas-demo-views.js';

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
      const hourlyRate = 50;

      const currentCost = teamSize * hours * hourlyRate * 4;
      const withMekong = TIERS.pro.price;
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

      const goal = 'Build a REST API with auth and deploy to Cloudflare';
      info('');
      info('   Step 1: CLASSIFY complexity');
      info(`   Goal: "${goal}"`);
      const complexity = engine.openclaw.classifyComplexity(goal);
      success(`   Complexity: ${complexity}`);

      info('');
      info('   Step 2: SUBMIT to OpenClaw Engine');
      const mission = await engine.openclaw.submitMission({ goal, complexity });
      success(`   Mission ID: ${mission.id}`);
      success(`   Status: ${mission.status}`);
      info(`   Credits used: ${mission.creditsUsed} MCU`);

      info('');
      info('   Step 3: ENGINE HEALTH');
      const health = engine.openclaw.getHealth();
      info(`   Uptime: ${Math.round(health.uptime / 1000)}s`);
      info(`   AGI Score: ${health.agiScore}/100`);
      info(`   Circuit Breaker: ${health.circuitBreakerState}`);

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
    .action(renderDemoTiersView);

  demo
    .command('pricing-calc [customers] [distribution]')
    .description('Revenue projection calculator — model different customer mixes')
    .option('--churn <percent>', 'Monthly churn rate', '5')
    .option('--months <n>', 'Projection months', '12')
    .action(renderPricingCalcView);
}
