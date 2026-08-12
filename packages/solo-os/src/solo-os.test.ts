import { describe, it, expect, beforeEach } from 'vitest';
import { CompanyBrain, DEPARTMENTS } from './company-brain.js';
import {
  ProductAgent, EngineeringAgent, SalesAgent, MarketingAgent,
  FinanceAgent, LegalAgent, HRAgent, SupportAgent,
} from './department-agents.js';
import { DailyCycle } from './daily-cycle.js';
import { KPIDashboard } from './kpi-dashboard.js';
import { RecipeEngine } from './automation-recipes.js';

// ── CompanyBrain ─────────────────────────────────────────────────────────────

describe('CompanyBrain', () => {
  let brain: CompanyBrain;

  beforeEach(() => { brain = new CompanyBrain(); });

  it('starts with empty goal', () => {
    expect(brain.getGoal()).toBe('');
  });

  it('setGoal stores goal', () => {
    brain.setGoal('Launch SaaS MVP');
    expect(brain.getGoal()).toBe('Launch SaaS MVP');
  });

  it('decompose returns 8 tasks, one per department', () => {
    const tasks = brain.decompose('Build product');
    expect(tasks).toHaveLength(8);
    const depts = tasks.map((t) => t.department);
    for (const d of DEPARTMENTS) expect(depts).toContain(d);
  });

  it('each decomposed task has priority and deadline', () => {
    const tasks = brain.decompose('Grow revenue');
    for (const t of tasks) {
      expect(['high', 'medium', 'low']).toContain(t.priority);
      expect(t.deadline).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('synthesizeStandup returns today date', () => {
    brain.setGoal('Test goal');
    const report = brain.synthesizeStandup();
    expect(report.date).toBe(new Date().toISOString().split('T')[0]);
    expect(report.departments).toHaveProperty('product');
  });

  it('getCompanyHealth score 0-100', () => {
    const health = brain.getCompanyHealth();
    expect(health.score).toBeGreaterThanOrEqual(0);
    expect(health.score).toBeLessThanOrEqual(100);
    expect(Object.keys(health.departments)).toHaveLength(8);
  });

  it('updateDepartmentStatus clamps health', () => {
    brain.updateDepartmentStatus('engineering', 'blocked', 150);
    const health = brain.getCompanyHealth();
    expect(health.departments['engineering']).toBe(100);

    brain.updateDepartmentStatus('engineering', 'blocked', -10);
    const health2 = brain.getCompanyHealth();
    expect(health2.departments['engineering']).toBe(0);
  });

  it('standup blockers lists low-health depts', () => {
    brain.updateDepartmentStatus('sales', 'blocked', 30);
    const report = brain.synthesizeStandup();
    expect(report.blockers.some((b) => b.includes('sales'))).toBe(true);
  });
});

// ── DepartmentAgents ─────────────────────────────────────────────────────────

describe('DepartmentAgents', () => {
  it('ProductAgent execute returns success', () => {
    const agent = new ProductAgent();
    const result = agent.execute('Build auth feature');
    expect(result.success).toBe(true);
    expect(result.output).toContain('[Product]');
    expect(result.duration).toBeGreaterThanOrEqual(0);
  });

  it('EngineeringAgent tracks deploys', () => {
    const agent = new EngineeringAgent();
    agent.execute('Deploy v1');
    agent.execute('Deploy v2');
    const kpis = agent.getKPIs();
    const deploy = kpis.find((k) => k.name === 'deploys_per_week');
    expect(deploy?.value).toBe(2);
  });

  it('SalesAgent getStatus idle with empty queue', () => {
    const agent = new SalesAgent();
    expect(agent.getStatus()).toBe('idle');
  });

  it('MarketingAgent increments content count', () => {
    const agent = new MarketingAgent();
    agent.execute('Write blog post');
    agent.execute('Tweet thread');
    const kpis = agent.getKPIs();
    const content = kpis.find((k) => k.name === 'content_pieces');
    expect(content?.value).toBe(2);
  });

  it('FinanceAgent MRR grows per execution', () => {
    const agent = new FinanceAgent();
    agent.execute('Record MRR');
    agent.execute('Record MRR');
    const kpis = agent.getKPIs();
    const mrr = kpis.find((k) => k.name === 'mrr_usd');
    expect(mrr?.value).toBe(1000);
  });

  it('all 8 agents have name and kpis', () => {
    const agents = [
      new ProductAgent(), new EngineeringAgent(), new SalesAgent(),
      new MarketingAgent(), new FinanceAgent(), new LegalAgent(),
      new HRAgent(), new SupportAgent(),
    ];
    for (const a of agents) {
      expect(typeof a.name).toBe('string');
      expect(a.getKPIs().length).toBeGreaterThan(0);
    }
  });
});

// ── DailyCycle ───────────────────────────────────────────────────────────────

describe('DailyCycle', () => {
  let cycle: DailyCycle;

  beforeEach(() => {
    cycle = new DailyCycle([
      new ProductAgent(), new EngineeringAgent(), new SalesAgent(),
      new MarketingAgent(), new FinanceAgent(), new LegalAgent(),
      new HRAgent(), new SupportAgent(),
    ]);
  });

  it('getCurrentPhase returns valid phase', () => {
    const phase = cycle.getCurrentPhase();
    expect(['morning', 'workday', 'evening', 'weekend']).toContain(phase);
  });

  it('runMorning returns assignments for all agents', () => {
    const brief = cycle.runMorning();
    expect(Object.keys(brief.assignments)).toHaveLength(8);
    expect(Array.isArray(brief.priorities)).toBe(true);
  });

  it('runWorkday dispatches tasks and returns results', () => {
    const brain = new CompanyBrain();
    const tasks = brain.decompose('Ship MVP');
    const results = cycle.runWorkday(tasks);
    expect(results.length).toBeGreaterThan(0);
    for (const r of results) {
      expect(typeof r.dept).toBe('string');
      expect(r.completed + r.failed).toBeGreaterThanOrEqual(1);
    }
  });

  it('runEvening summarizes day', () => {
    const brain = new CompanyBrain();
    cycle.runWorkday(brain.decompose('Test goal'));
    const report = cycle.runEvening();
    expect(typeof report.summary).toBe('string');
    expect(Array.isArray(report.tomorrow)).toBe(true);
    expect(Array.isArray(report.blockers)).toBe(true);
  });

  it('runWeeklyReview returns score 0-100', () => {
    const brain = new CompanyBrain();
    cycle.runWorkday(brain.decompose('Week task'));
    cycle.runEvening();
    const okr = cycle.runWeeklyReview();
    expect(okr.score).toBeGreaterThanOrEqual(0);
    expect(okr.score).toBeLessThanOrEqual(100);
    expect(Array.isArray(okr.objectives)).toBe(true);
    expect(okr.objectives.length).toBeGreaterThan(0);
  });
});

// ── KPIDashboard ─────────────────────────────────────────────────────────────

describe('KPIDashboard', () => {
  let dash: KPIDashboard;

  beforeEach(() => { dash = new KPIDashboard(); });

  it('recordMetric updates snapshot', () => {
    dash.recordMetric('mrr', 5000);
    expect(dash.getMetrics().mrr).toBe(5000);
  });

  it('getMetrics returns full snapshot shape', () => {
    const snap = dash.getMetrics();
    expect(snap).toHaveProperty('mrr');
    expect(snap).toHaveProperty('activeUsers');
    expect(snap).toHaveProperty('churnRate');
    expect(snap).toHaveProperty('nps');
    expect(snap).toHaveProperty('burnRate');
    expect(snap).toHaveProperty('runwayMonths');
    expect(snap).toHaveProperty('timestamp');
  });

  it('checkAlerts fires on high churn', () => {
    dash.recordMetric('churnRate', 10);
    const alerts = dash.checkAlerts();
    const churnAlert = alerts.find((a) => a.metric === 'churnRate');
    expect(churnAlert).toBeDefined();
    expect(churnAlert?.severity).toBe('critical');
  });

  it('checkAlerts fires on low NPS', () => {
    dash.recordMetric('nps', 20);
    const alerts = dash.checkAlerts();
    expect(alerts.some((a) => a.metric === 'nps')).toBe(true);
  });

  it('checkAlerts fires on short runway', () => {
    dash.recordMetric('runwayMonths', 3);
    const alerts = dash.checkAlerts();
    expect(alerts.some((a) => a.metric === 'runwayMonths')).toBe(true);
  });

  it('no alerts when metrics are healthy', () => {
    dash.recordMetric('churnRate', 2);
    dash.recordMetric('nps', 60);
    dash.recordMetric('runwayMonths', 18);
    dash.recordMetric('burnRate', 10000);
    expect(dash.checkAlerts()).toHaveLength(0);
  });

  it('getDepartmentHealth returns 8 scores', () => {
    const health = dash.getDepartmentHealth();
    expect(Object.keys(health)).toHaveLength(8);
    for (const score of Object.values(health)) {
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    }
  });

  it('generateReport returns markdown with headers', () => {
    dash.recordMetric('mrr', 8000);
    const report = dash.generateReport();
    expect(report).toContain('# KPI Report');
    expect(report).toContain('## Core Metrics');
    expect(report).toContain('## Alerts');
    expect(report).toContain('## Department Health');
    expect(report).toContain('$8,000');
  });
});

// ── RecipeEngine ─────────────────────────────────────────────────────────────

describe('RecipeEngine', () => {
  let engine: RecipeEngine;

  beforeEach(() => { engine = new RecipeEngine(); });

  it('lists 4 built-in recipes', () => {
    expect(engine.listRecipes()).toHaveLength(4);
  });

  it('addRecipe adds custom recipe', () => {
    engine.addRecipe({
      name: 'custom-flow',
      slaHours: 1,
      trigger: 'manual',
      steps: ['step-a', 'step-b'],
    });
    expect(engine.listRecipes()).toHaveLength(5);
  });

  it('executeRecipe returns success for known recipe', () => {
    const result = engine.executeRecipe('new-customer-onboard', { userId: 'u1' });
    expect(result.success).toBe(true);
    expect(result.stepsCompleted).toBe(4);
  });

  it('executeRecipe returns failure for unknown recipe', () => {
    const result = engine.executeRecipe('nonexistent', {});
    expect(result.success).toBe(false);
    expect(result.stepsCompleted).toBe(0);
  });

  it('getRecipeStatus tracks execution count', () => {
    engine.executeRecipe('bug-fix-deploy', {});
    engine.executeRecipe('bug-fix-deploy', {});
    const status = engine.getRecipeStatus('bug-fix-deploy');
    expect(status.executionCount).toBe(2);
    expect(status.successRate).toBe(1);
  });

  it('getRecipeStatus returns zeros for unexecuted recipe', () => {
    const status = engine.getRecipeStatus('monthly-close');
    expect(status.executionCount).toBe(0);
    expect(status.avgDuration).toBe(0);
    expect(status.successRate).toBe(0);
  });

  it('all built-in recipes have slaHours and steps', () => {
    for (const r of engine.listRecipes()) {
      expect(r.slaHours).toBeGreaterThan(0);
      expect(r.steps.length).toBeGreaterThan(0);
      expect(typeof r.trigger).toBe('string');
    }
  });
});
