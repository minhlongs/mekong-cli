/**
 * @agencyos/vibe-fnb — F&B Operations SDK
 *
 * Reusable across all F&B projects (84tea, com-anh-duong-10x, vibe-coding-cafe).
 * Menu management, inventory tracking, recipe costing, kitchen workflow.
 *
 * Usage:
 *   import { createMenuEngine, createInventoryTracker } from '@agencyos/vibe-fnb';
 *   const menu = createMenuEngine({ currency: 'VND' });
 *   const inventory = createInventoryTracker({ alertThreshold: 10 });
 */

// ─── Types ──────────────────────────────────────────────────────

export interface MenuItem {
  id: string;
  name: string;
  category: MenuCategory;
  price: number;
  currency: string;
  costOfGoods: number;
  ingredients: Ingredient[];
  isAvailable: boolean;
  tags: string[];
}

export type MenuCategory =
  | 'hot-drinks'
  | 'cold-drinks'
  | 'food'
  | 'dessert'
  | 'combo'
  | 'seasonal';

export interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
  costPerUnit: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  currentStock: number;
  unit: string;
  alertThreshold: number;
  lastRestocked: string;
}

export interface RecipeCost {
  totalCost: number;
  marginPercent: number;
  suggestedPrice: number;
}

// ─── Menu Engine ────────────────────────────────────────────────

export interface MenuEngineConfig {
  currency: string;
  defaultMargin?: number;
}

export function createMenuEngine(config: MenuEngineConfig) {
  const { currency, defaultMargin = 0.65 } = config;

  return {
    calculateRecipeCost(ingredients: Ingredient[]): RecipeCost {
      const totalCost = ingredients.reduce(
        (sum, ing) => sum + ing.quantity * ing.costPerUnit,
        0,
      );
      const suggestedPrice = Math.ceil(totalCost / (1 - defaultMargin) / 1000) * 1000;
      return {
        totalCost,
        marginPercent: defaultMargin * 100,
        suggestedPrice,
      };
    },

    formatPrice(amount: number): string {
      return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency,
      }).format(amount);
    },
  };
}

// ─── Inventory Tracker ──────────────────────────────────────────

export interface InventoryTrackerConfig {
  alertThreshold: number;
}

export function createInventoryTracker(config: InventoryTrackerConfig) {
  const { alertThreshold } = config;

  return {
    checkLowStock(items: InventoryItem[]): InventoryItem[] {
      return items.filter((item) => item.currentStock <= (item.alertThreshold || alertThreshold));
    },

    calculateReorderQuantity(item: InventoryItem, dailyUsage: number, leadDays: number): number {
      const safetyStock = dailyUsage * 2;
      return Math.ceil(dailyUsage * leadDays + safetyStock - item.currentStock);
    },
  };
}
