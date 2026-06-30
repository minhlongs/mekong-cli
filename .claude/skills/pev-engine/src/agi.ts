/**
 * AGI Components — optional subsystems loaded lazily.
 *
 * Each component (reflection, world model, tool registry, collaboration,
 * code evolution, vector memory) is loaded on demand and silently skipped
 * if unavailable. This keeps the core engine lightweight.
 *
 * In TypeScript/ClaudeKit, these are stub interfaces that can be implemented
 * by consumers. The engine works without any of them.
 */

import type { RecipeStep, ExecutionResult } from "./types";

// ---------------------------------------------------------------------------
// Stub interfaces (implement these in your application)
// ---------------------------------------------------------------------------

export interface ReflectionEngine {
  reflect(params: {
    goal: string;
    status: string;
    durationMs: number;
    error: string;
  }): ReflectionResult;
  getStrategySuggestion(command: string): string | null;
}

export interface ReflectionResult {
  lessonLearned?: string;
  strategyChange?: string;
}

export interface WorldModel {
  snapshot(): WorldSnapshot;
  diff(before: WorldSnapshot, after: WorldSnapshot): WorldDiff;
  predictSideEffects(goal: string): RiskPrediction;
}

export interface WorldSnapshot {
  timestamp: number;
  data: Record<string, unknown>;
}

export interface WorldDiff {
  summary(): string;
}

export interface RiskPrediction {
  riskLevel: "low" | "medium" | "high";
  warnings: string[];
}

export interface ToolRegistry {
  suggestTool(goal: string): ToolSuggestion | null;
  execute(name: string, args: Record<string, unknown>): ToolResult;
}

export interface ToolSuggestion {
  name: string;
  description: string;
}

export interface ToolResult {
  success: boolean;
  output: string;
  error?: string;
}

export interface CollaborationProtocol {
  assignRoles(goal: string): RoleAssignment[];
  submitReview(params: {
    reviewer: string;
    target: string;
    approved: boolean;
    feedback: string[];
  }): void;
}

export interface RoleAssignment {
  agent: string;
  role: string;
}

export interface CodeEvolutionEngine {
  getJournal(limit: number): CodeChange[];
  getStats(): Record<string, number>;
}

export interface CodeChange {
  id: string;
  description: string;
  timestamp: number;
}

export interface VectorMemoryStore {
  search(collection: string, vector: number[], topK: number): MemoryResult[];
  upsert(params: {
    collection: string;
    id: string;
    vector: number[];
    payload: Record<string, unknown>;
  }): void;
  getOrCreateCollection(name: string): void;
}

export interface MemoryResult {
  score: number;
  payload: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// AGIComponents container
// ---------------------------------------------------------------------------

export type AGIComponentMap = {
  reflection: ReflectionEngine | null;
  worldModel: WorldModel | null;
  toolRegistry: ToolRegistry | null;
  collaboration: CollaborationProtocol | null;
  codeEvolution: CodeEvolutionEngine | null;
  vectorMemory: VectorMemoryStore | null;
};

export class AGIComponents implements AGIComponentMap {
  reflection: ReflectionEngine | null = null;
  worldModel: WorldModel | null = null;
  toolRegistry: ToolRegistry | null = null;
  collaboration: CollaborationProtocol | null = null;
  codeEvolution: CodeEvolutionEngine | null = null;
  vectorMemory: VectorMemoryStore | null = null;

  constructor(_components?: Partial<AGIComponentMap>) {
    // Components are set externally by the orchestrator.
    // No lazy loading in TS — consumers inject what they have.
    if (_components) {
      Object.assign(this, _components);
    }
  }

  // -------------------------------------------------------------------------
  // Pre-execution hints
  // -------------------------------------------------------------------------

