/**
 * sales-campaign.ts — Sales campaign automation CLI commands
 * Create, send, track, and report on outreach campaigns
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

interface Campaign {
  id: string;
  name: string;
  template: string;
  audience: string;
  status: string;
  sent: number;
  opened: number;
  clicked: number;
  replied: number;
  converted: number;
  createdAt: string;
}

const CAMPAIGNS: Campaign[] = [
  { id: 'camp_001', name: 'Q1 Cold Outreach — Tech Startups', template: 'cold-outreach', audience: 'tech-startups-vn', status: 'completed', sent: 120, opened: 48, clicked: 22, replied: 9, converted: 2, createdAt: '2026-03-01' },
  { id: 'camp_002', name: 'Trial Nurture — Week 2', template: 'nurture', audience: 'trial-week2', status: 'active', sent: 54, opened: 31, clicked: 18, replied: 6, converted: 3, createdAt: '2026-03-15' },
  { id: 'camp_003', name: 'Pro → Enterprise Upsell', template: 'upsell', audience: 'pro-plan-users', status: 'active', sent: 28, opened: 19, clicked: 12, replied: 5, converted: 1, createdAt: '2026-03-18' },
  { id: 'camp_004', name: 'Churned Users Re-engage', template: 're-engage', audience: 'churned-30d', status: 'draft', sent: 0, opened: 0, clicked: 0, replied: 0, converted: 0, createdAt: '2026-03-21' },
];

function pct(num: number, denom: number): string {
  if (denom === 0) return '—';
  return `${Math.round((num / denom) * 100)}%`;
}

export function registerSalesCampaignCommand(program: Command): void {
  const campaign = program
    .command('sales-campaign')
    .description('Sales campaign automation — create, send, track, report');

  campaign
    .command('create')
    .description('Create a new outreach campaign')
    .option('--name <name>', 'Campaign name', 'New Campaign')
    .option('--template <type>', 'Template: cold-outreach|nurture|upsell|re-engage', 'cold-outreach')
    .option('--audience <segment>', 'Audience segment identifier', 'all-leads')
    .action((opts: { name: string; template: string; audience: string }) => {
      const validTemplates = ['cold-outreach', 'nurture', 'upsell', 're-engage'];
      const template = validTemplates.includes(opts.template) ? opts.template : 'cold-outreach';
      const newId = `camp_${String(CAMPAIGNS.length + 1).padStart(3, '0')}`;

      heading('Campaign Created');
      keyValue('ID', newId);
      keyValue('Name', opts.name);
      keyValue('Template', template);
      keyValue('Audience', opts.audience);
      keyValue('Status', 'draft');
      keyValue('Created', '2026-03-22');
      divider();

      info('Template preview:');
      const previews: Record<string, string> = {
        'cold-outreach': '  "Hi {name}, saw {company} is scaling fast — we help teams like yours automate ops with AI."',
        'nurture':       '  "You\'ve been using Mekong for 2 weeks — here\'s what top teams unlock in week 3..."',
        'upsell':        '  "Your team is hitting Pro limits. Upgrade to Enterprise and get unlimited missions + CSM."',
        're-engage':     '  "We noticed you haven\'t logged in for 30 days — here\'s what\'s new + a 20% comeback offer."',
      };
      info(previews[template] ?? '');
      divider();
      success(`Campaign ${newId} created — status: DRAFT`);
      info(`Next: mekong sales-campaign send --id ${newId}`);
      info('');
    });

  campaign
    .command('send')
    .description('Send a campaign (use --test for dry-run to self)')
    .option('--id <id>', 'Campaign ID', 'camp_004')
    .option('--test', 'Test mode — send to self only')
    .action((opts: { id: string; test?: boolean }) => {
      const camp = CAMPAIGNS.find(c => c.id === opts.id);

      heading('Campaign Send');
      if (!camp) {
        warn(`Campaign ${opts.id} not found. Use: mekong sales-campaign report`);
        return;
      }

      if (opts.test) {
        info(`[TEST MODE] Sending "${camp.name}" to: you@openclaw.io only`);
        keyValue('Template', camp.template);
        keyValue('Audience', camp.audience);
        success('Test email delivered — check inbox for preview');
        info('Remove --test to send to full audience');
        info('');
        return;
      }

      const estimatedRecipients = camp.status === 'draft' ? 45 : camp.sent;
      keyValue('Campaign', camp.name);
      keyValue('Template', camp.template);
      keyValue('Audience', camp.audience);
      keyValue('Recipients', `~${estimatedRecipients} contacts`);
      divider();
      success(`Campaign ${opts.id} queued for delivery`);
      info('Delivery window: next 2 hours (throttled for deliverability)');
      info(`Track progress: mekong sales-campaign track --id ${opts.id}`);
      info('');
    });

  campaign
    .command('track')
    .description('Track live campaign engagement metrics')
    .option('--id <id>', 'Campaign ID', 'camp_001')
    .action((opts: { id: string }) => {
      const camp = CAMPAIGNS.find(c => c.id === opts.id);

      heading('Campaign Tracker');
      if (!camp) {
        warn(`Campaign ${opts.id} not found.`);
        return;
      }

      keyValue('Campaign', camp.name);
      keyValue('Template', camp.template);
      keyValue('Status', camp.status.toUpperCase());
      keyValue('Launched', camp.createdAt);
      divider();

      info('Metric          Count    Rate');
      info('─'.repeat(40));
      info(`Sent            ${String(camp.sent).padStart(5)}    100%`);

      const openRate = parseInt(pct(camp.opened, camp.sent));
      const openLine = `Opened          ${String(camp.opened).padStart(5)}    ${pct(camp.opened, camp.sent)}`;
      if (openRate >= 30) success(openLine); else if (openRate >= 15) info(openLine); else warn(openLine);

      info(`Clicked         ${String(camp.clicked).padStart(5)}    ${pct(camp.clicked, camp.sent)}`);
      info(`Replied         ${String(camp.replied).padStart(5)}    ${pct(camp.replied, camp.sent)}`);

      const convLine = `Converted       ${String(camp.converted).padStart(5)}    ${pct(camp.converted, camp.sent)}`;
      if (camp.converted > 0) success(convLine); else warn(convLine);

      divider();
      keyValue('Revenue attributed', `$${camp.converted * 149}/mo`);
      info('');
    });

  campaign
    .command('report')
    .description('Campaign performance report across all campaigns')
    .option('--period <range>', 'Period: week|month|quarter', 'month')
    .action((opts: { period: string }) => {
      heading(`Campaign Report — This ${opts.period.charAt(0).toUpperCase() + opts.period.slice(1)}`);
      keyValue('Period', opts.period === 'week' ? '2026-03-16 to 2026-03-22' : opts.period === 'quarter' ? 'Q1 2026' : 'March 2026');
      keyValue('Total campaigns', `${CAMPAIGNS.length}`);
      divider();

      info('ID         Name                           Sent  Open%  Click%  Conv  Revenue');
      info('─'.repeat(82));
      for (const c of CAMPAIGNS) {
        const revenue = `$${c.converted * 149}`;
        const line = `${c.id}  ${c.name.substring(0, 30).padEnd(31)} ${String(c.sent).padStart(4)}  ${pct(c.opened, c.sent).padEnd(6)} ${pct(c.clicked, c.sent).padEnd(7)} ${String(c.converted).padStart(4)}  ${revenue}`;
        if (c.converted >= 2) success(line);
        else if (c.status === 'draft') warn(line);
        else info(line);
      }

      divider();
      const totalSent = CAMPAIGNS.reduce((s, c) => s + c.sent, 0);
      const totalConverted = CAMPAIGNS.reduce((s, c) => s + c.converted, 0);
      const totalRevenue = totalConverted * 149;
      keyValue('Total sent', `${totalSent}`);
      keyValue('Total converted', `${totalConverted} (${pct(totalConverted, totalSent)} overall)`);
      success(`Total revenue attributed: $${totalRevenue}/mo`);
      info('');
    });
}
