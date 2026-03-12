/** Collect and aggregate metrics from all modules into unified dashboard data */
import { format } from 'date-fns';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { CrmStore } from '../crm/store.js';
import type { FinanceStore } from '../finance/store.js';
import type { AndonBoard } from './types.js';

export interface AggregatedMetrics {
  mrr: number;
  totalCustomers: number;
  activeCustomers: number;
  openTickets: number;
  criticalTickets: number;
  todayRevenue: number;
  todayExpenses: number;
  overdueInvoices: number;
  overdueAmount: number;
  slaAtRisk: number;
  recentActivity: Array<{ action: string; timestamp: string; source: string }>;
}

export class MetricsAggregator {
  constructor(
    private crm: CrmStore,
    private finance: FinanceStore,
  ) {}

  async collectAll(): Promise<Result<AggregatedMetrics>> {
    try {
      const todayStr = format(new Date(), 'yyyy-MM-dd');
      const nowIso = format(new Date(), "yyyy-MM-dd'T'HH:mm:ss");

      const [customersResult, ticketsResult, invoicesResult, revenueResult, expensesResult] =
        await Promise.all([
          this.crm.getAll('customers'),
          this.crm.getAll('tickets'),
          this.finance.getInvoices(),
          this.finance.getRevenue({ from: todayStr, to: todayStr }),
          this.finance.getExpenses({ from: todayStr, to: todayStr }),
        ]);

      if (!customersResult.ok) return err(customersResult.error);
      if (!ticketsResult.ok) return err(ticketsResult.error);
      if (!invoicesResult.ok) return err(invoicesResult.error);
      if (!revenueResult.ok) return err(revenueResult.error);
      if (!expensesResult.ok) return err(expensesResult.error);

      const customers = customersResult.value;
      const tickets = ticketsResult.value;
      const invoices = invoicesResult.value;

      const activeCustomers = customers.filter((c) => c.status === 'active');
      const mrr = activeCustomers.reduce((s, c) => s + c.mrr, 0);

      const openTickets = tickets.filter(
        (t) => t.status === 'open' || t.status === 'in_progress',
      );
      const criticalTickets = openTickets.filter((t) => t.priority === 'critical');

      const slaAtRisk = openTickets.filter(
        (t) => t.priority === 'critical' && t.slaDeadline && t.slaDeadline <= nowIso,
      );

      const overdueInvoices = invoices.filter(
        (inv) =>
          inv.status === 'overdue' || (inv.status === 'sent' && inv.dueDate < todayStr),
      );
      const overdueAmount = overdueInvoices.reduce((s, inv) => s + inv.total, 0);

      const todayRevenue = revenueResult.value.reduce((s, r) => s + r.amount, 0);
      const todayExpenses = expensesResult.value.reduce((s, e) => s + e.amount, 0);

      // Build recent activity from tickets and invoices (last 10 events)
      const activity: Array<{ action: string; timestamp: string; source: string }> = [];

      const recentTickets = tickets
        .filter((t) => t.resolvedAt)
        .sort((a, b) => (b.resolvedAt! > a.resolvedAt! ? 1 : -1))
        .slice(0, 5);

      for (const t of recentTickets) {
        activity.push({
          action: `Ticket resolved: ${t.subject}`,
          timestamp: t.resolvedAt!,
          source: 'crm',
        });
      }

      const recentInvoices = invoices
        .filter((inv) => inv.status === 'paid' && inv.paidAt)
        .sort((a, b) => (b.paidAt! > a.paidAt! ? 1 : -1))
        .slice(0, 5);

      for (const inv of recentInvoices) {
        activity.push({
          action: `Invoice paid: ${inv.number} — $${inv.total.toFixed(2)}`,
          timestamp: inv.paidAt!,
          source: 'finance',
        });
      }

      activity.sort((a, b) => (b.timestamp > a.timestamp ? 1 : -1));

      return ok({
        mrr: Math.round(mrr * 100) / 100,
        totalCustomers: customers.length,
        activeCustomers: activeCustomers.length,
        openTickets: openTickets.length,
        criticalTickets: criticalTickets.length,
        todayRevenue: Math.round(todayRevenue * 100) / 100,
        todayExpenses: Math.round(todayExpenses * 100) / 100,
        overdueInvoices: overdueInvoices.length,
        overdueAmount: Math.round(overdueAmount * 100) / 100,
        slaAtRisk: slaAtRisk.length,
        recentActivity: activity.slice(0, 10),
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getQuickStats(): Promise<Result<AndonBoard['quickStats']>> {
    const result = await this.collectAll();
    if (!result.ok) return err(result.error);
    const m = result.value;

    // Next deadline: earliest overdue invoice due date
    const invoicesResult = await this.finance.getInvoices();
    let nextDeadline = 'None';
    if (invoicesResult.ok) {
      const overdue = invoicesResult.value
        .filter((inv) => inv.status === 'sent' || inv.status === 'overdue')
        .sort((a, b) => (a.dueDate < b.dueDate ? -1 : 1));
      if (overdue.length > 0) {
        nextDeadline = `${overdue[0]!.number} due ${overdue[0]!.dueDate}`;
      }
    }

    return ok({
      mrr: `$${m.mrr.toFixed(2)}`,
      customers: String(m.activeCustomers),
      openTickets: String(m.openTickets),
      todayRevenue: `$${m.todayRevenue.toFixed(2)}`,
      todayExpenses: `$${m.todayExpenses.toFixed(2)}`,
      agentBudgetUsed: '$0.00',
      nextDeadline,
    });
  }

  determineStatus(metrics: AggregatedMetrics): AndonBoard['status'] {
    const hasCritical =
      metrics.criticalTickets > 0 || metrics.slaAtRisk > 0 || metrics.overdueInvoices > 2;
    const hasWarning =
      metrics.openTickets > 10 || metrics.overdueInvoices > 0 || metrics.slaAtRisk > 0;

    if (hasCritical) return 'red';
    if (hasWarning) return 'yellow';
    return 'green';
  }

  buildAlerts(metrics: AggregatedMetrics): AndonBoard['alerts'] {
    const alerts: AndonBoard['alerts'] = [];
    const now = new Date().toISOString();

    if (metrics.slaAtRisk > 0) {
      alerts.push({
        level: 'critical',
        message: `${metrics.slaAtRisk} ticket(s) SLA breached`,
        source: 'crm',
        timestamp: now,
      });
    }
    if (metrics.criticalTickets > 0) {
      alerts.push({
        level: 'critical',
        message: `${metrics.criticalTickets} critical ticket(s) open`,
        source: 'crm',
        timestamp: now,
      });
    }
    if (metrics.overdueInvoices > 0) {
      alerts.push({
        level: metrics.overdueInvoices > 2 ? 'critical' : 'warning',
        message: `${metrics.overdueInvoices} overdue invoice(s) — $${metrics.overdueAmount.toFixed(2)} outstanding`,
        source: 'finance',
        timestamp: now,
      });
    }
    if (metrics.openTickets > 10) {
      alerts.push({
        level: 'warning',
        message: `High ticket volume: ${metrics.openTickets} open`,
        source: 'crm',
        timestamp: now,
      });
    }

    return alerts;
  }
}
