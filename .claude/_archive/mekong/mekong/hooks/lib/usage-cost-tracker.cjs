/**
 * usage-cost-tracker.cjs — AI Usage Cost Tracking Engine
 *
 * Tracks Claude Code session token usage and computes cost using live
 * LiteLLM pricing with hardcoded DeepSeek V4 fallback.
 *
 * Architecture:
 *   - Fetches LiteLLM model pricing (24h disk cache, 4s timeout, fail-silent)
 *   - Parses current session JSONL transcript for token usage
 *   - Computes per-model daily cost: sum((tokens × price) / 1e6)
 *   - Deduplicates by messageId:requestId across files
 *   - Per-file mtime+size cache (process lifetime)
 *   - ALL errors are fail-open — cost tracking never blocks routing
 *
 * Ported from: tawgroup/taw-terminal (MIT) — src/main/index.ts pricing engine
 *
 * Usage:
 *   const tracker = require('./lib/usage-cost-tracker.cjs');
 *   const cost = tracker.getSessionCost(sessionId);
 *   // → { flash: { tokens, cost }, pro: { tokens, cost }, totalCost }
 *
 *   // Background refresh (fire-and-forget)
 *   tracker.refreshPricing();
 *
 * @module usage-cost-tracker
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const LITELLM_URL = 'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json';
const PRICING_CACHE_PATH = path.join(os.tmpdir(), 'ck-pricing-cache.json');
const COST_OUTPUT_PATH = path.join(os.tmpdir(), 'ck-usage-cost.json');
const PRICING_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const FETCH_TIMEOUT_MS = 4000;

/**
 * Hardcoded DeepSeek V4 pricing fallback (USD per 1M tokens).
 * Format: [input, output, cache_create, cache_read]
 * Verified against LiteLLM model_prices_and_context_window.json 2026-07-01.
 */
const DEEPSEEK_PRICING_FALLBACK = Object.freeze({
  'deepseek-v4-flash':       [0.003, 0.003, 0, 0],
  'deepseek-v4-pro[1m]':     [0.14,  0.14,  0, 0],
  'deepseek-v4-pro':         [0.14,  0.14,  0, 0], // without [1m] suffix
});

/**
 * Anthropic Claude pricing fallback (USD per 1M tokens).
 * Format: [input, output, cache_create, cache_read]
 * Source: TAW Terminal hardcoded table, verified 2026-06-21.
 */
const CLAUDE_PRICING_FALLBACK = Object.freeze({
  'claude-opus-4-8':         [5,  25, 6.25, 0.5],
  'claude-opus-4-5':         [5,  25, 6.25, 0.5],
  'claude-opus-4-1':         [15, 75, 18.75, 1.5],
  'claude-opus-4-0':         [15, 75, 18.75, 1.5],
  'claude-sonnet-4-6':       [3,  15, 3.75, 0.3],
  'claude-sonnet-4-5':       [3,  15, 3.75, 0.3],
  'claude-haiku-4-5':        [1,  5,  1.25, 0.1],
});

/** Combined fallback: DeepSeek + Claude. DeepSeek takes priority (our primary provider). */
const PRICING_FALLBACK = Object.freeze(Object.assign(
  {},
  CLAUDE_PRICING_FALLBACK,
  DEEPSEEK_PRICING_FALLBACK
));

// ═══════════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════════

/** @type {Record<string, [number,number,number,number]> | null} */
let livePricing = null;

/** @type {Map<string, {mtime: number, size: number, entries: Array}>} */
const fileCache = new Map();

// ═══════════════════════════════════════════════════════════════════════════
// PRICING ENGINE (ported from TAW Terminal src/main/index.ts)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Convert LiteLLM flat JSON to a Price4 record.
 * Skips entries without input_cost_per_token. Normalizes keys to lowercase.
 * Multiplies per-token costs by 1e6 to produce per-1M-token prices.
 *
 * @param {Object} json - Raw LiteLLM JSON
 * @returns {Record<string, [number,number,number,number]>}
 */
