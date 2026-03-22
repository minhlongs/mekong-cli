/**
 * sales-lead.ts — Sales lead qualification CLI commands
 * Wires SalesBot from @mekong/raas-marketplace into CLI for enterprise sales
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

interface LeadInput {
  name: string;
  email: string;
  company: string;
  size: number;
  budget: number;
  useCase: string;
}

function qualifyLead(lead: LeadInput): { score: number; tier: string; reasoning: string } {
  let score = 0;
  const reasons: string[] = [];

  if (lead.size >= 500) { score += 40; reasons.push('large enterprise'); }
  else if (lead.size >= 50) { score += 25; reasons.push('mid-market'); }
  else if (lead.size >= 10) { score += 15; reasons.push('small business'); }
  else { score += 5; reasons.push('solo/micro'); }

  if (lead.budget >= 400) { score += 40; reasons.push('enterprise budget'); }
  else if (lead.budget >= 100) { score += 25; reasons.push('pro budget'); }
  else if (lead.budget >= 40) { score += 15; reasons.push('starter budget'); }
  else { score += 5; reasons.push('limited budget'); }

  const words = lead.useCase.split(' ').length;
  if (words >= 10) { score += 20; reasons.push('clear use case'); }
  else if (words >= 5) { score += 12; reasons.push('partial use case'); }
  else { score += 5; reasons.push('vague use case'); }

  let tier = 'starter';
  if (lead.size >= 200 || lead.budget >= 400) tier = 'enterprise';
  else if (lead.size >= 20 || lead.budget >= 100) tier = 'pro';

  return { score, tier, reasoning: reasons.join(', ') };
}

export function registerSalesLeadCommand(program: Command): void {
  const sales = program
    .command('sales')
    .description('Sales tools — lead qualification, scoring, pipeline');

  sales
    .command('score')
    .description('Score and qualify a lead')
    .option('--company <name>', 'Company name', 'Unknown')
    .option('--name <name>', 'Contact name', 'Contact')
    .option('--email <email>', 'Contact email', 'contact@example.com')
    .option('--size <n>', 'Company headcount', '10')
    .option('--budget <usd>', 'Monthly budget USD', '100')
    .option('--use-case <text>', 'Use case description', 'AI automation for business')
    .action((opts: { company: string; name: string; email: string; size: string; budget: string; useCase: string }) => {
      const lead: LeadInput = {
        name: opts.name,
        email: opts.email,
        company: opts.company,
        size: parseInt(opts.size, 10),
        budget: parseInt(opts.budget, 10),
        useCase: opts.useCase,
      };

      const result = qualifyLead(lead);

      heading('Lead Qualification Report');
      keyValue('Company', lead.company);
      keyValue('Contact', `${lead.name} <${lead.email}>`);
      keyValue('Team size', `${lead.size} people`);
      keyValue('Budget', `$${lead.budget}/mo`);
      keyValue('Use case', lead.useCase);
      divider();

      const scoreBar = '\u2588'.repeat(Math.round(result.score / 5));
      const scoreLabel = result.score >= 80 ? 'HOT' : result.score >= 50 ? 'WARM' : 'COLD';

      if (result.score >= 80) success(`Score: ${result.score}/100 [${scoreBar}] ${scoreLabel}`);
      else if (result.score >= 50) info(`Score: ${result.score}/100 [${scoreBar}] ${scoreLabel}`);
      else warn(`Score: ${result.score}/100 [${scoreBar}] ${scoreLabel}`);

      keyValue('Recommended tier', result.tier.toUpperCase());
      keyValue('Reasoning', result.reasoning);
      divider();

      info('Suggested actions:');
      if (result.score >= 80) {
        info('  1. Schedule enterprise demo call immediately');
        info('  2. Send custom proposal: mekong sales proposal --company ...');
        info('  3. Assign to senior AE');
      } else if (result.score >= 50) {
        info('  1. Send ROI calculator: mekong demo roi ' + lead.size + ' 20');
        info('  2. Add to nurture sequence');
        info('  3. Follow up in 3 days');
      } else {
        info('  1. Add to self-serve onboarding');
        info('  2. Send starter tier info');
        info('  3. Monitor engagement');
      }
      info('');
    });

  sales
    .command('pipeline')
    .description('Show sales pipeline summary')
    .action(() => {
      heading('Sales Pipeline Summary');

      info('Stage           | Count | Value     | Avg Score');
      divider();
      info('Prospect        |   --  |   --      |   --');
      info('Qualified       |   --  |   --      |   --');
      info('Demo Scheduled  |   --  |   --      |   --');
      info('Proposal Sent   |   --  |   --      |   --');
      info('Closed Won      |   --  |   --      |   --');
      divider();
      warn('No CRM data yet. Use `mekong sales score` to add leads.');
      info('');
      info('Quick start:');
      info('  mekong sales score --company "Acme" --size 50 --budget 200');
      info('  mekong sales score --company "StartupX" --size 5 --budget 50');
      info('');
    });

  sales
    .command('proposal')
    .description('Generate sales proposal for a lead')
    .option('--company <name>', 'Company name', 'Acme Corp')
    .option('--name <name>', 'Contact name', 'Decision Maker')
    .option('--size <n>', 'Team size', '20')
    .option('--budget <usd>', 'Budget USD/mo', '200')
    .option('--use-case <text>', 'Use case', 'AI-powered business automation')
    .action((opts: { company: string; name: string; size: string; budget: string; useCase: string }) => {
      const size = parseInt(opts.size, 10);
      const budget = parseInt(opts.budget, 10);

      let tier = 'starter';
      let price = 49;
      if (size >= 200 || budget >= 400) { tier = 'enterprise'; price = 499; }
      else if (size >= 20 || budget >= 100) { tier = 'pro'; price = 149; }

      heading(`Custom Proposal for ${opts.company}`);
      info(`Prepared for: ${opts.name}`);
      info(`Company Size: ${size} people | Budget: $${budget}/mo`);
      divider();
      info('');
      success(`Recommended Plan: ${tier.toUpperCase()} ($${price}/mo)`);
      info('');
      info('What You Get:');
      info('  - AI-powered mission orchestration (OpenClaw Engine)');
      info('  - Plan -> Execute -> Verify automation loop');
      info('  - 342+ CLI commands across 5 business layers');
      if (tier === 'enterprise') {
        info('  - Unlimited credits');
        info('  - Priority support + dedicated CSM');
        info('  - Custom integrations');
      } else if (tier === 'pro') {
        info('  - 1,000 credits/month');
        info('  - Email support');
        info('  - Marketplace access');
      } else {
        info('  - 200 credits/month');
        info('  - Community support');
      }
      info('');
      info(`ROI Projection for ${opts.company}:`);
      const hourlyRate = 50;
      const savedHours = size * 5; // 5h/dev/week automated
      const monthlySaving = savedHours * hourlyRate * 4;
      keyValue('Hours saved/month', `${savedHours * 4}h`);
      keyValue('Cost saved/month', `$${monthlySaving.toLocaleString()}`);
      keyValue('Mekong cost', `$${price}/mo`);
      success(`Net ROI: ${Math.round((monthlySaving - price) / price * 100)}%`);
      info('');
      info('Next Steps:');
      info('  1. Start 14-day free trial');
      info('  2. Book onboarding: calendly.com/openclaw/onboard');
      info('  3. Questions? support@openclaw.io');
      info('');
    });
}
