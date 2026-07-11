/**
 * VentureOS CLI — Phase 0-3 Bootstrap
 *
 * Commands: init, list, show, export, decision new, event log, gate check,
 * workflow run/list/chain, compile <id> <compiler>/list, portfolio, compare, status
 * Runs via: npx tsx tools/cli/venture.ts <command> [args]
 */

import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

import { loadWorkflow, listWorkflows, runWorkflow } from '../../lib/workflow-runner.ts';
import { loadCompiler, listCompilers, runCompiler } from '../../lib/compiler.ts';
import { chainWorkflows, type ChainResult } from '../../lib/workflow-chain.ts';
import { listVentures, getVentureDetail, compareVentures } from '../../lib/portfolio.ts';
import type { WorkflowContext } from '../../lib/workflow-types.ts';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const VENTURES_DIR = join(ROOT, 'ventures');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function die(msg: string, code = 1): never {
  console.error(`\x1b[31mError:\x1b[0m ${msg}`);
  process.exit(code);
}

function info(msg: string) {
  console.log(`\x1b[36m->\x1b[0m ${msg}`);
}

function ok(msg: string) {
  console.log(`\x1b[32m✓\x1b[0m ${msg}`);
}

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function today(): string {
  return new Date().toISOString().split('T')[0].replace(/-/g, '');
}

function ts(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
}

function loadVenture(id: string) {
  const dir = join(VENTURES_DIR, id);
  if (!existsSync(dir)) die(`Venture not found: ${id}`);
  const toml = readFileSync(join(dir, 'venture.toml'), 'utf-8');
  const state = JSON.parse(readFileSync(join(dir, 'state.json'), 'utf-8'));
  return { dir, toml, state };
}

// ─── init ─────────────────────────────────────────────────────────────────────

async function cmdInit(args: string[]) {
  const nameIdx = args.indexOf('--name');
  const typeIdx = args.indexOf('--type');
  const name = nameIdx >= 0 && args[nameIdx + 1] ? args[nameIdx + 1] : args[0];
  const vtype = typeIdx >= 0 && args[typeIdx + 1] ? args[typeIdx + 1] : 'startup';

  if (!name) die('Usage: venture init <name> [--type startup|saas|studio]');

  const id = `${vtype}-${new Date().getFullYear()}-${slugify(name)}`;
  const dir = join(VENTURES_DIR, id);
  if (existsSync(dir)) die(`Venture "${id}" already exists`);

  const { mkdirSync } = await import('fs');
  mkdirSync(join(dir, 'workspace'), { recursive: true });
  mkdirSync(join(dir, 'artifacts'), { recursive: true });
  mkdirSync(join(dir, 'artifacts', 'market-research'), { recursive: true });
  mkdirSync(join(dir, 'artifacts', 'compiled'), { recursive: true });
  mkdirSync(join(dir, 'decisions'), { recursive: true });
  mkdirSync(join(dir, 'knowledge', 'local'), { recursive: true });
  mkdirSync(join(dir, 'wal'), { recursive: true });
  writeFileSync(join(dir, 'wal', 'current.jsonl'), '');

  const td = today();
  writeFileSync(join(dir, 'venture.toml'), `[id]
name = "${name}"
id = "${id}"
type = "${vtype}"
created_at = "${td}"

[lifecycle]
current_phase = "01"
phase_label = "IDENTIFY"

[state]
status = "active"
first_start = false
`);
  writeFileSync(join(dir, 'state.json'), JSON.stringify({
    current_phase: '01', phase_label: 'IDENTIFY', status: 'active',
    created_at: td, updated_at: td, gates_passed: [], decisions_count: 0, events_count: 0,
  }, null, 2));

  ok(`Venture "${id}" created at phase 01 (IDENTIFY)`);
  info(`Dir: ${dir}`);
  console.log(' venture workflow run <id> research/market-research — start research');
  console.log(' venture compile <id> business-plan — generate business plan');
}

// ─── list ─────────────────────────────────────────────────────────────────────

function cmdList() {
  if (!existsSync(VENTURES_DIR)) { info('No ventures. Run init first.'); return; }
  const entries = readdirSync(VENTURES_DIR, { withFileTypes: true }).filter((e) => e.isDirectory());
  if (entries.length === 0) { info('No ventures.'); return; }

  const PHASES: Record<string, string> = {
    '01': 'IDENTIFY','02': 'IDEA','03': 'VALIDATE','04': 'ARCHITECT',
    '05': 'INCORPORATE','06': 'SEED','07': 'BUILD','08': 'SCALE','09': 'EXIT',
  };

  console.log('\nID NAME PHASE');
  console.log('─'.repeat(90));
  for (const e of entries) {
    const cfg = join(VENTURES_DIR, e.name, 'venture.toml');
    let name = e.name, ph = '??';
    if (existsSync(cfg)) {
      const raw = readFileSync(cfg, 'utf-8');
      const nm = raw.match(/^name\s*=\s*"([^"]+)"/m);
      const pm = raw.match(/^current_phase\s*=\s*"(\d+)"/m);
      if (nm) name = nm[1]; if (pm) ph = pm[1];
    }
    console.log(`${e.name.padEnd(39)} ${name.padEnd(23)} ${ph} ${PHASES[ph] ?? ''}`);
  }
  console.log(`\n${entries.length} venture(s)\n`);
}

