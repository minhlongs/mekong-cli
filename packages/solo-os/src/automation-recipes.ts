export interface Recipe {
  name: string;
  slaHours: number;
  steps: string[];
  trigger: string;
}

export interface RecipeResult {
  success: boolean;
  stepsCompleted: number;
  duration: number;
}

export interface RecipeStatus {
  name: string;
  executionCount: number;
  avgDuration: number;
  successRate: number;
}

interface ExecutionRecord {
  success: boolean;
  duration: number;
  stepsCompleted: number;
}

const BUILT_IN_RECIPES: Recipe[] = [
  {
    name: 'new-customer-onboard',
    slaHours: 24,
    trigger: 'payment.success',
    steps: ['send welcome email', 'provision account', 'schedule onboarding call', 'send training docs'],
  },
  {
    name: 'bug-fix-deploy',
    slaHours: 2,
    trigger: 'issue.critical',
    steps: ['triage bug report', 'implement fix', 'run test suite', 'deploy to production'],
  },
  {
    name: 'lead-to-payment',
    slaHours: 48,
    trigger: 'lead.created',
    steps: ['qualify lead', 'schedule product demo', 'send proposal', 'close deal'],
  },
  {
    name: 'monthly-close',
    slaHours: 24,
    trigger: 'schedule.month-end',
    steps: ['reconcile transactions', 'generate financial report', 'review with stakeholders', 'submit to accounting'],
  },
];

export class RecipeEngine {
  private recipes: Map<string, Recipe> = new Map();
  private history: Map<string, ExecutionRecord[]> = new Map();

  constructor() {
    for (const r of BUILT_IN_RECIPES) {
      this.recipes.set(r.name, r);
    }
  }

  addRecipe(recipe: Recipe): void {
    this.recipes.set(recipe.name, recipe);
  }

  listRecipes(): Recipe[] {
    return Array.from(this.recipes.values());
  }

  executeRecipe(name: string, context: Record<string, unknown>): RecipeResult {
    const recipe = this.recipes.get(name);
    if (!recipe) {
      return { success: false, stepsCompleted: 0, duration: 0 };
    }

    const start = Date.now();
    let stepsCompleted = 0;

    for (const step of recipe.steps) {
      try {
        // Simulate step execution with context awareness
        const _ = { step, context };
        void _;
        stepsCompleted++;
      } catch {
        const duration = Date.now() - start;
        const record: ExecutionRecord = { success: false, duration, stepsCompleted };
        this.recordHistory(name, record);
        return { success: false, stepsCompleted, duration };
      }
    }

    const duration = Date.now() - start;
    const record: ExecutionRecord = { success: true, duration, stepsCompleted };
    this.recordHistory(name, record);

    return { success: true, stepsCompleted, duration };
  }

  getRecipeStatus(name: string): RecipeStatus {
    const records = this.history.get(name) ?? [];
    const execCount = records.length;

    if (execCount === 0) {
      return { name, executionCount: 0, avgDuration: 0, successRate: 0 };
    }

    const avgDuration = records.reduce((s, r) => s + r.duration, 0) / execCount;
    const successRate = records.filter((r) => r.success).length / execCount;

    return { name, executionCount: execCount, avgDuration, successRate };
  }

  private recordHistory(name: string, record: ExecutionRecord): void {
    const records = this.history.get(name) ?? [];
    records.push(record);
    if (records.length > 100) records.shift();
    this.history.set(name, records);
  }
}
