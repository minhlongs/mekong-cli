/**
 * `mekong workflow` — Automation workflow management subcommands (Wave 51).
 *
 *   mekong workflow create         Create new workflow from template
 *   mekong workflow list           List all workflows with status
 *   mekong workflow run <id>       Execute a workflow by ID
 *   mekong workflow history        Show execution history
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

/** Mock workflow data for demo output */
const MOCK_WORKFLOWS = [
  { id: 'wf-001', name: 'Onboarding khách hàng mới',   status: 'active', steps: 5, lastRun: '2026-03-21' },
  { id: 'wf-002', name: 'Xử lý đơn hàng tự động',      status: 'active', steps: 8, lastRun: '2026-03-22' },
  { id: 'wf-003', name: 'Báo cáo doanh thu hàng ngày', status: 'paused', steps: 3, lastRun: '2026-03-20' },
  { id: 'wf-004', name: 'Follow-up lead tự động',       status: 'draft',  steps: 6, lastRun: 'never'      },
];

const MOCK_HISTORY = [
  { runId: 'run-091', name: 'Onboarding khách hàng mới',   status: 'success', duration: '1m 23s', credits: 2 },
  { runId: 'run-090', name: 'Xử lý đơn hàng tự động',     status: 'success', duration: '0m 47s', credits: 3 },
  { runId: 'run-089', name: 'Báo cáo doanh thu hàng ngày', status: 'failed',  duration: '0m 12s', credits: 1 },
  { runId: 'run-088', name: 'Follow-up lead tự động',      status: 'success', duration: '2m 05s', credits: 4 },
];

const TEMPLATES = ['default', 'parallel', 'sequential'] as const;

function showEngineHealth(engine?: MekongEngine, label = 'Engine Status'): void {
  try {
    const health = engine?.openclaw?.getHealth();
    if (!health) return;
    divider();
    info(label);
    keyValue('  Uptime', `${Math.round(health.uptime / 1000)}s`);
    keyValue('  Missions completed', `${health.missionsCompleted}`);
    keyValue('  AGI score', `${health.agiScore}/100`);
    keyValue('  Circuit breaker', health.circuitBreakerState);
  } catch { /* engine not ready */ }
}

export function registerWorkflowCommand(program: Command, engine?: MekongEngine): void {
  const cmd = program.command('workflow').description('Automation workflow management');

  // ── workflow create ────────────────────────────────────────────────────────
  cmd.command('create')
    .description('Create new workflow from template')
    .option('--name <name>', 'Workflow name', 'New Workflow')
    .option('--template <template>', 'Template type (default|parallel|sequential)', 'default')
    .action((opts: { name?: string; template?: string }) => {
      const name = opts.name ?? 'New Workflow';
      const template = opts.template ?? 'default';
      if (!TEMPLATES.includes(template as typeof TEMPLATES[number])) {
        warn(`Unknown template "${template}". Valid: ${TEMPLATES.join(', ')}`);
        return;
      }
      heading('Create Workflow');
      const id = `wf-${String(Date.now()).slice(-3)}`;
      const stepsMap: Record<string, number> = { default: 4, parallel: 6, sequential: 5 };
      const steps = stepsMap[template] ?? 4;

      // Use classifyComplexity for step count recommendation
      let recommendedSteps = steps;
      try {
        const complexity = engine?.openclaw?.classifyComplexity(name);
        if (complexity === 'epic') recommendedSteps = Math.max(steps, 8);
        else if (complexity === 'complex') recommendedSteps = Math.max(steps, 6);
        if (complexity) keyValue('AI complexity estimate', complexity);
      } catch { /* engine not ready */ }

      keyValue('Workflow ID', id);
      keyValue('Name', name);
      keyValue('Template', template);
      keyValue('Steps', String(recommendedSteps));
      keyValue('Status', 'draft');
      keyValue('Created', new Date().toISOString().slice(0, 10));
      divider();
      success(`Workflow "${name}" created with ${recommendedSteps} steps`);
      info('Use: mekong workflow run <id> to execute');
    });

  // ── workflow list ──────────────────────────────────────────────────────────
  cmd.command('list')
    .description('List all workflows with status')
    .action(() => {
      heading('Workflows');
      for (const wf of MOCK_WORKFLOWS) {
        const statusTag = wf.status === 'active' ? 'ACTIVE' : wf.status === 'paused' ? 'PAUSE' : 'DRAFT ';
        console.log(`  [${statusTag}] ${wf.id}  ${wf.name.padEnd(30)} ${wf.steps} steps  last: ${wf.lastRun}`);
      }
      divider();
      info(`Total: ${MOCK_WORKFLOWS.length} workflows`);
    });

  // ── workflow run <workflow-id> ─────────────────────────────────────────────
  cmd.command('run')
    .argument('<workflow-id>', 'Workflow ID to execute')
    .description('Execute a workflow by ID')
    .action((workflowId: string) => {
      const wf = MOCK_WORKFLOWS.find(w => w.id === workflowId);
      if (!wf) {
        warn(`Workflow "${workflowId}" not found`);
        info('Use: mekong workflow list to see available workflows');
        return;
      }
      heading(`Run Workflow: ${wf.name}`);
      keyValue('Workflow ID', wf.id);
      keyValue('Steps', String(wf.steps));

      // Classify complexity before execution
      try {
        const complexity = engine?.openclaw?.classifyComplexity(wf.name);
        if (complexity) keyValue('Complexity estimate', complexity);
      } catch { /* engine not ready */ }

      divider();
      for (let i = 1; i <= wf.steps; i++) {
        console.log(`  [DONE] Step ${i}/${wf.steps}: Executing task ${i}...`);
      }
      divider();

      // Fire-and-forget: AI-assisted workflow execution analysis
      void engine?.openclaw?.submitMission({
        goal: `Analyze and optimize workflow execution: ${wf.name}`,
        complexity: 'trivial',
      });

      success(`Workflow "${wf.name}" completed successfully`);
      info('Credits used: 3 MCU');
    });

  // ── workflow history ───────────────────────────────────────────────────────
  cmd.command('history')
    .description('Show workflow execution history')
    .option('--limit <n>', 'Max records to show', '10')
    .action((opts: { limit?: string }) => {
      const limit = parseInt(opts.limit ?? '10', 10);
      heading('Workflow Execution History');
      const rows = MOCK_HISTORY.slice(0, limit);
      for (const row of rows) {
        const tag = row.status === 'success' ? 'OK  ' : 'FAIL';
        console.log(`  [${tag}] ${row.runId}  ${row.name.padEnd(30)} ${row.duration.padEnd(8)} ${row.credits} MCU`);
      }

      // Engine stats footer
      showEngineHealth(engine, 'Engine Stats');
      divider();
      info(`Showing ${rows.length} recent executions`);
    });
}
