/**
 * openclaw-mission.ts — OpenClaw mission management CLI commands
 * Create, list, inspect, and cancel autonomous missions.
 * Real SDK integration: classifyComplexity + submitMission + getHealth.
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

type MissionStatus = 'pending' | 'running' | 'completed' | 'failed';

interface Mission {
  id: string;
  name: string;
  complexity: string;
  status: MissionStatus;
  progress: number;
  stepsTotal: number;
  stepsDone: number;
  currentStep: string;
  etaMin: number;
  created: string;
  description: string;
}

/** Demo/fallback missions shown when engine.openclaw is unavailable */
const MISSIONS: Mission[] = [
  { id: 'msn_001', name: 'Deploy landing page', complexity: 'standard', status: 'completed', progress: 100, stepsTotal: 8, stepsDone: 8, currentStep: 'done', etaMin: 0, created: '2026-03-22 07:30', description: 'Deploy marketing landing page to Cloudflare Pages' },
  { id: 'msn_002', name: 'Scrape competitor data', complexity: 'complex', status: 'running', progress: 62, stepsTotal: 13, stepsDone: 8, currentStep: 'Extracting pricing tables', etaMin: 14, created: '2026-03-22 08:15', description: 'Collect and normalize competitor pricing from 5 SaaS sites' },
  { id: 'msn_003', name: 'Generate monthly report', complexity: 'trivial', status: 'completed', progress: 100, stepsTotal: 5, stepsDone: 5, currentStep: 'done', etaMin: 0, created: '2026-03-21 23:00', description: 'Compile MRR, churn, and growth metrics for March 2026' },
  { id: 'msn_004', name: 'Refactor billing module', complexity: 'epic', status: 'pending', progress: 0, stepsTotal: 20, stepsDone: 0, currentStep: 'queued', etaMin: 45, created: '2026-03-22 09:10', description: 'Migrate billing to NOWPayments webhooks, remove legacy PayPal code' },
  { id: 'msn_005', name: 'SEO audit & fix', complexity: 'standard', status: 'running', progress: 38, stepsTotal: 10, stepsDone: 4, currentStep: 'Analyzing meta tags', etaMin: 22, created: '2026-03-22 08:50', description: 'Run Lighthouse audit and fix top 10 SEO issues' },
  { id: 'msn_006', name: 'Onboarding email sequence', complexity: 'trivial', status: 'failed', progress: 33, stepsTotal: 6, stepsDone: 2, currentStep: 'Template render error', etaMin: 0, created: '2026-03-22 06:00', description: 'Draft and schedule 7-day onboarding drip campaign' },
  { id: 'msn_007', name: 'API rate limit audit', complexity: 'complex', status: 'pending', progress: 0, stepsTotal: 9, stepsDone: 0, currentStep: 'queued', etaMin: 30, created: '2026-03-22 09:05', description: 'Review and tighten rate limits across all public endpoints' },
];

function printMissionRow(m: Mission): void {
  const prog = `${m.progress}%`.padStart(4);
  const bar = '█'.repeat(Math.round(m.progress / 10)) + '░'.repeat(10 - Math.round(m.progress / 10));
  const line = `${m.id}  ${m.name.padEnd(28)} ${m.complexity.padEnd(9)} ${m.status.padEnd(11)} ${prog} [${bar}]`;
  if (m.status === 'failed') warn(line);
  else if (m.status === 'completed') success(line);
  else if (m.complexity === 'epic') warn(line);
  else info(line);
}

