#!/usr/bin/env node
/**
 * solo-ops-stats-server.mjs — Solo Ops KPI Dashboard
 * Lightweight HTTP server on port 3001.
 * Reads from .mekong/logs/ — NO direct D1 access.
 *
 * Routes:
 *   GET /         → HTML dashboard (auto-refresh 30s)
 *   GET /api/kpis → JSON KPI snapshot
 *
 * Usage: node scripts/solo-ops-stats-server.mjs
 */

import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PORT = 3001;
const PROJECT_ROOT = join(fileURLToPath(import.meta.url), '../../');
const LOGS_DIR = join(PROJECT_ROOT, '.mekong/logs');

const NEMOTRON_HEALTH_URL = 'http://192.168.11.111:11436/v1/models';
const DEEPSEEK_HEALTH_URL = 'http://192.168.11.111:11435/v1/models';
const GATEWAY_HEALTH_URL  = 'https://api.agencyos.network/health';

// --- Data Readers ---

/** Read last entry from health.jsonl */
function readHealthLog() {
  const path = join(LOGS_DIR, 'health.jsonl');
  if (!existsSync(path)) return null;
  try {
    const lines = readFileSync(path, 'utf8').trim().split('\n').filter(Boolean);
    return lines.length ? JSON.parse(lines[lines.length - 1]) : null;
  } catch { return null; }
}

/** Read kpi-snapshot.json */
function readKpiSnapshot() {
  const path = join(LOGS_DIR, 'kpi-snapshot.json');
  if (!existsSync(path)) return null;
  try { return JSON.parse(readFileSync(path, 'utf8')); }
  catch { return null; }
}

/** Parse today's heartbeat log for loop counts */
function readHeartbeatLog() {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const path = join(LOGS_DIR, `heartbeat-${date}.log`);
  if (!existsSync(path)) return { total: 0, success: 0, failed: 0 };
  try {
    const lines = readFileSync(path, 'utf8').split('\n').filter(Boolean);
    const success = lines.filter(l => /success|completed|ok/i.test(l)).length;
    const failed  = lines.filter(l => /error|fail|exception/i.test(l)).length;
    return { total: lines.length, success, failed };
  } catch { return { total: 0, success: 0, failed: 0 }; }
}

/** Live-probe an LLM or API endpoint (fire-and-forget with timeout) */
async function probeEndpoint(url, timeoutMs = 3000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    return res.ok ? 'up' : 'down';
  } catch { return 'down'; }
  finally { clearTimeout(timer); }
}

// --- KPI Builder ---

async function buildKpis() {
  const [nemotron, deepseek, gateway] = await Promise.all([
    probeEndpoint(NEMOTRON_HEALTH_URL),
    probeEndpoint(DEEPSEEK_HEALTH_URL),
    probeEndpoint(GATEWAY_HEALTH_URL),
  ]);

  const healthLog  = readHealthLog();
  const snapshot   = readKpiSnapshot();
  const heartbeat  = readHeartbeatLog();

  return {
    ts: new Date().toISOString(),
    system: {
      nemotron,
      deepseek,
      gateway,
      lastHealthEntry: healthLog,
    },
    ops: {
      loopsToday:   heartbeat.total,
      loopsSuccess: heartbeat.success,
      loopsFailed:  heartbeat.failed,
      uptimePct: heartbeat.total > 0
        ? Math.round((heartbeat.success / heartbeat.total) * 100)
        : null,
    },
    snapshot,
  };
}

// --- HTML Dashboard ---

function badge(status) {
  const color = status === 'up' ? '#22c55e' : '#ef4444';
  const label = status === 'up' ? 'UP' : 'DOWN';
  return `<span style="background:${color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700">${label}</span>`;
}

function renderDashboard({ system, ops, snapshot, ts }) {
  const css = '*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:24px}.sub{font-size:12px;color:#94a3b8;margin-bottom:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}.card{background:#1e293b;border-radius:10px;padding:18px}.card h2{font-size:12px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:12px}table{width:100%;border-collapse:collapse}td{padding:6px 0;font-size:13px;vertical-align:middle}td:first-child{color:#94a3b8;width:55%}td:last-child{font-weight:600;text-align:right}.num{font-size:26px;font-weight:800;color:#38bdf8}.ts{font-size:11px;color:#475569;margin-top:16px;text-align:right}.fail{color:#f87171}.ok{color:#4ade80}';
  const snapshotCard = snapshot
    ? `<div class="card"><h2>KPI Snapshot</h2><table>${
        Object.entries(snapshot).filter(([k])=>k!=='ts'&&k!=='date').slice(0,8)
          .map(([k,v])=>`<tr><td>${k}</td><td>${v??'—'}</td></tr>`).join('')
      }</table></div>` : '';
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta http-equiv="refresh" content="30"><title>Solo Ops Dashboard</title><style>${css}</style></head>
<body><h1 style="font-size:20px;font-weight:700;margin-bottom:4px">Solo Ops Dashboard</h1>
<div class="sub">M1 Max &nbsp;·&nbsp; auto-refresh 30s</div>
<div class="grid">
<div class="card"><h2>System Health</h2><table>
  <tr><td>Nemotron (fast)</td><td>${badge(system.nemotron)}</td></tr>
  <tr><td>DeepSeek R1 (deep)</td><td>${badge(system.deepseek)}</td></tr>
  <tr><td>API Gateway</td><td>${badge(system.gateway)}</td></tr>
</table></div>
<div class="card"><h2>Today's Loops</h2><table>
  <tr><td>Total executed</td><td class="num">${ops.loopsToday}</td></tr>
  <tr><td>Successful</td><td class="${ops.loopsSuccess>0?'ok':''}">${ops.loopsSuccess}</td></tr>
  <tr><td>Failed</td><td class="${ops.loopsFailed>0?'fail':''}">${ops.loopsFailed}</td></tr>
  <tr><td>Uptime</td><td>${ops.uptimePct!==null?ops.uptimePct+'%':'N/A'}</td></tr>
</table></div>
${snapshotCard}
</div><div class="ts">Last updated: ${new Date(ts).toLocaleString('en-GB',{hour12:false})}</div>
</body></html>`;
}

// --- HTTP Server ---

const server = createServer(async (req, res) => {
  const url = req.url.split('?')[0];

  if (url === '/api/kpis') {
    try {
      const kpis = await buildKpis();
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(kpis, null, 2));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  if (url === '/') {
    try {
      const kpis = await buildKpis();
      const html = renderDashboard(kpis);
      res.writeHead(200, { 'Content-Type': 'text/html', 'Cache-Control': 'no-store' });
      res.end(html);
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end(`Error: ${err.message}`);
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found');
});

// Bind localhost only — prevents LAN exposure without auth
const HOST = process.env.HOST || '127.0.0.1';
server.listen(PORT, HOST, () => {
  console.log(`Solo Ops Dashboard running → http://localhost:${PORT}`);
  console.log(`KPI API               → http://localhost:${PORT}/api/kpis`);
  console.log(`Logs dir              → ${LOGS_DIR}`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`Port ${PORT} already in use. Kill existing process or change PORT.`);
  } else {
    console.error('Server error:', err);
  }
  process.exit(1);
});
