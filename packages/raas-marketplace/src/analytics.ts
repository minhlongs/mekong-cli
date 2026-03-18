export type SalesEventType = "visit" | "signup" | "trial" | "purchase" | "churn";

export interface SalesEvent {
  type: SalesEventType;
  tenantId: string;
  amount: number; // USD/mo, 0 for non-purchase events
  timestamp: Date;
}

export interface FunnelStep {
  stage: SalesEventType;
  count: number;
  conversionRate: number; // percentage vs previous stage
}

export class SalesAnalytics {
  private events: SalesEvent[] = [];

  recordEvent(event: SalesEvent): void {
    this.events.push({ ...event });
  }

  getConversionFunnel(): FunnelStep[] {
    const stages: SalesEventType[] = ["visit", "signup", "trial", "purchase"];
    const counts = stages.map((stage) => ({
      stage,
      count: this.events.filter((e) => e.type === stage).length,
    }));

    return counts.map((item, i) => {
      const prevCount = i === 0 ? item.count : counts[i - 1].count;
      const conversionRate =
        prevCount === 0 ? 0 : Math.round((item.count / prevCount) * 10000) / 100;
      return { ...item, conversionRate };
    });
  }

  getMRR(): number {
    const activeCustomers = new Map<string, number>();

    for (const e of this.events) {
      if (e.type === "purchase") {
        activeCustomers.set(e.tenantId, e.amount);
      }
      if (e.type === "churn") {
        activeCustomers.delete(e.tenantId);
      }
    }

    const total = Array.from(activeCustomers.values()).reduce((s, v) => s + v, 0);
    return Math.round(total * 100) / 100;
  }

  getChurnRate(): number {
    const purchases = new Set(
      this.events.filter((e) => e.type === "purchase").map((e) => e.tenantId)
    );
    const churns = new Set(
      this.events.filter((e) => e.type === "churn").map((e) => e.tenantId)
    );
    if (purchases.size === 0) return 0;
    return Math.round((churns.size / purchases.size) * 10000) / 100;
  }

  getLTV(): number {
    const mrr = this.getMRR();
    const churnRate = this.getChurnRate();
    // LTV = MRR / churnRate (as fraction); if no churn, assume 24mo
    if (churnRate === 0) return Math.round(mrr * 24 * 100) / 100;
    return Math.round((mrr / (churnRate / 100)) * 100) / 100;
  }

  generateWeeklySalesReport(): string {
    const funnel = this.getConversionFunnel();
    const mrr = this.getMRR();
    const churn = this.getChurnRate();
    const ltv = this.getLTV();
    const totalEvents = this.events.length;

    const funnelRows = funnel
      .map((s) => `| ${s.stage} | ${s.count} | ${s.conversionRate}% |`)
      .join("\n");

    return `# Weekly Sales Report
Generated: ${new Date().toISOString().split("T")[0]}

## Key Metrics
| Metric | Value |
|--------|-------|
| MRR | $${mrr} |
| Churn Rate | ${churn}% |
| LTV | $${ltv} |
| Total Events | ${totalEvents} |

## Conversion Funnel
| Stage | Count | Conversion |
|-------|-------|-----------|
${funnelRows}

## Summary
${mrr > 0 ? `Monthly Recurring Revenue is $${mrr}.` : "No active subscribers yet."}
${churn > 10 ? "Churn is above 10% — investigate retention issues." : "Churn is within healthy range."}
`;
  }
}
