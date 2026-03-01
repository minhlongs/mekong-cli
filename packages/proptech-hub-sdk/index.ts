/**
 * @agencyos/proptech-hub-sdk — Unified PropTech Hub
 *
 * Facade consolidating property management, valuation, and smart building operations.
 *
 * Quick Start:
 *   import { createPropertyManager, createValuationEngine } from '@agencyos/proptech-hub-sdk';
 *
 * Sub-path imports:
 *   import { createPropertyManager } from '@agencyos/proptech-hub-sdk/property';
 *   import { createValuationEngine } from '@agencyos/proptech-hub-sdk/valuation';
 *   import { createSmartBuildingController } from '@agencyos/proptech-hub-sdk/smart-building';
 */

export { createPropertyManager, createListingEngine, createTenantScreener, createLeaseManager } from './property-facade';
export { createValuationEngine, createMarketAnalyzer, createComparablesFinder } from './valuation-facade';
export { createSmartBuildingController, createAccessManager, createEnergyMonitor } from './smart-building-facade';
