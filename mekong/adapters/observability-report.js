#!/usr/bin/env node
/**
 * observability-report.js
 * CLI report tool for the Mekong AI OS observability system.
 * Provides summaries of token usage, errors, traces, and daemon health.
 *
 * Usage:
 *   node observability-report.js [command]
 *
 * Commands:
 *   today              — Summary of today's token usage by agent
 *   week               — Summary of last 7 days
 *   errors             — Top 10 errors by count
 *   errors --recent    — Last 10 errors by last_seen
 *   trace --last <n>   — Last N trace entries
 *   trace --agent <id> — Trace entries for a specific agent
 *   status             — All daemons health check summary
 */

const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

const SYSTEM_DIR = path.resolve(process.env.HOME || '~', '.system');
const SCRIPT_DIR = __dirname;
const TOKENS_DB = path.join(SYSTEM_DIR, 'tokens.db');
const ERRORS_DB = path.join(SYSTEM_DIR, 'errors.db');
const TRACE_LOG = path.join(SYSTEM_DIR, 'trace.log');
const HEALTH_CHECK = path.join(SCRIPT_DIR, 'health-check.sh');

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function die(msg, code = 1) {
  console.error(`[ERROR] ${msg}`);
  process.exit(code);
}

function query(db, sql) {
  const result = spawnSync('sqlite3', ['-json', db, sql], {
    encoding: 'utf-8',
    shell: false,
    maxBuffer: 10 * 1024 * 1024
  });
  if (result.status !== 0) {
    die(`SQLite query failed: ${result.stderr}`);
  }
  try {
    return JSON.parse(result.stdout || '[]');
  } catch (e) {
    return [];
  }
}

function printTable(rows, cols) {
  if (rows.length === 0) {
    console.log('  (no data)');
    return;
  }
  // Calculate column widths
  const widths = cols.map(col => Math.max(col.header.length, ...rows.map(r => String(r[col.key] || '').length)));
  const sep = (w) => '─'.repeat(w);

  // Header
  const header = cols.map((col, i) => String(col.header).padEnd(widths[i])).join(' ┃ ');
  const separator = cols.map((col, i) => sep(widths[i])).join('━╋━');
  console.log('  ' + header);
  console.log('  ' + separator);

  // Rows
  for (const row of rows) {
    const line = cols.map((col, i) => String(row[col.key] ?? '').padEnd(widths[i])).join(' ┃ ');
    console.log('  ' + line);
  }
  console.log('');
}

function formatDate(iso) {
  if (!iso) return '-';
  // sqlite datetime format: 2026-05-28 12:34:56
  return iso.replace('T', ' ').slice(0, 19);
}

// -------------------------------------------------------
// Commands
// -------------------------------------------------------

function cmdToday() {
  if (!fs.existsSync(TOKENS_DB)) {
    console.log('No tokens.db found — no data recorded yet.\n');
    return;
  }

  const sql = `
    SELECT
      agent,
      SUM(input_tokens) AS input_tokens,
      SUM(output_tokens) AS output_tokens,
      SUM(input_tokens + output_tokens) AS total_tokens,
      SUM(cost_cents) AS cost_cents,
      COUNT(*) AS calls
    FROM token_usage
    WHERE date(created_at) = date('now')
    GROUP BY agent
    ORDER BY total_tokens DESC;
  `;

  console.log('\n📊 Today\'s Token Usage by Agent');
  console.log('='.repeat(60));
  const rows = query(TOKENS_DB, sql);
  if (rows.length === 0) {
    console.log('  No token usage recorded today.\n');
    return;
  }
  printTable(rows, [
    { key: 'agent', header: 'Agent' },
    { key: 'calls', header: 'Calls' },
    { key: 'input_tokens', header: 'Input' },
    { key: 'output_tokens', header: 'Output' },
    { key: 'total_tokens', header: 'Total' },
    { key: 'cost_cents', header: 'Cost (¢)' }
  ]);
}

