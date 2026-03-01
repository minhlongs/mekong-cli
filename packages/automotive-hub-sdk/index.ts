/**
 * @agencyos/automotive-hub-sdk — Unified Automotive Hub
 *
 * Facade consolidating fleet management, EV charging networks, battery analytics,
 * and mobility-as-a-service (MaaS) operations.
 *
 * Quick Start:
 *   import { createFleetManager, createChargingNetwork } from '@agencyos/automotive-hub-sdk';
 *
 * Sub-path imports:
 *   import { createFleetManager } from '@agencyos/automotive-hub-sdk/fleet';
 *   import { createChargingNetwork } from '@agencyos/automotive-hub-sdk/ev';
 *   import { createMobilityPlatform } from '@agencyos/automotive-hub-sdk/mobility';
 */

export { createFleetManager, createVehicleTracker } from './fleet-facade';
export { createChargingNetwork, createBatteryAnalyzer } from './ev-facade';
export { createMobilityPlatform, createRouteOptimizer } from './mobility-facade';
