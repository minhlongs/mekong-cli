import type { SopRun } from '../types/sop.js';

export interface SopMetrics {
  runId: string;
  sopName: string;
  totalDurationMs: number;
  stepCount: number;
  successCount: number;
  failedCount: number;
  retryCount: number;
  stepDurations: Array<{ stepId: string; durationMs: number; status: string }>;
  averageStepDurationMs: number;
}

/** Collect metrics from a completed SOP run */
export function collectMetrics(run: SopRun): SopMetrics {
  const startTime = new Date(run.startedAt).getTime();
  const endTime = run.completedAt ? new Date(run.completedAt).getTime() : Date.now();

  const stepDurations = run.steps.map((step) => {
    const stepStart = new Date(step.startedAt).getTime();
    const stepEnd = step.completedAt ? new Date(step.completedAt).getTime() : stepStart;
    return {
      stepId: step.stepId,
      durationMs: stepEnd - stepStart,
      status: step.status,
    };
  });

  const successCount = run.steps.filter((s) => s.status === 'success').length;
  const failedCount = run.steps.filter((s) => s.status === 'failed').length;
  const retryCount = run.steps.reduce((sum, s) => sum + s.retryCount, 0);
  const totalStepDuration = stepDurations.reduce((sum, s) => sum + s.durationMs, 0);

  return {
    runId: run.id,
    sopName: run.sopName,
    totalDurationMs: endTime - startTime,
    stepCount: run.steps.length,
    successCount,
    failedCount,
    retryCount,
    stepDurations,
    averageStepDurationMs: run.steps.length > 0 ? totalStepDuration / run.steps.length : 0,
  };
}

/** Compare two runs and return improvement suggestions */
export function compareRuns(current: SopMetrics, previous: SopMetrics): string[] {
  const suggestions: string[] = [];

  if (current.totalDurationMs > previous.totalDurationMs * 1.2) {
    suggestions.push(
      `Run took ${Math.round((current.totalDurationMs / previous.totalDurationMs - 1) * 100)}% longer than previous`,
    );
  }

  if (current.retryCount > previous.retryCount) {
    suggestions.push(
      `More retries (${current.retryCount} vs ${previous.retryCount}) — check flaky steps`,
    );
  }

  if (current.failedCount > 0 && previous.failedCount === 0) {
    const failedSteps = current.stepDurations
      .filter((s) => s.status === 'failed')
      .map((s) => s.stepId);
    suggestions.push(`New failures in: ${failedSteps.join(', ')}`);
  }

  return suggestions;
}