function pricingFromLiteLLM(json) {
  const out = {};
  if (!json || typeof json !== 'object') return out;

  for (const [key, val] of Object.entries(json)) {
    if (!val || typeof val !== 'object' || val.input_cost_per_token == null) continue;
    out[key.toLowerCase()] = [
      (val.input_cost_per_token || 0) * 1e6,
      (val.output_cost_per_token || 0) * 1e6,
      (val.cache_creation_input_token_cost || 0) * 1e6,
      (val.cache_read_input_token_cost || 0) * 1e6,
    ];
  }
  return out;
}

/**
 * Read pricing cache from disk. Returns null if missing, stale, or corrupt.
 *
 * @returns {Record<string, [number,number,number,number]> | null}
 */
function readPricingCache() {
  try {
    if (!fs.existsSync(PRICING_CACHE_PATH)) return null;
    const raw = fs.readFileSync(PRICING_CACHE_PATH, 'utf8');
    const cache = JSON.parse(raw);
    if (!cache || typeof cache.fetchedAt !== 'number') return null;
    if (Date.now() - cache.fetchedAt > PRICING_CACHE_TTL_MS) return null;
    if (!cache.map || typeof cache.map !== 'object') return null;
    return cache.map;
  } catch {
    return null;
  }
}

/**
 * Write pricing cache to disk atomically (tmp + rename).
 *
 * @param {Record<string, [number,number,number,number]>} map
 */
function writePricingCache(map) {
  const tmpFile = `${PRICING_CACHE_PATH}.${process.pid}.${Date.now()}.tmp`;
  try {
    fs.writeFileSync(tmpFile, JSON.stringify({
      fetchedAt: Date.now(),
      map,
    }));
    fs.renameSync(tmpFile, PRICING_CACHE_PATH);
  } catch {
    try { fs.unlinkSync(tmpFile); } catch { /* best-effort */ }
  }
}

/**
 * Refresh pricing from LiteLLM. Fire-and-forget — never throws.
 * Reads disk cache first; skips fetch if cache < 24h old.
 * On success, updates livePricing global. On failure, leaves existing pricing intact.
 *
 * @returns {Promise<void>}
 */
async function refreshPricing() {
  // 1. Try disk cache first
  const cached = readPricingCache();
  if (cached) {
    livePricing = cached;
    return;
  }

  // 2. Fetch from LiteLLM with timeout
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

    const response = await fetch(LITELLM_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) return;
    const json = await response.json();
    const map = pricingFromLiteLLM(json);

    if (Object.keys(map).length > 0) {
      livePricing = map;
      writePricingCache(map);
    }
  } catch {
    // Fail-silent: stale cache or hardcoded fallback takes over
  }
}

/**
 * Resolve model price using 4-tier fallback:
 *   1. Exact match in live pricing
 *   2. Prefixed match (deepseek/ + model, anthropic/ + model)
 *   3. Hardcoded fallback table (PRICING_FALLBACK)
 *   4. Regex heuristic on model name
 *
 * @param {string} model - Model name (e.g., "deepseek-v4-flash")
 * @returns {[number,number,number,number]} [input, output, cache_create, cache_read] per-1M USD
 */
