/**
 * solo-os.ts — Solo Founder OS CLI commands
 * Start the AI company, check status, generate reports.
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerSoloOsCommand(program: Command, _engine: MekongEngine): void {
  const solo = program
    .command('solo')
    .description('SoloOS — AI-operated company for solo founders');

  solo
    .command('start <goal>')
    .description('Start company brain with a business goal')
    .action(async (goal: string) => {
      try {
        // @ts-expect-error rootDir constraint
        const { CompanyBrain } = await import('../../../solo-os/src/company-brain.js');
        // @ts-expect-error rootDir constraint
        const { DailyCycle } = await import('../../../solo-os/src/daily-cycle.js');
        // @ts-expect-error rootDir constraint
        const { default: departmentAgents } = await import('../../../solo-os/src/department-agents.js');

        const brain = new CompanyBrain();
        brain.setGoal(goal);
        const tasks = brain.decompose(goal);

        info(`── SoloOS Started ──`);
        info(`Goal: ${goal}`);
        info(`Decomposed into ${tasks.length} department tasks:`);
        for (const t of tasks) {
          info(`  [${t.priority}] ${t.department}: ${t.task}`);
        }

        const cycle = new DailyCycle(departmentAgents);
        const morning = cycle.runMorning();
        info(`\nMorning brief: ${morning.priorities.length} priorities assigned`);

        success('SoloOS running. Use "mekong solo status" to check.');
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  solo
    .command('status')
    .description('Show company health and department statuses')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { CompanyBrain } = await import('../../../solo-os/src/company-brain.js');
        // @ts-expect-error rootDir constraint
        const { KPIDashboard } = await import('../../../solo-os/src/kpi-dashboard.js');

        const brain = new CompanyBrain();
        const health = brain.getCompanyHealth();
        const kpi = new KPIDashboard();
        const metrics = kpi.getMetrics();
        const alerts = kpi.checkAlerts();

        info(`── Company Health: ${health.score}/100 ──`);
        for (const [dept, score] of Object.entries(health.departments)) {
          info(`  ${dept}: ${score}/100`);
        }

        info(`\n── KPIs ──`);
        info(`MRR: $${metrics.mrr} | Users: ${metrics.activeUsers} | Churn: ${(metrics.churnRate * 100).toFixed(1)}%`);
        info(`NPS: ${metrics.nps} | Runway: ${metrics.runwayMonths}mo`);

        if (alerts.length > 0) {
          info(`\n── Alerts (${alerts.length}) ──`);
          for (const a of alerts) {
            info(`  [${a.severity}] ${a.metric}: ${a.current} (threshold: ${a.threshold})`);
          }
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  solo
    .command('report')
    .description('Generate daily/weekly report')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { KPIDashboard } = await import('../../../solo-os/src/kpi-dashboard.js');
        // @ts-expect-error rootDir constraint
        const { RecipeEngine } = await import('../../../solo-os/src/automation-recipes.js');

        const kpi = new KPIDashboard();
        const report = kpi.generateReport();
        info(report);

        const recipes = new RecipeEngine();
        info('\n── Automation Recipes ──');
        for (const r of recipes.listRecipes()) {
          info(`  ${r.name}: ${r.slaHours}h SLA, ${r.steps.length} steps`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
