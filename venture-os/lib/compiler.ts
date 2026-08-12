/**
 * VentureOS Compiler — transforms venture artifacts into final outputs
 *
 * Compilers are pipeline modules that:
 * 1. Gather inputs from artifacts/ and knowledge/
 * 2. Apply transformation rules (structure, content, validation)
 * 3. Emit compiled outputs (docs, specs, configs)
 *
 * Output naming: {venture_id}_{compiler_id}_{timestamp}.{ext}
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface CompilerInput {
  name: string;
  type: string;
  required: boolean;
  path: string;
}

export interface CompilerOutput {
  name: string;
  type: string;
  path: string;
}

export interface CompilerDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  inputs: CompilerInput[];
  outputs: CompilerOutput[];
}

export interface CompilerResult {
  compilerId: string;
  success: boolean;
  outputs: Array<{ name: string; path: string; size: number }>;
  errors: string[];
  warnings: string[];
  compiledAt: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ts(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
}

function die(msg: string): never {
  console.error(`\x1b[31mError:\x1b[0m ${msg}`);
  process.exit(1);
}

function isDir(p: string): boolean {
  try { return statSync(p).isDirectory(); } catch { return false; }
}

// ─── Compiler Loading ────────────────────────────────────────────────────────

export function loadCompiler(compilerId: string): CompilerDefinition {
  let path: string;
  if (compilerId.includes('/')) {
    path = join(ROOT, 'workflows', 'compiler', compilerId, 'compiler.yaml');
  } else {
    const found = findCompiler(compilerId);
    if (!found) die(`Compiler not found: ${compilerId}`);
    path = found;
  }
  if (!existsSync(path)) die(`Compiler not found: ${path}`);
  return parseCompilerYaml(readFileSync(path, 'utf-8'));
}

function findCompiler(id: string): string | null {
  const compilerRoot = join(ROOT, 'workflows', 'compiler');
  if (!existsSync(compilerRoot)) return null;
  for (const category of readdirSync(compilerRoot)) {
    const catDir = join(compilerRoot, category);
    if (!isDir(catDir)) continue;
    const flatYaml = join(catDir, 'compiler.yaml');
    if (existsSync(flatYaml)) {
      try {
        const def = parseCompilerYaml(readFileSync(flatYaml, 'utf-8'));
        if (def.id === id) return flatYaml;
      } catch { /* skip */ }
    }
    for (const name of readdirSync(catDir)) {
      const candidate = join(catDir, name, 'compiler.yaml');
      if (existsSync(candidate)) {
        try {
          const def = parseCompilerYaml(readFileSync(candidate, 'utf-8'));
          if (def.id === `${category}/${name}` || def.id === name) return candidate;
        } catch { /* skip */ }
      }
    }
  }
  return null;
}

export function listCompilers(): Array<{ id: string; name: string }> {
  const compilers: Array<{ id: string; name: string }> = [];
  const compilerRoot = join(ROOT, 'workflows', 'compiler');
  if (!existsSync(compilerRoot)) return compilers;
  for (const category of readdirSync(compilerRoot)) {
    const catDir = join(compilerRoot, category);
    if (!isDir(catDir)) continue;
    const directYaml = join(catDir, 'compiler.yaml');
    if (existsSync(directYaml)) {
      try {
        const def = parseCompilerYaml(readFileSync(directYaml, 'utf-8'));
        compilers.push({ id: def.id, name: def.name });
      } catch { /* skip */ }
    }
    for (const name of readdirSync(catDir)) {
      const yamlPath = join(catDir, name, 'compiler.yaml');
      if (!existsSync(yamlPath)) continue;
      try {
        const def = parseCompilerYaml(readFileSync(yamlPath, 'utf-8'));
        compilers.push({ id: def.id, name: def.name });
      } catch { /* skip */ }
    }
  }
  return compilers;
}

// ─── Compiler Runner ─────────────────────────────────────────────────────────

