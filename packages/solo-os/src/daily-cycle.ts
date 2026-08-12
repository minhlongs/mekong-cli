import type { DepartmentTask } from './company-brain.js';
import type { DepartmentAgent, AgentResult } from './department-agents.js';

export interface MorningBrief {
  priorities: string[];
  assignments: Record<string, string>;
}

export interface WorkdayResult {
  dept: string;
  completed: number;
  failed: number;
}

export interface EveningReport {
  summary: string;
  tomorrow: string[];
  blockers: string[];
}

export interface WeeklyOKR {
  objectives: string[];
  keyResults: string[];
  score: number;
}

type Phase = 'morning' | 'workday' | 'evening' | 'weekend';

function getPhaseByHour(hour: number): Phase {
  if (hour >= 6 && hour < 10) return 'morning';
  if (hour >= 10 && hour < 18) return 'workday';
  if (hour >= 18 && hour < 22) return 'evening';
  return 'weekend';
}

export class DailyCycle {
  private agents: Map<string, DepartmentAgent>;
  private completedToday: WorkdayResult[] = [];
  private weekResults: WorkdayResult[][] = [];

  constructor(agents: DepartmentAgent[]) {
    this.agents = new Map(agents.map((a) => [a.name, a]));
  }

  getCurrentPhase(): Phase {
    const hour = new Date().getHours();
    return getPhaseByHour(hour);
  }

  runMorning(): MorningBrief {
    this.completedToday = [];
    const priorities: string[] = [];
    const assignments: Record<string, string> = {};

    for (const [name, agent] of this.agents) {
      const kpis = agent.getKPIs();
      const reds = kpis.filter((k) => k.status === 'red');
      if (reds.length > 0) {
        priorities.push(`${name}: fix ${reds.map((k) => k.name).join(', ')}`);
      }
      assignments[name] = agent.taskQueue[0] ?? `Continue ${name} operations`;
    }

    return { priorities, assignments };
  }

  runWorkday(tasks: DepartmentTask[]): WorkdayResult[] {
    const resultMap = new Map<string, WorkdayResult>();

    for (const task of tasks) {
      const agent = this.agents.get(task.department);
      if (!agent) continue;

      let entry = resultMap.get(task.department);
      if (!entry) {
        entry = { dept: task.department, completed: 0, failed: 0 };
        resultMap.set(task.department, entry);
      }

      const result: AgentResult = agent.execute(task.task);
      if (result.success) {
        entry.completed++;
      } else {
        entry.failed++;
      }
    }

    this.completedToday = Array.from(resultMap.values());
    return this.completedToday;
  }

  runEvening(): EveningReport {
    const totalCompleted = this.completedToday.reduce((s, r) => s + r.completed, 0);
    const totalFailed = this.completedToday.reduce((s, r) => s + r.failed, 0);
    const blockers = this.completedToday
      .filter((r) => r.failed > 0)
      .map((r) => `${r.dept}: ${r.failed} task(s) failed`);

    const tomorrow = Array.from(this.agents.keys()).map(
      (name) => `${name}: resume pending queue`,
    );

    const summary =
      `Completed ${totalCompleted} tasks across ${this.completedToday.length} departments. ` +
      `Failed: ${totalFailed}. Blockers: ${blockers.length}.`;

    this.weekResults.push([...this.completedToday]);

    return { summary, tomorrow, blockers };
  }

  runWeeklyReview(): WeeklyOKR {
    const allResults = this.weekResults.flat();
    const totalDone = allResults.reduce((s, r) => s + r.completed, 0);
    const totalFailed = allResults.reduce((s, r) => s + r.failed, 0);
    const total = totalDone + totalFailed;
    const score = total > 0 ? Math.round((totalDone / total) * 100) : 0;

    const objectives = [
      'Grow MRR by 20% MoM',
      'Ship 2 major features',
      'Achieve NPS > 50',
      'Reduce churn < 3%',
    ];

    const keyResults = Array.from(this.agents.values()).flatMap((a) =>
      a.getKPIs()
        .filter((k) => k.status !== 'green')
        .map((k) => `${a.name}/${k.name}: ${k.value}/${k.target}`),
    );

    this.weekResults = [];
    return { objectives, keyResults, score };
  }
}
