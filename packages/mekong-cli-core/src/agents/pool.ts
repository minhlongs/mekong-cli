/**
 * AgentPool — manages lifecycle of WorkerAgent instances with WIP limit enforcement.
 */
import type { AgentDefinition } from '../types/agent.js';
import { WorkerAgent, type WorkerDeps } from './worker.js';

export class AgentPool {
  private agents: Map<string, WorkerAgent> = new Map();
  private definitions: Map<string, AgentDefinition> = new Map();
  private deps: WorkerDeps;
  private wipLimit: number;

  constructor(deps: WorkerDeps, wipLimit: number = 3) {
    this.deps = deps;
    this.wipLimit = wipLimit;
  }

  /** Register an agent definition for future spawning */
  registerDefinition(definition: AgentDefinition): void {
    this.definitions.set(definition.name, definition);
  }

  /** Spawn a new agent from a registered definition */
  spawn(definitionName: string): WorkerAgent {
    const definition = this.definitions.get(definitionName);
    if (!definition) {
      throw new Error(`Agent definition "${definitionName}" not found`);
    }
    if (this.activeCount >= this.wipLimit) {
      throw new Error(`WIP limit (${this.wipLimit}) reached — cannot spawn more agents`);
    }

    const agent = new WorkerAgent(definition, this.deps);
    this.agents.set(agent.id, agent);
    return agent;
  }

  /** Get a tracked agent by ID */
  get(agentId: string): WorkerAgent | undefined {
    return this.agents.get(agentId);
  }

  /** Remove an agent from the pool (call after completion) */
  release(agentId: string): boolean {
    return this.agents.delete(agentId);
  }

  /** Count of currently active (non-completed) agents */
  get activeCount(): number {
    return Array.from(this.agents.values()).filter(a => a.status === 'running').length;
  }

  /** Total agents currently tracked in pool */
  get size(): number {
    return this.agents.size;
  }

  /** List all registered definition names */
  listDefinitions(): string[] {
    return Array.from(this.definitions.keys());
  }

  /** Remove all agents from pool */
  clear(): void {
    this.agents.clear();
  }
}
