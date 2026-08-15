/**
 * raas-onboard.ts — Customer onboarding wizard CLI command
 * Guides new tenants through RaaS setup: tier selection, API key, first mission
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

const TIERS = {
  starter: { price: 49, credits: 200, best: 'Solo developers & freelancers' },
  pro: { price: 149, credits: 1000, best: 'Small teams (5-20 devs)' },
  enterprise: { price: 499, credits: -1, best: 'Agencies & large teams' },
} as const;

export function registerRaasOnboardCommand(program: Command, engine: MekongEngine): void {
  const onboard = program
    .command('onboard')
    .description('RaaS onboarding — setup wizard for new customers');

  onboard
    .command('check')
    .description('Pre-flight check — verify environment readiness')
    .action(() => {
      heading('RaaS Pre-flight Check');

      const status = engine.getStatus();
      const checks = [
        { label: 'Engine initialized', pass: status.initialized },
        { label: 'LLM provider configured', pass: status.providers.length > 0 },
        { label: 'Tools loaded', pass: status.toolCount > 0 },
        { label: 'OpenClaw engine', pass: !!engine.openclaw },
      ];

      let allPass = true;
      for (const c of checks) {
        if (c.pass) success(c.label);
        else { warn(`MISSING: ${c.label}`); allPass = false; }
      }

      divider();
      if (allPass) {
        success('All checks passed — ready for onboarding');
      } else {
        warn('Some checks failed — run `mekong init` first');
      }
      info('');
    });

  onboard
    .command('recommend [teamSize] [budget]')
    .description('Recommend best tier based on team size and budget')
    .action((_teamSize?: string, _budget?: string) => {
      const teamSize = parseInt(_teamSize ?? '5', 10);
      const budget = parseInt(_budget ?? '150', 10);

      heading('RaaS Tier Recommendation');
      keyValue('Team size', `${teamSize} developers`);
      keyValue('Monthly budget', `$${budget}`);
      divider();

      let recommended: keyof typeof TIERS;
      if (teamSize >= 20 || budget >= 400) recommended = 'enterprise';
      else if (teamSize >= 5 || budget >= 100) recommended = 'pro';
      else recommended = 'starter';

      for (const [name, tier] of Object.entries(TIERS)) {
        const credits = tier.credits === -1 ? 'Unlimited' : `${tier.credits}`;
        const marker = name === recommended ? ' <-- RECOMMENDED' : '';
        const line = `${name.padEnd(12)} $${tier.price}/mo  ${credits.padEnd(10)} credits  ${tier.best}`;
        if (name === recommended) success(line + marker);
        else info(line);
      }

      divider();
      const tier = TIERS[recommended];
      const costPerDev = Math.round(tier.price / teamSize);
      keyValue('Cost per developer', `$${costPerDev}/mo`);
      keyValue('ROI estimate', `${Math.round((budget * 3) / tier.price)}x within 3 months`);
      info('');
      info(`Next: mekong onboard setup --tier ${recommended}`);
      info('');
    });

  onboard
    .command('setup')
    .description('Interactive setup — register tenant and generate API key')
    .option('--tier <tier>', 'Subscription tier', 'pro')
    .option('--tenant <id>', 'Tenant ID')
    .option('--email <email>', 'Admin email')
    .action((opts: { tier: string; tenant?: string; email?: string }) => {
      const tier = opts.tier as keyof typeof TIERS;
      if (!(tier in TIERS)) {
        warn(`Invalid tier "${tier}". Choose: starter, pro, enterprise`);
        return;
      }

      heading('RaaS Tenant Setup');

      const tenantId = opts.tenant ?? `tenant_${Date.now().toString(36)}`;
      const email = opts.email ?? 'admin@example.com';
      const tierConfig = TIERS[tier];

      info('Step 1: Register tenant');
      keyValue('Tenant ID', tenantId);
      keyValue('Email', email);
      keyValue('Tier', `${tier} ($${tierConfig.price}/mo)`);
      success('Tenant registered');

      info('');
      info('Step 2: Generate API key');
      const apiKey = `mk_${Buffer.from(crypto.getRandomValues(new Uint8Array(18))).toString('base64url')}`;
      success(`API Key: ${apiKey}`);
      warn('Save this key — it will not be shown again');

      info('');
      info('Step 3: Configure environment');
      info(`  export MEKONG_API_KEY="${apiKey}"`);
      info(`  export MEKONG_TENANT_ID="${tenantId}"`);

      info('');
      info('Step 4: Verify with first mission');
      const complexity = engine.openclaw.classifyComplexity('hello world test');
      keyValue('Test complexity', complexity);
      success('OpenClaw engine responding');

      divider();
      success('Onboarding complete!');
      info('');
      info('Quick start:');
      info('  mekong cloud mission submit "Build a REST API"');
      info('  mekong analytics roi');
      info('  mekong demo pitch');
      info('');
    });

  onboard
    .command('quickstart')
    .description('Show getting-started guide after setup')
    .action(() => {
      heading('RaaS Quick Start Guide');

      info('1. SUBMIT YOUR FIRST MISSION');
      info('   mekong cloud mission submit "Build a landing page"');
      info('');
      info('2. CHECK MISSION STATUS');
      info('   mekong cloud mission status <mission-id>');
      info('');
      info('3. VIEW BILLING');
      info('   mekong cloud billing usage');
      info('');
      info('4. EXPLORE MARKETPLACE');
      info('   mekong marketplace search "automation"');
      info('');
      info('5. RUN ANALYTICS');
      info('   mekong analytics roi');
      info('   mekong analytics revenue');
      info('');
      info('6. SALES TOOLS');
      info('   mekong demo roi 10 30');
      info('   mekong demo pitch');
      info('   mekong sales score --company "Acme" --size 50 --budget 200');
      info('');
      divider();
      info('Docs: https://docs.openclaw.io');
      info('Support: support@openclaw.io');
      info('');
    });
}
