/** Auto-generate daily standup report */
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import chalk from 'chalk';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { CrmStore } from '../crm/store.js';
import type { FinanceStore } from '../finance/store.js';
import type { DailyStandup } from './types.js';

interface SopMetrics {
  runsCompleted?: number;
  codeCommits?: number;
  scheduled?: string[];
}

export class DailyStandupGenerator {
  constructor(
    private crm: CrmStore,
    private finance: FinanceStore,
    private sopMetricsPath: string,
  ) {}

  async generate(): Promise<Result<DailyStandup>> {
    try {
      const today = new Date();
      const yesterday = subDays(today, 1);
      const yStart = format(startOfDay(yesterday), "yyyy-MM-dd'T'HH:mm:ss");
      const yEnd = format(endOfDay(yesterday), "yyyy-MM-dd'T'HH:mm:ss");

      const [invoicesResult, revenueResult, ticketsResult, customersResult, sopMetrics] =
        await Promise.all([
          this.finance.getInvoices(),
          this.finance.getRevenue({ from: yStart, to: yEnd }),
          this.crm.getAll('tickets'),
          this.crm.getAll('customers'),
          this.loadSopMetrics(),
        ]);

      if (!invoicesResult.ok) return err(invoicesResult.error);
      if (!revenueResult.ok) return err(revenueResult.error);
      if (!ticketsResult.ok) return err(ticketsResult.error);
      if (!customersResult.ok) return err(customersResult.error);

      const allInvoices = invoicesResult.value;
      const todayStr = format(today, 'yyyy-MM-dd');

      const invoicesSent = allInvoices.filter(
        (inv) => inv.createdAt >= yStart && inv.createdAt <= yEnd,
      ).length;
      const revenueYesterday = revenueResult.value.reduce((s, r) => s + r.amount, 0);

      const resolvedTickets = ticketsResult.value.filter(
        (t) => t.resolvedAt && t.resolvedAt >= yStart && t.resolvedAt <= yEnd,
      );

      const openTickets = ticketsResult.value.filter(
        (t) => t.status === 'open' || t.status === 'in_progress',
      );

      const overdueInvoices = allInvoices.filter(
        (inv) => inv.status === 'overdue' || (inv.status === 'sent' && inv.dueDate < todayStr),
      );

      const activeCustomers = customersResult.value.filter((c) => c.status === 'active');
      const mrr = activeCustomers.reduce((s, c) => s + c.mrr, 0);

      // Follow-ups: leads with nextFollowUp today
      const leadsResult = await this.crm.getAll('leads');
      const followUps = leadsResult.ok
        ? leadsResult.value
            .filter((l) => l.nextFollowUp?.startsWith(todayStr))
            .map((l) => ({
              contact: `${l.name} (${l.company ?? l.email})`,
              reason: `Lead follow-up — status: ${l.status}`,
              priority: l.score > 70 ? 'high' : 'normal',
            }))
        : [];

      // SLA at-risk tickets
      const slaAtRisk = openTickets
        .filter(
          (t) =>
            t.priority === 'critical' &&
            t.slaDeadline &&
            t.slaDeadline <= format(today, "yyyy-MM-dd'T'HH:mm:ss"),
        )
        .map((t) => `SLA at risk: ticket ${t.id} — "${t.subject}"`);

      const overdueMessages = overdueInvoices.map(
        (inv) => `Overdue invoice ${inv.number} — $${inv.total.toFixed(2)} from ${inv.customerName}`,
      );

      const blockers = [...overdueMessages, ...slaAtRisk];

      return ok({
        date: todayStr,
        yesterday: {
          tasksCompleted: resolvedTickets.map((t) => `Resolved: ${t.subject}`),
          sopRunsCompleted: sopMetrics.runsCompleted ?? 0,
          codeCommits: sopMetrics.codeCommits ?? 0,
          ticketsResolved: resolvedTickets.length,
          invoicesSent,
          revenue: Math.round(revenueYesterday * 100) / 100,
        },
        today: {
          scheduledTasks: sopMetrics.scheduled ?? [],
          followUps,
          deadlines: overdueInvoices.map((inv) => ({
            item: `Invoice ${inv.number} — ${inv.customerName}`,
            dueDate: inv.dueDate,
          })),
          sopScheduled: sopMetrics.scheduled ?? [],
        },
        blockers,
        metrics: {
          mrrCurrent: Math.round(mrr * 100) / 100,
          mrrTarget: 0, // user-defined target, defaulting to 0
          openTickets: openTickets.length,
          overdueInvoices: overdueInvoices.length,
          budgetUsedToday: 0, // cost tracker integration future
        },
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  renderCli(standup: DailyStandup): string {
    const lines: string[] = [];
    lines.push(chalk.bold.cyan(`\n  DAILY STANDUP — ${standup.date}`));
    lines.push(chalk.gray('  ' + '─'.repeat(48)));

    lines.push(chalk.bold('\n  YESTERDAY'));
    if (standup.yesterday.tasksCompleted.length === 0) {
      lines.push(chalk.gray('    No tasks recorded'));
    } else {
      for (const t of standup.yesterday.tasksCompleted) {
        lines.push(chalk.green(`    ✓ ${t}`));
      }
    }
    lines.push(chalk.gray(`    SOP runs: ${standup.yesterday.sopRunsCompleted}`));
    lines.push(chalk.gray(`    Commits: ${standup.yesterday.codeCommits}`));
    lines.push(chalk.gray(`    Tickets resolved: ${standup.yesterday.ticketsResolved}`));
    lines.push(chalk.gray(`    Invoices sent: ${standup.yesterday.invoicesSent}`));
    lines.push(chalk.gray(`    Revenue: $${standup.yesterday.revenue.toFixed(2)}`));

    lines.push(chalk.bold('\n  TODAY'));
    if (standup.today.followUps.length === 0) {
      lines.push(chalk.gray('    No follow-ups scheduled'));
    } else {
      for (const f of standup.today.followUps) {
        const color = f.priority === 'high' ? chalk.yellow : chalk.white;
        lines.push(color(`    → ${f.contact}: ${f.reason}`));
      }
    }
    for (const d of standup.today.deadlines) {
      lines.push(chalk.yellow(`    ⏰ Due ${d.dueDate}: ${d.item}`));
    }

    lines.push(chalk.bold('\n  BLOCKERS'));
    if (standup.blockers.length === 0) {
      lines.push(chalk.green('    None'));
    } else {
      for (const b of standup.blockers) {
        lines.push(chalk.red(`    ✗ ${b}`));
      }
    }

    lines.push(chalk.bold('\n  METRICS'));
    lines.push(chalk.white(`    MRR: $${standup.metrics.mrrCurrent.toFixed(2)}`));
    lines.push(chalk.white(`    Open tickets: ${standup.metrics.openTickets}`));
    lines.push(chalk.white(`    Overdue invoices: ${standup.metrics.overdueInvoices}`));

    lines.push('');
    return lines.join('\n');
  }

  private async loadSopMetrics(): Promise<SopMetrics> {
    if (!existsSync(this.sopMetricsPath)) return {};
    try {
      const raw = await readFile(this.sopMetricsPath, 'utf-8');
      return JSON.parse(raw) as SopMetrics;
    } catch {
      return {};
    }
  }
}
