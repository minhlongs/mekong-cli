import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DailyStandupGenerator } from '../../src/dashboard/daily-standup.js';
import { MetricsAggregator } from '../../src/dashboard/metrics-aggregator.js';
import { DashboardRenderer } from '../../src/dashboard/renderer.js';
import type { CrmStore } from '../../src/crm/store.js';
import type { FinanceStore } from '../../src/finance/store.js';
import { ok } from '../../src/types/common.js';

// ── Minimal stubs ──────────────────────────────────────────────────────────

function makeCrm(overrides: Partial<CrmStore> = {}): CrmStore {
  return {
    getAll: vi.fn().mockResolvedValue(ok([])),
    getById: vi.fn().mockResolvedValue(ok(null)),
    save: vi.fn(),
    delete: vi.fn(),
    deleteAll: vi.fn(),
    ...overrides,
  } as unknown as CrmStore;
}

function makeFinance(overrides: Partial<FinanceStore> = {}): FinanceStore {
  return {
    getAll: vi.fn().mockResolvedValue(ok([])),
    getById: vi.fn().mockResolvedValue(ok(null)),
    save: vi.fn(),
    delete: vi.fn(),
    getInvoices: vi.fn().mockResolvedValue(ok([])),
    getExpenses: vi.fn().mockResolvedValue(ok([])),
    getRevenue: vi.fn().mockResolvedValue(ok([])),
    nextInvoiceNumber: vi.fn(),
    ...overrides,
  } as unknown as FinanceStore;
}

// ── DailyStandupGenerator ──────────────────────────────────────────────────

describe('DailyStandupGenerator', () => {
  it('generate() returns ok with empty data', async () => {
    const gen = new DailyStandupGenerator(makeCrm(), makeFinance(), '/nonexistent/sop.json');
    const result = await gen.generate();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(result.value.blockers).toBeInstanceOf(Array);
    expect(result.value.yesterday.ticketsResolved).toBe(0);
  });

  it('generate() counts overdue invoices as blockers', async () => {
    const today = new Date().toISOString().slice(0, 10);
    const past = '2020-01-01';
    const finance = makeFinance({
      getInvoices: vi.fn().mockResolvedValue(
        ok([
          {
            id: 'inv1', number: 'INV-2020-001', customerId: 'c1',
            customerName: 'Acme', customerEmail: 'a@b.com',
            items: [], subtotal: 100, tax: 0, taxRate: 0, total: 100,
            currency: 'USD', status: 'overdue', dueDate: past,
            createdAt: past + 'T00:00:00', updatedAt: past + 'T00:00:00',
          },
        ]),
      ),
    });
    const gen = new DailyStandupGenerator(makeCrm(), finance, '/nonexistent/sop.json');
    const result = await gen.generate();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.blockers.length).toBeGreaterThan(0);
    expect(result.value.metrics.overdueInvoices).toBe(1);
  });

  it('renderCli() returns non-empty string with sections', async () => {
    const gen = new DailyStandupGenerator(makeCrm(), makeFinance(), '/nonexistent/sop.json');
    const result = await gen.generate();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const output = gen.renderCli(result.value);
    expect(output).toContain('DAILY STANDUP');
    expect(output).toContain('YESTERDAY');
    expect(output).toContain('TODAY');
    expect(output).toContain('BLOCKERS');
    expect(output).toContain('METRICS');
  });
});

// ── MetricsAggregator ──────────────────────────────────────────────────────

