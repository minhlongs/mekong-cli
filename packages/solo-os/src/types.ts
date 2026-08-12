/**
 * Solo OS type definitions — automation pipelines for solo founder RaaS operations
 */

/** Standard cron expression e.g. '0 9 * * 1-5' */
export type CronExpression = string;

/** Automation pipeline definition linking a schedule to an agent */
export interface Pipeline {
  id: string;
  name: string;
  schedule: CronExpression;
  /** References an agent id from openclaw-agents registry */
  agentId: string;
  /** Prompt template supporting {{variable}} interpolation */
  inputTemplate: string;
  enabled: boolean;
}

/** Record of a single pipeline execution attempt */
export interface PipelineRun {
  runId: string;
  pipelineId: string;
  startedAt: string; // ISO 8601
  completedAt?: string; // ISO 8601
  status: 'running' | 'completed' | 'failed';
  output?: string;
  creditsUsed: number;
}

/** Top-level Solo OS configuration */
export interface SoloConfig {
  pipelines: Pipeline[];
  dailyCreditBudget: number;
  alertWebhook?: string;
}

/** Aggregated daily business metrics */
export interface DailySummary {
  date: string; // YYYY-MM-DD
  leadsGenerated: number;
  contentPublished: number;
  ticketsResolved: number;
  creditsUsed: number;
  creditsRemaining: number;
}
