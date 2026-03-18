export type Department =
  | 'product'
  | 'engineering'
  | 'sales'
  | 'marketing'
  | 'finance'
  | 'legal'
  | 'hr'
  | 'support';

export const DEPARTMENTS: Department[] = [
  'product', 'engineering', 'sales', 'marketing',
  'finance', 'legal', 'hr', 'support',
];

export interface DepartmentTask {
  department: Department;
  task: string;
  priority: 'high' | 'medium' | 'low';
  deadline?: string;
}

export interface StandupReport {
  date: string;
  departments: Record<Department, string>;
  blockers: string[];
  highlights: string[];
}

export interface CompanyHealth {
  score: number;
  departments: Record<string, number>;
}

interface DepartmentState {
  status: string;
  health: number;
  tasks: DepartmentTask[];
}

const TASK_TEMPLATES: Record<Department, (goal: string) => string> = {
  product:     (g) => `Define features and roadmap for: ${g}`,
  engineering: (g) => `Build and ship technical solution for: ${g}`,
  sales:       (g) => `Identify and close customers for: ${g}`,
  marketing:   (g) => `Create awareness and demand for: ${g}`,
  finance:     (g) => `Model unit economics and budget for: ${g}`,
  legal:       (g) => `Review contracts and compliance for: ${g}`,
  hr:          (g) => `Hire or assign agents to execute: ${g}`,
  support:     (g) => `Prepare FAQ and onboarding docs for: ${g}`,
};

const PRIORITY_MAP: Record<Department, 'high' | 'medium' | 'low'> = {
  product:     'high',
  engineering: 'high',
  sales:       'high',
  marketing:   'medium',
  finance:     'medium',
  legal:       'medium',
  hr:          'low',
  support:     'low',
};

export class CompanyBrain {
  private goal = '';
  private state: Record<Department, DepartmentState>;

  constructor() {
    this.state = Object.fromEntries(
      DEPARTMENTS.map((d) => [d, { status: 'idle', health: 75, tasks: [] }]),
    ) as unknown as Record<Department, DepartmentState>;
  }

  setGoal(goal: string): void {
    this.goal = goal;
    const tasks = this.decompose(goal);
    for (const t of tasks) {
      this.state[t.department].tasks.push(t);
      this.state[t.department].status = 'working';
    }
  }

  decompose(goal: string): DepartmentTask[] {
    const deadline = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0];

    return DEPARTMENTS.map((dept) => ({
      department: dept,
      task: TASK_TEMPLATES[dept](goal),
      priority: PRIORITY_MAP[dept],
      deadline,
    }));
  }

  updateDepartmentStatus(dept: Department, status: string, health: number): void {
    this.state[dept].status = status;
    this.state[dept].health = Math.max(0, Math.min(100, health));
  }

  synthesizeStandup(): StandupReport {
    const departments = Object.fromEntries(
      DEPARTMENTS.map((d) => [d, this.state[d].status]),
    ) as Record<Department, string>;

    const blockers = DEPARTMENTS
      .filter((d) => this.state[d].health < 50)
      .map((d) => `${d}: health at ${this.state[d].health}%`);

    const highlights = DEPARTMENTS
      .filter((d) => this.state[d].health >= 85)
      .map((d) => `${d}: performing well (${this.state[d].health}%)`);

    return {
      date: new Date().toISOString().split('T')[0],
      departments,
      blockers,
      highlights,
    };
  }

  getCompanyHealth(): CompanyHealth {
    const deptScores = Object.fromEntries(
      DEPARTMENTS.map((d) => [d, this.state[d].health]),
    );
    const score = Math.round(
      DEPARTMENTS.reduce((sum, d) => sum + this.state[d].health, 0) / DEPARTMENTS.length,
    );
    return { score, departments: deptScores };
  }

  getGoal(): string {
    return this.goal;
  }
}
