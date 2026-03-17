/**
 * roiaas.ts — ROIaaS Command Stack registration
 * Registers all 5 command levels: studio, cto, pm, dev, worker
 * Each level delegates to the level below via Gateway.delegateDown()
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { ROIAAS_LEVELS } from '../../core/gateway.js';
import type { RoiaasLevel } from '../../core/gateway.js';
import { success, error as showError, info } from '../ui/output.js';
import { withSpinner } from '../ui/spinner.js';

interface LevelCommand {
  name: string;
  description: string;
  credits: number;
  delegatesTo?: string[];
}

const STUDIO_COMMANDS: LevelCommand[] = [
  { name: 'audit', description: 'Full portfolio ROI audit across all projects', credits: 10, delegatesTo: ['cto:review'] },
  { name: 'portfolio', description: 'Portfolio dashboard — P&L, MRR, runway', credits: 5 },
  { name: 'allocate', description: 'Reallocate MCU budget across projects', credits: 3, delegatesTo: ['cto:budget'] },
  { name: 'invest', description: 'Add new project to portfolio', credits: 8, delegatesTo: ['cto:onboard', 'pm:plan'] },
  { name: 'divest', description: 'Archive/sunset a portfolio project', credits: 5, delegatesTo: ['cto:archive'] },
  { name: 'report', description: 'Generate investor report', credits: 5, delegatesTo: ['cto:scorecard'] },
  { name: 'roi', description: 'ROI scorecard across all projects', credits: 3 },
  { name: 'strategy', description: 'Strategic planning session', credits: 8, delegatesTo: ['cto:roadmap', 'pm:okr'] },
];

const CTO_COMMANDS: LevelCommand[] = [
  { name: 'review', description: 'Full project health review', credits: 5, delegatesTo: ['dev:audit', 'dev:test'] },
  { name: 'roadmap', description: 'Technical roadmap generation', credits: 5, delegatesTo: ['pm:plan'] },
  { name: 'budget', description: 'MCU budget allocation within project', credits: 3 },
  { name: 'architect', description: 'Architecture decision record (ADR)', credits: 5, delegatesTo: ['dev:design'] },
  { name: 'onboard', description: 'Onboard new project to OpenClaw', credits: 8, delegatesTo: ['pm:plan', 'dev:scaffold'] },
  { name: 'archive', description: 'Archive project', credits: 3, delegatesTo: ['worker:backup'] },
  { name: 'scorecard', description: 'CTO ROI scorecard for single project', credits: 3 },
  { name: 'deploy', description: 'Production deployment decision + execution', credits: 5, delegatesTo: ['dev:deploy', 'worker:health'] },
  { name: 'incident', description: 'Incident response orchestration', credits: 8, delegatesTo: ['dev:debug', 'worker:rollback'] },
  { name: 'team', description: 'Team capacity planning and task routing', credits: 3, delegatesTo: ['pm:sprint'] },
];

const PM_COMMANDS: LevelCommand[] = [
  { name: 'plan', description: 'Create implementation plan with phases', credits: 5 },
  { name: 'sprint', description: 'Sprint planning — backlog to sprint tasks', credits: 3, delegatesTo: ['dev:feature'] },
  { name: 'standup', description: 'Daily standup report', credits: 1 },
  { name: 'okr', description: 'Set/review OKRs and key results', credits: 3 },
  { name: 'milestone', description: 'Milestone tracking and status', credits: 2 },
  { name: 'backlog', description: 'Backlog grooming — prioritize and estimate', credits: 3 },
  { name: 'retro', description: 'Sprint retrospective', credits: 3 },
  { name: 'scope', description: 'Scope definition and boundary setting', credits: 3 },
  { name: 'delegate', description: 'Break task and delegate to dev level', credits: 3, delegatesTo: ['dev:feature', 'dev:fix'] },
];

const DEV_COMMANDS: LevelCommand[] = [
  { name: 'feature', description: 'Implement a feature end-to-end', credits: 8, delegatesTo: ['worker:code', 'worker:test'] },
  { name: 'fix', description: 'Fix a bug', credits: 3, delegatesTo: ['worker:code', 'worker:test'] },
  { name: 'test', description: 'Run and fix test suite', credits: 3, delegatesTo: ['worker:test'] },
  { name: 'audit', description: 'Code quality audit', credits: 3, delegatesTo: ['worker:scan'] },
  { name: 'deploy', description: 'Deploy to target environment', credits: 3, delegatesTo: ['worker:build', 'worker:push'] },
  { name: 'debug', description: 'Debug with root cause analysis', credits: 5, delegatesTo: ['worker:trace', 'worker:log'] },
  { name: 'review', description: 'Code review', credits: 3, delegatesTo: ['worker:scan'] },
  { name: 'scaffold', description: 'Scaffold new component/module', credits: 3, delegatesTo: ['worker:code'] },
  { name: 'refactor', description: 'Refactor code with safety checks', credits: 5, delegatesTo: ['worker:code', 'worker:test'] },
  { name: 'design', description: 'Technical design document', credits: 3 },
];

const WORKER_COMMANDS: LevelCommand[] = [
  { name: 'code', description: 'Write/edit specific files', credits: 1 },
  { name: 'test', description: 'Run specific test suite', credits: 1 },
  { name: 'build', description: 'Run build pipeline', credits: 1 },
  { name: 'scan', description: 'Static analysis scan', credits: 1 },
  { name: 'push', description: 'Git push to remote', credits: 1 },
  { name: 'commit', description: 'Git commit with conventional message', credits: 1 },
  { name: 'health', description: 'Health check — HTTP, process, resource', credits: 1 },
  { name: 'rollback', description: 'Rollback to previous deployment', credits: 2 },
  { name: 'backup', description: 'Backup files/db to storage', credits: 2 },
  { name: 'log', description: 'Fetch and analyze logs', credits: 1 },
  { name: 'trace', description: 'Trace execution path', credits: 1 },
  { name: 'exec', description: 'Execute shell command (sandboxed)', credits: 1 },
];

const LEVEL_COMMANDS: Record<RoiaasLevel, LevelCommand[]> = {
  studio: STUDIO_COMMANDS,
  cto: CTO_COMMANDS,
  pm: PM_COMMANDS,
  dev: DEV_COMMANDS,
  worker: WORKER_COMMANDS,
};

function registerLevelCommands(
  program: Command,
  engine: MekongEngine,
  level: RoiaasLevel,
  commands: LevelCommand[],
): void {
  const levelDef = ROIAAS_LEVELS[level];
  const levelCmd = program
    .command(level)
    .description(`${levelDef.icon} ${levelDef.chapter} — ROIaaS ${level.toUpperCase()} commands`);

  for (const cmd of commands) {
    levelCmd
      .command(`${cmd.name} [args...]`)
      .description(`${cmd.description} (${cmd.credits} MCU)`)
      .option('-p, --project <path>', 'Target project path')
      .option('--dry-run', 'Show what would execute without running')
      .action(async (args: string[], opts: { project?: string; dryRun?: boolean }) => {
        const goal = args.join(' ');
        const fullCommand = `${level}:${cmd.name}`;

        if (opts.dryRun) {
          info(`[DRY RUN] ${fullCommand} — ${cmd.credits} MCU`);
          if (cmd.delegatesTo?.length) {
            info(`  Delegates to: ${cmd.delegatesTo.join(', ')}`);
          }
          return;
        }

        try {
          const result = await withSpinner(
            `${levelDef.icon} ${fullCommand}: ${goal || cmd.description}`,
            () => engine.gateway.dispatch(fullCommand, [goal, ...(opts.project ? ['--project', opts.project] : [])]),
          );
          success(`${fullCommand} completed (${cmd.credits} MCU)`);
          console.log(result);
        } catch (err) {
          showError(err instanceof Error ? err.message : String(err));
          process.exitCode = 1;
        }
      });
  }
}

export function registerRoiaasCommands(program: Command, engine: MekongEngine): void {
  for (const [level, commands] of Object.entries(LEVEL_COMMANDS)) {
    registerLevelCommands(program, engine, level as RoiaasLevel, commands);
  }
}
