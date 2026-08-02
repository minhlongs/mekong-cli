#!/usr/bin/env node
/**
 * kv-cache-builder.cjs - KV Cache-optimized prompt builder
 *
 * Separates prompt content into STATIC (byte-identical) and DYNAMIC (changing) sections.
 * KV Cache on DeepSeek V4 works only when the prompt prefix remains identical across requests.
 *
 * Architecture:
 *   STATIC SECTIONS (prefix, never changes between requests):
 *     - System instructions
 *     - Rules
 *     - Naming conventions
 *     - Paths
 *     - Plan context (without timestamps)
 *     - Modularization rules
 *     - Coding standards
 *
 *   DYNAMIC SECTIONS (suffix, appended at the end):
 *     - Session stats (DateTime, Memory, CPU)
 *     - Context usage percentage
 *     - Usage limits
 *     - Timestamps
 *
 *   CACHED KV PREFIX          DYNAMIC CHANGE
 *   ┌──────────────────┐      ┌──────────────┐
 *   │ STATIC SECTIONS   │ +   │ DYNAMIC STUFF │
 *   │ (byte-identical)  │     │ (appended)    │
 *   └──────────────────┘     └──────────────┘
 *   ←──── CACHED ──────→     ←── NEW COMPUTE ──→
 *
 * Prompt canonicalization:
 *   - Normalize whitespace, newlines, markdown formatting
 *   - No timestamp insertion in static sections
 *   - No random wording
 *   - Byte-identical output for the same config + project state
 *   - Section ordering is fixed and never reordered
 *
 * @module kv-cache-builder
 */
'use strict';

const path = require('path');
const crypto = require('crypto');

// Model routing guidance — deterministic static content
const modelRouter = require('./model-router.cjs');

// ═════════════════════════════════════════════════════════════════════════════
// SECTION ORDER — NEVER REORDER
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Canonical section ordering for static prompt prefix.
 * This ordering is FIXED — never reorder these sections.
 * Reordering changes the byte stream and breaks KV cache.
 */
const STATIC_SECTION_ORDER = Object.freeze([
  'language',         // Language instructions
  'rules',            // Development rules
  'routing',          // Model routing guidance (Flash/Pro)
  'modularization',   // Modularization guidelines
  'paths',            // Reports/plans/docs paths
  'planContext',      // Plan context (no timestamps)
  'naming'            // Naming conventions
]);

const DYNAMIC_SECTION_ORDER = Object.freeze([
  'session',          // Session stats (DateTime, Memory, CPU)
  'context',          // Context usage
  'usage'             // Usage limits
]);

// ═════════════════════════════════════════════════════════════════════════════
// CANONICALIZATION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Normalize whitespace for deterministic output.
 * - Collapse multiple blank lines to exactly one blank line
 * - Remove trailing whitespace from each line
 * - Ensure file ends with exactly one newline
 * - Remove leading blank lines
 *
 * @param {string} text - Raw text to normalize
 * @returns {string} Normalized text
 */
function canonicalize(text) {
  if (typeof text !== 'string' || !text) return text;

  let result = text
    // Remove trailing whitespace from each line
    .replace(/[ \t]+$/gm, '')
    // Collapse 3+ newlines to exactly 2 (one blank line)
    .replace(/\n{3,}/g, '\n\n')
    // Remove leading blank lines
    .replace(/^\n+/, '')
    // Ensure exactly one trailing newline
    .replace(/\n*$/, '\n');

  return result;
}

/**
 * Stable stringify for deterministic JSON output.
 * Object keys are sorted alphabetically for consistent output.
 *
 * @param {Object} obj - Object to stringify
 * @returns {string} Deterministic JSON string
 */
function stableStringify(obj) {
  if (obj === null || obj === undefined) return '';
  if (typeof obj !== 'object') return String(obj);
  if (Array.isArray(obj)) {
    return '[' + obj.map(v => stableStringify(v)).join(',') + ']';
  }
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + stableStringify(obj[k])).join(',') + '}';
}

/**
 * Compute a hash for the static prefix to detect prefix stability.
 * The same hash = same KV cache hit.
 *
 * @param {string} staticPrefix - The canonical static prefix
 * @returns {string} SHA-256 hex hash of the prefix
 */
function hashPrefix(staticPrefix) {
  return crypto.createHash('sha256').update(staticPrefix, 'utf8').digest('hex');
}

/**
 * Normalize section heading format to consistent markdown.
 * All section headings use `## Title` format.
 *
 * @param {string} text - Section text to normalize
 * @returns {string} Normalized text
 */
