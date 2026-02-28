/**
 * @agencyos/vibe-pos — Point-of-Sale Operations SDK
 *
 * Reusable POS engine for restaurant/cafe apps (com-anh-duong-10x, vibe-coding-cafe).
 * Order management, table tracking, kitchen display system, receipt generation.
 *
 * Usage:
 *   import { createOrderEngine, OrderStatus } from '@agencyos/vibe-pos';
 *   const engine = createOrderEngine({ taxRate: 0.08 });
 *   const order = engine.createOrder({ tableId: 'T1', items: [...] });
 */

// ─── Types ──────────────────────────────────────────────────────

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready'
  | 'served'
  | 'paid'
  | 'cancelled';

export interface OrderItem {
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  notes?: string;
}

export interface Order {
  id: string;
  tableId: string;
  items: OrderItem[];
  status: OrderStatus;
  subtotal: number;
  tax: number;
  total: number;
  createdAt: string;
}

export interface TableStatus {
  id: string;
  name: string;
  isOccupied: boolean;
  currentOrderId?: string;
  capacity: number;
}

// ─── Order Engine ───────────────────────────────────────────────

export interface OrderEngineConfig {
  taxRate: number;
  serviceCharge?: number;
}

export function createOrderEngine(config: OrderEngineConfig) {
  const { taxRate, serviceCharge = 0 } = config;

  return {
    calculateOrderTotal(items: OrderItem[]): { subtotal: number; tax: number; service: number; total: number } {
      const subtotal = items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
      const tax = Math.round(subtotal * taxRate);
      const service = Math.round(subtotal * serviceCharge);
      return { subtotal, tax, service, total: subtotal + tax + service };
    },

    getNextStatus(current: OrderStatus): OrderStatus | null {
      const flow: Record<OrderStatus, OrderStatus | null> = {
        pending: 'confirmed',
        confirmed: 'preparing',
        preparing: 'ready',
        ready: 'served',
        served: 'paid',
        paid: null,
        cancelled: null,
      };
      return flow[current];
    },

    canCancel(status: OrderStatus): boolean {
      return ['pending', 'confirmed'].includes(status);
    },
  };
}

// ─── Kitchen Display ────────────────────────────────────────────

export interface KitchenTicket {
  orderId: string;
  tableId: string;
  items: OrderItem[];
  priority: 'normal' | 'rush';
  createdAt: string;
}

export function createKitchenDisplay() {
  return {
    sortByPriority(tickets: KitchenTicket[]): KitchenTicket[] {
      return [...tickets].sort((a, b) => {
        if (a.priority === 'rush' && b.priority !== 'rush') return -1;
        if (a.priority !== 'rush' && b.priority === 'rush') return 1;
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      });
    },

    estimateWaitMinutes(queueLength: number, avgPrepTime: number): number {
      return Math.ceil(queueLength * avgPrepTime);
    },
  };
}
