#!/usr/bin/env node
/**
 * log-token-usage.js
 * Records token usage for agent interactions into ~/.system/tokens.db (SQLite).
 *
 * Usage:
 *   node log-token-usage.js --agent <id> --model <name> --task <id> --input <n> --output <n> [--cache <0|1>] [--cost <cents>]
 *
 * Example:
 *   node log-token-usage.js --agent coder_1 --model qwen3.6:35b --task task_123 --input 1500 --output 500 --cache 1 --cost 0
 *
 * Output:
 *   Prints summary of today's token usage.
 */

const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

const SYSTEM_DIR = path.resolve(process.env.HOME || '~', '.system');
const TOKENS_DB = path.join(SYSTEM_DIR, 'tokens.db');

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function die(msg, code = 1) {
  console.error(`[ERROR] ${msg}`);
  process.exit(code);
}

function runSql(db, sql, params = []) {
  const args = [db];
  if (params.length > 0) {
    // Use parameterised query via sqlite3 stdin
    const result = spawnSync('sqlite3', [db], {
      input: `.param set @p${params.map((_, i) => i).join(' @p')}\n${sql}`,
      encoding: 'utf-8',
      shell: false
    });
    return result;
  }
  const result = spawnSync('sqlite3', ['-json', db, sql], {
    encoding: 'utf-8',
    shell: false
  });
  return result;
}

function query(db, sql) {
  const result = spawnSync('sqlite3', ['-json', db, sql], {
    encoding: 'utf-8',
    shell: false,
    maxBuffer: 10 * 1024 * 1024
  });
  return result;
}

function ensureDb() {
  if (!fs.existsSync(TOKENS_DB)) {
    const init = spawnSync('sqlite3', [TOKENS_DB], {
      input: `
CREATE TABLE IF NOT EXISTS token_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent TEXT NOT NULL,
  model TEXT NOT NULL,
  task_id TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_hit INTEGER DEFAULT 0,
  cost_cents INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_token_agent ON token_usage(agent);
CREATE INDEX IF NOT EXISTS idx_token_created ON token_usage(created_at);
`,
      encoding: 'utf-8',
      shell: false
    });
    if (init.status !== 0) die(`Failed to create tokens.db: ${init.stderr}`);
  }
}

// -------------------------------------------------------
// Parse Args
// -------------------------------------------------------

const args = process.argv.slice(2);
const parsed = { agent: null, model: null, task: null, input: 0, output: 0, cache: 0, cost: 0 };

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--agent': parsed.agent = args[++i]; break;
    case '--model': parsed.model = args[++i]; break;
    case '--task': parsed.task = args[++i]; break;
    case '--input': parsed.input = parseInt(args[++i], 10); break;
    case '--output': parsed.output = parseInt(args[++i], 10); break;
    case '--cache': parsed.cache = parseInt(args[++i], 10); break;
    case '--cost': parsed.cost = parseInt(args[++i], 10); break;
    default:
      die(`Unknown option: ${args[i]}`);
  }
}

if (!parsed.agent) die('--agent is required');
if (!parsed.model) die('--model is required');
if (isNaN(parsed.input) || parsed.input < 0) die('--input must be non-negative integer');
if (isNaN(parsed.output) || parsed.output < 0) die('--output must be non-negative integer');

// -------------------------------------------------------
// Insert Record
// -------------------------------------------------------

ensureDb();

const insertSql = `
INSERT INTO token_usage (agent, model, task_id, input_tokens, output_tokens, cache_hit, cost_cents)
VALUES ('${parsed.agent.replace(/'/g, "''")}', '${parsed.model.replace(/'/g, "''")}', '${(parsed.task || '').replace(/'/g, "''")}', ${parsed.input}, ${parsed.output}, ${parsed.cache}, ${parsed.cost});
`;

const result = spawnSync('sqlite3', [TOKENS_DB], {
  input: insertSql,
  encoding: 'utf-8',
  shell: false
});

if (result.status !== 0) {
  die(`Insert failed: ${result.stderr}`);
}

console.log(`[OK] Token usage recorded: ${parsed.agent} / ${parsed.model} (in: ${parsed.input}, out: ${parsed.output})`);

// -------------------------------------------------------
// Today's Summary
// -------------------------------------------------------

const summarySql = `
SELECT
  COALESCE(SUM(input_tokens), 0) AS total_input,
  COALESCE(SUM(output_tokens), 0) AS total_output,
  COALESCE(SUM(cost_cents), 0) AS total_cost,
  COUNT(*) AS num_calls
FROM token_usage
WHERE date(created_at) = date('now');
`;

const summary = spawnSync('sqlite3', ['-json', TOKENS_DB, summarySql], {
  encoding: 'utf-8',
  shell: false
});

if (summary.status === 0 && summary.stdout.trim()) {
  try {
    const rows = JSON.parse(summary.stdout);
    if (rows.length > 0) {
      const r = rows[0];
      console.log(`\nToday's Usage Summary:`);
      console.log(`  Calls:        ${r.num_calls}`);
      console.log(`  Input tokens: ${r.total_input}`);
      console.log(`  Output tokens:${r.total_output}`);
      console.log(`  Total tokens: ${parseInt(r.total_input) + parseInt(r.total_output)}`);
      console.log(`  Cost (cents): ${r.total_cost}`);
    }
  } catch (e) {
    console.log(`\n[WARN] Could not parse today's summary: ${e.message}`);
  }
} else {
  console.log(`\n[WARN] No token usage data for today.`);
}