function normalizeSectionHeading(text) {
  return text
    .replace(/^### /gm, '## ')    // ### → ##
    .replace(/^# /gm, '## ')       // # → ##
    .replace(/^==+$/gm, '')        // Remove === separators
    .replace(/^--+$/gm, '')        // Remove --- separators
    .replace(/\*\*\[IMPORTANT\]/g, '**[IMPORTANT]');
}

// ═════════════════════════════════════════════════════════════════════════════
// STATIC SECTION BUILDERS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build static rules section (deterministic, no timestamps).
 * All content is based on deterministic config state filesystem paths.
 *
 * @param {Object} params
 * @param {string} [params.devRulesPath] - Path to dev rules
 * @param {string} [params.catalogScript] - Path to catalog script
 * @param {string} [params.skillsVenv] - Path to skills venv
 * @returns {string[]} Lines for rules section (always identical for same config)
 */
function buildStaticRulesSection({ devRulesPath, catalogScript, skillsVenv }) {
  const lines = ['## Rules'];

  if (devRulesPath) {
    lines.push(`- Read and follow development rules: "${devRulesPath}"`);
  }

  lines.push('- Markdown files are organized in: Plans → "plans/" directory, Docs → "docs/" directory');
  lines.push('- **IMPORTANT:** DO NOT create markdown files out of "plans/" or "docs/" directories UNLESS the user explicitly requests it.');

  if (catalogScript) {
    lines.push(`- Activate skills: Run \`python ${catalogScript} --skills\` to generate a skills catalog and analyze it, then activate the relevant skills that are needed for the task during the process.`);
    lines.push(`- Execute commands: Run \`python ${catalogScript} --commands\` to generate a commands catalog and analyze it, then execute the relevant SlashCommands that are needed for the task during the process.`);
  }

  if (skillsVenv) {
    lines.push(`- Python scripts in .claude/skills/: Use \`${skillsVenv}\``);
  }

  lines.push("- When skills' scripts are failed to execute, always fix them and run again, repeat until success.");
  lines.push('- Follow **YAGNI (You Aren\'t Gonna Need It) - KISS (Keep It Simple, Stupid) - DRY (Don\'t Repeat Yourself)** principles');
  lines.push('- Sacrifice grammar for the sake of concision when writing reports.');
  lines.push('- In reports, list any unresolved questions at the end, if any.');
  lines.push('- IMPORTANT: Ensure token consumption efficiency while maintaining high quality.');
  lines.push('');

  return lines;
}

/**
 * Build static modularization section (deterministic, no timestamps).
 *
 * @returns {string[]} Lines for modularization section
 */
function buildStaticModularizationSection() {
  return [
    '## **[IMPORTANT] Consider Modularization:**',
    '- Check existing modules before creating new',
    '- Analyze logical separation boundaries (functions, classes, concerns)',
    '- Use kebab-case naming with descriptive names, it\'s fine if the file name is long because this ensures file names are self-documenting for LLM tools (Grep, Glob, Search)',
    '- Write descriptive code comments',
    '- After modularization, continue with main task',
    '- When not to modularize: Markdown files, plain text files, bash scripts, configuration files, environment variables files, etc.',
    ''
  ];
}

/**
 * Build static paths section (deterministic, no timestamps).
 *
 * @param {Object} params
 * @param {string} params.reportsPath - Reports path
 * @param {string} params.plansPath - Plans path
 * @param {string} params.docsPath - Docs path
 * @param {number} [params.docsMaxLoc=800] - Max lines of code for docs
 * @returns {string[]} Lines for paths section
 */
function buildStaticPathsSection({ reportsPath, plansPath, docsPath, docsMaxLoc = 800 }) {
  return [
    '## Paths',
    `Reports: ${reportsPath} | Plans: ${plansPath}/ | Docs: ${docsPath}/ | docs.maxLoc: ${docsMaxLoc}`,
    ''
  ];
}

/**
 * Build static plan context section (deterministic, no timestamps).
 * NOTE: Does NOT include git branch — that changes between checkouts and
 * would break KV cache. Git branch is moved to dynamic section.
 *
 * @param {Object} params
 * @param {string} params.planLine - Plan status line (deterministic for session)
 * @param {string} params.reportsPath - Reports path
 * @param {string} [params.validationMode] - Validation mode
 * @param {number} [params.validationMin] - Min questions
 * @param {number} [params.validationMax] - Max questions
 * @returns {string[]} Lines for plan context section
 */
function buildStaticPlanContextSection({ planLine, reportsPath, validationMode, validationMin, validationMax }) {
  const lines = ['## Plan Context'];
  lines.push(planLine);
  lines.push(`- Reports: ${reportsPath}`);
  lines.push(`- Validation: mode=${validationMode || 'prompt'}, questions=${validationMin || 3}-${validationMax || 8}`);
  lines.push('');

  return lines;
}

/**
 * Build static naming section (deterministic, no timestamps).
 *
 * @param {Object} params
 * @param {string} params.reportsPath - Reports path
 * @param {string} params.plansPath - Plans path
 * @param {string} params.namePattern - Naming pattern
 * @returns {string[]} Lines for naming section
 */
function buildStaticNamingSection({ reportsPath, plansPath, namePattern }) {
  return [
    '## Naming',
    `- Report: \`${reportsPath}{type}-${namePattern}.md\``,
    `- Plan dir: \`${plansPath}/${namePattern}/\``,
    '- Replace `{type}` with: agent name, report type, or context',
    '- Replace `{slug}` in pattern with: descriptive-kebab-slug'
  ];
}

/**
 * Build static language section (deterministic).
 *
 * @param {Object} params
 * @param {string} [params.thinkingLanguage] - Language for thinking
 * @param {string} [params.responseLanguage] - Language for response
 * @returns {string[]} Lines for language section
 */
function buildStaticLanguageSection({ thinkingLanguage, responseLanguage }) {
  const effectiveThinking = thinkingLanguage || (responseLanguage ? 'en' : null);
  const hasThinking = effectiveThinking && effectiveThinking !== responseLanguage;
  const hasResponse = responseLanguage;
  const lines = [];

  if (hasThinking || hasResponse) {
    lines.push('## Language');
    if (hasThinking) {
      lines.push(`- Thinking: Use ${effectiveThinking} for reasoning (logic, precision).`);
    }
    if (hasResponse) {
      lines.push(`- Response: Respond in ${responseLanguage} (natural, fluent).`);
    }
    lines.push('');
  }

  return lines;
}

/**
 * Build static model routing section (deterministic).
 *
 * This section tells the model which tier to use for which type of task.
 * Content is generated by model-router.cjs and is always byte-identical
 * (no timestamps, no dynamic content).
 *
 * @returns {string[]} Lines for routing section
 */
function buildStaticRoutingSection() {
  const guidance = modelRouter.buildRoutingGuidance();
  if (!guidance) return [];
  // Split into lines for section assembly
  return guidance.split('\n').map(l => l || '');
}

// ═════════════════════════════════════════════════════════════════════════════
// STATIC PREFIX BUILDER
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build the complete static prefix — byte-identical for the same config.
 * This is the part that KV cache will serve from cache.
 *
 * @param {Object} params - All static parameters
 * @param {Object} params.hooksConfig - Hooks config (for section toggles)
 * @returns {{ content: string, lines: string[], hash: string }}
 */
function buildStaticPrefix(params) {
  const hooksConfig = params.hooksConfig || {};

  const sections = {};

  // Language — always first
  sections.language = buildStaticLanguageSection({ thinkingLanguage: params.thinkingLanguage, responseLanguage: params.responseLanguage });

  // Static sections in canonical order
  sections.rules = buildStaticRulesSection({ devRulesPath: params.devRulesPath, catalogScript: params.catalogScript, skillsVenv: params.skillsVenv });
  sections.routing = buildStaticRoutingSection();
  sections.modularization = buildStaticModularizationSection();
  sections.paths = buildStaticPathsSection({ reportsPath: params.reportsPath, plansPath: params.plansPath, docsPath: params.docsPath, docsMaxLoc: params.docsMaxLoc });
  sections.planContext = buildStaticPlanContextSection({ planLine: params.planLine, reportsPath: params.reportsPath, validationMode: params.validationMode, validationMin: params.validationMin, validationMax: params.validationMax });
  sections.naming = buildStaticNamingSection({ reportsPath: params.reportsPath, plansPath: params.plansPath, namePattern: params.namePattern });

  // Build in canonical order
  const allLines = [];
  for (const sectionName of STATIC_SECTION_ORDER) {
    const sectionLines = sections[sectionName] || [];
    // Skip empty sections
    if (sectionLines.length === 0) continue;
    allLines.push(...sectionLines);
  }

  const rawContent = allLines.join('\n');
  const content = canonicalize(rawContent);
  const hash = hashPrefix(content);

  return { content, lines: allLines, hash, sections };
}

// ═════════════════════════════════════════════════════════════════════════════
// DYNAMIC SECTION BUILDERS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build dynamic session section — contains timestamps and variable system stats.
 * This MUST be at the END of the prompt to preserve KV cache prefix.
 * The content here changes every request and is NOT cached.
 *
 * @param {Object} [staticEnv] - Pre-computed static environment info
 * @returns {string[]} Lines for session section
 */
function buildDynamicSessionSection(staticEnv = {}) {
  let memUsed = 0;
  let memTotal = 0;
  let memPercent = 0;
  let cpuUsage = 0;
  let cpuSystem = 0;

  try {
    memUsed = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);
    memTotal = Math.round(require('os').totalmem() / 1024 / 1024);
    memPercent = Math.round((memUsed / memTotal) * 100);
    cpuUsage = Math.round((process.cpuUsage().user / 1000000) * 100);
    cpuSystem = Math.round((process.cpuUsage().system / 1000000) * 100);
  } catch { /* best-effort */ }

  let cwd = staticEnv.cwd || '';
  if (!cwd) try { cwd = process.cwd(); } catch { cwd = ''; }

  let timezone = staticEnv.timezone || '';
  if (!timezone) try { timezone = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch { /* ignore */ }

  // NOTE: Date and dynamic stats are intentionally here — they change per request
  // and should NOT be in the static prefix.
  let dateTime = 'unknown';
  try { dateTime = new Date().toLocaleString(); } catch { /* ignore */ }

  let osPlatform = staticEnv.osPlatform || '';
  if (!osPlatform) try { osPlatform = process.platform; } catch { osPlatform = ''; }

  let user = staticEnv.user || process.env.USERNAME || process.env.USER || '';
  let locale = staticEnv.locale || process.env.LANG || '';

  return [
    '## Session',
    `- DateTime: ${dateTime}`,
    `- CWD: ${cwd}`,
    `- Timezone: ${timezone}`,
    `- Working directory: ${cwd}`,
    `- OS: ${osPlatform}`,
    `- User: ${user}`,
    `- Locale: ${locale}`,
    `- Memory usage: ${memUsed}MB/${memTotal}MB (${memPercent}%)`,
    `- CPU usage: ${cpuUsage}% user / ${cpuSystem}% system`,
    '- Spawning multiple subagents can cause performance issues, spawn and delegate tasks intelligently based on the available system resources.',
    '- Remember that each subagent only has 200K tokens in context window, spawn and delegate tasks intelligently to make sure their context windows don\'t get bloated.',
    '- IMPORTANT: Include these environment information when prompting subagents to perform tasks.',
    ''
  ];
}

/**
 * Build dynamic context section — context usage percentage from statusline cache.
 *
 * @param {string} sessionId - Session ID
 * @returns {string[]} Lines for context section
 */
function buildDynamicContextSection(sessionId) {
  if (!sessionId) return [];

  try {
    const os = require('os');
    const fs = require('fs');
    const contextPath = path.join(os.tmpdir(), `ck-context-${sessionId}.json`);
    if (!fs.existsSync(contextPath)) return [];

    const data = JSON.parse(fs.readFileSync(contextPath, 'utf-8'));
    // Only use fresh data (< 5 min old)
    if (Date.now() - data.timestamp > 300000) return [];

    const lines = ['## Current Session\'s Context'];
    const usedK = Math.round(data.tokens / 1000);
    const sizeK = Math.round(data.size / 1000);
    lines.push(`- Context: ${data.percent}% used (${usedK}K/${sizeK}K tokens)`);
    lines.push('- **NOTE:** Optimize the workflow for token efficiency');

    if (data.percent >= 90) {
      lines.push('- **CRITICAL:** Context nearly full - consider compaction or being concise, update current phase\'s status before the compaction.');
    } else if (data.percent >= 70) {
      lines.push('- **WARNING:** Context usage moderate - being concise and optimize token efficiency.');
    }

    lines.push('');
    return lines;
  } catch {
    return [];
  }
}

/**
 * Build dynamic usage section — usage limits from cache.
 * These change as the API resets limits.
 *
 * @returns {string[]} Lines for usage section
 */
function buildDynamicUsageSection() {
  try {
    const os = require('os');
    const fs = require('fs');
    const USAGE_CACHE_FILE = path.join(os.tmpdir(), 'ck-usage-limits-cache.json');
    const WARN_THRESHOLD = 70;
    const CRITICAL_THRESHOLD = 90;

    if (!fs.existsSync(USAGE_CACHE_FILE)) return [];
    const cache = JSON.parse(fs.readFileSync(USAGE_CACHE_FILE, 'utf-8'));
    if (Date.now() - cache.timestamp >= 300000) return [];
    const usage = cache.data;
    if (!usage) return [];

    const lines = [];
    const parts = [];

    if (usage.five_hour) {
      const util = usage.five_hour.utilization;
      const pct = typeof util === 'number' ? Math.round(util) : null;
      if (pct !== null) {
        if (pct >= CRITICAL_THRESHOLD) parts.push(`5h: ${pct}% [CRITICAL]`);
        else if (pct >= WARN_THRESHOLD) parts.push(`5h: ${pct}% [WARNING]`);
        else parts.push(`5h: ${pct}%`);
      }

      if (usage.five_hour.resets_at) {
        const resetTime = new Date(usage.five_hour.resets_at);
        const remaining = Math.floor(resetTime.getTime() / 1000) - Math.floor(Date.now() / 1000);
        if (remaining > 0 && remaining <= 18000) {
          const hours = Math.floor(remaining / 3600);
          const mins = Math.floor((remaining % 3600) / 60);
          parts.push(`resets in ${hours}h ${mins}m`);
        }
      }
    }

    if (usage.seven_day?.utilization != null) {
      const pct = Math.round(usage.seven_day.utilization);
      if (pct >= CRITICAL_THRESHOLD) parts.push(`7d: ${pct}% [CRITICAL]`);
      else if (pct >= WARN_THRESHOLD) parts.push(`7d: ${pct}% [WARNING]`);
      else parts.push(`7d: ${pct}%`);
    }

    if (parts.length > 0) {
      lines.push('## Usage Limits');
      lines.push(`- ${parts.join(' | ')}`);
      lines.push('');
    }

    return lines;
  } catch {
    return [];
  }
}

/**
 * Build dynamic git branch section — branches change between checkouts.
 *
 * @param {string} [gitBranch] - Current git branch
 * @returns {string[]} Lines for git branch
 */
function buildDynamicBranchSection(gitBranch) {
  if (!gitBranch) return [];
  return ['', `## Branch`, `- Current branch: ${gitBranch}`, ''];
}

// ═════════════════════════════════════════════════════════════════════════════
// DYNAMIC SUFFIX BUILDER
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build the dynamic suffix — content that changes between requests.
 * This is appended AFTER the static prefix so KV cache still hits on the prefix.
 *
 * @param {Object} params
 * @param {string} [params.sessionId] - Session ID
 * @param {Object} [params.staticEnv] - Static environment info
 * @param {string} [params.gitBranch] - Current git branch
 * @returns {{ content: string, lines: string[], tokenEstimate: number }}
 */
function buildDynamicSuffix(params = {}) {
  const allLines = [];

  // Dynamic sections in canonical order
  const sessionLines = buildDynamicSessionSection(params.staticEnv);
  if (sessionLines.length > 0) allLines.push(...sessionLines);

  const contextLines = buildDynamicContextSection(params.sessionId);
  if (contextLines.length > 0) allLines.push(...contextLines);

  const usageLines = buildDynamicUsageSection();
  if (usageLines.length > 0) allLines.push(...usageLines);

  const branchLines = buildDynamicBranchSection(params.gitBranch);
  if (branchLines.length > 0) allLines.push(...branchLines);

  const content = canonicalize(allLines.join('\n'));
  // Rough token estimate: ~4 chars per token
  const tokenEstimate = Math.ceil(content.length / 4);

  return { content, lines: allLines, tokenEstimate };
}

// ═════════════════════════════════════════════════════════════════════════════
// METRICS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Estimate KV cache metrics.
 *
 * @param {Object} params
 * @param {string} params.staticContent - The static prefix
 * @param {string} params.dynamicContent - The dynamic suffix
 * @returns {{
 *   staticTokens: number,
 *   dynamicTokens: number,
 *   totalTokens: number,
 *   cacheHitRatio: number,
 *   prefixHash: string,
 *   prefixStable: boolean,
 *   previousHash: string|null
 * }}
 */
function estimateKVCacheMetrics({ staticContent, dynamicContent }) {
  const staticTokens = Math.ceil(staticContent.length / 4);
  const dynamicTokens = Math.ceil(dynamicContent.length / 4);
  const totalTokens = staticTokens + dynamicTokens;
  const prefixHash = hashPrefix(staticContent);

  // Try to read previous hash for stability check
  const os = require('os');
  const fs = require('fs');
  const metricsPath = path.join(os.tmpdir(), 'ck-kv-cache-metrics.json');
  let previousHash = null;
  let prefixStable = true;

  try {
    if (fs.existsSync(metricsPath)) {
      const prev = JSON.parse(fs.readFileSync(metricsPath, 'utf-8'));
      previousHash = prev.prefixHash || null;
      prefixStable = previousHash === prefixHash;
    }
  } catch {
    // First run or corrupted cache
  }

  // Estimate cache hit ratio based on prefix stability
  // If prefix is stable, ~100% of static tokens hit cache
  // Dynamic tokens always miss cache
  const cacheHitRatio = totalTokens > 0
    ? prefixStable ? Math.round((staticTokens / totalTokens) * 100) : 0
    : 0;

  return {
    staticTokens,
    dynamicTokens,
    totalTokens,
    cacheHitRatio,
    prefixHash,
    prefixStable,
    previousHash
  };
}

/**
 * Persist KV cache metrics to temp file for diagnostics.
 *
 * @param {Object} metrics - Metrics from estimateKVCacheMetrics()
 */
function persistMetrics(metrics) {
  try {
    const os = require('os');
    const fs = require('fs');
    const metricsPath = path.join(os.tmpdir(), 'ck-kv-cache-metrics.json');

    let history = [];
    try {
      if (fs.existsSync(metricsPath)) {
        history = JSON.parse(fs.readFileSync(metricsPath, 'utf-8')).history || [];
      }
    } catch { /* start fresh */ }

    // Keep last 100 entries
    history.push({
      timestamp: Date.now(),
      ...metrics
    });
    if (history.length > 100) history = history.slice(-100);

    // Calculate averages
    const avgDynamicTokens = history.length > 0
      ? Math.round(history.reduce((sum, m) => sum + m.dynamicTokens, 0) / history.length)
      : 0;

    const compactionEvents = history.filter(m => !m.prefixStable).length;

    fs.writeFileSync(metricsPath, JSON.stringify({
      prefixHash: metrics.prefixHash,
      history
    }, null, 2));

    // Return enriched metrics
    return {
      ...metrics,
      avgDynamicTokens,
      compactionEvents,
      totalRequests: history.length
    };
  } catch {
    return metrics;
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// ORCHESTRATION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build complete KV cache-optimized reminder content.
 * Static prefix (byte-identical) + dynamic suffix (appended).
 *
 * @param {Object} params - All parameters
 * @returns {{
 *   staticPrefix: { content: string, lines: string[], hash: string, sections: Object },
 *   dynamicSuffix: { content: string, lines: string[], tokenEstimate: number },
 *   metrics: Object,
 *   fullContent: string
 * }}
 */
function buildKVCacheReminder(params) {
  // Build static prefix (byte-identical for same config)
  const staticPrefix = buildStaticPrefix(params);

  // Build dynamic suffix (changes per request)
  const dynamicSuffix = buildDynamicSuffix({
    sessionId: params.sessionId,
    staticEnv: params.staticEnv,
    gitBranch: params.gitBranch
  });

  // Combine: static prefix + dynamic suffix
  const fullContent = canonicalize(staticPrefix.content + '\n' + dynamicSuffix.content);

  // Metrics
  const rawMetrics = estimateKVCacheMetrics({
    staticContent: staticPrefix.content,
    dynamicContent: dynamicSuffix.content
  });
  const metrics = persistMetrics(rawMetrics);

  return {
    staticPrefix,
    dynamicSuffix,
    metrics,
    fullContent
  };
}

// ═════════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═════════════════════════════════════════════════════════════════════════════

module.exports = {
  // Constants
  STATIC_SECTION_ORDER,
  DYNAMIC_SECTION_ORDER,

  // Canonicalization
  canonicalize,
  stableStringify,
  hashPrefix,
  normalizeSectionHeading,

  // Static section builders
  buildStaticRulesSection,
  buildStaticRoutingSection,
  buildStaticModularizationSection,
  buildStaticPathsSection,
  buildStaticPlanContextSection,
  buildStaticNamingSection,
  buildStaticLanguageSection,

  // Dynamic section builders
  buildDynamicSessionSection,
  buildDynamicContextSection,
  buildDynamicUsageSection,
  buildDynamicBranchSection,

  // Main entry points
  buildStaticPrefix,
  buildDynamicSuffix,
  buildKVCacheReminder,

  // Metrics
  estimateKVCacheMetrics,
  persistMetrics
};
