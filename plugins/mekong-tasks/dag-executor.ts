/**
 * dag-executor.ts — DAG orchestration engine for mekong-tasks.
 *
 * Responsibilities:
 *   - Topological sort of TaskSteps into execution waves
 *   - Parallel execution of independent steps per wave
 *   - Skip downstream waves on failure
 *   - Delegate per-step retries to dag-step-runner
 */

import { runStep } from './dag-step-runner.js';
import type {
  TaskStep,
  StepResult,
  TaskResult,
  TaskStatus,
  ProgressCallback,
} from './types.js';

// ─── Topological sort ─────────────────────────────────────────────────────────

/**
 * Returns execution waves — arrays of steps safe to run in parallel.
 * Each wave's steps have all their deps satisfied by previous waves.
 * Throws on cycle or unknown dependency reference.
 */
export function topologicalWaves(steps: TaskStep[]): TaskStep[][] {
  const idToStep = new Map(steps.map((s) => [s.id, s]));
  const remaining = new Set(steps.map((s) => s.id));
  const completed = new Set<string>();
  const waves: TaskStep[][] = [];

  // Validate dep references upfront
  for (const step of steps) {
    for (const dep of step.deps) {
      if (!idToStep.has(dep)) {
        throw new Error(`Step "${step.id}" has unknown dependency "${dep}"`);
      }
    }
  }

  let safety = steps.length + 1;

  while (remaining.size > 0) {
    if (--safety < 0) {
      throw new Error(
        `Cycle detected in DAG. Remaining: ${[...remaining].join(', ')}`
      );
    }

    const wave = [...remaining].filter((id) =>
      idToStep.get(id)!.deps.every((dep) => completed.has(dep))
    );

    if (wave.length === 0) {
      throw new Error(
        `Cycle detected in DAG. Remaining: ${[...remaining].join(', ')}`
      );
    }

    waves.push(wave.map((id) => idToStep.get(id)!));
    wave.forEach((id) => { remaining.delete(id); completed.add(id); });
  }

  return waves;
}

// ─── Wave execution ───────────────────────────────────────────────────────────

function emitSkip(
  step: TaskStep,
  taskId: string,
  results: StepResult[],
  onProgress: ProgressCallback
): void {
  results.push({
    stepId: step.id,
    status: 'skipped',
    stdout: '',
    stderr: '',
    durationMs: 0,
    attempts: 0,
  });
  onProgress({
    taskId,
    stepId: step.id,
    status: 'skipped',
    message: `Skipped: ${step.name} (upstream failed)`,
    timestamp: Date.now(),
  });
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Executes all steps in topological wave order.
 * Steps within a wave run concurrently. A wave failure cancels remaining waves.
 */
export async function executeDag(
  taskId: string,
  steps: TaskStep[],
  onProgress: ProgressCallback
): Promise<TaskResult> {
  const taskStart = Date.now();
  const allResults: StepResult[] = [];
  let taskFailed = false;

  let waves: TaskStep[][];
  try {
    waves = topologicalWaves(steps);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[mekong-tasks] [${taskId}] DAG sort error: ${msg}`);
    return { taskId, status: 'failed', stepResults: [], totalDurationMs: 0 };
  }

  console.log(
    `[mekong-tasks] [${taskId}] ${steps.length} steps / ${waves.length} wave(s)`
  );

  for (const wave of waves) {
    if (taskFailed) {
      wave.forEach((s) => emitSkip(s, taskId, allResults, onProgress));
      continue;
    }

    const waveResults = await Promise.all(
      wave.map((step) => runStep(step, taskId, onProgress))
    );

    for (const result of waveResults) {
      allResults.push(result);
      const status: TaskStatus = result.status === 'completed' ? 'completed' : 'failed';
      onProgress({
        taskId,
        stepId: result.stepId,
        status,
        message:
          status === 'completed'
            ? `Done: ${result.stepId} (${result.durationMs}ms)`
            : `Failed: ${result.stepId} — ${result.error ?? 'unknown'}`,
        timestamp: Date.now(),
      });
      if (result.status === 'failed') taskFailed = true;
    }
  }

  const finalStatus: TaskStatus = taskFailed ? 'failed' : 'completed';
  console.log(
    `[mekong-tasks] [${taskId}] ${finalStatus} in ${Date.now() - taskStart}ms`
  );

  return {
    taskId,
    status: finalStatus,
    stepResults: allResults,
    totalDurationMs: Date.now() - taskStart,
  };
}
