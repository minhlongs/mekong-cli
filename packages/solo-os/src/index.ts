export {
  CompanyBrain,
  DEPARTMENTS,
  type Department,
  type DepartmentTask,
  type StandupReport,
  type CompanyHealth,
} from './company-brain.js';

export {
  DepartmentAgent,
  ProductAgent,
  EngineeringAgent,
  SalesAgent,
  MarketingAgent,
  FinanceAgent,
  LegalAgent,
  HRAgent,
  SupportAgent,
  type AgentResult,
  type KPI,
} from './department-agents.js';

export {
  DailyCycle,
  type MorningBrief,
  type WorkdayResult,
  type EveningReport,
  type WeeklyOKR,
} from './daily-cycle.js';

export {
  KPIDashboard,
  type MetricSnapshot,
  type Alert,
} from './kpi-dashboard.js';

export {
  RecipeEngine,
  type Recipe,
  type RecipeResult,
  type RecipeStatus,
} from './automation-recipes.js';

// ── Solo OS Pipeline Automation ───────────────────────────────────────────────

export type {
  CronExpression,
  Pipeline,
  PipelineRun,
  SoloConfig,
  DailySummary,
} from './types.js';

export { shouldRun } from './cron-matcher.js';
export { PipelineRunner } from './pipeline-runner.js';
export { DEFAULT_PIPELINES, getDefaultPipeline } from './default-pipelines.js';
export { DashboardReporter } from './dashboard-reporter.js';

import type { SoloConfig, Pipeline, PipelineRun } from './types.js';
import { shouldRun } from './cron-matcher.js';
import { PipelineRunner } from './pipeline-runner.js';
import { DEFAULT_PIPELINES } from './default-pipelines.js';

/** Merge default pipelines with user config, user pipelines take precedence by id */
export function initSoloOS(config: SoloConfig): SoloConfig {
  const userIds = new Set(config.pipelines.map((p) => p.id));
  const merged = [
    ...config.pipelines,
    ...DEFAULT_PIPELINES.filter((p) => !userIds.has(p.id)),
  ];
  return { ...config, pipelines: merged };
}

/** Return enabled pipelines whose cron schedule fires at the given time */
export function getScheduledPipelines(config: SoloConfig, now: Date = new Date()): Pipeline[] {
  return config.pipelines.filter((p) => p.enabled && shouldRun(p.schedule, now));
}

/** Runtime status snapshot for the current Solo OS session */
export function getStatus(
  config: SoloConfig,
  runner: PipelineRunner,
): { activePipelines: number; todayRuns: number; creditsUsed: number } {
  const runs: PipelineRun[] = runner.getRuns();
  const today = new Date().toISOString().split('T')[0];
  const todayRuns = runs.filter((r) => r.startedAt.startsWith(today));
  const creditsUsed = todayRuns.reduce((sum, r) => sum + r.creditsUsed, 0);
  return {
    activePipelines: config.pipelines.filter((p) => p.enabled).length,
    todayRuns: todayRuns.length,
    creditsUsed,
  };
}
