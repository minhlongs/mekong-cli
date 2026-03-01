/**
 * @agencyos/hospitality-hub-sdk — Unified Hospitality Hub
 *
 * Facade consolidating hotel booking, guest experience, loyalty programs,
 * housekeeping scheduling, and revenue management operations.
 *
 * Quick Start:
 *   import { createBookingEngine, createGuestManager } from '@agencyos/hospitality-hub-sdk';
 *
 * Sub-path imports:
 *   import { createBookingEngine } from '@agencyos/hospitality-hub-sdk/booking';
 *   import { createGuestManager } from '@agencyos/hospitality-hub-sdk/guest';
 *   import { createRevenueManager } from '@agencyos/hospitality-hub-sdk/operations';
 */

export { createBookingEngine, createRoomInventoryManager } from './booking-facade';
export { createGuestManager, createLoyaltyProgram } from './guest-facade';
export { createRevenueManager, createHousekeepingScheduler } from './operations-facade';
