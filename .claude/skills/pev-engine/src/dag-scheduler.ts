/**
 * PEV Engine — DAG Scheduler
 *
 * Port of Mekong CLI's DAGScheduler.
 * Topological parallel execution of recipe steps with dependency tracking.
 * Uses Promise.all with concurrency limiting instead of ThreadPoolExecutor.
 */

import type { Step, DAGStepResult, StepResult } from './types.js';

export class DAGScheduler {
  private steps: Map<number, Step>;
  private max_workers: number;
  private completed: Set<number>;
  private failed: Set<number>;
  private cancelled: Set<number>;

  constructor(steps: Step[], max_workers: number = 4) {
    this.steps = new Map(steps.map(s => [parseInt(s.id.split('-')[1] || s.id, 10), s]));
    this.max_workers = max_workers;
    this.completed = new Set();
    this.failed = new Set();
    this.cancelled = new Set();
  }

  getReadySteps(): Step[] {
    const ready: Step[] = [];
    for (const [order, step] of this.steps) {
      if (this.completed.has(order) || this.failed.has(order) || this.cancelled.has(order)) {
        continue;
      }
      const deps = step.deps.map(d => parseInt(d.split('-')[1] || d, 10));
      if (deps.every(d => this.completed.has(d))) {
        ready.push(step);
      }
    }
    return ready;
  }

  markCompleted(order: number): void {
    this.completed.add(order);
  }

  markFailed(order: number): void {
    this.failed.add(order);
    this.cancelDownstream(order);
  }

  private cancelDownstream(failedOrder: number): void {
    const queue: number[] = [failedOrder];
    while (queue.length > 0) {
      const current = queue.shift()!;
      for (const [order, step] of this.steps) {
        if (this.cancelled.has(order)) continue;
        const deps = step.deps.map(d => parseInt(d.split('-')[1] || d, 10));
        if (deps.includes(current)) {
          this.cancelled.add(order);
          queue.push(order);
        }
      }
    }
  }

  isDone(): boolean {
    const allOrders = new Set(this.steps.keys());
    return allOrders.size === this.completed.size + this.failed.size + this.cancelled.size;
  }

  get cancelledSteps(): number[] {
    return Array.from(this.cancelled);
  }

  hasDependencies(): boolean {
    for (const step of this.steps.values()) {
      if (step.deps.length > 0) return true;
    }
    return false;
  }

  /**
   * Execute all steps respecting DAG dependencies.
   * @param executorFn - async function that executes a step and returns StepResult
   * @param onComplete - optional callback after each step completes
   */
  async executeAll(
    executorFn: (step: Step) => Promise<StepResult>,
    onComplete?: (order: number, result: DAGStepResult) => void,
  ): Promise<Map<number, DAGStepResult>> {
    const results = new Map<number, DAGStepResult>();
    const inFlight = new Set<number>();

    while (!this.isDone()) {
      const ready = this.getReadySteps().filter(s => !inFlight.has(parseInt(s.id.split('-')[1] || s.id, 10)));

      if (ready.length === 0) break;

      // Execute ready steps with concurrency limit
      const batch = ready.slice(0, this.max_workers);
      for (const step of batch) {
        const order = parseInt(step.id.split('-')[1] || step.id, 10);
        inFlight.add(order);
      }

      const batchResults = await Promise.allSettled(
        batch.map(step => executorFn(step)),
      );

      for (let i = 0; i < batch.length; i++) {
        const step = batch[i];
        const order = parseInt(step.id.split('-')[1] || step.id, 10);
        const settled = batchResults[i];

        if (settled.status === 'fulfilled') {
          const stepResult = settled.value;
          const passed = stepResult.verification.passed;
          const dagResult: DAGStepResult = {
            order,
            success: passed,
            result: stepResult,
          };
          results.set(order, dagResult);

          if (passed) {
            this.markCompleted(order);
          } else {
            this.markFailed(order);
          }
        } else {
          const dagResult: DAGStepResult = {
            order,
            success: false,
            error: settled.reason instanceof Error ? settled.reason.message : String(settled.reason),
          };
          results.set(order, dagResult);
          this.markFailed(order);
        }

        inFlight.delete(order);
        onComplete?.(order, results.get(order)!);
      }
    }

    return results;
  }
}

/**
 * Validate DAG has no circular dependencies using Kahn's algorithm.
 */
export function validateDag(steps: Step[]): string | null {
  const orders = new Set(steps.map(s => parseInt(s.id.split('-')[1] || s.id, 10)));
  const adj = new Map<number, number[]>();
  const inDegree = new Map<number, number>();

  for (const order of orders) {
    adj.set(order, []);
    inDegree.set(order, 0);
  }

  for (const step of steps) {
    const stepOrder = parseInt(step.id.split('-')[1] || step.id, 10);
    for (const dep of step.deps) {
      const depOrder = parseInt(dep.split('-')[1] || dep, 10);
      adj.get(depOrder)!.push(stepOrder);
      inDegree.set(stepOrder, (inDegree.get(stepOrder) || 0) + 1);
    }
  }

  const queue: number[] = [];
  for (const [order, degree] of inDegree) {
    if (degree === 0) queue.push(order);
  }

  let visited = 0;
  while (queue.length > 0) {
    const node = queue.shift()!;
    visited++;
    for (const neighbor of adj.get(node) ?? []) {
      const newDegree = (inDegree.get(neighbor) || 0) - 1;
      inDegree.set(neighbor, newDegree);
      if (newDegree === 0) queue.push(neighbor);
    }
  }

  if (visited !== orders.size) {
    return 'Circular dependency detected in recipe steps';
  }
  return null;
}