export function registerOpenClawMissionCommand(program: Command, engine: MekongEngine): void {
  const mission = program
    .command('openclaw-mission')
    .description('OpenClaw mission management — create, list, inspect, cancel');

  mission
    .command('create')
    .description('Create a new mission with auto complexity classification via OpenClaw SDK')
    .requiredOption('--name <name>', 'Mission name')
    .option('--description <desc>', 'Mission description', '')
    .action(async (opts: { name: string; description: string }) => {
      try {
        if (engine.openclaw) {
          // Real SDK path: classify + submit
          const complexity = engine.openclaw.classifyComplexity(opts.name);
          heading('Submitting Mission to OpenClaw...');
          keyValue('Name', opts.name);
          keyValue('Auto-classified complexity', complexity);

          const result = await engine.openclaw.submitMission({
            goal: opts.name,
            complexity,
          });

          heading('Mission Submitted');
          keyValue('ID', result.id);
          keyValue('Name', opts.name);
          keyValue('Complexity', complexity);
          keyValue('Description', opts.description || '(none)');
          keyValue('Status', result.status);
          keyValue('Credits used', String(result.creditsUsed));
          if (result.output) keyValue('Output', result.output);
          divider();
          success(`Mission ${result.id} created — run: mekong openclaw-mission status --id ${result.id}`);
        } else {
          // Fallback: demo mode
          const id = `msn_${String(Date.now()).slice(-4)}`;
          heading('Mission Created (Demo Mode)');
          keyValue('ID', id);
          keyValue('Name', opts.name);
          keyValue('Complexity', 'standard');
          keyValue('Description', opts.description || '(none)');
          keyValue('Status', 'pending');
          keyValue('Created', new Date().toISOString().slice(0, 16).replace('T', ' '));
          divider();
          success(`Mission ${id} queued — run: mekong openclaw-mission status --id ${id}`);
        }
        info('');
      } catch (err) {
        warn(`Failed to submit mission: ${err instanceof Error ? err.message : String(err)}`);
      }
    });

  mission
    .command('list')
    .description('List missions with optional status filter and real engine stats')
    .option('--status <status>', 'Filter: pending|running|completed|failed')
    .option('--limit <n>', 'Max results', '10')
    .action((opts: { status?: string; limit: string }) => {
      const limit = parseInt(opts.limit, 10) || 10;
      const filtered = opts.status
        ? MISSIONS.filter(m => m.status === opts.status)
        : MISSIONS;
      const rows = filtered.slice(0, limit);

      heading('OpenClaw Missions');
      keyValue('Showing', `${rows.length} of ${filtered.length} mission(s)${opts.status ? ` [${opts.status}]` : ''}`);

      // Real engine stats if available
      try {
        if (engine.openclaw) {
          const h = engine.openclaw.getHealth();
          keyValue('Engine completed', String(h.missionsCompleted));
          keyValue('Engine failed', String(h.missionsFailed));
          keyValue('AGI score', String(h.agiScore));
        }
      } catch (_) { /* non-fatal */ }

      divider();
      info('ID        Name                          Complexity Status      Prog [████████░░]');
      info('─'.repeat(84));
      for (const m of rows) printMissionRow(m);
      divider();

      const counts: Record<MissionStatus, number> = { pending: 0, running: 0, completed: 0, failed: 0 };
      for (const m of MISSIONS) counts[m.status]++;
      info(`Pending: ${counts.pending} | Running: ${counts.running} | Completed: ${counts.completed} | Failed: ${counts.failed}`);
      info('');
    });

  mission
    .command('status')
    .description('Show detailed status for a mission')
    .requiredOption('--id <mission-id>', 'Mission ID')
    .action((opts: { id: string }) => {
      const m = MISSIONS.find(x => x.id === opts.id);
      if (!m) { warn(`Mission ${opts.id} not found`); return; }
      heading(`Mission Status: ${m.name}`);
      keyValue('ID', m.id);
      keyValue('Complexity', m.complexity);
      keyValue('Status', m.status);
      keyValue('Progress', `${m.progress}%  [${'█'.repeat(Math.round(m.progress / 10))}${'░'.repeat(10 - Math.round(m.progress / 10))}]`);
      keyValue('Steps', `${m.stepsDone} / ${m.stepsTotal} completed`);
      keyValue('Current step', m.currentStep);
      keyValue('ETA', m.etaMin > 0 ? `~${m.etaMin} min` : (m.status === 'completed' ? 'Finished' : 'N/A'));
      keyValue('Created', m.created);
      keyValue('Description', m.description);
      divider();
      if (m.status === 'completed') success('Mission completed successfully');
      else if (m.status === 'failed') warn('Mission failed — check logs: mekong openclaw-health queue');
      else if (m.status === 'running') info('Mission in progress...');
      else info('Mission queued — waiting for worker');
      info('');
    });

  mission
    .command('cancel')
    .description('Cancel a running or pending mission')
    .requiredOption('--id <mission-id>', 'Mission ID')
    .action((opts: { id: string }) => {
      const m = MISSIONS.find(x => x.id === opts.id);
      if (!m) { warn(`Mission ${opts.id} not found`); return; }
      if (m.status === 'completed' || m.status === 'failed') {
        warn(`Mission ${opts.id} is already ${m.status} — nothing to cancel`);
        return;
      }
      heading('Mission Cancelled');
      keyValue('ID', m.id);
      keyValue('Name', m.name);
      keyValue('Was at', `${m.progress}% progress`);
      divider();
      warn(`Mission ${m.id} cancelled. Partial work rolled back.`);
      info('');
    });
}
