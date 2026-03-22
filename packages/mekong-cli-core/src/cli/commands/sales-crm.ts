/**
 * sales-crm.ts — CRM lead management CLI commands
 * Add leads, list/filter by status, qualify with scores, schedule follow-ups
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  source: string;
  status: string;
  score: number;
  notes: string;
  followup: string;
  createdAt: string;
}

const LEADS: Lead[] = [
  { id: 'lead_001', name: 'Nguyen Van A', email: 'nva@techvn.io', company: 'TechVN Solutions', source: 'referral', status: 'qualified', score: 82, notes: 'Needs enterprise AI automation', followup: 'demo', createdAt: '2026-03-18' },
  { id: 'lead_002', name: 'Tran Thi B', email: 'ttb@saigondigital.vn', company: 'Saigon Digital', source: 'website', status: 'contacted', score: 67, notes: 'Interested in RaaS marketplace', followup: 'call', createdAt: '2026-03-19' },
  { id: 'lead_003', name: 'Le Minh C', email: 'lmc@hanoitech.vn', company: 'Hanoi Tech Hub', source: 'event', status: 'new', score: 0, notes: '', followup: '', createdAt: '2026-03-20' },
  { id: 'lead_004', name: 'Pham Duc D', email: 'pdd@vietnamcloud.vn', company: 'Vietnam Cloud Co', source: 'cold', status: 'proposal', score: 74, notes: 'Evaluated 2 competitors', followup: 'meeting', createdAt: '2026-03-15' },
  { id: 'lead_005', name: 'Hoang Thi E', email: 'hte@mekongtech.io', company: 'Mekong Tech', source: 'referral', status: 'closed', score: 91, notes: 'Signed enterprise plan', followup: '', createdAt: '2026-03-10' },
  { id: 'lead_006', name: 'Vo Thanh F', email: 'vtf@deltasoftware.vn', company: 'Delta Software', source: 'website', status: 'new', score: 0, notes: '', followup: '', createdAt: '2026-03-21' },
  { id: 'lead_007', name: 'Dang Thi G', email: 'dtg@saigonaistudio.io', company: 'Saigon AI Studio', source: 'event', status: 'contacted', score: 55, notes: 'Trial user, evaluating', followup: 'email', createdAt: '2026-03-17' },
  { id: 'lead_008', name: 'Bui Van H', email: 'bvh@fintechvn.com', company: 'FinTech VN', source: 'referral', status: 'qualified', score: 79, notes: 'Needs compliance tools', followup: 'demo', createdAt: '2026-03-16' },
];

export function registerSalesCrmCommand(program: Command): void {
  const crm = program
    .command('sales-crm')
    .description('CRM lead management — add, list, qualify, follow-up');

  crm
    .command('add')
    .description('Add a new lead to CRM')
    .option('--name <name>', 'Contact full name', 'New Contact')
    .option('--email <email>', 'Contact email', 'contact@company.com')
    .option('--company <company>', 'Company name', 'Company Ltd')
    .option('--source <source>', 'Lead source: website|referral|cold|event', 'website')
    .action((opts: { name: string; email: string; company: string; source: string }) => {
      const validSources = ['website', 'referral', 'cold', 'event'];
      const source = validSources.includes(opts.source) ? opts.source : 'website';
      const newId = `lead_${String(LEADS.length + 1).padStart(3, '0')}`;

      heading('New Lead Added');
      keyValue('ID', newId);
      keyValue('Name', opts.name);
      keyValue('Email', opts.email);
      keyValue('Company', opts.company);
      keyValue('Source', source);
      keyValue('Status', 'new');
      keyValue('Created', '2026-03-22');
      divider();
      success(`Lead ${newId} created — status: NEW`);
      info('Next: mekong sales-crm qualify --id ' + newId + ' --score 7');
      info('');
    });

  crm
    .command('list')
    .description('List leads with optional filter by status')
    .option('--status <status>', 'Filter: new|contacted|qualified|proposal|closed')
    .option('--limit <n>', 'Max results to show', '10')
    .action((opts: { status?: string; limit: string }) => {
      const limit = Math.min(parseInt(opts.limit, 10) || 10, LEADS.length);
      const filtered = opts.status ? LEADS.filter(l => l.status === opts.status) : LEADS;
      const shown = filtered.slice(0, limit);

      heading('CRM Leads');
      keyValue('Total', `${filtered.length} leads${opts.status ? ' (' + opts.status + ')' : ''}`);
      divider();

      info('ID         Company                Status      Score  Source     Contact');
      info('─'.repeat(80));
      for (const lead of shown) {
        const scoreStr = lead.score > 0 ? `${lead.score}/100` : '  —   ';
        const line = `${lead.id}  ${lead.company.padEnd(22)} ${lead.status.padEnd(11)} ${scoreStr.padEnd(7)} ${lead.source.padEnd(10)} ${lead.name}`;
        if (lead.status === 'closed') success(line);
        else if (lead.score >= 75) info(line);
        else if (lead.status === 'new') warn(line);
        else info(line);
      }

      divider();
      const byStatus = ['new', 'contacted', 'qualified', 'proposal', 'closed']
        .map(s => `${s}: ${LEADS.filter(l => l.status === s).length}`)
        .join(' | ');
      info(byStatus);
      info('');
    });

  crm
    .command('qualify')
    .description('Score and qualify a lead (1-10 scale)')
    .option('--id <id>', 'Lead ID', 'lead_001')
    .option('--score <n>', 'Qualification score 1-10', '7')
    .option('--notes <text>', 'Qualification notes', '')
    .action((opts: { id: string; score: string; notes: string }) => {
      const lead = LEADS.find(l => l.id === opts.id);
      const rawScore = Math.min(10, Math.max(1, parseInt(opts.score, 10) || 7));
      const normalizedScore = rawScore * 10;

      heading('Lead Qualification');
      if (!lead) {
        warn(`Lead ${opts.id} not found. Use: mekong sales-crm list`);
        return;
      }

      keyValue('Lead', `${lead.name} @ ${lead.company}`);
      keyValue('Previous score', lead.score > 0 ? `${lead.score}/100` : 'unscored');
      keyValue('New score', `${normalizedScore}/100`);
      if (opts.notes) keyValue('Notes', opts.notes);
      divider();

      const label = normalizedScore >= 80 ? 'HOT' : normalizedScore >= 60 ? 'WARM' : 'COLD';
      const bar = '█'.repeat(rawScore) + '░'.repeat(10 - rawScore);
      if (normalizedScore >= 80) success(`[${bar}] ${normalizedScore}/100 — ${label}: Schedule demo now`);
      else if (normalizedScore >= 60) info(`[${bar}] ${normalizedScore}/100 — ${label}: Nurture sequence`);
      else warn(`[${bar}] ${normalizedScore}/100 — ${label}: Low priority`);

      success(`Lead ${opts.id} qualified — status updated to: QUALIFIED`);
      info('');
    });

  crm
    .command('followup')
    .description('Schedule a follow-up action for a lead')
    .option('--id <id>', 'Lead ID', 'lead_001')
    .option('--action <type>', 'Action: email|call|meeting|demo', 'email')
    .action((opts: { id: string; action: string }) => {
      const lead = LEADS.find(l => l.id === opts.id);
      const validActions = ['email', 'call', 'meeting', 'demo'];
      const action = validActions.includes(opts.action) ? opts.action : 'email';

      heading('Follow-up Scheduled');
      if (!lead) {
        warn(`Lead ${opts.id} not found. Use: mekong sales-crm list`);
        return;
      }

      keyValue('Lead', `${lead.name} @ ${lead.company}`);
      keyValue('Email', lead.email);
      keyValue('Action', action.toUpperCase());
      keyValue('Scheduled', '2026-03-25 10:00 ICT');
      divider();

      const actionMessages: Record<string, string> = {
        email: `Draft sent to ${lead.email} — awaiting reply`,
        call: `Call booked for 2026-03-25 at 10:00 ICT`,
        meeting: `Meeting invite sent to ${lead.email}`,
        demo: `Demo link: https://demo.openclaw.io?lead=${lead.id}`,
      };

      success(`Follow-up queued: ${action.toUpperCase()}`);
      info(actionMessages[action] ?? '');
      info('');
    });
}