// ─── show ─────────────────────────────────────────────────────────────────────

function cmdShow(args: string[]) {
  const id = args[0];
  if (!id) die('Usage: venture show <venture-id>');
  const { dir, toml, state } = loadVenture(id);
  const eventsDir = join(dir, 'wal');
  const walFiles = existsSync(eventsDir) ? readdirSync(eventsDir).filter(f => f.endsWith('.jsonl')).sort() : [];
  let latest: string | null = null;
  for (const f of walFiles) {
    const lines = readFileSync(join(eventsDir, f), 'utf-8').split('\n').filter(Boolean);
    if (lines.length) latest = lines[lines.length - 1];
  }
  const dCount = readdirSync(join(dir, 'decisions')).filter(f => f.endsWith('.md')).length;

  console.log(`\n\x1b[1m${id}\x1b[0m`);
  console.log('─'.repeat(50));
  for (const l of toml.split('\n').filter(l => l.trim())) console.log(` ${l}`);
  console.log('\nRuntime:');
  console.log(JSON.stringify(state, null, 2).split('\n').map((l, i) => i === 0 ? l : ` ${l}`).join('\n'));
  console.log(`\nDecisions: ${dCount}`);
  if (latest) {
    const ev = JSON.parse(latest);
    console.log(`Latest event: ${ev.type} @ ${ev.timestamp}`);
  }
  console.log('');
}

// ─── export ───────────────────────────────────────────────────────────────────

function cmdExport(args: string[]) {
  const id = args[0];
  if (!id) die('Usage: venture export <venture-id>');
  const { dir } = loadVenture(id);
  const list = (d: string, prefix = ''): string[] => {
    const out: string[] = [];
    for (const e of readdirSync(d, { withFileTypes: true })) {
      const path = join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      out.push(rel);
      if (e.isDirectory()) out.push(...list(path, rel));
    }
    return out;
  };
  console.log(JSON.stringify({ venture: id, files: list(dir) }, null, 2));
}

// ─── decision new ─────────────────────────────────────────────────────────────

function cmdDecisionNew(args: string[]) {
  const id = args[0];
  const type = args[1];
  const ti = args.indexOf('--title');
  const pi = args.indexOf('--problem');
  const title = ti >= 0 && args[ti + 1] ? args[ti + 1] : '';
  const problem = pi >= 0 && args[pi + 1] ? args[pi + 1] : '';

  if (!id || !type) die('Usage: venture decision new <id> <type> --title "..." --problem "..."');
  if (!title || !problem) die('Missing --title or --problem');

  const { dir, state } = loadVenture(id);
  const did = `decision-${slugify(title)}-${new Date().getFullYear()}${String(new Date().getMonth() + 1).padStart(2, '0')}`;
  const d = {
    id: did, venture_id: id, phase: state.current_phase, type,
    status: 'proposed', created_at: ts(), title, problem,
    options: [], chosen: null, rationale: '', consequences: [],
  };
  writeFileSync(join(dir, 'decisions', `${did}.md`), toMd(d));
  state.decisions_count = (state.decisions_count ?? 0) + 1;
  state.updated_at = today();
  writeFileSync(join(dir, 'state.json'), JSON.stringify(state, null, 2));
  ok(`Decision created: ${did}`);
}