function modelPrice(model) {
  const m = (model || '').toLowerCase().trim();
  if (!m) return [0, 0, 0, 0];

  // Tier 1: Exact match in live pricing
  if (livePricing && livePricing[m]) return livePricing[m];

  // Tier 2: Prefixed match (provider/model format in LiteLLM)
  if (livePricing) {
    for (const prefix of ['deepseek/', 'anthropic/']) {
      const key = prefix + m;
      if (livePricing[key]) return livePricing[key];
    }
  }

  // Tier 3: Hardcoded fallback table
  if (PRICING_FALLBACK[m]) return PRICING_FALLBACK[m];

  // Tier 4: Regex heuristic
  if (m.includes('deepseek')) {
    if (m.includes('pro')) return [0.14, 0.14, 0, 0];
    if (m.includes('flash')) return [0.003, 0.003, 0, 0];
    return [0.003, 0.003, 0, 0]; // default DeepSeek = flash pricing
  }
  if (m.includes('opus')) {
    return /opus-4-[01]|3-opus/.test(m) ? [15, 75, 18.75, 1.5] : [5, 25, 6.25, 0.5];
  }
  if (m.includes('haiku')) {
    return /haiku-3|3-5-haiku/.test(m) ? [0.8, 4, 1, 0.08] : [1, 5, 1.25, 0.1];
  }
  if (m.includes('sonnet')) {
    return [3, 15, 3.75, 0.3];
  }

  // Default: assume flash-tier pricing (cheapest)
  return [0.003, 0.003, 0, 0];
}

// ═══════════════════════════════════════════════════════════════════════════
// TRANSCRIPT PARSER (ported from TAW Terminal src/main/index.ts)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * @typedef {Object} UsageEntry
 * @property {string} timestamp - ISO timestamp
 * @property {string} [messageId] - Unique message ID for dedup
 * @property {string} [requestId] - Unique request ID for dedup
 * @property {string} [model] - Model name used
 * @property {number} input - Input tokens
 * @property {number} output - Output tokens
 * @property {number} cacheCreation - Cache creation tokens
 * @property {number} cacheRead - Cache read tokens
 */

/**
 * @typedef {Object} CostSummary
 * @property {number} tokens - Total tokens
 * @property {number} cost - Total cost in USD
 * @property {number} input - Total input tokens (incl. cache)
 * @property {number} output - Total output tokens
 * @property {Object<string,{tokens:number, cost:number}>} byModel - Per-model breakdown
 */

/**
 * Parse a single Claude Code JSONL transcript file.
 * Uses fast-skip: checks for "usage" substring before JSON.parse.
 * Caches results by mtime+size (process lifetime).
 *
 * @param {string} filePath - Absolute path to .jsonl file
 * @returns {UsageEntry[]}
 */
function parseTranscriptFile(filePath) {
  // Check file cache
  let st;
  try { st = fs.statSync(filePath); } catch { return []; }
  const cached = fileCache.get(filePath);
  if (cached && cached.mtime === st.mtimeMs && cached.size === st.size) {
    return cached.entries;
  }

  const entries = [];
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    const lines = raw.split('\n');

    for (const line of lines) {
      if (!line.trim()) continue;
      // Fast skip: avoid JSON.parse on lines without usage data
      if (line.indexOf('"usage"') === -1) continue;

      try {
        const obj = JSON.parse(line);
        const msg = obj.message;
        if (!msg || !msg.usage) continue;

        const usage = msg.usage;
        entries.push({
          timestamp: obj.timestamp || '',
          messageId: msg.id || '',
          requestId: obj.requestId || '',
          model: msg.model || '',
          input: usage.input_tokens || 0,
          output: usage.output_tokens || 0,
          cacheCreation: usage.cache_creation_input_tokens || 0,
          cacheRead: usage.cache_read_input_tokens || 0,
        });
      } catch {
        // Skip malformed JSON lines
      }
    }
  } catch {
    // File read error — return empty
  }

  // Cache for process lifetime
  fileCache.set(filePath, { mtime: st.mtimeMs, size: st.size, entries });
  return entries;
}

/**
 * Find all JSONL transcript files for a given session.
 * Scans ~/.claude/projects/ for files matching the session ID.
 *
 * @param {string} sessionId - Claude Code session ID
 * @returns {string[]} Absolute paths to JSONL files
 */
