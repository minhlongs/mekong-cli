/**
 * Graph execution pattern — DAG-based task execution respecting dependency order.
 */
import type { TaskAssignment, AgentMessage } from '../../types/agent.js';
import type { WorkerAgent } from '../worker.js';
import { emit } from '../../core/events.js';

export interface GraphNode {
  task: TaskAssignment;
  dependencies: string[]; // task IDs this node depends on
}

export interface GraphResult {
  results: Map<string, AgentMessage>;
  executionOrder: string[];
  completedCount: number;
  failedCount: number;
  totalDurationMs: number;
}

/** Execute tasks as a DAG — respects dependency order, parallelises independent nodes */
export async function executeGraph(
  nodes: GraphNode[],
  createWorker: (taskId: string) => WorkerAgent,
): Promise<GraphResult> {
  const results = new Map<string, AgentMessage>();
  const executionOrder: string[] = [];
  let completedCount = 0;
  let failedCount = 0;
  const startTime = Date.now();

  const pending = new Set(nodes.map(n => n.task.id));
  const nodeMap = new Map(nodes.map(n => [n.task.id, n]));

  while (pending.size > 0) {
    // Find tasks whose dependencies are all satisfied
    const ready: GraphNode[] = [];
    for (const taskId of pending) {
      const node = nodeMap.get(taskId)!;

      const anyDepFailed = node.dependencies.some(dep => results.get(dep)?.type === 'error');
      if (anyDepFailed) {
        pending.delete(taskId);
        results.set(taskId, makeError(`dep-err-${taskId}`, 'graph-pattern', 'Skipped: dependency failed', {}, node.task.priority));
        failedCount++;
        continue;
      }

      const allDepsComplete = node.dependencies.every(dep => results.has(dep));
      if (allDepsComplete) ready.push(node);
    }

    if (ready.length === 0 && pending.size > 0) {
      // Circular dependency deadlock
      for (const taskId of pending) {
        results.set(taskId, makeError(`deadlock-${taskId}`, 'graph-pattern', 'Deadlock: circular dependency detected', {}, 'normal'));
        failedCount++;
      }
      break;
    }

    // Execute all ready nodes in parallel
    const batchPromises = ready.map(async (node) => {
      // Inject dependency outputs into task inputs
      for (const depId of node.dependencies) {
        const depResult = results.get(depId);
        if (depResult) {
          node.task.inputs[`dep_${depId}`] = depResult.payload.content;
        }
      }

      const worker = createWorker(node.task.id);
      try {
        const result = await worker.execute(node.task);
        return { taskId: node.task.id, result };
      } catch (error) {
        return {
          taskId: node.task.id,
          result: makeError(
            `err-${node.task.id}`,
            'graph-pattern',
            error instanceof Error ? error.message : String(error),
            {},
            node.task.priority,
          ),
        };
      }
    });

    const batchResults = await Promise.all(batchPromises);
    for (const { taskId, result } of batchResults) {
      results.set(taskId, result);
      pending.delete(taskId);
      executionOrder.push(taskId);
      if (result.type === 'error') failedCount++;
      else completedCount++;
      emit('task:completed', { taskId });
    }
  }

  return { results, executionOrder, completedCount, failedCount, totalDurationMs: Date.now() - startTime };
}

function makeError(
  id: string,
  from: string,
  content: string,
  metadata: Record<string, unknown>,
  priority: AgentMessage['priority'],
): AgentMessage {
  return {
    id,
    from,
    to: 'orchestrator',
    type: 'error',
    payload: { content, metadata, artifacts: [] },
    timestamp: new Date().toISOString(),
    priority,
  };
}
