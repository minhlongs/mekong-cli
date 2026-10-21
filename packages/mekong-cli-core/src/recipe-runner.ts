/**
 * Recipe Runner — Load, filter, và execute recipes.
 */
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadRecipe, resolveRecipePath } from '../../../plugins/mekong-tasks/recipe-loader.js';
import type { Recipe } from '../../../plugins/mekong-tasks/types.js';
import { PlatformDetector } from './core/platform-detector.js';
import {
  runRecipe,
  formatCookSummary,
  type CookOptions,
  type RunResult,
  type CookSummary,
} from './recipe-executor.js';

export {
  runRecipe,
  formatCookSummary,
  type CookOptions,
  type RunResult,
  type CookSummary,
};

function getRecipesDir(customDir?: string): string {
  if (customDir && existsSync(customDir)) return resolve(customDir);
  const defaultDir = join(process.cwd(), 'recipes');
  if (!existsSync(defaultDir)) {
    throw new Error(`Recipes directory not found: ${defaultDir}`);
  }
  return defaultDir;
}

interface RecipeIndexEntry {
  name: string;
  path: string;
  category?: string;
  tags?: string[];
  platforms?: string[];
}

async function loadIndex(recipesDir: string): Promise<{ recipes: RecipeIndexEntry[] }> {
  const indexPath = join(recipesDir, 'INDEX.json');
  if (!existsSync(indexPath)) {
    throw new Error(`INDEX.json not found in ${recipesDir}`);
  }
  const content = await readFile(indexPath, 'utf-8');
  return JSON.parse(content) as { recipes: RecipeIndexEntry[] };
}

function assignPlatforms(recipe: Recipe, platforms?: string[]): Recipe {
  if (platforms && !recipe.platforms) {
    (recipe as { platforms?: string[] }).platforms = platforms;
  }
  return recipe;
}

export async function loadAllRecipes(recipesDir?: string): Promise<Recipe[]> {
  const dir = getRecipesDir(recipesDir);
  const index = await loadIndex(dir);
  const recipes: Recipe[] = [];

  for (const entry of index.recipes) {
    try {
      const absPath = resolveRecipePath(dir, entry.path);
      const recipe = await loadRecipe(absPath);
      recipes.push(assignPlatforms(recipe, entry.platforms));
    } catch (err) {
      console.warn(`Failed to load recipe ${entry.name}: ${err}`);
    }
  }
  return recipes;
}

export async function loadRecipeByName(
  name: string,
  recipesDir?: string,
): Promise<Recipe | null> {
  const dir = getRecipesDir(recipesDir);
  const index = await loadIndex(dir);
  const entry = index.recipes.find((r) => r.name === name || r.path.includes(name));
  if (!entry) return null;
  const absPath = resolveRecipePath(dir, entry.path);
  const recipe = await loadRecipe(absPath);
  return assignPlatforms(recipe, entry.platforms);
}

function recipeMatchesPlatform(recipe: Recipe, platform: string): boolean {
  if (!recipe.platforms || recipe.platforms.length === 0) {
    return platform === 'general';
  }
  return recipe.platforms.includes(platform);
}

export function filterRecipesByPlatform(
  recipes: Recipe[],
  platform: string,
): Recipe[] {
  return recipes.filter((r) => recipeMatchesPlatform(r, platform));
}

export async function cook(options: CookOptions = {}): Promise<CookSummary> {
  const recipesDir = getRecipesDir(options.recipesDir);
  const platform = options.platform || 'general';
  const allRecipes = await loadAllRecipes(recipesDir);

  try {
    const detector = new PlatformDetector(process.cwd());
    const detection = detector.detectPlatform();
    if (detection.platform !== platform) {
      console.warn(`[WARN] Detected platform: ${detection.platform} (confidence: ${detection.confidence.toFixed(2)})`);
      console.warn(`[WARN] Requested platform: ${platform} - proceeding with filter`);
    }
  } catch {
    // PlatformDetector may fail if no git, ignore
  }

  let targetRecipes = allRecipes;
  if (options.platform) {
    const beforeCount = targetRecipes.length;
    targetRecipes = filterRecipesByPlatform(targetRecipes, options.platform);
    console.log(`[INFO] Running ${platform}-only mode (${targetRecipes.length}/${beforeCount} recipes matched)`);
  }

  if (options.recipeName) {
    const recipe = await loadRecipeByName(options.recipeName, recipesDir);
    if (!recipe) throw new Error(`Recipe not found: ${options.recipeName}`);
    if (options.platform && !recipeMatchesPlatform(recipe, options.platform)) {
      console.warn(`[SKIP] Recipe "${recipe.name}" does not support platform: ${platform}`);
      return { total: allRecipes.length, matched: 0, skipped: 1, results: [] };
    }
    targetRecipes = [recipe];
  }

  const results: RunResult[] = [];
  for (const recipe of targetRecipes) {
    console.log(`\n[RUN] Recipe: ${recipe.name}`);
    try {
      results.push(await runRecipe(recipe, options));
    } catch (err: unknown) {
      results.push({
        recipeName: recipe.name,
        status: 'failed',
        stepsCompleted: 0,
        stepsFailed: 0,
        error: err instanceof Error ? err.message : String(err),
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