  printPreExecutionHints(
    _goal: string,
    _log: (msg: string) => void,
  ): WorldSnapshot | null {
    let worldBefore: WorldSnapshot | null = null;

    if (this.worldModel) {
      try {
        worldBefore = this.worldModel.snapshot();
        _log("🌍 World snapshot captured");
      } catch {
        // silently skip
      }
    }

    if (this.reflection) {
      try {
        const hint = this.reflection.getStrategySuggestion(_goal);
        if (hint) _log(`🪞 Strategy hint: ${hint.slice(0, 60)}`);
      } catch {
        // silently skip
      }
    }

    if (this.toolRegistry) {
      try {
        const suggested = this.toolRegistry.suggestTool(_goal);
        if (suggested) {
          _log(
            `🔧 Tool available: ${suggested.name} — ${suggested.description.slice(0, 40)}`,
          );
        }
      } catch {
        // silently skip
      }
    }

    if (this.worldModel) {
      try {
        const prediction = this.worldModel.predictSideEffects(_goal);
        if (prediction.riskLevel === "high") {
          _log(
            `⚠️ High-risk action detected: ${prediction.warnings.slice(0, 2).join("; ")}`,
          );
        }
      } catch {
        // silently skip
      }
    }

    if (this.collaboration) {
      try {
        const roles = this.collaboration.assignRoles(_goal);
        if (roles.length > 0) {
          const assigned = roles
            .slice(0, 2)
            .map((r) => `${r.agent}: ${r.role}`)
            .join(", ");
          _log(`🤝 Agents assigned: ${assigned}`);
        }
      } catch {
        // silently skip
      }
    }

    return worldBefore;
  }

  // -------------------------------------------------------------------------
  // Post-execution pipeline
  // -------------------------------------------------------------------------

  runPostExecution(params: {
    goal: string;
    status: string;
    durationMs: number;
    worldBefore: WorldSnapshot | null;
    errors: string[];
    log: (msg: string) => void;
  }): void {
    const { goal, status, durationMs, worldBefore, errors, log } = params;

    // Reflection
    if (this.reflection) {
      try {
        const reflection = this.reflection.reflect({
          goal,
          status,
          durationMs,
          error: errors[0] ?? "",
        });
        if (reflection.lessonLearned) {
          log(`🪞 Reflection: ${reflection.lessonLearned.slice(0, 80)}`);
        }
        if (reflection.strategyChange) {
          log(`🪞 Strategy change: ${reflection.strategyChange.slice(0, 60)}`);
        }
      } catch {
        // silently skip
      }
    }

    // World diff
    if (this.worldModel && worldBefore) {
      try {
        const worldAfter = this.worldModel.snapshot();
        const worldDiff = this.worldModel.diff(worldBefore, worldAfter);
        const diffSummary = worldDiff.summary();
        if (diffSummary && diffSummary !== "No changes detected") {
          log(`🌍 World changes: ${diffSummary.slice(0, 100)}`);
        }
      } catch {
        // silently skip
      }
    }

    // Code evolution stats
    if (this.codeEvolution) {
      try {
        const stats = this.codeEvolution.getStats();
        const attempts = stats.total_attempts ?? 0;
        if (attempts > 0) {
          const rate = stats.success_rate ?? 0;
          log(`🧬 Evolution: ${attempts} attempts, ${(rate * 100).toFixed(0)}% success rate`);
        }
      } catch {
        // silently skip
      }
    }

    // Vector memory
    if (this.vectorMemory) {
      try {
        const vec = this.hashGoal(goal);
        const goalId = this.hashId(goal);
        this.vectorMemory.getOrCreateCollection("goal_history");
        this.vectorMemory.upsert({
          collection: "goal_history",
          id: goalId,
          vector: vec,
          payload: {
            goal,
            status,
            duration_ms: durationMs,
            errors: errors.slice(0, 3),
          },
        });
      } catch {
        // silently skip
      }
    }

    // Collaboration review
    if (this.collaboration) {
      try {
        this.collaboration.submitReview({
          reviewer: "orchestrator",
          target: goal.slice(0, 30),
          approved: status === "success",
          feedback: errors.length > 0 ? [errors[0]] : ["Completed successfully"],
        });
      } catch {
        // silently skip
      }
    }
  }

  // -------------------------------------------------------------------------
  // Utility
  // -------------------------------------------------------------------------

  private hashGoal(goal: string): number[] {
    // Simple hash → vector placeholder (replace with real embedding)
    let hash = 0;
    for (let i = 0; i < goal.length; i++) {
      hash = ((hash << 5) - hash + goal.charCodeAt(i)) | 0;
    }
    // Produce a 16-dim vector from the hash
    const vec: number[] = [];
    for (let i = 0; i < 16; i++) {
      vec.push(((hash >> i) & 0xff) / 255);
    }
    return vec;
  }

  private hashId(goal: string): string {
    // Simple hash-based ID (use crypto.subtle in production)
    let hash = 0;
    for (let i = 0; i < goal.length; i++) {
      hash = ((hash << 5) - hash + goal.charCodeAt(i)) | 0;
    }
    return Math.abs(hash).toString(16).slice(0, 12);
  }
}
