/**
 * openclaw-health-views.ts — Rendering views for OpenClaw engine health CLI commands
 */
import {
  missionHeader, panel, panelClose, kv, kvColor, telemetryBar,
  hRule, section, tableHeader, tableRow, statusDot, statusBadge,
} from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

export interface Worker {
  id: string;
  status: 'active' | 'idle' | 'draining';
  task: string;
  cpuPct: number;
  memMb: number;
  uptime: string;
}

export const WORKERS: Worker[] = [
  { id: 'wkr_a1b2', status: 'active', task: 'msn_002 — Extracting pricing tables', cpuPct: 34, memMb: 312, uptime: '1h 22m' },
  { id: 'wkr_c3d4', status: 'active', task: 'msn_005 — Analyzing meta tags', cpuPct: 18, memMb: 198, uptime: '42m' },
  { id: 'wkr_e5f6', status: 'idle', task: '(waiting for mission)', cpuPct: 2, memMb: 88, uptime: '3h 05m' },
  { id: 'wkr_g7h8', status: 'draining', task: 'msn_006 — Cleanup after failure', cpuPct: 5, memMb: 104, uptime: '4h 18m' },
];

export function formatUptime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const parts: string[] = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  parts.push(`${minutes}m`);
  return parts.join(' ');
}

export function workerColor(status: Worker['status']): string {
  return status === 'active' ? '#10b981' : status === 'draining' ? '#f59e0b' : '#22d3ee';
}

export function renderWorkersView(): void {
  missionHeader('WORKER TELEMETRY', 'RESOURCE MONITORING');

  panel('WORKER POOL');
  const totalCpu = WORKERS.reduce((s, w) => s + w.cpuPct, 0);
  const totalMem = WORKERS.reduce((s, w) => s + w.memMb, 0);
  telemetryBar('Total CPU', totalCpu, 100);
  telemetryBar('Total Memory', (totalMem / 2), 2048);

  hRule();
  tableHeader(['ID', 'STATUS', 'CPU%', 'MEM(MB)', 'UPTIME']);

  for (const w of WORKERS) {
    const statusLabel = w.status === 'active' ? 'ACTIVE' : w.status === 'draining' ? 'DRAIN' : 'IDLE';
    tableRow([w.id, statusLabel, `${w.cpuPct}%`, String(w.memMb), w.uptime], workerColor(w.status));
  }

  hRule();
  kv('Total Workers', String(WORKERS.length));
  kv('Aggregate CPU', `${totalCpu}%`);
  kv('Aggregate Memory', `${totalMem} MB`);

  const activeCount = WORKERS.filter(w => w.status === 'active').length;
  const idleCount = WORKERS.filter(w => w.status === 'idle').length;
  const drainCount = WORKERS.filter(w => w.status === 'draining').length;
  kv('Breakdown', `${activeCount} active  ${idleCount} idle  ${drainCount} draining`);
  panelClose();

  panel('WORKER DETAILS');
  for (const w of WORKERS) {
    section(w.id);
    kvColor('Status', w.status.toUpperCase(), workerColor(w.status));
    kv('Task', w.task);
    telemetryBar('CPU', w.cpuPct, 100);
    telemetryBar('Memory', (w.memMb / 2), 512);
    kv('Uptime', w.uptime);
  }
  panelClose();
  console.log('');
}

export function renderCircuitView(engine: MekongEngine): void {
  missionHeader('CIRCUIT BREAKER', 'FAULT PROTECTION SYSTEM');

  panel('BREAKER STATE');
  try {
    if (engine.openclaw) {
      const h = engine.openclaw.getHealth();
      const state = h.circuitBreakerState;

      if (state === 'closed') {
        statusBadge('GO');
        kvColor('State', 'CLOSED — normal operation', '#10b981');
      } else if (state === 'open') {
        statusBadge('NO-GO');
        kvColor('State', 'OPEN — rejecting requests', '#ef4444');
      } else {
        statusBadge('STANDBY');
        kvColor('State', 'HALF-OPEN — testing recovery', '#f59e0b');
      }

      kv('Failure Threshold', '5 failures within 10 min');
      kv('Reset Timeout', '60 seconds (after OPEN)');
    } else {
      statusBadge('GO');
      kvColor('State', 'CLOSED — normal operation', '#10b981');
      kv('Failure Threshold', '5 failures within 10 min');
      kv('Current Failures', '1');
      kv('Last Failure', '2026-03-22 06:02:11 UTC');
      kvColor('Last Failure Reason', 'TemplateRenderError — onboarding-email', '#f59e0b');
      kv('Reset Timeout', '60 seconds (after OPEN)');
    }
  } catch (err: unknown) {
    statusBadge('NO-GO');
    kvColor('State', 'ERROR — check engine logs', '#ef4444');
    const msg = err instanceof Error ? err.message : String(err);
    kv('Error', msg.substring(0, 50));
  }
  panelClose();

  panel('STATE MACHINE');
  statusDot('green', 'CLOSED → normal operation, requests flow through');
  statusDot('red', 'OPEN → failures exceeded threshold, requests rejected fast');
  statusDot('amber', 'HALF-OPEN → testing recovery, 1 probe request allowed');
  hRule();
  section('TRANSITIONS');
  kvColor('CLOSED→OPEN', '5+ failures in 10 min window', '#ef4444');
  kvColor('OPEN→HALF-OPEN', '60s reset timeout expires', '#f59e0b');
  kvColor('HALF-OPEN→CLOSED', 'Probe request succeeds', '#10b981');
  kvColor('HALF-OPEN→OPEN', 'Probe request fails', '#ef4444');
  panelClose();

  panel('HEALTH SUMMARY');
  try {
    if (engine.openclaw) {
      const h = engine.openclaw.getHealth();
      if (h.circuitBreakerState === 'closed') {
        statusBadge('GO');
        kvColor('Result', 'Engine operating normally', '#10b981');
        if (h.missionsFailed > 0) {
          kvColor('Alert', `${h.missionsFailed} failure(s) — monitor for recurrence`, '#f59e0b');
        }
      } else if (h.circuitBreakerState === 'open') {
        statusBadge('NO-GO');
        kvColor('Result', 'New missions being rejected', '#ef4444');
        kv('Auto-retry', 'After reset timeout expires');
      } else {
        statusBadge('STANDBY');
        kvColor('Result', 'Probe request in progress', '#f59e0b');
      }
    } else {
      statusBadge('GO');
      kvColor('Result', 'Circuit is CLOSED — operating normally', '#10b981');
      kvColor('Alert', '1 failure recorded — monitor for recurrence (threshold: 5)', '#f59e0b');
    }
  } catch {
    statusBadge('NO-GO');
    kvColor('Result', 'Unable to determine state', '#ef4444');
  }
  panelClose();
  console.log('');
}
