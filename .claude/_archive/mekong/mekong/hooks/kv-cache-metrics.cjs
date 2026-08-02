#!/usr/bin/env node
/**
 * KV Cache Metrics - PostToolUse Hook
 *
 * Reads KV cache metrics from temp file and logs diagnostics.
 * Metrics are written by kv-cache-builder.cjs on each prompt cycle,
 * and compaction events are recorded by session-init.cjs on compact.
 *
 * Features:
 *   - Reports estimated KV cache hit %
 *   - Tracks prefix stability across requests
 *   - Tracks static/dynamic token counts
 *   - Reports compaction events (from dedicated compactionHistory)
 *   - Reports average incremental tokens
 *
 * Exit Codes:
 *   0 - Success (non-blocking, always allows continuation)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const modelRouter = require('./lib/model-router.cjs');
const { isHookEnabled } = require('./lib/ck:config-utils.cjs');

// Early exit if hook disabled in config
if (!isHookEnabled('kv-cache-metrics')) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

const ROUTING_LOG = path.join(os.tmpdir(), modelRouter.ROUTING_LOG_FILENAME);
const METRICS_FILE = path.join(os.tmpdir(), 'ck-kv-cache-metrics.json');

/**
 * Read KV cache metrics from temp file.
 *
 * @returns {Object|null} Metrics data or null
 */
function readMetrics() {
  try {
    if (!fs.existsSync(METRICS_FILE)) return null;
    const data = JSON.parse(fs.readFileSync(METRICS_FILE, 'utf8'));
    return data;
  } catch {
    return null;
  }
}

/**
 * Format metrics for human-readable output.
 *
 * Compaction events are tracked SEPARATELY from prefix stability.
 * - compactionHistory: set by session-init.cjs on each compact event
 * - history[n].prefixStable: set by kv-cache-builder.cjs on each request
 * This avoids conflating auto-compaction with static prefix changes.
 *
 * @param {Object} data - Metrics data from temp file
 * @returns {string} Formatted metrics string
 */
function formatMetrics(data) {
  if (!data || !data.history || data.history.length === 0) {
    return '';
  }

  const history = data.history;
  const latest = history[history.length - 1];
  const totalRequests = history.length;

  // Calculate prefix stability (how often the static prefix hash changed)
  const prefixChanges = history.filter(h => !h.prefixStable).length;
  const prefixStabilityPct = Math.round(((totalRequests - prefixChanges) / totalRequests) * 100);

  // Calculate average dynamic tokens
  const avgDynamicTokens = Math.round(
    history.reduce((sum, h) => sum + (h.dynamicTokens || 0), 0) / totalRequests
  );

  // Calculate average total tokens
  const avgTotalTokens = Math.round(
    history.reduce((sum, h) => sum + (h.totalTokens || 0), 0) / totalRequests
  );

  // Compaction events: read from dedicated compactionHistory array
  // (set by session-init.cjs on compact events) rather than inferring from prefix changes
  const compactionEvents = (data.compactionHistory && data.compactionHistory.length) || 0;
  const lastCompaction = compactionEvents > 0
    ? data.compactionHistory[data.compactionHistory.length - 1]
    : null;
  const lastCompactionLabel = lastCompaction
    ? new Date(lastCompaction.timestamp).toLocaleString()
    : 'N/A';

  // Latest metrics
  const hitPct = latest.cacheHitRatio || 0;
  const staticK = Math.round((latest.staticTokens || 0) / 1000);
  const dynamicK = Math.round((latest.dynamicTokens || 0) / 1000);
  const totalK = Math.round((latest.totalTokens || 0) / 1000);
  const stableIcon = latest.prefixStable ? '✓' : '✗';

  const lines = [
    '## KV Cache Diagnostics',
    '',
    `| Metric | Value |`,
    `|--------|-------|`,
    `| Estimated KV Cache Hit % | ${hitPct}% |`,
    `| Static Prefix Stable? | ${stableIcon} |`,
    `| Prefix Stability (all-time) | ${prefixStabilityPct}% |`,
    `| Static Tokens | ${staticK}K |`,
    `| Dynamic Tokens (latest) | ${dynamicK}K |`,
    `| Total Tokens (latest) | ${totalK}K |`,
    `| Avg Dynamic Tokens | ${Math.round(avgDynamicTokens / 1000)}K |`,
    `| Avg Total Tokens | ${Math.round(avgTotalTokens / 1000)}K |`,
    `| Compaction Events | ${compactionEvents} |`,
    `| Last Compaction | ${lastCompactionLabel} |`,
    `| Total Requests | ${totalRequests} |`,
    '',
    `### Model Routing`,
    `| 🔀 | Tier | Default | Escalation |`,
    `|---|------|---------|------------|`,
    `| ⚡ | Flash (Executor) | ✓ 85-95% | → Pro on complexity |`,
    `| 🏗️ | Pro (Architect) | — 5-15% | ← return to Flash after plan |`,
    '',
    '### Routing Decisions (Runtime)',
    buildRuntimeRoutingMetrics(),
    ''
  ];

  return lines.join('\n');
}