describe('MetricsAggregator', () => {
  let agg: MetricsAggregator;

  beforeEach(() => {
    agg = new MetricsAggregator(makeCrm(), makeFinance());
  });

  it('collectAll() returns ok with empty stores', async () => {
    const result = await agg.collectAll();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.mrr).toBe(0);
    expect(result.value.openTickets).toBe(0);
    expect(result.value.overdueInvoices).toBe(0);
  });

  it('determineStatus() returns green with no issues', () => {
    const metrics = {
      mrr: 1000, totalCustomers: 5, activeCustomers: 5,
      openTickets: 0, criticalTickets: 0, todayRevenue: 100,
      todayExpenses: 50, overdueInvoices: 0, overdueAmount: 0,
      slaAtRisk: 0, recentActivity: [],
    };
    expect(agg.determineStatus(metrics)).toBe('green');
  });

  it('determineStatus() returns yellow with open tickets > 10', () => {
    const metrics = {
      mrr: 0, totalCustomers: 0, activeCustomers: 0,
      openTickets: 11, criticalTickets: 0, todayRevenue: 0,
      todayExpenses: 0, overdueInvoices: 0, overdueAmount: 0,
      slaAtRisk: 0, recentActivity: [],
    };
    expect(agg.determineStatus(metrics)).toBe('yellow');
  });

  it('determineStatus() returns red with SLA breach', () => {
    const metrics = {
      mrr: 0, totalCustomers: 0, activeCustomers: 0,
      openTickets: 1, criticalTickets: 1, todayRevenue: 0,
      todayExpenses: 0, overdueInvoices: 0, overdueAmount: 0,
      slaAtRisk: 1, recentActivity: [],
    };
    expect(agg.determineStatus(metrics)).toBe('red');
  });

  it('buildAlerts() produces critical alert for SLA breach', () => {
    const metrics = {
      mrr: 0, totalCustomers: 0, activeCustomers: 0,
      openTickets: 1, criticalTickets: 0, todayRevenue: 0,
      todayExpenses: 0, overdueInvoices: 0, overdueAmount: 0,
      slaAtRisk: 2, recentActivity: [],
    };
    const alerts = agg.buildAlerts(metrics);
    expect(alerts.some((a) => a.level === 'critical')).toBe(true);
  });

  it('getQuickStats() returns formatted strings', async () => {
    const result = await agg.getQuickStats();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.mrr).toMatch(/^\$/);
    expect(result.value.todayRevenue).toMatch(/^\$/);
  });
});

// ── DashboardRenderer ──────────────────────────────────────────────────────

describe('DashboardRenderer', () => {
  it('render() includes board structure', () => {
    const agg = new MetricsAggregator(makeCrm(), makeFinance());
    const renderer = new DashboardRenderer(agg);
    const board = {
      status: 'green' as const,
      alerts: [],
      quickStats: {
        mrr: '$1,000', customers: '5', openTickets: '2',
        todayRevenue: '$200', todayExpenses: '$50',
        agentBudgetUsed: '$0', nextDeadline: 'None',
      },
      recentActivity: [],
    };
    const output = renderer.render(board);
    expect(output).toContain('ANDON BOARD');
    expect(output).toContain('QUICK STATS');
    expect(output).toContain('ALERTS');
    expect(output).toContain('RECENT ACTIVITY');
    expect(output).toContain('No active alerts');
  });

  it('render() shows critical alert in red board', () => {
    const agg = new MetricsAggregator(makeCrm(), makeFinance());
    const renderer = new DashboardRenderer(agg);
    const board = {
      status: 'red' as const,
      alerts: [
        { level: 'critical' as const, message: 'SLA breached', source: 'crm', timestamp: new Date().toISOString() },
      ],
      quickStats: {
        mrr: '$0', customers: '0', openTickets: '1',
        todayRevenue: '$0', todayExpenses: '$0',
        agentBudgetUsed: '$0', nextDeadline: 'None',
      },
      recentActivity: [],
    };
    const output = renderer.render(board);
    expect(output).toContain('SLA breached');
    expect(output).toContain('CRITICAL');
  });

  it('buildBoard() returns ok result', async () => {
    const agg = new MetricsAggregator(makeCrm(), makeFinance());
    const renderer = new DashboardRenderer(agg);
    const result = await renderer.buildBoard();
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(['green', 'yellow', 'red']).toContain(result.value.status);
  });
});