export async function runCompiler(
  compilerId: string,
  ventureDir: string,
  ventureId: string,
): Promise<CompilerResult> {
  const def = loadCompiler(compilerId);
  const result: CompilerResult = {
    compilerId,
    success: true,
    outputs: [],
    errors: [],
    warnings: [],
    compiledAt: new Date().toISOString(),
  };

  console.log(`\n\x1b[1mRunning compiler: ${def.name}\x1b[0m`);
  console.log(` Venture: ${ventureId}`);
  console.log(` Inputs: ${def.inputs.length} | Outputs: ${def.outputs.length}\n`);

  function getArtifactPath(input: CompilerInput, ventureDir: string, ventureId: string): string {
    const primary = join(ventureDir, input.path.replace('{venture_id}', ventureId));
    if (existsSync(primary)) return primary;
    return join(ventureDir, 'knowledge', 'local', input.path.replace('{venture_id}', ''));
  }

  const inputs = new Map<string, unknown>();
  for (const input of def.inputs) {
    const resolved = resolveInput(input, ventureDir, ventureId);
    if (resolved === null) {
      if (input.required) {
        result.errors.push(`Missing required input: ${input.name} (${input.path})`);
        result.success = false;
      } else {
        result.warnings.push(`Missing optional input: ${input.name}`);
      }
    } else {
      const artifactPath = getArtifactPath(input, ventureDir, ventureId);
      if (!validateArtifact(artifactPath, input.type)) {
        result.warnings.push(`Invalid artifact: ${input.name} (type: ${input.type}) — skipping`);
        continue;
      }
      inputs.set(input.name, resolved);
    }
  }

  if (!result.success) {
    result.compiledAt = new Date().toISOString();
    appendWAL(ventureDir, { type: 'compile_complete', compiler_id: compilerId, success: false, errors: result.errors });
    return result;
  }

  try {
    const outputs = await compilePipeline(def, inputs, ventureDir, ventureId);
    result.outputs = outputs;
    appendWAL(ventureDir, { type: 'compile_complete', compiler_id: compilerId, success: true, outputs: outputs.map(o => o.name) });
    console.log(`\n\x1b[32m✓\x1b[0m Compiler complete: ${outputs.length} output(s)`);
  } catch (err) {
    result.success = false;
    result.errors.push(err instanceof Error ? err.message : String(err));
    appendWAL(ventureDir, { type: 'compile_complete', compiler_id: compilerId, success: false, errors: result.errors });
    console.log(`\n\x1b[31m✗\x1b[0m Compiler failed: ${result.errors[0]}`);
  }

  result.compiledAt = new Date().toISOString();
  return result;
}

// ─── Input Resolution ────────────────────────────────────────────────────────

function resolveInput(input: CompilerInput, ventureDir: string, ventureId: string): unknown | null {
  // idea_description: pull from decisions/*.md frontmatter (problem field), then state.json
if (input.name === 'idea_description') {
const idea = extractIdeaFromDecisions(ventureDir) ?? loadFile(join(ventureDir, 'state.json'));
if (idea) return idea;
}
const artifactPath = join(ventureDir, input.path.replace('{venture_id}', ventureId));
if (!existsSync(artifactPath)) {
const knowledgeBase = join(ventureDir, 'knowledge', 'local', input.path.replace('{venture_id}', ''));
if (existsSync(knowledgeBase)) return loadFile(knowledgeBase);
return null;
}
return loadFile(artifactPath);
}

/** Read decisions/*.md frontmatter and return the first `problem:` value as idea text. */
function extractIdeaFromDecisions(ventureDir: string): string | null {
const decisionsDir = join(ventureDir, 'decisions');
if (!existsSync(decisionsDir)) return null;
const files = readdirSync(decisionsDir).filter((f) => f.endsWith('.md'));
if (files.length === 0) return null;
for (const file of files) {
const raw = readFileSync(join(decisionsDir, file), 'utf-8');
const m = raw.match(/^problem:\s*["'\"\']?(.+?)["'\"\']?\s*$/m);
if (m?.[1]) return m[1].trim();
}
return null;
}

function loadFile(path: string): unknown {
  const content = readFileSync(path, 'utf-8');
  try { return JSON.parse(content); } catch { /* not JSON */ }
  if (path.endsWith('.toml') || /^\s*\[[\w.\]]+\]\s*$/.test(content)) {
    return parseToml(content);
  }
  return content;
}

// ─── TOML Parser ────────────────────────────────────────────────────────────

function parseToml(content: string): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  let cur: Record<string, unknown> = result;

  for (const raw of content.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;

    const secMatch = line.match(/^\[([^\]\r\n]+)\]$/);
    if (secMatch) {
      const keys = secMatch[1].split('.');
      cur = result;
      for (const k of keys) {
        if (!(k in cur) || typeof (cur as Record<string, unknown>)[k] !== 'object') {
          (cur as Record<string, unknown>)[k] = {} as Record<string, unknown>;
        }
        cur = (cur as Record<string, unknown>)[k] as Record<string, unknown>;
      }
      continue;
    }

    const kvMatch = line.match(/^(\w+)\s*=\s*"(.*)"$/);
    if (kvMatch) {
      (cur as Record<string, unknown>)[kvMatch[1]] = kvMatch[2];
    }
  }

  return result;
}

