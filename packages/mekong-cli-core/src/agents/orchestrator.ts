/**
 * OrchestratorAgent — decomposes goals into tasks and selects the right execution pattern.
 */
import type { OrchestrationPattern, TaskAssignment, AgentMessage, AgentDefinition } from '../types/agent.js';
import { AgentPool } from './pool.js';
import { executeSequential } from './patterns/sequential.js';
import { executeHierarchical } from './patterns/hierarchical.js';
import { executeGraph, type GraphNode } from './patterns/graph.js';
import { emit } from '../core/events.js';
import type { WorkerDeps } from './worker.js';

export interface OrchestratorPlan {
  pattern: OrchestrationPattern;
  tasks: TaskAssignment[];
  dependencies?: Map<string, string[]>; // taskId → dependency taskIds
  estimatedCost: number;
  estimatedTimeSeconds: number;
}

export interface OrchestratorResult {
  success: boolean;
  pattern: OrchestrationPattern;
  results: AgentMessage[];
  completedCount: number;
  failedCount: number;
  totalDurationMs: number;
}

export class OrchestratorAgent {
  private pool: AgentPool;
  private workerDeps: WorkerDeps;

  constructor(deps: WorkerDeps, wipLimit: number = 3) {
    this.workerDeps = deps;
    this.pool = new AgentPool(deps, wipLimit);
  }

  /** Register an agent definition available for spawning */
  registerAgent(definition: AgentDefinition): void {
    this.pool.registerDefinition(definition);
  }

  /** Infer the best execution pattern for the given task set */
  selectPattern(tasks: TaskAssignment[], dependencies?: Map<string, string[]>): OrchestrationPattern {
    if (tasks.length <= 1) return 'sequential';
    if (dependencies && dependencies.size > 0) {
      const hasBranching = Array.from(dependencies.values()).some(deps => deps.length > 1);
      return hasBranching ? 'graph' : 'sequential';
    }
    return 'hierarchical';
  }

  /** Build a plan from tasks and optional dependency map */
  plan(tasks: TaskAssignment[], dependencies?: Map<string, string[]>): OrchestratorPlan {
    const pattern = this.selectPattern(tasks, dependencies);
    return {
      pattern,
      tasks,
      dependencies,
      estimatedCost: tasks.length * 0.01,
      estimatedTimeSeconds: tasks.length * 30,
    };
  }

  /** Execute a plan using the selected pattern */
  async execute(plan: OrchestratorPlan, agentDefinitionName: string): Promise<OrchestratorResult> {
    emit('engine:started', { pattern: plan.pattern, taskCount: plan.tasks.length });

    const createWorker = (_indexOrId: number | string) =>
      this.pool.spawn(agentDefinitionName);

    let results: AgentMessage[] = [];
    let completedCount = 0;
    let failedCount = 0;
    let totalDurationMs = 0;

    switch (plan.pattern) {
      case 'sequential': {
        const r = await executeSequential(plan.tasks, (idx) => createWorker(idx));
        results = r.results;
        completedCount = r.completedCount;
        failedCount = r.failedCount;
        totalDurationMs = r.totalDurationMs;
        break;
      }

      case 'hierarchical': {
        const r = await executeHierarchical(plan.tasks, (idx) => createWorker(idx));
        results = r.childResults;
        completedCount = r.completedCount;
        failedCount = r.failedCount;
        totalDurationMs = r.totalDurationMs;
        break;
      }

      case 'graph': {
        const nodes: GraphNode[] = plan.tasks.map(task => ({
          task,
          dependencies: plan.dependencies?.get(task.id) ?? [],
        }));
        const r = await executeGraph(nodes, (taskId) => createWorker(taskId));
        results = Array.from(r.results.values());
        completedCount = r.completedCount;
        failedCount = r.failedCount;
        totalDurationMs = r.totalDurationMs;
        break;
      }

      case 'reactive': {
        // Reactive not yet implemented — fallback to sequential
        const r = await executeSequential(plan.tasks, (idx) => createWorker(idx));
        results = r.results;
        completedCount = r.completedCount;
        failedCount = r.failedCount;
        totalDurationMs = r.totalDurationMs;
        break;
      }
    }

    this.pool.clear();
    emit('engine:stopped', { completedCount, failedCount });

    return {
      success: failedCount === 0,
      pattern: plan.pattern,
      results,
      completedCount,
      failedCount,
      totalDurationMs,
    };
  }
}
