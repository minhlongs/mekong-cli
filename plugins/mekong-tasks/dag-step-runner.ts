/**
 * dag-step-runner.ts — single step execution with retry logic.
 *
 * Isolated from the wave orchestrator so each file stays under 200 lines.
 */

import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type { TaskStep, StepResult, ProgressCallback } from './types.js';

const execAsync = promisify(exec);

export const STEP_TIMEOUT_MS = 5 * 60 * 1000; // 5 min
const BASE_RETRY_DELAY_MS = 500;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Executes a single step command with exponential-backoff retry.
 * Reports running / retry progress via callback.
 */
export async function runStep(
  step: TaskStep,
  taskId: string,
  onProgress: ProgressCallback
): Promise<StepResult> {
  const maxRetries = step.maxRetries ?? 2;
  const startMs = Date.now();
  let lastError = '';

  for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
    onProgress({
      taskId,
      stepId: step.id,
      status: 'running',
      message:
        attempt === 1
          ? `Starting: ${step.name}`
          : `Retry ${attempt - 1}/${maxRetries}: ${step.name}`,
      timestamp: Date.now(),
    });

    try {
      const { stdout, stderr } = await execAsync(step.command, {
        timeout: STEP_TIMEOUT_MS,
        shell: '/bin/sh',
      });

      const durationMs = Date.now() - startMs;
      console.log(`[mekong-tasks] [${taskId}] [${step.id}] OK (${durationMs}ms)`);

      return {
        stepId: step.id,
        status: 'completed',
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        durationMs,
        attempts: attempt,
      };
    } catch (err) {
      const e = err as NodeJS.ErrnoException & { stdout?: string; stderr?: string };
      lastError = e.message ?? String(err);
      const isLast = attempt === maxRetries + 1;
      console.error(
        `[mekong-tasks] [${taskId}] [${step.id}] attempt ${attempt} failed: ${lastError}`
      );
      if (!isLast) await delay(BASE_RETRY_DELAY_MS * 2 ** (attempt - 1));
    }
  }

  return {
    stepId: step.id,
    status: 'failed',
    stdout: '',
    stderr: lastError,
    durationMs: Date.now() - startMs,
    attempts: maxRetries + 1,
    error: lastError,
  };
}
