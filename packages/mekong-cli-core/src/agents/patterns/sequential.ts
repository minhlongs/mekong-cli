/**
 * Sequential execution pattern — tasks run in order, output chained to next input.
 */
import type { TaskAssignment, AgentMessage } from '../../types/agent.js';
import type { WorkerAgent } from '../worker.js';

export interface SequentialResult {
  results: AgentMessage[];
  completedCount: number;
  failedCount: number;
  totalDurationMs: number;
}

/** Execute tasks in order, passing output from one to the next */
export async function executeSequential(
  tasks: TaskAssignment[],
  createWorker: (taskIdx: number) => WorkerAgent,
): Promise<SequentialResult> {
  const results: AgentMessage[] = [];
  let completedCount = 0;
  let failedCount = 0;
  const startTime = Date.now();

  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i];

    // Inject previous task output as input
    if (i > 0 && results[i - 1]) {
      task.inputs = {
        ...task.inputs,
        previousOutput: results[i - 1].payload.content,
      };
    }

    const worker = createWorker(i);
    try {
      const result = await worker.execute(task);
      results.push(result);
      if (result.type === 'error') {
        failedCount++;
        break; // Stop on error in sequential mode
      }
      completedCount++;
    } catch (error) {
      failedCount++;
      results.push({
        id: `err-${i}`,
        from: 'sequential-pattern',
        to: 'orchestrator',
        type: 'error',
        payload: {
          content: error instanceof Error ? error.message : String(error),
          metadata: { taskIndex: i },
          artifacts: [],
        },
        timestamp: new Date().toISOString(),
        priority: task.priority,
      });
      break;
    }
  }

  return {
    results,
    completedCount,
    failedCount,
    totalDurationMs: Date.now() - startTime,
  };
}
