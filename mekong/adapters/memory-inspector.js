#!/usr/bin/env node
/**
 * memory-inspector.js
 * CLI tool for inspecting and querying ~/.system/memory.db.
 * Provides stats, search, recent entries, agent-specific views, and integrity checks.
 *
 * Usage:
 *   node memory-inspector.js [command]
 *
 * Commands:
 *   stats              — Show memory.db stats (table sizes, row counts)
 *   search <text>      — Search memory entries
 *   recent --limit <n> — Recent entries (default 10)
 *   agent <name>       — Show entries for a specific agent
 *   health             — Check memory.db integrity
 */

const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

const SYSTEM_DIR = path.resolve(process.env.HOME || '~', '.system');
const MEMORY_DB = path.join(SYSTEM_DIR, 'memory.db');

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
    // Return an empty result — the DB might not exist
    return [];
  }
  try {
    return JSON.parse(result.stdout || '[]');
  } catch (e) {
    return [];
  }
}

function run(db, sql) {
  const result = spawnSync('sqlite3', [db, sql], {
    encoding: 'utf-8',
    shell: false
  });
  return result;
}

function printTable(rows, cols) {
  if (rows.length === 0) {
    console.log('  (no data)\n');
    return;
  }
  const widths = cols.map(col => Math.max(col.header.length, ...rows.map(r => String(r[col.key] || '').length)));
  const header = cols.map((col, i) => String(col.header).padEnd(widths[i])).join(' ┃ ');
  const separator = cols.map((col, i) => '─'.repeat(widths[i])).join('━╋━');
  console.log('  ' + header);
  console.log('  ' + separator);
  for (const row of rows) {
    const line = cols.map((col, i) => String(row[col.key] ?? '').padEnd(widths[i])).join(' ┃ ');
    console.log('  ' + line);
  }
  console.log('');
}

function checkDb() {
  if (!fs.existsSync(MEMORY_DB)) {
    console.log('');
    console.log('  ⚠️  memory.db not found at:');
    console.log(`     ${MEMORY_DB}`);
    console.log('  No memory data has been persisted yet.\n');
    return false;
  }
  return true;
}

// -------------------------------------------------------
// Commands
// -------------------------------------------------------

function cmdStats() {
  console.log('\n📊 Memory DB Stats');
  console.log('='.repeat(60));

  if (!checkDb()) return;

  const fileSize = fs.statSync(MEMORY_DB).size;
  console.log(`  Database:       ${MEMORY_DB}`);
  console.log(`  File size:      ${(fileSize / 1024).toFixed(1)} KB (${fileSize} bytes)`);

  // List all tables
  const tablesRes = spawnSync('sqlite3', [MEMORY_DB, ".tables"], {
    encoding: 'utf-8',
    shell: false
  });

  if (tablesRes.status !== 0) {
    console.log('  [WARN] Could not list tables.\n');
    return;
  }

  const tables = tablesRes.stdout.trim().split(/\s+/).filter(Boolean);

  if (tables.length === 0) {
    console.log('  No tables found.\n');
    return;
  }

  console.log('');
  console.log('  Tables:');
  for (const table of tables) {
    const countRes = run(MEMORY_DB, `SELECT COUNT(*) FROM "${table}";`);
    const count = countRes.stdout.trim();
    const schemaRes = run(MEMORY_DB, `SELECT sql FROM sqlite_master WHERE type='table' AND name='${table}';`);
    const schema = schemaRes.stdout.trim();
    console.log(`    ${table}: ${count} rows`);
    if (schema) {
      // Print columns succinctly: extract column names from CREATE TABLE
      const cols = schema.replace(/^CREATE TABLE\s+\S+\s*\(/i, '').replace(/\);?\s*$/, '');
      const colNames = cols.split(',').map(c => c.trim().split(/\s+/)[0]).join(', ');
      console.log(`      Columns: ${colNames}`);
    }
  }
  console.log('');
}