function findSessionTranscripts(sessionId) {
  const projectsDir = path.join(os.homedir(), '.claude', 'projects');
  const files = [];

  if (!sessionId) return files;

  try {
    // Direct match: ~/.claude/projects/-Users-macbook/<sessionId>.jsonl
    const entries = fs.readdirSync(projectsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const projectDir = path.join(projectsDir, entry.name);
      try {
        const projectFiles = fs.readdirSync(projectDir, { withFileTypes: true });
        for (const pf of projectFiles) {
          if (pf.isFile() && pf.name.endsWith('.jsonl') && pf.name.includes(sessionId)) {
            files.push(path.join(projectDir, pf.name));
          }
        }
      } catch {
        // Skip unreadable project dirs
      }
    }
  } catch {
    // projects dir doesn't exist or isn't readable
  }

  return files;
}

/**
 * Compute cost for a set of usage entries, grouped by model.
 * Deduplicates by messageId:requestId across all entries.
 *
 * Formula: cost = (input_tokens × input_price + output_tokens × output_price
 *           + cache_creation × cache_create_price + cache_read × cache_read_price) / 1e6
 *
 * @param {UsageEntry[]} entries
 * @returns {CostSummary}
 */
function computeCost(entries) {
  const seen = new Set();
  const byModel = {};
  let totalTokens = 0;
  let totalCost = 0;
  let totalInput = 0;
  let totalOutput = 0;

  for (const entry of entries) {
    // Dedup by messageId:requestId
    const dedupKey = `${entry.messageId}:${entry.requestId}`;
    if (dedupKey === ':') continue; // skip entries with no IDs
    if (seen.has(dedupKey)) continue;
    seen.add(dedupKey);

    const model = entry.model || 'unknown';
    const [pi, po, pcw, pcr] = modelPrice(model);

    // Cache breakdown fields are subsets of input_tokens (not additive).
    // Non-cache input = total input minus cache breakdowns.
    const nonCacheInput = Math.max(0, entry.input - entry.cacheCreation - entry.cacheRead);
    const inputTokens = entry.input; // total input (already includes cache breakdowns)
    const outputTokens = entry.output;
    const tokens = inputTokens + outputTokens;
    const cost = (nonCacheInput * pi + entry.output * po +
                  entry.cacheCreation * pcw + entry.cacheRead * pcr) / 1e6;

    totalTokens += tokens;
    totalCost += cost;
    totalInput += inputTokens;
    totalOutput += outputTokens;

    if (!byModel[model]) {
      byModel[model] = { tokens: 0, cost: 0 };
    }
    byModel[model].tokens += tokens;
    byModel[model].cost += cost;
  }

  return { tokens: totalTokens, cost: totalCost, input: totalInput, output: totalOutput, byModel };
}

/**
 * Get cost summary for a Claude Code session.
 * This is the main entry point — call with session ID from CK_SESSION_ID env.
 *
 * @param {string} sessionId - Claude Code session ID
 * @returns {CostSummary}
 */
function getSessionCost(sessionId) {
  if (!sessionId) return emptyCost();

  const files = findSessionTranscripts(sessionId);
  if (files.length === 0) return emptyCost();

  const allEntries = [];
  for (const file of files) {
    allEntries.push(...parseTranscriptFile(file));
  }

  return computeCost(allEntries);
}

/**
 * Get cost summary broken down by Flash vs Pro tiers.
 * Categorizes model names: "flash" in name → Flash tier, "pro" → Pro tier.
 *
 * @param {string} sessionId
 * @returns {{ flash: CostSummary, pro: CostSummary, totalCost: number, totalTokens: number }}
 */