// ─── Value Formatting ────────────────────────────────────────────────────────

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return 'undefined';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (Array.isArray(v)) {
    if (v.length === 0) return '(empty)';
    return v.map(item => ` - ${formatValue(item)}`).join('\n');
  }
  if (typeof v === 'object') {
    return Object.entries(v as Record<string, unknown>)
      .map(([k, val]) => ` ${k}: ${formatValue(val)}`)
      .join('\n');
  }
  return String(v);
}

// ─── Compiler Pipeline ───────────────────────────────────────────────────────

async function compilePipeline(
  def: CompilerDefinition,
  inputs: Map<string, unknown>,
  ventureDir: string,
  ventureId: string,
): Promise<Array<{ name: string; path: string; size: number }>> {
  const results: Array<{ name: string; path: string; size: number }> = [];

  for (const output of def.outputs) {
    const rawPath = output.path.replace('{venture_id}', ventureId);
    const outPath = join(ventureDir, 'artifacts', 'compiled', rawPath.replace(/^compiled\//, ''));
    mkdirSync(dirname(outPath), { recursive: true });

    let content: string;
    switch (output.type) {
      case 'markdown': content = compileMarkdown(inputs, def, ventureDir); break;
      case 'json': content = JSON.stringify(compileJson(inputs, def), null, 2); break;
      case 'yaml': content = compileYaml(inputs, def); break;
      default: content = compileMarkdown(inputs, def, ventureDir);
    }

    writeFileSync(outPath, content);
    results.push({ name: output.name, path: output.path, size: content.length });
    console.log(` \x1b[32m✓\x1b[0m ${output.name} → ${output.path}`);
  }

  return results;
}

// ─── Markdown Compiler (template.md + inline fallback) ──────────────────────

function compileMarkdown(inputs: Map<string, unknown>, def: CompilerDefinition, ventureDir?: string): string {
  const venture = inputs.get('venture_id');
  const idea = inputs.get('idea_description');
  const market = inputs.get('market_research') as Record<string, unknown> | undefined;

  // Parse venture data: input may be raw TOML string or already-parsed object
  let ventureObj: Record<string, unknown> | null = null;
  if (typeof venture === 'string') {
    const parsed = parseToml(venture);
    if (parsed.id) {
      ventureObj = parsed;
    } else if (ventureDir) {
      const tp = join(ventureDir, 'venture.toml');
      if (existsSync(tp)) ventureObj = parseToml(readFileSync(tp, 'utf-8'));
    }
  } else if (typeof venture === 'object' && venture !== null) {
    ventureObj = venture as Record<string, unknown>;
  }

  // Load lifecycle from state.json
  let lifecyclePhase = 'ideation', lifecycleLabel = 'Ideation';
  if (ventureDir) {
    const sp = join(ventureDir, 'state.json');
    if (existsSync(sp)) {
      try {
        const state = JSON.parse(readFileSync(sp, 'utf-8'));
        lifecyclePhase = state.current_phase ?? 'ideation';
        lifecycleLabel = state.phase_label ?? 'Ideation';
      } catch { /* ignore */ }
    }
  }

  // Extract venture fields (handles nested TOML like {id: {name, id, type}})
  function getV(obj: Record<string, unknown> | null, key: string): string {
    if (!obj) return 'unknown';
    if (typeof obj[key] === 'string') return obj[key];
    for (const val of Object.values(obj)) {
      if (val && typeof val === 'object' && !Array.isArray(val)) {
        const n = val as Record<string, unknown>;
        if (typeof n[key] === 'string') return n[key];
      }
    }
    return 'unknown';
  }
  const id = getV(ventureObj, 'id');
  const name = getV(ventureObj, 'name');
  const type = getV(ventureObj, 'type');
  const ventureHeader = type ? `${name} (${type}) — ${id}` : `${name} — ${id}`;

  // Extract idea description — prefer structured fields, fall back to raw string
  let ideaText: string;
  if (typeof idea === 'object' && idea !== null) {
    const i = idea as Record<string, unknown>;
    ideaText =
      (typeof i.description === 'string' && i.description) ||
      (typeof i.summary === 'string' && i.summary) ||
      (typeof i.vision === 'string' && i.vision) ||
      'No idea description yet.';
  } else if (typeof idea === 'string' && idea) {
    ideaText = idea;
  } else {
    ideaText = 'No idea description yet.';
  }

  // Build template render context
  const lifecycle = { current_phase: lifecyclePhase, phase_label: lifecycleLabel };
  const templateCtx: Record<string, unknown> = {
    venture: { name, type, id },
    idea: { description: ideaText },
    lifecycle,
    market: market ?? null,
    compiledAt: new Date().toISOString(),
  };
  // Flat aliases for {{key.subkey}} access
  templateCtx['venture.name'] = name;
  templateCtx['venture.type'] = type;
  templateCtx['venture.id'] = id;
  templateCtx['idea.description'] = ideaText;
  templateCtx['lifecycle.current_phase'] = lifecyclePhase;
  templateCtx['lifecycle.phase_label'] = lifecycleLabel;
  templateCtx['compiled_at'] = new Date().toISOString();
  // Flat aliases for market fields (supports standalone {{market.xxx}} in templates)
  templateCtx['market.tam'] = market?.tam ?? 'N/A';
  templateCtx['market.sam'] = market?.sam ?? 'N/A';
  templateCtx['market.som'] = market?.som ?? 'N/A';
  templateCtx['market.trends'] = (market?.trends ?? market?.marketTrends) ?? [];
  templateCtx['market.competitors'] = (market?.competitors ?? market?.competitorList) ?? [];

  // ─── Try template.md first ───────────────────────────────────────────────────
  const compilerId = def.id;
  const templatePath = join(ROOT, 'workflows', 'compiler', compilerId, 'template.md');

  if (existsSync(templatePath)) {
    try {
      const template = readFileSync(templatePath, 'utf-8');
      return renderMustache(template, templateCtx, market);
    } catch {
      // fall through to inline template
    }
  }

  // ─── Inline fallback (existing behavior) ────────────────────────────────────
  const lines: string[] = [
    `# ${def.name}`, '',
    `> Generated: ${new Date().toISOString()}`,
    `> Venture: ${ventureHeader}`, '',
    '## Problem', '', ideaText.slice(0, 200), '',
    '## Market Context', '',
  ];

  if (market) {
    lines.push('**TAM:**'); lines.push(formatValue(market.tam ?? 'unknown')); lines.push('');
    lines.push('**SAM:**'); lines.push(formatValue(market.sam ?? 'unknown')); lines.push('');
    lines.push('**SOM:**'); lines.push(formatValue(market.som ?? 'unknown')); lines.push('');

    const trendsSource = market.trends ?? market.marketTrends;
    if (Array.isArray(trendsSource) && trendsSource.length > 0) {
      lines.push('**Trends:**');
      for (const t of trendsSource) lines.push(` - ${formatValue(t)}`);
      lines.push('');
    }

    const compsSource = market.competitors ?? market.competitorList;
    if (Array.isArray(compsSource) && compsSource.length > 0) {
      lines.push('**Competitors:**');
      for (const c of compsSource) lines.push(` - ${formatValue(c)}`);
      lines.push('');
    }
  } else {
    lines.push('No market research data available.');
  }

  lines.push('', '---', `> Compiled by VentureOS ${def.version}`);
  return lines.join('\n');
}

// ─── Mustache Template Renderer ──────────────────────────────────────────────

function renderMustache(template: string, ctx: Record<string, unknown>, market?: Record<string, unknown> | null): string {
  let output = template;

  // 1. Handle {{#market}} ... {{/market}} blocks and section blocks
  if (market) {
    output = renderMarketSection(output, market);
  } else {
    // Remove empty market blocks
    output = output.replace(/\{\{#market\}\}[\s\S]*?\{\{\/market\}\}/g, '');
    output = output.replace(/\{\{#market\.\w+\}\}[\s\S]*?\{\{\/\w+\.\w+\}\}/g, '');
  }

  // 2. Simple {{key}} or {{key.subkey}} → value replacement
  output = output.replace(/\{\{([a-zA-Z_][\w.]*)\}\}/g, (_match: string, key: string) => {
    if (key.includes('.')) {
      const val = traverseCtx(key, ctx);
      return val !== `{{${key}}}` ? val : _match;
    }
    return ctx[key] as string ?? _match;
  });

  // 3. Remove any remaining unmatched closing tags
  output = output.replace(/\{\{\/\w+(?:\.\w+)*\}\}/g, '');

  // 4. Strip any lines that still contain raw placeholders
  output = output.split('\n').filter(line => !/\{\{/.test(line)).join('\n');

  return output;
}

function traverseCtx(path: string, ctx: Record<string, unknown>): string {
  const parts = path.split('.');
  let current: unknown = ctx;
  for (const part of parts) {
    if (typeof current === 'object' && current !== null && part in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return `{{${path}}}`;
    }
  }
  return typeof current === 'string' ? current : formatValue(current);
}

function renderMarketSection(template: string, market: Record<string, unknown>): string {
  let output = template;

  // Replace {{#market}} ... {{/market}} blocks
  output = output.replace(/\{\{#market\}\}([\s\S]*?)\{\{\/market\}\}/g, (_match: string, block: string) => {
    let rendered = block;

    // TAM/SAM/SOM
    rendered = rendered.replace(/\{\{market\.tam\}\}/g, formatValue(market.tam ?? 'N/A'));
    rendered = rendered.replace(/\{\{market\.sam\}\}/g, formatValue(market.sam ?? 'N/A'));
    rendered = rendered.replace(/\{\{market\.som\}\}/g, formatValue(market.som ?? 'N/A'));

    // Trends array
    const trends = (market.trends ?? market.marketTrends) as string[] | undefined;
    if (Array.isArray(trends) && trends.length > 0) {
      const trendsPattern = /\{\{#market\.trends\}\}([\s\S]*?)\{\{\/market\.trends\}\}/;
      rendered = rendered.replace(trendsPattern, () => trends.map(t => ` - ${t}`).join('\n'));
    } else {
      rendered = rendered.replace(/\{\{#market\.trends\}\}[\s\S]*?\{\{\/market\.trends\}\}/g, '');
    }

    // Competitors array
    const competitors = (market.competitors ?? market.competitorList) as string[] | undefined;
    if (Array.isArray(competitors) && competitors.length > 0) {
      const compsPattern = /\{\{#market\.competitors\}\}([\s\S]*?)\{\{\/market\.competitors\}\}/;
      rendered = rendered.replace(compsPattern, () => competitors.map(c => ` - ${c}`).join('\n'));
    } else {
      rendered = rendered.replace(/\{\{#market\.competitors\}\}[\s\S]*?\{\{\/market\.competitors\}\}/g, '');
    }

    return rendered;
  });

  return output;
}

// ─── JSON / YAML Compilers ──────────────────────────────────────────────────

function compileJson(inputs: Map<string, unknown>, def: CompilerDefinition): Record<string, unknown> {
  const obj: Record<string, unknown> = { _compiler: def.id, _compiled_at: new Date().toISOString() };
  for (const [key, value] of inputs) obj[key] = value;
  return obj;
}

function compileYaml(inputs: Map<string, unknown>, def: CompilerDefinition): string {
  const obj = compileJson(inputs, def);
  return jsonToYaml(obj);
}

// ─── Artifact Validation ─────────────────────────────────────────────────────

function validateArtifact(path: string, expectedType: string): boolean {
  try {
    if (!existsSync(path)) return false;
    const stat = statSync(path);
    if (stat.size === 0) return false;

    const normalized = expectedType.toLowerCase();
    if (normalized === 'json') {
      const content = readFileSync(path, 'utf-8');
      JSON.parse(content);
      return true;
    }
    if (normalized === 'markdown' || normalized === 'md') return true;
    if (normalized === 'string') return true;
    if (normalized === 'toml') {
      const content = readFileSync(path, 'utf-8');
      return content.includes('=') || content.includes(':') || content.includes('[');
    }
    return true;
  } catch {
    return false;
  }
}

// ─── YAML Serializer ────────────────────────────────────────────────────────

function jsonToYaml(obj: unknown, indent: number = 0): string {
  const pad = ' '.repeat(indent);
  if (obj === null || obj === undefined) return `${pad}null`;
  if (typeof obj === 'boolean') return `${pad}${obj}`;
  if (typeof obj === 'number') return `${pad}${obj}`;
  if (typeof obj === 'string') return `${pad}"${obj.replace(/"/g, '\\"')}"`;
  if (Array.isArray(obj)) {
    return obj.map(v => `${pad}-\n${jsonToYaml(v, indent + 1).trim()}`).join('\n');
  }
  if (typeof obj === 'object') {
    return Object.entries(obj as Record<string, unknown>).map(([k, v]) => `${pad}${k}:\n${jsonToYaml(v, indent + 1).trim()}`).join('\n');
  }
  return `${pad}${String(obj)}`;
}

// ─── WAL ─────────────────────────────────────────────────────────────────────

function appendWAL(ventureDir: string, event: Record<string, unknown>) {
  const walDir = join(ventureDir, 'wal');
  if (!existsSync(walDir)) mkdirSync(walDir, { recursive: true });
  const walFile = join(walDir, 'current.jsonl');
  const existing = existsSync(walFile) ? readFileSync(walFile, 'utf-8') : '';
  writeFileSync(walFile, existing + JSON.stringify(event) + '\n');
}

// ─── YAML Parser ─────────────────────────────────────────────────────────────

function parseCompilerYaml(content: string): CompilerDefinition {
  const result: Record<string, unknown> = {};
  let currentSection = result;

  for (const rawLine of content.split('\n')) {
    const trimmed = rawLine.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const sectionMatch = trimmed.match(/^\[(.+)\]$/);
    if (sectionMatch) {
      currentSection = {} as Record<string, unknown>;
      result[sectionMatch[1]] = currentSection;
      continue;
    }

    const colonIdx = trimmed.indexOf(':');
    if (colonIdx < 0) continue;
    const key = trimmed.slice(0, colonIdx).trim();
    let value: unknown = trimmed.slice(colonIdx + 1).trim();

    if (typeof value === 'string' && ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'")))) {
      value = value.slice(1, -1);
    }
    if (typeof value === 'string' && value.startsWith('[')) {
      const groups: string[][] = [];
      let cur = '', depth = 0, skipping = false;
      for (const ch of value) {
        if (skipping) {
          if (ch === '[') { depth = 1; cur = '['; skipping = false; }
          continue;
        }
        if (ch === '[') { depth++; cur += ch; }
        else if (ch === ']') { depth--; cur += ch; if (depth === 0) { groups.push(parseYamlArrayItem(cur)); cur = ''; skipping = true; } }
        else { cur += ch; }
      }
      value = groups;
    }
    if (typeof value === 'string' && value.startsWith('- ')) value = value.slice(2);

    currentSection[key] = value;
  }

  function parseYamlArrayItem(raw: string): string[] {
    const inner = raw.slice(1, -1).trim();
    const items: string[] = [];
    let item = '', inBrackets = 0;
    for (const c of inner) {
      if (c === '[') { inBrackets++; item += c; }
      else if (c === ']') { inBrackets--; item += c; }
      else if (c === ',' && inBrackets === 0) { items.push(item.trim().replace(/^["']|["']$/g, '')); item = ''; }
      else { item += c; }
    }
    if (item.trim()) items.push(item.trim().replace(/^["']|["']$/g, ''));
    return items;
  }

  const inputs: CompilerInput[] = [];
  const outputs: CompilerOutput[] = [];
  if (Array.isArray(result.inputs)) {
    for (const item of result.inputs) {
      if (Array.isArray(item) && item.length >= 4) {
        inputs.push({ name: String(item[0]), type: String(item[1]), required: String(item[2]) === 'true', path: String(item[3]) });
      }
    }
  }
  if (Array.isArray(result.outputs)) {
    for (const item of result.outputs) {
      if (Array.isArray(item) && item.length >= 3) {
        outputs.push({ name: String(item[0]), type: String(item[1]), path: String(item[2]) });
      }
    }
  }

  return {
    id: result.id as string,
    name: result.name as string,
    description: (result.description as string) ?? '',
    version: (result.version as string) ?? '0.1.0',
    inputs,
    outputs,
  };
}
