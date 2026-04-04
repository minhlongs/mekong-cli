/**
 * mekong-tasks — OpenClaw /tasks adapter plugin
 *
 * Wires Mekong recipe files to the OpenClaw /tasks background task board.
 * Supports both JSON DAG recipes and Markdown step-list recipes.
 *
 * Usage:
 *   import { createMekongTasksPlugin } from '@mekong/mekong-tasks'
 *
 *   const plugin = createMekongTasksPlugin('/path/to/recipes')
 *   const task   = await plugin.register('business/revenue-engine.json')
 *   const result = await plugin.execute(task.id, (e) => console.log(e))
 */

import { randomUUID } from 'node:crypto';
import { loadRecipe } from './recipe-loader.js';
import { executeDag } from './dag-executor.js';
import { recipeToTaskSteps, applyArgs } from './recipe-to-steps.js';
import type {
  OpenClawTask,
  TaskStep,
  TaskResult,
  TaskStatus,
  TasksPlugin,
  ProgressCallback,
} from './types.js';

// ─── Plugin config ─────────────────────────────────────────────────────────────

export interface MekongTasksPluginConfig {
  /** Absolute path to recipes/ directory */
  recipesDir: string;
  /** Default max retries per step (default: 2) */
  defaultMaxRetries?: number;
}

// ─── Plugin class ─────────────────────────────────────────────────────────────

export class MekongTasksPlugin implements TasksPlugin {
  readonly name = 'mekong-tasks';
  readonly version = '1.0.0';

  private readonly recipesDir: string;
  private readonly defaultMaxRetries: number;
  private readonly store = new Map<string, OpenClawTask>();

  constructor(config: MekongTasksPluginConfig) {
    this.recipesDir = config.recipesDir;
    this.defaultMaxRetries = config.defaultMaxRetries ?? 2;
  }

  /**
   * Loads a recipe file and registers it as an OpenClaw task.
   *
   * @param recipePath  Path relative to recipesDir (e.g. "sales/pipeline-build.json")
   * @param args        Substitutions for $ARGUMENTS / $KEY placeholders in commands
   */
  async register(
    recipePath: string,
    args: Record<string, string> = {}
  ): Promise<OpenClawTask> {
    const absPath = recipePath.startsWith('/')
      ? recipePath
      : `${this.recipesDir}/${recipePath}`;

    console.log(`[mekong-tasks] loading recipe: ${absPath}`);
    const recipe = await loadRecipe(absPath);

    const rawSteps = recipeToTaskSteps(recipe, this.defaultMaxRetries);
    const steps = applyArgs(rawSteps, args);

    const task: OpenClawTask = {
      id: randomUUID(),
      name: recipe.name,
      description: recipe.description,
      recipePath,
      steps,
      status: 'pending',
      createdAt: Date.now(),
    };

    this.store.set(task.id, task);
    console.log(
      `[mekong-tasks] registered "${task.name}" (id=${task.id}, steps=${steps.length})`
    );
    return task;
  }

  /**
   * Executes a registered task through the DAG executor.
   * Fires ProgressEvents for every step state change — consumed by /tasks board.
   */
  async execute(
    taskId: string,
    onProgress?: ProgressCallback
  ): Promise<TaskResult> {
    const task = this.store.get(taskId);
    if (!task) throw new Error(`Task not found: ${taskId}`);
    if (task.status === 'running') throw new Error(`Task already running: ${taskId}`);

    const progressFn: ProgressCallback =
      onProgress ??
      ((e) => console.log(`[mekong-tasks] [${e.taskId}] ${e.stepId} ${e.status}: ${e.message}`));

    task.status = 'running';
    task.startedAt = Date.now();
    this.store.set(taskId, task);

    const result = await executeDag(taskId, task.steps, progressFn);

    task.status = result.status;
    task.completedAt = Date.now();
    if (result.status === 'failed') {
      const failedStep = result.stepResults.find((r) => r.status === 'failed');
      task.error = failedStep?.error ?? 'Unknown error';
    }
    this.store.set(taskId, task);

    return result;
  }

  list(): OpenClawTask[] {
    return [...this.store.values()];
  }

  get(taskId: string): OpenClawTask | undefined {
    return this.store.get(taskId);
  }
}

// ─── Factory helper ───────────────────────────────────────────────────────────

/**
 * Creates a MekongTasksPlugin bound to the given recipes directory.
 *
 * Example registration with OpenClaw /tasks system:
 *   const plugin = createMekongTasksPlugin(path.join(process.cwd(), 'recipes'))
 *   openClaw.tasks.registerPlugin(plugin)
 */
export function createMekongTasksPlugin(
  recipesDir: string,
  options?: Partial<Omit<MekongTasksPluginConfig, 'recipesDir'>>
): MekongTasksPlugin {
  return new MekongTasksPlugin({ recipesDir, ...options });
}

// Re-export types for consumers
export type {
  OpenClawTask,
  TaskStep,
  TaskResult,
  TaskStatus,
  ProgressCallback,
  TasksPlugin,
} from './types.js';