function cmdSearch(text) {
  console.log(`\n🔍 Search Memory: "${text}"`);
  console.log('='.repeat(60));

  if (!checkDb()) return;

  if (!text) {
    die('Search text required.\nUsage: node memory-inspector.js search <text>');
  }

  const esc = text.replace(/'/g, "''");

  // Try to search across multiple common memory schemas
  const searches = [
    { table: 'memories', cols: ['content', 'summary', 'tags'] },
    { table: 'memory', cols: ['content', 'summary', 'tags'] },
    { table: 'entries', cols: ['content', 'title', 'description'] },
    { table: 'messages', cols: ['content', 'role', 'text'] },
    { table: 'conversations', cols: ['content', 'title'] },
    { table: 'embeddings', cols: ['content', 'text'] },
    { table: 'documents', cols: ['content', 'title', 'body'] }
  ];

  let anyResults = false;

  for (const search of searches) {
    // Check if table exists first
    const checkRes = run(MEMORY_DB, `SELECT name FROM sqlite_master WHERE type='table' AND name='${search.table}';`);
    if (!checkRes.stdout.trim()) continue;

    const searchClauses = search.cols.map(c => `COALESCE(${c}, '') LIKE '%${esc}%'`).join(' OR ');
    const sql = `SELECT * FROM "${search.table}" WHERE ${searchClauses} LIMIT 20;`;

    const rows = query(MEMORY_DB, sql);
    if (rows.length > 0) {
      anyResults = true;
      console.log(`  Table: ${search.table} (${rows.length} matches)`);
      console.log('  ' + '─'.repeat(50));
      for (const row of rows) {
        // Find the most relevant column containing the text
        for (const col of search.cols) {
          if (row[col] && String(row[col]).toLowerCase().includes(text.toLowerCase())) {
            const val = String(row[col]);
            console.log(`    ${col}: ${val.length > 200 ? val.slice(0, 200) + '...' : val}`);
            break;
          }
        }
        if (row.id || row.rowid) console.log(`    id: ${row.id || row.rowid}`);
        if (row.created_at || row.timestamp) console.log(`    at: ${row.created_at || row.timestamp}`);
        console.log('');
      }
    }
  }

  if (!anyResults) {
    console.log('  No matches found.\n');
  }
}

function cmdRecent(limit = 10) {
  console.log(`\n🕐 Recent Memory Entries (last ${limit})`);
  console.log('='.repeat(60));

  if (!checkDb()) return;

  // Try to find the primary memory table
  const tablesRes = spawnSync('sqlite3', [MEMORY_DB, ".tables"], {
    encoding: 'utf-8',
    shell: false
  });

  const tables = tablesRes.stdout.trim().split(/\s+/).filter(Boolean);
  let found = false;

  const preferredOrder = ['memories', 'memory', 'entries', 'messages', 'conversations', 'documents', 'embeddings'];
  for (const pref of preferredOrder) {
    if (tables.includes(pref)) {
      const sql = `SELECT * FROM "${pref}" ORDER BY rowid DESC LIMIT ${limit};`;
      const rows = query(MEMORY_DB, sql);
      if (rows.length > 0) {
        found = true;
        const keys = Object.keys(rows[0]).filter(k => !k.startsWith('embedding') && k !== 'vector');
        const displayKeys = keys.slice(0, 5); // Limit columns for readability
        printTable(rows, displayKeys.map(k => ({ key: k, header: k })));
      }
      break;
    }
  }

  if (!found) {
    console.log('  No recognizable memory tables found.\n');
    // Show all tables and their row counts as fallback
    if (tables.length > 0) {
      console.log('  Available tables:');
      for (const table of tables) {
        const cnt = run(MEMORY_DB, `SELECT COUNT(*) FROM "${table}";`).stdout.trim();
        console.log(`    ${table}: ${cnt} rows`);
      }
    }
    console.log('');
  }
}

function cmdAgent(name) {
  console.log(`\n👤 Memory Entries for Agent: ${name}`);
  console.log('='.repeat(60));

  if (!checkDb()) return;

  if (!name) {
    die('Agent name required.\nUsage: node memory-inspector.js agent <name>');
  }

  const esc = name.replace(/'/g, "''");

  // Search across common schemas for agent-specific fields
  const tablesRes = spawnSync('sqlite3', [MEMORY_DB, ".tables"], {
    encoding: 'utf-8',
    shell: false
  });

  const tables = tablesRes.stdout.trim().split(/\s+/).filter(Boolean);
  let anyResults = false;

  for (const table of tables) {
    // Try common agent/memory column patterns
    const agentCols = ['agent', 'agent_id', 'role', 'author', 'user', 'created_by'];
    for (const col of agentCols) {
      const checkSql = `SELECT * FROM pragma_table_info('${table}') WHERE name='${col}';`;
      const colInfo = query(MEMORY_DB, checkSql);
      if (colInfo.length > 0) {
        const sql = `SELECT * FROM "${table}" WHERE "${col}" = '${esc}' LIMIT 20;`;
        const rows = query(MEMORY_DB, sql);
        if (rows.length > 0) {
          anyResults = true;
          console.log(`  Table: ${table} (matched by ${col}, ${rows.length} rows)`);
          console.log('  ' + '─'.repeat(50));
          const keys = Object.keys(rows[0]).filter(k => !k.startsWith('embedding') && k !== 'vector');
          printTable(rows, keys.map(k => ({ key: k, header: k })));
        }
      }
    }
  }

  if (!anyResults) {
    console.log(`  No entries found for agent "${name}".\n`);
  }
}

function cmdHealth() {
  console.log('\n🩺 Memory DB Health Check');
  console.log('='.repeat(60));

  if (!checkDb()) return;

  const fileSize = fs.statSync(MEMORY_DB).size;
  console.log(`  File:   ${MEMORY_DB}`);
  console.log(`  Size:   ${(fileSize / 1024).toFixed(1)} KB`);

  // Run integrity check
  const integrityRes = run(MEMORY_DB, 'PRAGMA integrity_check;');
  const integrity = integrityRes.stdout.trim();
  console.log(`  Integrity: ${integrity === 'ok' ? '✅ OK' : '❌ ' + integrity}`);

  // Quick check (table count)
  const tablesRes = run(MEMORY_DB, "SELECT COUNT(*) FROM sqlite_master WHERE type='table';");
  const tableCount = tablesRes.stdout.trim();
  console.log(`  Tables: ${tableCount}`);

  // Foreign key check
  const fkRes = run(MEMORY_DB, 'PRAGMA foreign_key_check;');
  const fkIssues = fkRes.stdout.trim();
  if (fkIssues) {
    console.log(`  Foreign Keys: ⚠️  Issues found:`);
    console.log(`    ${fkIssues}`);
  } else {
    console.log(`  Foreign Keys: ✅ OK`);
  }

  // Auto-vacuum status
  const avRes = run(MEMORY_DB, 'PRAGMA auto_vacuum;');
  const av = avRes.stdout.trim();
  console.log(`  Auto-vacuum: ${av === '1' ? '✅ ON' : av === '0' ? '⚠️  OFF' : av}`);

  // Page count and page size
  const pageCountRes = run(MEMORY_DB, 'PRAGMA page_count;');
  const pageSizeRes = run(MEMORY_DB, 'PRAGMA page_size;');
  const pageCount = parseInt(pageCountRes.stdout.trim());
  const pageSize = parseInt(pageSizeRes.stdout.trim());
  console.log(`  Pages:  ${pageCount} × ${pageSize}B = ${(pageCount * pageSize / 1024).toFixed(1)} KB`);

  console.log('');
}

// -------------------------------------------------------
// Parse CLI
// -------------------------------------------------------

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log(`
Usage: node memory-inspector.js [command]

Commands:
  stats              — Show memory.db stats (table sizes, row counts)
  search <text>      — Search memory entries
  recent --limit <n> — Recent entries (default 10)
  agent <name>       — Show entries for a specific agent
  health             — Check memory.db integrity
`);
  process.exit(0);
}

const command = args[0];

switch (command) {
  case 'stats':
    cmdStats();
    break;

  case 'search': {
    const text = args.slice(1).join(' ');
    cmdSearch(text);
    break;
  }

  case 'recent': {
    let limit = 10;
    const limitIdx = args.indexOf('--limit');
    if (limitIdx !== -1 && limitIdx + 1 < args.length) {
      limit = parseInt(args[limitIdx + 1], 10) || 10;
    }
    cmdRecent(limit);
    break;
  }

  case 'agent': {
    const name = args.slice(1).join(' ');
    cmdAgent(name);
    break;
  }

  case 'health':
    cmdHealth();
    break;

  default:
    die(`Unknown command: ${command}. Use "stats", "search", "recent", "agent", or "health".`);
}
