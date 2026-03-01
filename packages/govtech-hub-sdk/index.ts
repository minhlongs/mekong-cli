/**
 * @agencyos/govtech-hub-sdk — Unified GovTech Hub
 *
 * Facade package consolidating citizen services, digital identity, government
 * procurement, regulatory compliance, and audit trail management for public sector.
 *
 * Quick Start:
 *   import { createCitizenPortal, createProcurementManager, createComplianceEngine } from '@agencyos/govtech-hub-sdk';
 *
 * Sub-path imports:
 *   import { createCitizenPortal } from '@agencyos/govtech-hub-sdk/citizen';
 *   import { createProcurementManager } from '@agencyos/govtech-hub-sdk/procurement';
 *   import { createComplianceEngine } from '@agencyos/govtech-hub-sdk/compliance';
 */

// Citizen Services & Digital Identity
export {
  createCitizenPortal,
  createServiceDesk,
  createDigitalIDManager,
} from './citizen-facade';
export type { CitizenProfile, ServiceRequest, DigitalID } from './citizen-facade';

// Government Procurement
export {
  createProcurementManager,
  createTenderPortal,
  createVendorEvaluator,
} from './procurement-facade';
export type { Tender, ProcurementBid, Contract } from './procurement-facade';

// Regulatory Compliance & Audit
export {
  createComplianceEngine,
  createAuditLogger,
  createPolicyManager,
} from './compliance-facade';
export type { RegulatoryReport, AuditTrail, PolicyDocument } from './compliance-facade';
