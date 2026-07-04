/**
 * Recipe Runner — Load, filter, và execute recipes.
 *
 * Supports platform-based filtering và recipe execution.
 */

import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';

import { loadRecipe, resolveRecipePath } from '../../../plugins/mekong-tasks/recipe-loader.js';
import type { Recipe, MarkdownRecipe, JsonRecipe, MarkdownStep, DagGroup, DagCommand } from '../../../plugins/mekong-tasks/types.js';

import { PlatformDetector } from './core/platform-detector.js';

const execAsync = promisify(exec);

// ─── Types ────────────────────────────────────────────────────────────────────

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

// ─── Recipe Loader ────────────────────────────────────────────────────────────

/**
 * Get recipes directory absolute path
 */
function getRecipesDir(customDir?: string): string {
  if (customDir && existsSync(customDir)) {
    return resolve(customDir);
  }
  // Default: recipes/ at project root
  const projectRoot = process.cwd();
  const defaultDir = join(projectRoot, 'recipes');
  if (!existsSync(defaultDir)) {
    throw new Error(`Recipes directory not found: ${defaultDir}`);
  }
  return defaultDir;
}

/**
 * Load INDEX.json từ recipes directory
 */
async function loadIndex(recipesDir: string): Promise<{ recipes: Array<{ name: string; path: string; category?: string; tags?: string[]; platforms?: string[] }> }> {
  const indexPath = join(recipesDir, 'INDEX.json');
  if (!existsSync(indexPath)) {
    throw new Error(`INDEX.json not found in ${recipesDir}`);
  }
  const content = await readFile(indexPath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Load tất cả recipes từ INDEX
 */
export async function loadAllRecipes(recipesDir?: string): Promise<Recipe[]> {
  const dir = getRecipesDir(recipesDir);
  const index = await loadIndex(dir);
  const recipes: Recipe[] = [];

  for (const entry of index.recipes) {
    try {
      const absPath = resolveRecipePath(dir, entry.path);
      const recipe = await loadRecipe(absPath);
      // Merge platforms từ INDEX entry (nếu có)
      if (entry.platforms && !recipe.platforms) {
        (recipe as any).platforms = entry.platforms;
      }
      recipes.push(recipe);
    } catch (err) {
      console.warn(`Failed to load recipe ${entry.name}: ${err}`);
    }
  }

  return recipes;
}

/**
 * Load một recipe cụ thể bằng name
 */
export async function loadRecipeByName(
  name: string,
  recipesDir?: string
): Promise<Recipe | null> {
  const dir = getRecipesDir(recipesDir);
  const index = await loadIndex(dir);
  const entry = index.recipes.find((r) => r.name === name || r.path.includes(name));
  if (!entry) {
    return null;
  }
  const absPath = resolveRecipePath(dir, entry.path);
  const recipe = await loadRecipe(absPath);
  if (entry.platforms && !recipe.platforms) {
    (recipe as any).platforms = entry.platforms;
  }
  return recipe;
}

// ─── Platform Filtering ───────────────────────────────────────────────────────

/**
 * Kiểm tra recipe có phù hợp platform không
 */
function recipeMatchesPlatform(recipe: Recipe, platform: string): boolean {
  if (!recipe.platforms || recipe.platforms.length === 0) {
    // Mặc định: general recipes chạy trên mọi platform
    return platform === 'general';
  }
  return recipe.platforms.includes(platform);
}

/**
 * Filter recipes theo platform
 */
export function filterRecipesByPlatform(
  recipes: Recipe[],
  platform: string
): Recipe[] {
  return recipes.filter((r) => recipeMatchesPlatform(r, platform));
}

// ─── Recipe Executor ──────────────────────────────────────────────────────────

/**
 * Chuyển đổi Recipe thành Recipe type (simplified)
 */
function convertToExecutableRecipe(recipe: Recipe): any {
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
  } else {
    const jsonRecipe = recipe as JsonRecipe;
    // Convert DAG groups to flat steps
    const steps: any[] = [];
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
}

/**
 * Execute một shell step
 */
async function executeShellStep(command: string): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  try {
    const { stdout, stderr } = await execAsync(command, { maxBuffer: 1024 * 1024 * 10 });
    return { exitCode: 0, stdout, stderr };
  } catch (err: any) {
    return { exitCode: err.code ?? 1, stdout: '', stderr: err.message ?? String(err) };
  }
}

/**
 * Run một recipe đơn (simplified execution)
 */
export async function runRecipe(
  recipe: Recipe,
  _options: CookOptions = {}
): Promise<RunResult> {
  const startTime = Date.now();
  let steps: Array<{ order: number; title: string; description: string }> = [];

  if (recipe.format === 'markdown') {
    const mdRecipe = recipe as MarkdownRecipe;
    steps = mdRecipe.steps.map((s: MarkdownStep) => ({ order: s.order, title: s.title, description: s.command }));
  } else {
    const jsonRecipe = recipe as JsonRecipe;
    steps = jsonRecipe.dag.groups.flatMap((g: DagGroup) =>
      g.commands.map((c: DagCommand, idx: number) => ({
        order: idx + 1,
        title: c.id,
        description: c.args,
      }))
    );
  }

  let completed = 0;
  let failed = 0;
  let output = '';

  // Simple sequential execution
  for (const step of steps) {
    const stepTitle = step.title || `Step ${step.order}`;
    const command = step.description || '';
    
    output += `\n[RUN] ${stepTitle}\n`;
    output += `$ ${command}\n`;

    const result = await executeShellStep(command);
    
    if (result.exitCode === 0) {
      completed++;
      output += result.stdout + '\n';
    } else {
      failed++;
      output += `[ERROR] ${result.stderr}\n`;
      // Continue on failure for now
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

// ─── Main Cook Orchestrator ───────────────────────────────────────────────────

/**
 * Main cook function
 */
export async function cook(options: CookOptions = {}): Promise<CookSummary> {
  const recipesDir = getRecipesDir(options.recipesDir);
  const platform = options.platform || 'general';
  const allRecipes = await loadAllRecipes(recipesDir);
  
  // Platform detection (warning only)
  try {
    const detector = new PlatformDetector(process.cwd());
    const detection = detector.detectPlatform();
    if (detection.platform !== platform) {
      console.warn(`[WARN] Detected platform: ${detection.platform} (confidence: ${detection.confidence.toFixed(2)})`);
      console.warn(`[WARN] Requested platform: ${platform} - proceeding with filter`);
    }
  } catch (err) {
    // PlatformDetector may fail if no git, ignore
  }

  // Filter recipes
  let targetRecipes = allRecipes;
  if (options.platform) {
    const beforeCount = targetRecipes.length;
    targetRecipes = filterRecipesByPlatform(targetRecipes, options.platform);
    console.log(`[INFO] Running ${platform}-only mode (${targetRecipes.length}/${beforeCount} recipes matched)`);
  }

  // Filter by recipe name if specified
  if (options.recipeName) {
    const recipe = await loadRecipeByName(options.recipeName, recipesDir);
    if (!recipe) {
      throw new Error(`Recipe not found: ${options.recipeName}`);
    }
    // Check platform compatibility
    if (options.platform && !recipeMatchesPlatform(recipe, options.platform)) {
      console.warn(`[SKIP] Recipe "${recipe.name}" does not support platform: ${platform}`);
      return {
        total: allRecipes.length,
        matched: 0,
        skipped: 1,
        results: [],
      };
    }
    targetRecipes = [recipe];
  }

  // Run recipes
  const results: RunResult[] = [];
  for (const recipe of targetRecipes) {
    console.log(`\n[RUN] Recipe: ${recipe.name}`);
    try {
      const result = await runRecipe(recipe, options);
      results.push(result);
    } catch (err: any) {
      results.push({
        recipeName: recipe.name,
        status: 'failed',
        stepsCompleted: 0,
        stepsFailed: 0,
        error: err.message,
      });
    }
  }

  return {
    total: allRecipes.length,
    matched: targetRecipes.length,
    skipped: options.recipeName ? 0 : allRecipes.length - targetRecipes.length,
    results,
  };
}

// ─── Utilities ────────────────────────────────────────────────────────────────

/**
 * Format cook summary for console output
 */
export function formatCookSummary(summary: CookSummary): string {
  let output = `\n=== Cook Summary ===\n`;
  output += `Total recipes: ${summary.total}\n`;
  output += `Matched: ${summary.matched}\n`;
  output += `Skipped: ${summary.skipped}\n`;
  output += `\nResults:\n`;
  
  for (const result of summary.results) {
    const icon = result.status === 'success' ? '✓' : result.status === 'skipped' ? '⊘' : '✗';
    output += `  ${icon} ${result.recipeName} (${result.stepsCompleted}/${result.stepsCompleted + result.stepsFailed} steps)\n`;
    if (result.error) {
      output += `    Error: ${result.error}\n`;
    }
  }
  
  return output;
}
