import type { CrmSummary } from '../crm/types.js';
import type { FinancialSummary } from '../finance/types.js';

/** Daily Standup Report — auto-generated every morning */
export interface DailyStandup {
  date: string;
  yesterday: {
    tasksCompleted: string[];
    sopRunsCompleted: number;
    codeCommits: number;
    ticketsResolved: number;
    invoicesSent: number;
    revenue: number;
  };
  today: {
    scheduledTasks: string[];
    followUps: Array<{ contact: string; reason: string; priority: string }>;
    deadlines: Array<{ item: string; dueDate: string }>;
    sopScheduled: string[];
  };
  blockers: string[];
  metrics: {
    mrrCurrent: number;
    mrrTarget: number;
    openTickets: number;
    overdueInvoices: number;
    budgetUsedToday: number;
  };
}

/** Weekly Business Digest */
export interface WeeklyDigest {
  week: string;                                     // YYYY-Www
  period: { from: string; to: string };
  financial: FinancialSummary;
  crm: CrmSummary;
  operations: {
    sopRunsTotal: number;
    sopSuccessRate: number;
    avgSopDuration: number;
    topSOPs: Array<{ name: string; runs: number; avgTime: number }>;
    agentTokensUsed: number;
    agentCostTotal: number;
  };
  highlights: string[];                            // AI-generated key insights
  recommendations: string[];                       // AI-generated suggestions
  comparison: {
    revenueVsLastWeek: number;                     // percent change
    expensesVsLastWeek: number;
    customersVsLastWeek: number;
    ticketsVsLastWeek: number;
  };
}

/** Dashboard view for CLI — the Andon Board */
export interface AndonBoard {
  status: 'green' | 'yellow' | 'red';             // overall health
  alerts: Array<{
    level: 'info' | 'warning' | 'critical';
    message: string;
    source: string;
    timestamp: string;
  }>;
  quickStats: {
    mrr: string;
    customers: string;
    openTickets: string;
    todayRevenue: string;
    todayExpenses: string;
    agentBudgetUsed: string;
    nextDeadline: string;
  };
  recentActivity: Array<{
    action: string;
    timestamp: string;
    source: string;
  }>;
}
