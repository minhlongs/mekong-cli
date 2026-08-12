export interface MetricSnapshot {
  mrr: number;
  activeUsers: number;
  churnRate: number;
  nps: number;
  burnRate: number;
  runwayMonths: number;
  timestamp: string;
}

export interface Alert {
  metric: string;
  current: number;
  threshold: number;
  severity: 'warning' | 'critical';
}

interface ThresholdRule {
  threshold: number;
  severity: Alert['severity'];
  higherIsBad: boolean;
}

const THRESHOLDS: Record<string, ThresholdRule> = {
  churnRate:     { threshold: 5,  severity: 'critical', higherIsBad: true },
  nps:           { threshold: 30, severity: 'warning',  higherIsBad: false },
  runwayMonths:  { threshold: 6,  severity: 'critical', higherIsBad: false },
  burnRate:      { threshold: 50000, severity: 'warning', higherIsBad: true },
};

export class KPIDashboard {
  private metrics: Map<string, number[]> = new Map();
  private snapshot: MetricSnapshot = {
    mrr: 0, activeUsers: 0, churnRate: 0, nps: 0,
    burnRate: 0, runwayMonths: 12,
    timestamp: new Date().toISOString(),
  };

  recordMetric(name: string, value: number): void {
    const history = this.metrics.get(name) ?? [];
    history.push(value);
    if (history.length > 90) history.shift();
    this.metrics.set(name, history);

    if (name in this.snapshot) {
      (this.snapshot as unknown as Record<string, number>)[name] = value;
      this.snapshot.timestamp = new Date().toISOString();
    }
  }

  getMetrics(): MetricSnapshot {
    return { ...this.snapshot };
  }

  getDepartmentHealth(): Record<string, number> {
    const mrr = this.snapshot.mrr;
    const nps = this.snapshot.nps;
    const churn = this.snapshot.churnRate;
    const runway = this.snapshot.runwayMonths;
    const users = this.snapshot.activeUsers;

    return {
      product:     Math.min(100, 50 + Math.min(50, users / 2)),
      engineering: 80,
      sales:       Math.min(100, (mrr / 10000) * 100),
      marketing:   Math.min(100, 50 + Math.max(0, nps - 30)),
      finance:     Math.min(100, (runway / 12) * 100),
      legal:       85,
      hr:          75,
      support:     Math.min(100, Math.max(0, 100 - churn * 10)),
    };
  }

  checkAlerts(): Alert[] {
    const alerts: Alert[] = [];
    const snap = this.snapshot as unknown as Record<string, number>;

    for (const [metric, rule] of Object.entries(THRESHOLDS)) {
      const current = snap[metric] ?? 0;
      const breached = rule.higherIsBad
        ? current > rule.threshold
        : current < rule.threshold;

      if (breached) {
        alerts.push({ metric, current, threshold: rule.threshold, severity: rule.severity });
      }
    }

    return alerts;
  }

  generateReport(): string {
    const s = this.snapshot;
    const alerts = this.checkAlerts();
    const health = this.getDepartmentHealth();

    const alertLines = alerts.length
      ? alerts.map((a) => `- [${a.severity.toUpperCase()}] ${a.metric}: ${a.current} (threshold: ${a.threshold})`).join('\n')
      : '- None';

    const healthLines = Object.entries(health)
      .map(([d, h]) => `| ${d.padEnd(12)} | ${h.toFixed(0).padStart(3)}% |`)
      .join('\n');

    return [
      `# KPI Report — ${s.timestamp.split('T')[0]}`,
      '',
      '## Core Metrics',
      `- MRR: $${s.mrr.toLocaleString()}`,
      `- Active Users: ${s.activeUsers}`,
      `- Churn Rate: ${s.churnRate}%`,
      `- NPS: ${s.nps}`,
      `- Burn Rate: $${s.burnRate.toLocaleString()}/mo`,
      `- Runway: ${s.runwayMonths} months`,
      '',
      '## Alerts',
      alertLines,
      '',
      '## Department Health',
      '| Department   | Health |',
      '|--------------|--------|',
      healthLines,
    ].join('\n');
  }
}
