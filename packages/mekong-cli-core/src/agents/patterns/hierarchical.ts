/**
 * Hierarchical execution pattern — parallel batch execution with WIP limit (Kanban-style).
 */
import type { TaskAssignment, AgentMessage } from '../../types/agent.js';
import type { WorkerAgent } from '../worker.js';
import { emit } from '../../core/events.js';

export interface HierarchicalResult {
  childResults: AgentMessage[];
  completedCount: number;
  failedCount: number;
  totalDurationMs: number;
}

/** Execute children with WIP limit — processes in parallel batches */
export async function executeHierarchical(
  childTasks: TaskAssignment[],
  createWorker: (taskIdx: number) => WorkerAgent,
  wipLimit: number = 3,
): Promise<HierarchicalResult> {
  const childResults: AgentMessage[] = [];
  let completedCount = 0;
  let failedCount = 0;
  const startTime = Date.now();

  for (let i = 0; i < childTasks.length; i += wipLimit) {
    const batch = childTasks.slice(i, i + wipLimit);
    const batchPromises = batch.map(async (task, batchIdx) => {
      const idx = i + batchIdx;
      const worker = createWorker(idx);
      try {
        const result = await worker.execute(task);
        emit('task:completed', { taskId: task.id });
        return result;
      } catch (error) {
        return {
          id: `err-${idx}`,
          from: 'hierarchical-pattern',
          to: 'orchestrator',
          type: 'error' as const,
          payload: {
            content: error instanceof Error ? error.message : String(error),
            metadata: { taskIndex: idx },
            artifacts: [],
          },
          timestamp: new Date().toISOString(),
          priority: task.priority,
        } satisfies AgentMessage;
      }
    });

    const batchResults = await Promise.all(batchPromises);
    for (const result of batchResults) {
      childResults.push(result);
      if (result.type === 'error') failedCount++;
      else completedCount++;
    }
  }

  return {
    childResults,
    completedCount,
    failedCount,
    totalDurationMs: Date.now() - startTime,
  };
}
