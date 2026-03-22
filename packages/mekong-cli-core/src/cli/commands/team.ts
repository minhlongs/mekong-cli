/**
 * `mekong team` — Agent team management subcommands (Wave 47).
 *
 *   mekong team create <name>        Create new agent team with config
 *   mekong team list                 List all teams and member count
 *   mekong team assign <team> <task> Assign task to team
 *   mekong team dashboard            Show team performance dashboard
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

/** Mock Vietnamese company teams for demo output */
const MOCK_TEAMS = [
  { name: 'Đội Kinh Doanh', members: 4, tasks: 12, completed: 9, status: 'active' },
  { name: 'Đội Kỹ Thuật', members: 6, tasks: 18, completed: 15, status: 'active' },
  { name: 'Đội Marketing', members: 3, tasks: 8, completed: 6, status: 'active' },
  { name: 'Đội Hỗ Trợ', members: 2, tasks: 5, completed: 4, status: 'idle' },
];

const MOCK_TASKS = [
  'Phân tích thị trường Q2',
  'Triển khai chiến dịch email',
  'Tối ưu hóa pipeline bán hàng',
  'Báo cáo hiệu suất tháng 3',
];

export function registerTeamCommand(program: Command, engine?: MekongEngine): void {
  const cmd = program.command('team').description('Agent team management');

  // ── team create <name> ─────────────────────────────────────────────────────
  cmd.command('create')
    .argument('<name>', 'Team name')
    .description('Create new agent team with config')
    .option('--members <count>', 'Initial member count', '3')
    .action((name: string, opts: { members?: string }) => {
      heading('Create Team');
      const memberCount = parseInt(opts.members ?? '3', 10);
      keyValue('Team Name', name);
      keyValue('Members', String(memberCount));
      keyValue('Status', 'active');
      keyValue('Created', new Date().toISOString().slice(0, 10));
      divider();
      success(`Team "${name}" created with ${memberCount} members`);
      info('Use: mekong team assign <team> <task> to assign work');

      // Fire-and-forget: AI team optimization recommendations
      try {
        void engine?.openclaw?.submitMission({
          goal: `Analyze optimal configuration for new agent team "${name}" with ${memberCount} members`,
          complexity: 'trivial',
        });
      } catch { /* engine not ready */ }
    });

  // ── team list ──────────────────────────────────────────────────────────────
  cmd.command('list')
    .description('List all teams and member count')
    .option('--status <status>', 'Filter by status (active|idle)')
    .action((opts: { status?: string }) => {
      heading('Agent Teams');
      const teams = opts.status
        ? MOCK_TEAMS.filter(t => t.status === opts.status)
        : MOCK_TEAMS;
      if (teams.length === 0) {
        warn('No teams found');
        return;
      }
      for (const t of teams) {
        const completion = Math.round((t.completed / t.tasks) * 100);
        info(`  [${t.status === 'active' ? 'ACTIVE' : 'IDLE  '}] ${t.name.padEnd(20)} ${t.members} members  ${t.completed}/${t.tasks} tasks (${completion}%)`);
      }
      divider();
      info(`Total: ${teams.length} teams`);
    });

  // ── team assign <team> <task> ──────────────────────────────────────────────
  cmd.command('assign')
    .argument('<team>', 'Team name or ID')
    .argument('<task>', 'Task description or ID')
    .description('Assign task to team')
    .option('--priority <level>', 'Priority level (low|normal|high)', 'normal')
    .action((team: string, task: string, opts: { priority?: string }) => {
      heading('Assign Task');
      keyValue('Team', team);
      keyValue('Task', task);
      keyValue('Priority', opts.priority ?? 'normal');
      keyValue('Assigned At', new Date().toISOString());

      // Task complexity estimate via OpenClaw
      try {
        const complexity = engine?.openclaw?.classifyComplexity(task);
        if (complexity) keyValue('Complexity Estimate', complexity);
      } catch { /* engine not ready */ }

      divider();
      success(`Task "${task}" assigned to team "${team}"`);
      info(`Priority: ${opts.priority ?? 'normal'}`);
    });

  // ── team dashboard ─────────────────────────────────────────────────────────
  cmd.command('dashboard')
    .description('Show team performance dashboard')
    .action(() => {
      heading('Team Performance Dashboard');
      const totalMembers = MOCK_TEAMS.reduce((s, t) => s + t.members, 0);
      const totalTasks = MOCK_TEAMS.reduce((s, t) => s + t.tasks, 0);
      const totalCompleted = MOCK_TEAMS.reduce((s, t) => s + t.completed, 0);
      const overallRate = Math.round((totalCompleted / totalTasks) * 100);

      keyValue('Total Teams', String(MOCK_TEAMS.length));
      keyValue('Total Members', String(totalMembers));
      keyValue('Active Teams', String(MOCK_TEAMS.filter(t => t.status === 'active').length));
      keyValue('Tasks Completed', `${totalCompleted}/${totalTasks} (${overallRate}%)`);
      divider();

      info('Pending Tasks:');
      for (const task of MOCK_TASKS) {
        info(`  - ${task}`);
      }
      divider();

      // Engine Status footer section
      try {
        const health = engine?.openclaw?.getHealth();
        if (health) {
          info('Engine Status:');
          keyValue('  Missions Completed', String(health.missionsCompleted));
          keyValue('  AGI Score', String(health.agiScore));
          keyValue('  Circuit Breaker', health.circuitBreakerState);
        }
      } catch { /* engine not ready */ }

      success('Dashboard loaded');
    });
}
