/**
 * mekong-tasks plugin — TypeScript types
 *
 * Covers both recipe formats:
 *   - Markdown (.md): simple step list parsed from ## headings + shell commands
 *   - JSON (.json): DAG with groups, modes (parallel/sequential), depends_on
 */

// ─── Markdown recipe step ─────────────────────────────────────────────────────

export interface MarkdownStep {
  /** Step number (1-based, from heading order) */
  order: number;
  /** Heading text after "Step N:" */
  title: string;
  /** Shell command body under the heading */
  command: string;
}

export interface MarkdownRecipe {
  format: 'markdown';
  /** Display name (first # heading or filename) */
  name: string;
  description: string;
  path: string;
  steps: MarkdownStep[];
}

// ─── JSON DAG recipe ──────────────────────────────────────────────────────────

export type GroupMode = 'parallel' | 'sequential';

export interface DagCommand {
  /** Mekong command id (e.g. "market-analysis", "cook") */
  id: string;
  /** CLI args passed to the command, may contain $ARGUMENTS placeholder */
  args: string;
}

export interface DagGroup {
  /** Unique group id within the recipe */
  id: string;
  name: string;
  mode: GroupMode;
  commands: DagCommand[];
  /** Group ids this group must wait for before starting */
  depends_on: string[];
}

export interface DagOnComplete {
  compile_summary?: boolean;
  summary_file?: string;
  template?: string;
}

export interface JsonRecipe {
  format: 'json';
  id: string;
  name: string;
  description: string;
  trigger: string;
  path: string;
  output_dir: string;
  estimated_credits: number;
  estimated_minutes: number;
  /** Optional version / layer metadata */
  version?: string;
  layer?: string;
  dag: {
    groups: DagGroup[];
    on_complete?: DagOnComplete;
  };
}

// ─── Union recipe type ────────────────────────────────────────────────────────

export type Recipe = MarkdownRecipe | JsonRecipe;

// ─── OpenClaw /tasks board types ─────────────────────────────────────────────

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface TaskStep {
  /** Stable id: "<group.id>/<command.id>" for JSON, "step-N" for markdown */
  id: string;
  name: string;
  /** Shell command or mekong command string to execute */
  command: string;
  /** Step ids this step depends on */
  deps: string[];
  /** Retry limit for this step */
  maxRetries: number;
}

export interface OpenClawTask {
  /** Globally unique task id */
  id: string;
  /** Human readable label */
  name: string;
  description: string;
  /** Source recipe path (relative to recipes/) */
  recipePath: string;
  steps: TaskStep[];
  status: TaskStatus;
  createdAt: number;
  startedAt?: number;
  completedAt?: number;
  /** Aggregated error from any failed step */
  error?: string;
}

export interface StepResult {
  stepId: string;
  status: TaskStatus;
  stdout: string;
  stderr: string;
  durationMs: number;
  /** Number of attempts used (1 = first try succeeded) */
  attempts: number;
  error?: string;
}

export interface TaskResult {
  taskId: string;
  status: TaskStatus;
  stepResults: StepResult[];
  totalDurationMs: number;
}

// ─── Plugin registration interface ───────────────────────────────────────────

export interface ProgressEvent {
  taskId: string;
  stepId: string;
  status: TaskStatus;
  message: string;
  timestamp: number;
}

export type ProgressCallback = (event: ProgressEvent) => void;

export interface TasksPlugin {
  name: string;
  version: string;
  /** Register an OpenClaw task from a recipe path */
  register(recipePath: string, args?: Record<string, string>): Promise<OpenClawTask>;
  /** Execute a registered task */
  execute(taskId: string, onProgress?: ProgressCallback): Promise<TaskResult>;
  /** List all registered tasks */
  list(): OpenClawTask[];
  /** Get single task by id */
  get(taskId: string): OpenClawTask | undefined;
}