function toMd(d: Record<string, unknown>): string {
  const lines: string[] = ['---'];
  for (const [k, v] of Object.entries(d)) {
    lines.push(Array.isArray(v)
      ? `${k}:\n${(v as unknown[]).map(i => ` - ${typeof i === 'object' ? JSON.stringify(i) : i}`).join('\n')}`
      : `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
  }
  return `${lines.join('\n')}\n---\n`;
}

// ─── event log ────────────────────────────────────────────────────────────────

function cmdEventLog(args: string[]) {
  const id = args[0];
  if (!id) die('Usage: venture event log <venture-id>');
  const { dir } = loadVenture(id);
  const waldir = join(dir, 'wal');
  if (!existsSync(waldir)) { info('No WAL'); return; }
  const files = readdirSync(waldir).filter(f => f.endsWith('.jsonl')).sort();
  let total = 0;
  for (const f of files) {
    for (const line of readFileSync(join(waldir, f), 'utf-8').split('\n').filter(Boolean)) {
      const ev = JSON.parse(line);
      console.log(` ${ev.type} @ ${ev.timestamp}`);
      total++;
    }
  }
  info(total === 0 ? 'No events.' : `Total: ${total} event(s)`);
}

// ─── gate check ───────────────────────────────────────────────────────────────

function cmdGateCheck(args: string[]) {
  const id = args[0];
  const phase = args[1] || '03';
  if (!id) die('Usage: venture gate check <venture-id> [phase]');
  const { state } = loadVenture(id);
  const labels: Record<string, string> = {
    '01': 'IDENTIFY','02': 'IDEA','03': 'VALIDATE','04': 'ARCHITECT',
    '05': 'INCORPORATE','06': 'SEED','07': 'BUILD','08': 'SCALE','09': 'EXIT',
  };
  console.log(`\nGate check: ${id} -- phase ${phase} (${labels[phase] ?? ''})`);
  console.log('─'.repeat(50));
  if (phase === '03') {
    console.log('PMF Gate (Sean Ellis): ≥ 40% "Very Disappointed"');
    console.log(state.gates_passed?.includes('pmf-40') ? '\x1b[32m✓\x1b[0m Passed' : '\x1b[33m⊘\x1b[0m Not recorded');
  }
  console.log(`\nGates passed: ${(state.gates_passed ?? []).join(', ') || 'none'}`);
}

// ─── workflow run ─────────────────────────────────────────────────────────────

async function cmdWorkflowRun(args: string[]) {
  const id = args[0];
  const wfId = args[1];
  if (!id || !wfId) die('Usage: venture workflow run <venture-id> <workflow-id>');
  const { dir, state } = loadVenture(id);
  const wf = loadWorkflow(wfId);
  if (!wf.lifecycle_phases.includes(state.current_phase)) {
    info(`Workflow targets phases ${wf.lifecycle_phases.join(',')}, venture is in ${state.current_phase}`);
  }
  const ctx: WorkflowContext = {
    ventureId: id, ventureDir: dir,
    phase: state.current_phase, lifecyclePhase: state.phase_label,
    previousOutputs: {},
  };
  await runWorkflow(wfId, ctx);
}

function cmdWorkflowList() {
 const wfs = listWorkflows();
 if (wfs.length === 0) { info('No workflows found'); return; }
 console.log('\nID NAME PHASES');
 console.log('─'.repeat(70));
 for (const w of wfs) console.log(w.id.padEnd(35) + ' ' + w.name.padEnd(25) + ' ' + w.phases.join(','));
 console.log(`\n${wfs.length} workflow(s)\n`);
}

// ─── workflow chain ───────────────────────────────────────────────────────────

async function cmdWorkflowChain(args: string[]) {
 const id = args[0];
 const wfIds = args.slice(1);
 if (!id || wfIds.length === 0) die('Usage: venture workflow chain <venture-id> <workflow-id> [workflow-id...]');
 const { dir, state } = loadVenture(id);
 const result = await chainWorkflows(id, wfIds);
 console.log('\nChain result:');
 console.log(' Total: ' + String(result.total));
 console.log(' Passed: ' + String(result.succeeded));
 console.log(' Failed: ' + String(result.failed));
 if (result.artifacts.length > 0) {
  console.log(' Artifacts:');
  for (const a of result.artifacts) console.log(' ' + a);
 }
}

// ─── compile ──────────────────────────────────────────────────────────────────

async function cmdCompile(args: string[]) {
  const id = args[0];
  const compilerId = args[1];
  if (!id || !compilerId) die('Usage: venture compile <venture-id> <compiler-id>');
  const { dir } = loadVenture(id);
  await runCompiler(compilerId, dir, id);
}

function cmdCompileList() {
  const comps = listCompilers();
  if (comps.length === 0) { info('No compilers found'); return; }
  console.log('\nID NAME');
  console.log('─'.repeat(40));
  for (const c of comps) console.log(`${c.id.padEnd(25)} ${c.name}`);
  console.log(`\n${comps.length} compiler(s)\n`);
}

// ─── portfolio ────────────────────────────────────────────────────────────────

function cmdPortfolio() {
  const root = join(ROOT, 'ventures');
  const ventures = listVentures(root);
  if (ventures.length === 0) { info('No ventures'); return; }
  console.log('\nID NAME TYPE PHASE UPDATED');
  console.log('─'.repeat(90));
  for (const v of ventures) {
    console.log(`${v.id.padEnd(39)} ${v.name.padEnd(23)} ${v.type.padEnd(10)} ${v.phase} ${v.phaseLabel} ${v.updatedAt}`);
  }
  console.log(`\n${ventures.length} venture(s)\n`);
}

function cmdShowDetail(args: string[]) {
  const id = args[0];
  if (!id) die('Usage: venture show <venture-id>');
  const detail = getVentureDetail(join(ROOT, 'ventures'), id);
  if (!detail) die(`Venture not found: ${id}`);
  console.log(`\n\x1b[1m${detail.id}\x1b[0m`);
  console.log('─'.repeat(50));
  console.log(` Name: ${detail.name}`);
  console.log(` Type: ${detail.type}`);
  console.log(` Phase: ${detail.phase} — ${detail.phaseLabel}`);
  console.log(` Status: ${detail.status}`);
  console.log(` Updated: ${detail.updatedAt}`);
  console.log(`\n Decisions (${detail.decisions.length}):`);
  for (const d of detail.decisions) {
    console.log(` ${d.id}: ${d.title} [${d.type}]`);
  }
  console.log(`\n Recent events:`);
  for (const e of detail.recentEvents.slice(-5)) {
    console.log(` ${e.type} @ ${e.timestamp}`);
  }
  console.log('');
}

function cmdCompare(args: string[]) {
  if (args.length < 2) die('Usage: venture compare <id1> <id2> [id3...]');
  const result = compareVentures(join(ROOT, 'ventures'), args);
  if (!result) die('No valid ventures found');
  const dims = result.dimensions;
  const header = 'ID'.padEnd(40) + dims.map(d => d.padEnd(18)).join('');
  console.log('\n' + header);
  console.log('─'.repeat(header.length));
  for (const v of result.ventures) {
    const row = v.id.padEnd(40) + dims.map(d => String((v as Record<string, unknown>)[d] ?? '').padEnd(18)).join('');
    console.log(row);
  }
  console.log('');
}

function cmdStatus(args: string[]) {
  const id = args[0];
  if (!id) {
    const ventures = listVentures(join(ROOT, 'ventures'));
    const active = ventures.filter(v => v.status === 'active');
    console.log(`\n Total: ${ventures.length} | Active: ${active.length} | Completed: ${ventures.length - active.length}`);
    return;
  }
  const detail = getVentureDetail(join(ROOT, 'ventures'), id);
  if (!detail) die(`Venture not found: ${id}`);
  console.log(`\n${detail.id}: ${detail.status} (phase ${detail.phase} — ${detail.phaseLabel})`);
  console.log(` Decisions: ${detail.decisions.length} | Events: ${detail.recentEvents.length}`);
}

// ─── router ───────────────────────────────────────────────────────────────────

async function main() {
  type Cmd = (a: string[]) => Promise<void> | void;
  const cmds: Record<string, Cmd> = {
    init: cmdInit,
    list: cmdList,
    show: cmdShowDetail,
    export: cmdExport,
    portfolio: cmdPortfolio,
    compare: (a) => { if (a.length < 2) die('Usage: venture compare <id1> <id2> [id3...]'); cmdCompare(a); },
    status: cmdStatus,
    decision: async (a) => { const sub = a[0], rest = a.slice(1); if (sub === 'new') await cmdDecisionNew(rest); else die(`Unknown: ${sub}. Try: new`); },
    event: (a) => { const sub = a[0], rest = a.slice(1); if (sub === 'log') cmdEventLog(rest); else die(`Unknown: ${sub}. Try: log`); },
    gate: (a) => { const sub = a[0], rest = a.slice(1); if (sub === 'check') cmdGateCheck(rest); else die(`Unknown: ${sub}. Try: check`); },
    workflow: async (a) => { const sub = a[0], rest = a.slice(1); if (sub === 'run') await cmdWorkflowRun(rest); else if (sub === 'list') cmdWorkflowList(); else if (sub === 'chain') await cmdWorkflowChain(rest); else die(`Unknown: ${sub}. Try: run, list, chain`); },
    compile: async (a) => { const sub = a[0], rest = a.slice(1); if (sub === 'list') cmdCompileList(); else if (rest.length > 0) await cmdCompile([sub, ...rest]); else die('Usage: venture compile <id> <compiler> | venture compile list'); },
  };

  const argv = process.argv.slice(2);
  if (!argv.length) {
    console.log(`
VentureOS CLI v0.1
venture init <name> [--type startup|saas|studio]
venture list
venture show <id>
venture export <id>
venture decision new <id> <type> --title "..." --problem "..."
venture event log <id>
venture gate check <id> [phase]
venture workflow list
venture workflow run <id> <workflow-id>
venture workflow chain <id> <wf1> [wf2...]
venture portfolio
venture compare <id1> <id2> [id3...]
venture status [id]
venture compile list
venture compile <id> <compiler-id>
`);
    process.exit(0);
  }
  const cmd = argv[0];
  if (cmds[cmd]) {
    try { await cmds[cmd](argv.slice(1)); } catch (e) { die(String(e)); }
  } else die(`Unknown command: ${cmd}`);
}

main();
