/**
 * PipelineRunner — executes automation pipelines with variable interpolation.
 * Actual LLM calls happen via the daemon; this layer handles lifecycle tracking.
 */

import type { Pipeline, PipelineRun } from './types.js';

/** Render a template string by replacing {{key}} placeholders with values */
function renderTemplate(template: string, variables: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => variables[key] ?? `{{${key}}}`);
}

/** Generate a lightweight run ID without external dependencies */
function makeRunId(): string {
  return `run_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

/** Estimate credit cost based on rendered prompt length (1 credit per ~500 chars) */
function estimateCredits(prompt: string): number {
  return Math.max(1, Math.ceil(prompt.length / 500));
}

export class PipelineRunner {
  private runs: PipelineRun[] = [];

  /**
   * Execute a pipeline with the provided variables.
   * The resolved prompt is stored in output; actual LLM dispatch is async via daemon.
   */
  async run(
    pipeline: Pipeline,
    variables: Record<string, string> = {},
  ): Promise<PipelineRun> {
    const runId = makeRunId();
    const startedAt = new Date().toISOString();

    const pipelineRun: PipelineRun = {
      runId,
      pipelineId: pipeline.id,
      startedAt,
      status: 'running',
      creditsUsed: 0,
    };

    this.runs.push(pipelineRun);

    try {
      const resolvedPrompt = renderTemplate(pipeline.inputTemplate, variables);
      const creditsUsed = estimateCredits(resolvedPrompt);

      // Stub: daemon will pick up the resolved prompt for actual LLM execution
      pipelineRun.output = resolvedPrompt;
      pipelineRun.creditsUsed = creditsUsed;
      pipelineRun.status = 'completed';
      pipelineRun.completedAt = new Date().toISOString();
    } catch (err) {
      pipelineRun.status = 'failed';
      pipelineRun.completedAt = new Date().toISOString();
      pipelineRun.output = err instanceof Error ? err.message : String(err);
    }

    return pipelineRun;
  }

  /** All runs recorded in this runner instance */
  getRuns(): PipelineRun[] {
    return this.runs;
  }

  /** Runs for a specific pipeline id */
  getRunsForPipeline(pipelineId: string): PipelineRun[] {
    return this.runs.filter((r) => r.pipelineId === pipelineId);
  }
}
