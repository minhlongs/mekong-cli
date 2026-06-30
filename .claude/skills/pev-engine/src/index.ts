/**
 * PEV Engine — barrel export.
 *
 * Plan → Execute → Verify engine for ClaudeKit.
 * TypeScript port of Mekong CLI's orchestrator (Python → TS).
 */

// Types
export type {
  RecipeStep,
  Recipe,
  ExecutionResult,
  VerificationStatus,
  VerificationCheck,
  VerificationReport,
  VerificationCriteria,
  CustomCheck,
  OrchestrationStatus,
  StepResult,
  OrchestrationResult,
  RetryConfig,
  DagNodeResult,
  SkillMeta,
} from "./types";

// Verifier
export { verify } from "./verifier";

// DAG Scheduler
export { DAGScheduler, validateDag } from "./dag-scheduler";

// Retry Policy
export { RetryPolicy } from "./retry-policy";

// Rollback Handler
export { RollbackHandler, handleFailure } from "./rollback-handler";

// AGI Components
export {
  AGIComponents,
  type ReflectionEngine,
  type ReflectionResult,
  type WorldModel,
  type WorldSnapshot,
  type WorldDiff,
  type RiskPrediction,
  type ToolRegistry,
  type ToolSuggestion,
  type ToolResult,
  type CollaborationProtocol,
  type RoleAssignment,
  type CodeEvolutionEngine,
  type CodeChange,
  type VectorMemoryStore,
  type MemoryResult,
  type AGIComponentMap,
} from "./agi";
