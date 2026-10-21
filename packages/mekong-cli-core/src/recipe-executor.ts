/**
 * Recipe Executor — Shell step execution and summary formatting for recipes.
 */
import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type {
  Recipe,
  MarkdownRecipe,
  JsonRecipe,
  MarkdownStep,
  DagGroup,
  DagCommand,
} from '../../../plugins/mekong-tasks/types.js';

const execAsync = promisify(exec);

export interface CookOptions {
  platform?: string;
  recipeName?: string;
  recipesDir?: string;
  llmApiKey?: string;
  llmBaseUrl?: string;
  llmModel?: string;
}

export interface RunResult {
  recipeName: string;
  status: 'success' | 'failed' | 'skipped';
  stepsCompleted: number;
  stepsFailed: number;
  error?: string;
  output?: string;
}

export interface CookSummary {
  total: number;
  matched: number;
  skipped: number;
  results: RunResult[];
}

export interface ExecutableStep {
  order: number;
  title: string;
  description: string;
  mode: 'shell';
  depends_on: number[];
  params: Record<string, unknown>;
}

export interface ExecutableRecipe {
  name: string;
  description: string;
  platforms?: string[];
  steps: ExecutableStep[];
}

export function convertToExecutableRecipe(recipe: Recipe): ExecutableRecipe {
  if (recipe.format === 'markdown') {
    const mdRecipe = recipe as MarkdownRecipe;
    return {
      name: mdRecipe.name,
      description: mdRecipe.description,
      platforms: mdRecipe.platforms,
      steps: mdRecipe.steps.map((s: MarkdownStep) => ({
        order: s.order,
        title: s.title,
        description: s.command,
        mode: 'shell' as const,
        depends_on: [] as number[],
        params: {},
      })),
    };
  }
  const jsonRecipe = recipe as JsonRecipe;
  const steps: ExecutableStep[] = [];
  let order = 1;
  for (const group of jsonRecipe.dag.groups) {
    for (const cmd of group.commands) {
      steps.push({
        order: order++,
        title: cmd.id,
        description: cmd.args,
        mode: 'shell' as const,
        depends_on: [],
        params: {},
      });
    }
  }
  return {
    name: jsonRecipe.name,
    description: jsonRecipe.description,
    platforms: jsonRecipe.platforms,
    steps,
  };
}

export async function executeShellStep(
  command: string,
): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  try {
    const { stdout, stderr } = await execAsync(command, { maxBuffer: 1024 * 1024 * 10 });
    return { exitCode: 0, stdout, stderr };
  } catch (err: unknown) {
    const execErr = err as { code?: number; message?: string };
    return {
      exitCode: typeof execErr?.code === 'number' ? execErr.code : 1,
      stdout: '',
      stderr: execErr?.message ?? String(err),
    };
  }
}

export async function runRecipe(
  recipe: Recipe,
  _options: CookOptions = {},
): Promise<RunResult> {
  const startTime = Date.now();
  const steps: Array<{ order: number; title: string; description: string }> =
    recipe.format === 'markdown'
      ? (recipe as MarkdownRecipe).steps.map((s: MarkdownStep) => ({
          order: s.order,
          title: s.title,
          description: s.command,
        }))
      : (recipe as JsonRecipe).dag.groups.flatMap((g: DagGroup) =>
          g.commands.map((c: DagCommand, idx: number) => ({
            order: idx + 1,
            title: c.id,
            description: c.args,
          })),
        );

  let completed = 0;
  let failed = 0;
  let output = '';

  for (const step of steps) {
    const stepTitle = step.title || `Step ${step.order}`;
    const command = step.description || '';
    output += `\n[RUN] ${stepTitle}\n$ ${command}\n`;
    const result = await executeShellStep(command);
    if (result.exitCode === 0) {
      completed++;
      output += result.stdout + '\n';
    } else {
      failed++;
      output += `[ERROR] ${result.stderr}\n`;
    }
  }

  const duration = Date.now() - startTime;
  output += `\n[SUMMARY] ${recipe.name}: ${completed}/${completed + failed} steps in ${duration}ms\n`;

  return {
    recipeName: recipe.name,
    status: failed > 0 ? 'failed' : 'success',
    stepsCompleted: completed,
    stepsFailed: failed,
    output,
  };
}

export function formatCookSummary(summary: CookSummary): string {
  let output = `\n=== Cook Summary ===\nTotal recipes: ${summary.total}\nMatched: ${summary.matched}\nSkipped: ${summary.skipped}\n\nResults:\n`;
  for (const result of summary.results) {
    const icon = result.status === 'success' ? '✓' : result.status === 'skipped' ? '⊘' : '✗';
    output += `  ${icon} ${result.recipeName} (${result.stepsCompleted}/${result.stepsCompleted + result.stepsFailed} steps)\n`;
    if (result.error) output += `    Error: ${result.error}\n`;
  }
  return output;
}