/**
 * Build runtime routing metrics from routing decision log.
 * Shows actual Flash/Pro usage, cost estimates, escalation events.
 *
 * @returns {string} Markdown-formatted metrics table
 */
function buildRuntimeRoutingMetrics() {
  try {
    if (!fs.existsSync(ROUTING_LOG)) return '_No routing data yet_';

    const raw = fs.readFileSync(ROUTING_LOG, 'utf8').trim();
    if (!raw) return '_No routing data yet_';

    // Parse JSON Lines format (one JSON object per line)
    const log = raw.split('\n')
      .filter(Boolean)
      .map(line => {
        try { return JSON.parse(line); } catch { return null; }
      })
      .filter(Boolean);

    const total = log.length;
    const flashCalls = log.filter(d => d.tier === 'flash').length;
    const proCalls = log.filter(d => d.tier === 'pro').length;
    const escalations = log.filter(d => d.source === 'complexity' || d.source === 'failure').length;
    const explicitPro = log.filter(d => d.source === 'explicit').length;
    const avgScore = Math.round(log.reduce((s, d) => s + d.score, 0) / total);

    const flashPct = Math.round((flashCalls / total) * 100);
    const proPct = Math.round((proCalls / total) * 100);

    // Cost estimate using TIERS config constants
    const flashCostPerM = modelRouter.TIERS.FLASH.costPerMTokens;
    const proCostPerM = modelRouter.TIERS.PRO.costPerMTokens;
    const tokensPerRequest = 50000;
    const flashCost = flashCalls * tokensPerRequest * flashCostPerM / 1000000;
    const proCost = proCalls * tokensPerRequest * proCostPerM / 1000000;
    const totalCost = flashCost + proCost;
    const savings = proCalls * tokensPerRequest * (proCostPerM - flashCostPerM) / 1000000;

    const lines = [
      `| Metric | Value |`,
      `|--------|-------|`,
      `| Total Decisions | ${total} |`,
      `| Flash (⚡) | ${flashCalls} (${flashPct}%) |`,
      `| Pro (🏗️) | ${proCalls} (${proPct}%) |`,
      `| Complexity Escalations | ${escalations} |`,
      `| Explicit Pro Requests | ${explicitPro} |`,
      `| Avg Complexity Score | ${avgScore} |`,
      `| Est. Cost (Flash) | $${flashCost.toFixed(4)} |`,
      `| Est. Cost (Pro) | $${proCost.toFixed(4)} |`,
      `| Est. Total Cost | $${totalCost.toFixed(4)} |`,
      `| Est. Savings vs all-Pro | $${savings.toFixed(4)} |`
    ];

    return lines.join('\n');
  } catch {
    return '_Error reading routing log_';
  }
}

/**
 * Check if we recently printed metrics (don't spam every tool use).
 *
 * @returns {boolean} true if metrics were recently printed
 */
function shouldPrintMetrics() {
  try {
    const METRICS_PRINT_CACHE = path.join(os.tmpdir(), 'ck-kv-metrics-print.json');
    if (fs.existsSync(METRICS_PRINT_CACHE)) {
      const cache = JSON.parse(fs.readFileSync(METRICS_PRINT_CACHE, 'utf8'));
      // Only print every 5 tool uses or after prefix change
      if (Date.now() - cache.timestamp < 60000 && cache.count < 5) {
        cache.count++;
        fs.writeFileSync(METRICS_PRINT_CACHE, JSON.stringify(cache));
        return false;
      }
    }

    // Reset counter
    fs.writeFileSync(METRICS_PRINT_CACHE, JSON.stringify({ timestamp: Date.now(), count: 1 }));
    return true;
  } catch {
    return true;
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═════════════════════════════════════════════════════════════════════════════

async function main() {
  // Always allow operation to continue
  const result = { continue: true };

  try {
    const data = readMetrics();
    if (!data) {
      console.log(JSON.stringify(result));
      process.exit(0);
    }

    // Only print metrics periodically to avoid spamming the context
    if (shouldPrintMetrics()) {
      const formatted = formatMetrics(data);
      if (formatted) {
        console.log(formatted);
      }
    }
  } catch {
    // Always allow continuation
  }

  console.log(JSON.stringify(result));
  process.exit(0);
}

main().catch(() => {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
});
