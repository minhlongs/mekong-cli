export {
  CompanyBrain,
  DEPARTMENTS,
  type Department,
  type DepartmentTask,
  type StandupReport,
  type CompanyHealth,
} from './company-brain.js';

export {
  DepartmentAgent,
  ProductAgent,
  EngineeringAgent,
  SalesAgent,
  MarketingAgent,
  FinanceAgent,
  LegalAgent,
  HRAgent,
  SupportAgent,
  type AgentResult,
  type KPI,
} from './department-agents.js';

export {
  DailyCycle,
  type MorningBrief,
  type WorkdayResult,
  type EveningReport,
  type WeeklyOKR,
} from './daily-cycle.js';

export {
  KPIDashboard,
  type MetricSnapshot,
  type Alert,
} from './kpi-dashboard.js';

export {
  RecipeEngine,
  type Recipe,
  type RecipeResult,
  type RecipeStatus,
} from './automation-recipes.js';