function getTierCosts(sessionId) {
  const full = getSessionCost(sessionId);
  const flash = { tokens: 0, cost: 0, input: 0, output: 0, byModel: {} };
  const pro = { tokens: 0, cost: 0, input: 0, output: 0, byModel: {} };

  for (const [model, stats] of Object.entries(full.byModel)) {
    const modelLower = model.toLowerCase();
    if (/\bpro\b/.test(modelLower) || modelLower.includes('opus')) {
      pro.tokens += stats.tokens;
      pro.cost += stats.cost;
      pro.byModel[model] = stats;
    } else {
      flash.tokens += stats.tokens;
      flash.cost += stats.cost;
      flash.byModel[model] = stats;
    }
  }
  // Input/output split at tier level (approximate from model proportions)
  if (full.tokens > 0) {
    const flashRatio = flash.tokens / full.tokens;
    flash.input = Math.round(full.input * flashRatio);
    flash.output = Math.round(full.output * flashRatio);
    pro.input = full.input - flash.input;
    pro.output = full.output - flash.output;
  }

  return {
    flash,
    pro,
    totalCost: full.cost,
    totalTokens: full.tokens,
  };
}

/**
 * @returns {CostSummary} Zero-value cost summary
 */
function emptyCost() {
  return { tokens: 0, cost: 0, input: 0, output: 0, byModel: {} };
}

// ═══════════════════════════════════════════════════════════════════════════
// COST OUTPUT (for statusline / external consumers)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Write session cost to os.tmpdir()/ck:usage-cost.json for statusline consumption.
 * Atomic write (tmp + rename). Fail-silent.
 *
 * @param {string} sessionId
 */
function writeCostOutput(sessionId) {
  const tierCosts = getTierCosts(sessionId);
  const tmpFile = `${COST_OUTPUT_PATH}.${process.pid}.${Date.now()}.tmp`;
  try {
    fs.writeFileSync(tmpFile, JSON.stringify({
      timestamp: Date.now(),
      sessionId,
      ...tierCosts,
    }, null, 2));
    fs.renameSync(tmpFile, COST_OUTPUT_PATH);
  } catch {
    try { fs.unlinkSync(tmpFile); } catch { /* best-effort */ }
  }
}

/**
 * Format cost as a human-readable string for banner/statusline display.
 *
 * @param {string} sessionId
 * @returns {string}
 */
function formatCostSummary(sessionId) {
  const tierCosts = getTierCosts(sessionId);
  if (tierCosts.totalTokens === 0) return '';

  const parts = [];
  parts.push(`💰 Session cost: $${tierCosts.totalCost.toFixed(4)} | ${tierCosts.totalTokens.toLocaleString()} tokens`);

  if (tierCosts.flash.tokens > 0) {
    const pct = Math.round(tierCosts.flash.tokens / tierCosts.totalTokens * 100);
    parts.push(`⚡ Flash: $${tierCosts.flash.cost.toFixed(4)} (${pct}%)`);
  }
  if (tierCosts.pro.tokens > 0) {
    const pct = Math.round(tierCosts.pro.tokens / tierCosts.totalTokens * 100);
    parts.push(`🏗️ Pro: $${tierCosts.pro.cost.toFixed(4)} (${pct}%)`);
  }

  return parts.join(' | ');
}

// ═══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

// Try loading disk cache at require() time (synchronous, best-effort)
const diskCache = readPricingCache();
if (diskCache) {
  livePricing = diskCache;
}

// Fire-and-forget background refresh (never awaited — fail-silent)
refreshPricing();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Reset livePricing to null (for testing).
 * Forces modelPrice() to use hardcoded fallback only.
 */
function _resetPricingForTest() {
  livePricing = null;
  fileCache.clear();
}

module.exports = {
  // Pricing engine
  pricingFromLiteLLM,
  refreshPricing,
  modelPrice,
  readPricingCache,
  writePricingCache,
  _resetPricingForTest,

  // Transcript parser
  parseTranscriptFile,
  findSessionTranscripts,
  computeCost,

  // High-level API
  getSessionCost,
  getTierCosts,
  emptyCost,

  // Output
  writeCostOutput,
  formatCostSummary,

  // Constants
  PRICING_CACHE_PATH,
  COST_OUTPUT_PATH,
  LITELLM_URL,
  PRICING_FALLBACK,
  DEEPSEEK_PRICING_FALLBACK,
};