function cmdWeek() {
  if (!fs.existsSync(TOKENS_DB)) {
    console.log('No tokens.db found — no data recorded yet.\n');
    return;
  }

  const sql = `
    SELECT
      date(created_at) AS day,
      SUM(input_tokens) AS input_tokens,
      SUM(output_tokens) AS output_tokens,
      SUM(input_tokens + output_tokens) AS total_tokens,
      SUM(cost_cents) AS cost_cents,
      COUNT(*) AS calls
    FROM token_usage
    WHERE created_at >= datetime('now', '-7 days')
    GROUP BY date(created_at)
    ORDER BY day DESC;
  `;

  console.log('\n📈 Token Usage — Last 7 Days');
  console.log('='.repeat(60));
  const rows = query(TOKENS_DB, sql);
  if (rows.length === 0) {
    console.log('  No token usage in last 7 days.\n');
    return;
  }
  printTable(rows, [
    { key: 'day', header: 'Date' },
    { key: 'calls', header: 'Calls' },
    { key: 'input_tokens', header: 'Input' },
    { key: 'output_tokens', header: 'Output' },
    { key: 'total_tokens', header: 'Total' },
    { key: 'cost_cents', header: 'Cost (¢)' }
  ]);

  // Aggregated totals
  const totalInput = rows.reduce((s, r) => s + parseInt(r.input_tokens), 0);
  const totalOutput = rows.reduce((s, r) => s + parseInt(r.output_tokens), 0);
  const totalCalls = rows.reduce((s, r) => s + parseInt(r.calls), 0);
  console.log(`  Totals: ${totalCalls} calls, ${totalInput} in / ${totalOutput} out (${totalInput + totalOutput} total tokens)\n`);
}

function cmdErrors(recent = false) {
  if (!fs.existsSync(ERRORS_DB)) {
    console.log('No errors.db found.\n');
    return;
  }

  console.log('\n⚠️  Error Tracking');
  console.log('='.repeat(60));

  if (recent) {
    const sql = `
      SELECT id, component, error_type, context, count, last_seen
      FROM errors
      ORDER BY last_seen DESC
      LIMIT 10;
    `;
    const rows = query(ERRORS_DB, sql);
    if (rows.length === 0) {
      console.log('  No errors recorded.\n');
      return;
    }
    printTable(rows, [
      { key: 'id', header: 'ID' },
      { key: 'component', header: 'Component' },
      { key: 'error_type', header: 'Type' },
      { key: 'context', header: 'Context' },
      { key: 'count', header: 'Count' },
      { key: 'last_seen', header: 'Last Seen' }
    ]);
  } else {
    const sql = `
      SELECT id, component, error_type, context, count, last_seen
      FROM errors
      ORDER BY count DESC
      LIMIT 10;
    `;
    const rows = query(ERRORS_DB, sql);
    if (rows.length === 0) {
      console.log('  No errors recorded.\n');
      return;
    }
    printTable(rows, [
      { key: 'id', header: 'ID' },
      { key: 'component', header: 'Component' },
      { key: 'error_type', header: 'Type' },
      { key: 'count', header: 'Count' },
      { key: 'last_seen', header: 'Last Seen' }
    ]);
  }
}

function cmdTrace(last = null, agent = null) {
  if (!fs.existsSync(TRACE_LOG)) {
    console.log('No trace.log found.\n');
    return;
  }

  const content = fs.readFileSync(TRACE_LOG, 'utf-8');
  const lines = content.split('\n').filter(l => l && !l.startsWith('#'));

  console.log('\n📋 Trace Log');
  console.log('='.repeat(60));

  if (lines.length === 0) {
    console.log('  No trace entries.\n');
    return;
  }

  let filtered = lines;

  if (agent) {
    filtered = filtered.filter(l => l.includes(` | ${agent} | `));
  }

  if (last !== null) {
    filtered = filtered.slice(-last);
  }

  if (filtered.length === 0) {
    console.log('  No matching trace entries.\n');
    return;
  }

  // Parse and display as table
  const entries = filtered.map(l => {
    const parts = l.split(' | ');
    return {
      timestamp: parts[0] || '-',
      agent: parts[1] || '-',
      task: parts[2] || '-',
      model: parts[3] || '-',
      input: parts[4] || '-',
      output: parts[5] || '-',
      duration: parts[6] || '-',
      status: parts[7] || '-'
    };
  });

  printTable(entries, [
    { key: 'timestamp', header: 'Timestamp' },
    { key: 'agent', header: 'Agent' },
    { key: 'task', header: 'Task' },
    { key: 'model', header: 'Model' },
    { key: 'input', header: 'In' },
    { key: 'output', header: 'Out' },
    { key: 'duration', header: 'Dur(ms)' },
    { key: 'status', header: 'Status' }
  ]);
}

