/** CLI dashboard rendering — Unicode box-drawing Andon Board */
import chalk, { type ChalkInstance } from 'chalk';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { AndonBoard } from './types.js';
import type { MetricsAggregator } from './metrics-aggregator.js';

const WIDTH = 60;
const BOX = {
  tl: '┌', tr: '┐', bl: '└', br: '┘',
  h: '─', v: '│', lt: '├', rt: '┤', t: '┬', b: '┴', x: '┼',
} as const;

function pad(str: string, len: number): string {
  const visible = str.replace(/\x1B\[[0-9;]*m/g, '');
  const diff = len - visible.length;
  return diff > 0 ? str + ' '.repeat(diff) : str;
}

function hline(left: string, mid: string, right: string): string {
  return left + BOX.h.repeat(WIDTH - 2) + right;
}

function row(content: string): string {
  return BOX.v + ' ' + pad(content, WIDTH - 3) + BOX.v;
}

function statusColor(status: AndonBoard['status']): ChalkInstance {
  if (status === 'green') return chalk.green;
  if (status === 'yellow') return chalk.yellow;
  return chalk.red;
}

function statusIcon(status: AndonBoard['status']): string {
  if (status === 'green') return chalk.green('● OPERATIONAL');
  if (status === 'yellow') return chalk.yellow('● WARNING');
  return chalk.red('● CRITICAL');
}

function alertColor(level: 'info' | 'warning' | 'critical'): ChalkInstance {
  if (level === 'critical') return chalk.red;
  if (level === 'warning') return chalk.yellow;
  return chalk.cyan;
}

export class DashboardRenderer {
  constructor(private aggregator: MetricsAggregator) {}

  async buildBoard(): Promise<Result<AndonBoard>> {
    try {
      const metricsResult = await this.aggregator.collectAll();
      if (!metricsResult.ok) return err(metricsResult.error);

      const metrics = metricsResult.value;
      const status = this.aggregator.determineStatus(metrics);
      const alerts = this.aggregator.buildAlerts(metrics);

      const nextDeadlineResult = await this.aggregator.getQuickStats();
      const quickStats = nextDeadlineResult.ok
        ? nextDeadlineResult.value
        : {
            mrr: `$${metrics.mrr.toFixed(2)}`,
            customers: String(metrics.activeCustomers),
            openTickets: String(metrics.openTickets),
            todayRevenue: `$${metrics.todayRevenue.toFixed(2)}`,
            todayExpenses: `$${metrics.todayExpenses.toFixed(2)}`,
            agentBudgetUsed: '$0.00',
            nextDeadline: 'None',
          };

      return ok({
        status,
        alerts,
        quickStats,
        recentActivity: metrics.recentActivity,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  render(board: AndonBoard): string {
    const color = statusColor(board.status);
    const lines: string[] = [];

    // Header
    lines.push(color(hline(BOX.tl, BOX.t, BOX.tr)));
    const title = pad('  MEKONG ANDON BOARD', WIDTH - 4);
    lines.push(color(BOX.v) + chalk.bold(` ${title}`) + color(BOX.v));
    lines.push(color(BOX.v) + '  ' + statusIcon(board.status) + ' '.repeat(WIDTH - 18) + color(BOX.v));
    lines.push(color(hline(BOX.lt, BOX.x, BOX.rt)));

    // Quick stats (2-column layout)
    lines.push(color(row(chalk.bold('  QUICK STATS'))));
    const stats = board.quickStats;
    const statPairs: [string, string][] = [
      ['MRR',       stats.mrr],
      ['Customers', stats.customers],
      ['Tickets',   stats.openTickets],
      ['Revenue',   stats.todayRevenue],
      ['Expenses',  stats.todayExpenses],
      ['Next Due',  stats.nextDeadline],
    ];
    for (const [label, value] of statPairs) {
      const cell = `  ${chalk.gray(label.padEnd(12))} ${chalk.white(value)}`;
      lines.push(color(row(cell)));
    }
    lines.push(color(hline(BOX.lt, BOX.x, BOX.rt)));

    // Alerts
    lines.push(color(row(chalk.bold('  ALERTS'))));
    if (board.alerts.length === 0) {
      lines.push(color(row(chalk.green('  No active alerts'))));
    } else {
      for (const alert of board.alerts.slice(0, 5)) {
        const ac = alertColor(alert.level);
        const icon = alert.level === 'critical' ? '✗' : alert.level === 'warning' ? '⚠' : 'ℹ';
        const text = `  ${ac(icon)} [${alert.source}] ${alert.message}`;
        lines.push(color(row(text)));
      }
    }
    lines.push(color(hline(BOX.lt, BOX.x, BOX.rt)));

    // Recent activity
    lines.push(color(row(chalk.bold('  RECENT ACTIVITY'))));
    if (board.recentActivity.length === 0) {
      lines.push(color(row(chalk.gray('  No recent activity'))));
    } else {
      for (const act of board.recentActivity.slice(0, 4)) {
        const ts = act.timestamp.slice(0, 16).replace('T', ' ');
        const text = `  ${chalk.gray(ts)}  ${act.action}`;
        lines.push(color(row(text)));
      }
    }

    // Footer
    lines.push(color(hline(BOX.bl, BOX.b, BOX.br)));

    return lines.join('\n');
  }
}
