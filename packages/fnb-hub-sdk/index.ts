/**
 * @agencyos/fnb-hub-sdk — Unified F&B Hub
 *
 * Facade package consolidating restaurant operations, POS, table reservations,
 * food delivery logistics, driver fleet management, kitchen display system,
 * recipe database, and ingredient inventory tracking.
 *
 * Quick Start:
 *   import { createRestaurantManager, createDeliveryDispatcher, createKitchenDisplaySystem } from '@agencyos/fnb-hub-sdk';
 *
 * Sub-path imports:
 *   import { createRestaurantManager } from '@agencyos/fnb-hub-sdk/restaurant';
 *   import { createDeliveryDispatcher } from '@agencyos/fnb-hub-sdk/delivery';
 *   import { createKitchenDisplaySystem } from '@agencyos/fnb-hub-sdk/kitchen';
 */

// Restaurant Operations & Menu
export {
  createRestaurantManager,
  createTableReservationSystem,
  createMenuManager,
} from './restaurant-facade';
export type { Restaurant, TableReservation, MenuItem } from './restaurant-facade';

// Delivery & Driver Fleet
export {
  createDeliveryDispatcher,
  createZoneManager,
  createDriverFleet,
} from './delivery-facade';
export type { DeliveryOrder, DeliveryZone, DriverProfile } from './delivery-facade';

// Kitchen, Recipes & Ingredient Inventory
export {
  createKitchenDisplaySystem,
  createRecipeDatabase,
  createIngredientInventoryTracker,
} from './kitchen-facade';
export type { KitchenOrder, Recipe, IngredientStock } from './kitchen-facade';
