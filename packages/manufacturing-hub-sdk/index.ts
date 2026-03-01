/**
 * @agencyos/manufacturing-hub-sdk — Unified Manufacturing Hub
 *
 * Facade package consolidating production scheduling, MES, OEE tracking,
 * quality control, SPC charting, supply chain, and BOM management.
 *
 * Quick Start:
 *   import { createProductionScheduler, createQualityManager, createSupplyChainManager } from '@agencyos/manufacturing-hub-sdk';
 *
 * Sub-path imports:
 *   import { createProductionScheduler } from '@agencyos/manufacturing-hub-sdk/production';
 *   import { createQualityManager } from '@agencyos/manufacturing-hub-sdk/quality';
 *   import { createSupplyChainManager } from '@agencyos/manufacturing-hub-sdk/supply-chain';
 */

// Production Line & MES
export {
  createProductionScheduler,
  createMESController,
  createOEETracker,
} from './production-facade';
export type { ProductionOrder, MachineStatus, WorkOrder } from './production-facade';

// Quality Control & SPC
export {
  createQualityManager,
  createSPCEngine,
  createNCRTracker,
} from './quality-facade';
export type { QualityInspection, DefectReport, SPCChart } from './quality-facade';

// Supply Chain & BOM
export {
  createSupplyChainManager,
  createInventoryOptimizer,
  createBOMManager,
} from './supply-chain-facade';
export type { SupplyOrder, InventoryItem, BOMEntry } from './supply-chain-facade';
