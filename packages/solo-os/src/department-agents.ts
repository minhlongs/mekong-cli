export interface AgentResult {
  success: boolean;
  output: string;
  duration: number;
}

export interface KPI {
  name: string;
  value: number;
  target: number;
  status: 'green' | 'yellow' | 'red';
}

function kpiStatus(value: number, target: number, higherIsBetter = true): KPI['status'] {
  const ratio = higherIsBetter ? value / target : target / value;
  if (ratio >= 1) return 'green';
  if (ratio >= 0.7) return 'yellow';
  return 'red';
}

export abstract class DepartmentAgent {
  abstract name: string;
  abstract kpis: KPI[];
  taskQueue: string[] = [];

  abstract execute(task: string): AgentResult;
  abstract getKPIs(): KPI[];

  getStatus(): string {
    return this.taskQueue.length > 0 ? 'working' : 'idle';
  }

  protected timed(fn: () => string): AgentResult {
    const start = Date.now();
    try {
      const output = fn();
      return { success: true, output, duration: Date.now() - start };
    } catch (err) {
      return { success: false, output: String(err), duration: Date.now() - start };
    }
  }
}

export class ProductAgent extends DepartmentAgent {
  name = 'product';
  private roadmap: string[] = [];
  kpis: KPI[] = [
    { name: 'features_shipped', value: 0, target: 10, status: 'red' },
    { name: 'ice_backlog_size', value: 0, target: 20, status: 'red' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.roadmap.push(task);
      const iceScore = Math.floor(Math.random() * 100);
      this.kpis[0].value++;
      this.kpis[1].value = this.roadmap.length;
      return `[Product] ICE(${iceScore}) scored and added to roadmap: ${task}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].status = kpiStatus(this.kpis[0].value, this.kpis[0].target);
    this.kpis[1].status = kpiStatus(this.kpis[1].value, this.kpis[1].target);
    return this.kpis;
  }
}

export class EngineeringAgent extends DepartmentAgent {
  name = 'engineering';
  private deployCount = 0;
  private techDebt = 5;
  kpis: KPI[] = [
    { name: 'deploys_per_week', value: 0, target: 5, status: 'red' },
    { name: 'tech_debt_items', value: 5, target: 3, status: 'red' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.deployCount++;
      this.techDebt = Math.max(0, this.techDebt - 1);
      return `[Engineering] Deployed: ${task} (deploy #${this.deployCount}, debt: ${this.techDebt})`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.deployCount;
    this.kpis[1].value = this.techDebt;
    this.kpis[0].status = kpiStatus(this.deployCount, 5);
    this.kpis[1].status = kpiStatus(this.techDebt, 3, false);
    return this.kpis;
  }
}

export class SalesAgent extends DepartmentAgent {
  name = 'sales';
  private pipeline: string[] = [];
  private closed = 0;
  kpis: KPI[] = [
    { name: 'pipeline_size', value: 0, target: 10, status: 'red' },
    { name: 'closed_deals', value: 0, target: 5, status: 'red' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.pipeline.push(task);
      const closed = Math.random() > 0.5;
      if (closed) this.closed++;
      return `[Sales] Lead qualified. Closed: ${closed}. Pipeline: ${this.pipeline.length}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.pipeline.length;
    this.kpis[1].value = this.closed;
    this.kpis[0].status = kpiStatus(this.pipeline.length, 10);
    this.kpis[1].status = kpiStatus(this.closed, 5);
    return this.kpis;
  }
}

export class MarketingAgent extends DepartmentAgent {
  name = 'marketing';
  private contentCount = 0;
  kpis: KPI[] = [
    { name: 'content_pieces', value: 0, target: 12, status: 'red' },
    { name: 'campaigns_live', value: 0, target: 3, status: 'red' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.contentCount++;
      return `[Marketing] Published content #${this.contentCount}: ${task.slice(0, 60)}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.contentCount;
    this.kpis[1].value = Math.floor(this.contentCount / 4);
    this.kpis[0].status = kpiStatus(this.contentCount, 12);
    this.kpis[1].status = kpiStatus(Math.floor(this.contentCount / 4), 3);
    return this.kpis;
  }
}

export class FinanceAgent extends DepartmentAgent {
  name = 'finance';
  private mrr = 0;
  kpis: KPI[] = [
    { name: 'mrr_usd', value: 0, target: 10000, status: 'red' },
    { name: 'runway_months', value: 12, target: 12, status: 'green' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.mrr += 500;
      return `[Finance] Bookkeeping updated. MRR: $${this.mrr}. Task: ${task.slice(0, 50)}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.mrr;
    this.kpis[0].status = kpiStatus(this.mrr, 10000);
    return this.kpis;
  }
}

export class LegalAgent extends DepartmentAgent {
  name = 'legal';
  private reviewCount = 0;
  kpis: KPI[] = [
    { name: 'contracts_reviewed', value: 0, target: 5, status: 'red' },
    { name: 'compliance_score', value: 80, target: 90, status: 'yellow' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.reviewCount++;
      return `[Legal] Contract reviewed #${this.reviewCount}: ${task.slice(0, 60)}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.reviewCount;
    this.kpis[0].status = kpiStatus(this.reviewCount, 5);
    return this.kpis;
  }
}

export class HRAgent extends DepartmentAgent {
  name = 'hr';
  private agentCount = 0;
  kpis: KPI[] = [
    { name: 'agents_active', value: 0, target: 8, status: 'red' },
    { name: 'performance_reviews', value: 0, target: 4, status: 'red' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.agentCount++;
      return `[HR] Agent assigned #${this.agentCount} for: ${task.slice(0, 60)}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.agentCount;
    this.kpis[0].status = kpiStatus(this.agentCount, 8);
    return this.kpis;
  }
}

export class SupportAgent extends DepartmentAgent {
  name = 'support';
  private ticketsClosed = 0;
  kpis: KPI[] = [
    { name: 'tickets_closed', value: 0, target: 20, status: 'red' },
    { name: 'nps_score', value: 40, target: 50, status: 'yellow' },
  ];

  execute(task: string): AgentResult {
    return this.timed(() => {
      this.ticketsClosed++;
      return `[Support] FAQ updated. Tickets closed: ${this.ticketsClosed}. Task: ${task.slice(0, 50)}`;
    });
  }

  getKPIs(): KPI[] {
    this.kpis[0].value = this.ticketsClosed;
    this.kpis[0].status = kpiStatus(this.ticketsClosed, 20);
    return this.kpis;
  }
}
