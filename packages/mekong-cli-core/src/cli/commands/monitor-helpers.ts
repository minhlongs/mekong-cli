/**
 * monitor-helpers.ts — Time formatting, engine health display, and incident/SLA views for monitor CLI.
 */
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';

export const NOW = new Date('2026-03-22T09:30:00Z');

export function minutesAgo(n: number): string {
  const d = new Date(NOW.getTime() - n * 60 * 1000);
  return d.toISOString().replace('T', ' ').slice(0, 16) + 'Z';
}

export function hoursAgo(n: number): string {
  return minutesAgo(n * 60);
}

export function showEngineHealth(engine?: MekongEngine, label = 'Engine Status'): void {
  try {
    const health = engine?.openclaw?.getHealth();
    if (!health) return;
    divider();
    info(label);
    keyValue('  Uptime', `${Math.round(health.uptime / 1000)}s`);
    keyValue('  Missions completed', `${health.missionsCompleted}`);
    keyValue('  AGI score', `${health.agiScore}/100`);
    keyValue('  Circuit breaker', health.circuitBreakerState);
  } catch {
    /* engine not ready */
  }
}

export function renderMonitorIncidents(): void {
  heading('Incident History');
  divider();

  const incidents = [
    { id: 'INC-018', severity: 'P2', service: 'Worker Pool',    cause: 'Memory leak in recipe executor',        started: hoursAgo(18 * 24), duration: 23, mttr: 23, resolved: true },
    { id: 'INC-017', severity: 'P3', service: 'Webhook Relay',  cause: 'TLS cert renewal delay',                started: hoursAgo(35 * 24), duration: 8,  mttr: 8,  resolved: true },
    { id: 'INC-016', severity: 'P1', service: 'API Gateway',    cause: 'DDoS — rate limiter misconfiguration',  started: hoursAgo(52 * 24), duration: 41, mttr: 41, resolved: true },
    { id: 'INC-015', severity: 'P3', service: 'Dashboard',      cause: 'Deploy regression in auth middleware',  started: hoursAgo(68 * 24), duration: 12, mttr: 12, resolved: true },
    { id: 'INC-014', severity: 'P2', service: 'Worker Pool',    cause: 'LLM provider upstream outage',          started: hoursAgo(90 * 24), duration: 67, mttr: 67, resolved: true },
  ];

  for (const inc of incidents) {
    console.log(`  [${inc.id}] ${inc.severity}  ${inc.service.padEnd(16)} ${inc.cause}`);
    keyValue('    MTTR', `${inc.mttr} min`);
  }
  divider();

  const avgMttr = Math.round(incidents.reduce((s, i) => s + i.mttr, 0) / incidents.length);
  keyValue('Total incidents (90d)', String(incidents.length));
  keyValue('Avg MTTR',             `${avgMttr} min`);
  keyValue('P1 count',             String(incidents.filter(i => i.severity === 'P1').length));
  keyValue('P2 count',             String(incidents.filter(i => i.severity === 'P2').length));

  success('Incident history loaded');
}

export function renderMonitorSla(engine?: MekongEngine): void {
  heading('SLA Compliance Tracker');
  divider();

  const metrics = [
    { name: 'Uptime',          target: '99.95%',   actual: '99.96%', met: true  },
    { name: 'API p95 latency', target: '<200ms',   actual: '142ms',  met: true  },
    { name: 'MTTR (P1)',       target: '<60 min',  actual: '41 min', met: true  },
    { name: 'MTTR (P2)',       target: '<4 hours', actual: '45 min', met: true  },
    { name: 'Error rate',      target: '<0.1%',    actual: '0.08%',  met: true  },
    { name: 'Webhook p95',     target: '<150ms',   actual: '198ms',  met: false },
  ];

  heading('Current Period (March 2026)');
  for (const m of metrics) {
    const status = m.met ? 'MET   ' : 'BREACH';
    if (m.met) {
      success(`  ${status}  ${m.name.padEnd(20)} target: ${m.target.padEnd(10)} actual: ${m.actual}`);
    } else {
      warn(`  ${status}  ${m.name.padEnd(20)} target: ${m.target.padEnd(10)} actual: ${m.actual}`);
    }
  }

  try {
    const health = engine?.openclaw?.getHealth();
    if (health) {
      divider();
      info('OpenClaw SLA Metrics');
      keyValue('  AGI score',       `${health.agiScore}/100`);
      keyValue('  Circuit breaker', health.circuitBreakerState);
      keyValue('  Missions failed', `${health.missionsFailed}`);
    }
  } catch {
    /* engine not ready */
  }

  divider();
  const met = metrics.filter(m => m.met).length;
  keyValue('SLA compliance', `${met}/${metrics.length} metrics met`);
  keyValue('Overall status', met === metrics.length ? 'COMPLIANT' : 'PARTIAL BREACH');
  keyValue('Contract tier',  'Enterprise (99.95% SLA)');

  if (met === metrics.length) success('All SLA targets met');
  else warn(`${metrics.length - met} SLA target(s) breached — action required`);
}
