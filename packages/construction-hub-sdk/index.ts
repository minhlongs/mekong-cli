/**
 * @agencyos/construction-hub-sdk — Unified Construction Hub
 *
 * Facade package consolidating BIM, project management, safety compliance,
 * cost estimation, and field operations for construction projects.
 *
 * Quick Start:
 *   import { createProjectManager, createSafetyManager, createEstimationEngine } from '@agencyos/construction-hub-sdk';
 *
 * Sub-path imports:
 *   import { createProjectManager } from '@agencyos/construction-hub-sdk/project';
 *   import { createSafetyManager } from '@agencyos/construction-hub-sdk/safety';
 *   import { createEstimationEngine } from '@agencyos/construction-hub-sdk/estimation';
 */

// Project Management & BIM
export {
  createProjectManager,
  createBIMViewer,
  createRFITracker,
  createSubmittalManager,
} from './project-facade';
export type { ConstructionProject, BIMModel, RFI, Submittal } from './project-facade';

// Safety & Compliance
export {
  createSafetyManager,
  createIncidentReporter,
  createComplianceTracker,
} from './safety-facade';
export type { SafetyInspection, Incident, ComplianceCheck } from './safety-facade';

// Cost Estimation & Budgeting
export {
  createEstimationEngine,
  createBudgetTracker,
  createChangeOrderManager,
} from './estimation-facade';
export type { CostEstimate, LineItem, Budget, ChangeOrder } from './estimation-facade';
