/**
 * recipe-loader.ts — reads recipe files from recipes/ directory.
 *
 * Handles two formats:
 *   - JSON (.json): DAG-based recipes (business/, sales/, engineering/, etc.)
 *   - Markdown (.md): simple step-list recipes (hello-mekong.md, etc.)
 */

import { readFile } from 'node:fs/promises';
import { extname, basename, join } from 'node:path';
import type {
  Recipe,
  JsonRecipe,
  MarkdownRecipe,
  MarkdownStep,
  DagGroup,
} from './types.js';

// ─── JSON loader ──────────────────────────────────────────────────────────────

/**
 * Parses a JSON DAG recipe file.
 * Validates required fields and provides safe defaults for optional ones.
 */
function parseJsonRecipe(raw: unknown, filePath: string): JsonRecipe {
  const obj = raw as Record<string, unknown>;

  if (!obj.id || typeof obj.id !== 'string') {
    throw new Error(`Recipe at ${filePath} missing required field "id"`);
  }
  if (!obj.name || typeof obj.name !== 'string') {
    throw new Error(`Recipe at ${filePath} missing required field "name"`);
  }

  const dagRaw = (obj.dag ?? {}) as Record<string, unknown>;
  const groupsRaw = Array.isArray(dagRaw.groups) ? dagRaw.groups : [];

  const groups: DagGroup[] = groupsRaw.map((g: unknown, i: number) => {
    const group = g as Record<string, unknown>;
    return {
      id: String(group.id ?? `group-${i}`),
      name: String(group.name ?? `Group ${i}`),
      mode: group.mode === 'sequential' ? 'sequential' : 'parallel',
      commands: Array.isArray(group.commands)
        ? group.commands.map((c: unknown) => {
            const cmd = c as Record<string, unknown>;
            return {
              id: String(cmd.id ?? ''),
              args: String(cmd.args ?? ''),
            };
          })
        : [],
      depends_on: Array.isArray(group.depends_on)
        ? group.depends_on.map(String)
        : [],
    };
  });

  const onCompleteRaw = dagRaw.on_complete as Record<string, unknown> | undefined;

  return {
    format: 'json',
    id: obj.id,
    name: obj.name,
    description: String(obj.description ?? ''),
    trigger: String(obj.trigger ?? ''),
    path: filePath,
    output_dir: String(obj.output_dir ?? 'reports'),
    estimated_credits: Number(obj.estimated_credits ?? 0),
    estimated_minutes: Number(obj.estimated_minutes ?? 0),
    version: obj.version ? String(obj.version) : undefined,
    layer: obj.layer ? String(obj.layer) : undefined,
    dag: {
      groups,
      on_complete: onCompleteRaw
        ? {
            compile_summary: Boolean(onCompleteRaw.compile_summary),
            summary_file: onCompleteRaw.summary_file
              ? String(onCompleteRaw.summary_file)
              : undefined,
            template: onCompleteRaw.template
              ? String(onCompleteRaw.template)
              : undefined,
          }
        : undefined,
    },
  };
}

// ─── Markdown loader ──────────────────────────────────────────────────────────

/**
 * Parses a markdown recipe.
 *
 * Format expected:
 *   # Recipe Title
 *   ## Step N: Title
 *   <command>
 *
 * Steps are extracted from ## headings that start with "Step " (case-insensitive).
 * Command body = all non-blank lines between the heading and the next heading.
 */
function parseMarkdownRecipe(content: string, filePath: string): MarkdownRecipe {
  const lines = content.split('\n');

  // First # heading becomes the name
  const h1 = lines.find((l) => l.startsWith('# '));
  const name = h1 ? h1.slice(2).trim() : basename(filePath, '.md');

  // Description: first paragraph after h1, before any ## heading
  let descLines: string[] = [];
  let inDesc = !!h1;
  for (const line of lines) {
    if (line.startsWith('# ')) { inDesc = true; continue; }
    if (line.startsWith('## ')) { inDesc = false; break; }
    if (inDesc && line.trim()) descLines.push(line.trim());
  }
  const description = descLines.join(' ');

  const steps: MarkdownStep[] = [];
  let currentStep: MarkdownStep | null = null;
  const stepHeadingRe = /^## step\s+(\d+)[:\s]+(.+)/i;

  for (const line of lines) {
    const match = stepHeadingRe.exec(line);
    if (match) {
      if (currentStep) steps.push(currentStep);
      currentStep = {
        order: parseInt(match[1], 10),
        title: match[2].trim(),
        command: '',
      };
      continue;
    }
    // Accumulate command lines under the current step
    if (currentStep && !line.startsWith('#') && line.trim()) {
      currentStep.command = currentStep.command
        ? `${currentStep.command}\n${line.trim()}`
        : line.trim();
    }
  }
  if (currentStep) steps.push(currentStep);

  return {
    format: 'markdown',
    name,
    description,
    path: filePath,
    steps,
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Loads a recipe from an absolute or recipes/-relative file path.
 *
 * @param filePath  Absolute path to a .json or .md recipe file
 */
export async function loadRecipe(filePath: string): Promise<Recipe> {
  let content: string;
  try {
    content = await readFile(filePath, 'utf-8');
  } catch {
    throw new Error(`Cannot read recipe file: ${filePath}`);
  }

  const ext = extname(filePath).toLowerCase();

  if (ext === '.json') {
    let raw: unknown;
    try {
      raw = JSON.parse(content);
    } catch {
      throw new Error(`Invalid JSON in recipe: ${filePath}`);
    }
    return parseJsonRecipe(raw, filePath);
  }

  if (ext === '.md') {
    return parseMarkdownRecipe(content, filePath);
  }

  throw new Error(`Unsupported recipe format "${ext}" for: ${filePath}`);
}

/**
 * Resolves a relative recipe path (from INDEX.json) to an absolute path.
 *
 * @param recipesDir  Absolute path to the recipes/ directory
 * @param relativePath  Path from INDEX.json (e.g. "business/revenue-engine.json")
 */
export function resolveRecipePath(recipesDir: string, relativePath: string): string {
  return join(recipesDir, relativePath);
}
