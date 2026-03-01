/**
 * @agencyos/hospitality-hub-sdk — Operations Facade
 *
 * Provides unified interface for housekeeping scheduling, maintenance tracking,
 * and revenue management metrics (ADR, RevPAR, occupancy).
 */

export interface HousekeepingTask {
  id: string;
  roomId: string;
  priority: 'urgent' | 'high' | 'normal' | 'low';
  status: 'pending' | 'in-progress' | 'completed' | 'skipped';
  assignedTo?: string;
  type: 'checkout-clean' | 'stayover' | 'deep-clean' | 'turndown';
  scheduledAt: string;
  completedAt?: string;
}

export interface MaintenanceRequest {
  id: string;
  roomId: string;
  issue: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'in-progress' | 'resolved';
  reportedAt: string;
  resolvedAt?: string;
}

export interface RevenueMetrics {
  date: string;
  occupancyRate: number;
  adr: number;
  revpar: number;
  totalRevenue: number;
  roomsSold: number;
  roomsAvailable: number;
}

export function createRevenueManager() {
  return {
    getMetrics: async (_date: string) => ({} as RevenueMetrics),
    getDateRange: async (_startDate: string, _endDate: string) => [] as RevenueMetrics[],
    getForecast: async (_days: number) => [] as RevenueMetrics[],
  };
}

export function createHousekeepingScheduler() {
  return {
    getTasks: async (_date: string) => [] as HousekeepingTask[],
    assignTask: async (_taskId: string, _staffId: string) => ({ success: true }),
    completeTask: async (_taskId: string) => ({ success: true }),
    createMaintenanceRequest: async (_request: Omit<MaintenanceRequest, 'id' | 'reportedAt'>) => ({ id: '' }),
  };
}