function cmdStatus() {
  console.log('\n🔍 Daemon Health Check');
  console.log('='.repeat(60));

  // Check trace log
  const traceExists = fs.existsSync(TRACE_LOG);
  console.log(`  trace.log:         ${traceExists ? '✅ OK' : '❌ MISSING'} (${TRACE_LOG})`);

  // Check tokens DB
  const tokensExists = fs.existsSync(TOKENS_DB);
  if (tokensExists) {
    const rows = query(TOKENS_DB, 'SELECT COUNT(*) AS cnt FROM token_usage;');
    const cnt = rows[0]?.cnt ?? 0;
    console.log(`  tokens.db:         ✅ OK (${cnt} records)`);
  } else {
    console.log(`  tokens.db:         ❌ MISSING (${TOKENS_DB})`);
  }

  // Check errors DB
  const errorsExists = fs.existsSync(ERRORS_DB);
  if (errorsExists) {
    const rows = query(ERRORS_DB, 'SELECT COUNT(*) AS cnt FROM errors;');
    const cnt = rows[0]?.cnt ?? 0;
    console.log(`  errors.db:         ✅ OK (${cnt} records)`);
  } else {
    console.log(`  errors.db:         ❌ MISSING (${ERRORS_DB})`);
  }

  // Run health-check.sh if it exists
  if (fs.existsSync(HEALTH_CHECK)) {
    console.log('');
    console.log('  Running health-check.sh...');
    const result = spawnSync('bash', [HEALTH_CHECK], {
      encoding: 'utf-8',
      shell: false,
      timeout: 30000
    });
    if (result.status === 0) {
      console.log(result.stdout);
    } else {
      console.log(`  [WARN] health-check.sh exited with code ${result.status}`);
      if (result.stderr) console.log(`  ${result.stderr}`);
    }
  } else {
    console.log('');
    console.log('  health-check.sh:  ⚠️  NOT FOUND (optional)');
  }
  console.log('');
}

// -------------------------------------------------------
// Parse CLI
// -------------------------------------------------------

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log(`
Usage: node observability-report.js [command]

Commands:
  today              — Summary of today's token usage by agent
  week               — Summary of last 7 days
  errors             — Top 10 errors by count
  errors --recent    — Last 10 errors by last_seen
  trace --last <n>   — Last N trace entries
  trace --agent <id> — Trace entries for a specific agent
  status             — All daemons health check summary
`);
  process.exit(0);
}

const command = args[0];

switch (command) {
  case 'today':
    cmdToday();
    break;

  case 'week':
    cmdWeek();
    break;

  case 'errors': {
    const recent = args.includes('--recent');
    cmdErrors(recent);
    break;
  }

  case 'trace': {
    let last = null;
    let agent = null;
    const lastIdx = args.indexOf('--last');
    if (lastIdx !== -1 && lastIdx + 1 < args.length) {
      last = parseInt(args[lastIdx + 1], 10);
    }
    const agentIdx = args.indexOf('--agent');
    if (agentIdx !== -1 && agentIdx + 1 < args.length) {
      agent = args[agentIdx + 1];
    }
    cmdTrace(last, agent);
    break;
  }

  case 'status':
    cmdStatus();
    break;

  default:
    die(`Unknown command: ${command}. Use "today", "week", "errors", "trace", or "status".`);
}
