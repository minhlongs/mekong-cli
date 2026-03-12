import type { SopStep } from '../types/sop.js';

export interface DagNode {
  step: SopStep;
  dependencies: string[]; // step IDs this depends on
}

export interface ExecutionLayer {
  stepIds: string[]; // steps that can run in parallel within this layer
}

/** Build a DAG from SOP steps */
export function buildDag(steps: SopStep[]): DagNode[] {
  const nodes: DagNode[] = [];

  for (const step of steps) {
    const deps: string[] = [];
    // Find steps that point to this step via on_success
    for (const other of steps) {
      if (other.on_success === step.id) {
        deps.push(other.id);
      }
    }
    nodes.push({ step, dependencies: deps });
  }

  return nodes;
}

/** Topological sort — returns execution layers (steps in each layer can run in parallel) */
export function topoSort(nodes: DagNode[]): ExecutionLayer[] {
  const layers: ExecutionLayer[] = [];
  const completed = new Set<string>();
  const remaining = new Map(nodes.map((n) => [n.step.id, n]));

  while (remaining.size > 0) {
    const ready: string[] = [];
    for (const [id, node] of remaining) {
      if (node.dependencies.every((dep) => completed.has(dep))) {
        ready.push(id);
      }
    }

    if (ready.length === 0) {
      throw new Error(
        `Circular dependency detected among: ${Array.from(remaining.keys()).join(', ')}`,
      );
    }

    layers.push({ stepIds: ready });
    for (const id of ready) {
      completed.add(id);
      remaining.delete(id);
    }
  }

  return layers;
}

/** Validate DAG has no cycles and all dependencies exist */
export function validateDag(nodes: DagNode[]): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  const stepIds = new Set(nodes.map((n) => n.step.id));

  for (const node of nodes) {
    for (const dep of node.dependencies) {
      if (!stepIds.has(dep)) {
        errors.push(`Step "${node.step.id}" depends on non-existent step "${dep}"`);
      }
    }
  }

  try {
    topoSort(nodes);
  } catch {
    errors.push('Circular dependency detected');
  }

  return { valid: errors.length === 0, errors };
}
