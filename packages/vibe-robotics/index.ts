/**
 * @agencyos/vibe-robotics — Robotics & Automation Facade SDK
 *
 * Fleet management, predictive maintenance scheduling, digital twin simulation.
 *
 * Usage:
 *   import { createFleetManager, createMaintenanceScheduler, createDigitalTwinEngine } from '@agencyos/vibe-robotics';
 */

// ─── Types ──────────────────────────────────────────────────────

export type RobotStatus = 'idle' | 'active' | 'charging' | 'maintenance' | 'error' | 'offline';
export type MaintenanceType = 'preventive' | 'corrective' | 'predictive' | 'condition_based';
export type MaintenancePriority = 'critical' | 'high' | 'normal' | 'low';
export type TwinSyncStatus = 'synced' | 'stale' | 'diverged' | 'offline';

export interface SensorReading {
  sensorId: string;
  robotId: string;
  type: 'temperature' | 'vibration' | 'current' | 'voltage' | 'pressure' | 'speed';
  value: number;
  unit: string;
  timestamp: string;
}

export interface Robot {
  id: string;
  name: string;
  model: string;
  serialNumber: string;
  status: RobotStatus;
  batteryLevel: number;
  location: { x: number; y: number; z: number; zone: string };
  firmwareVersion: string;
  uptimeHours: number;
  totalOperatingHours: number;
  lastMaintenanceAt: string;
  nextMaintenanceDue: string;
  registeredAt: string;
}

export interface FleetTask {
  id: string;
  robotId: string;
  type: string;
  payload: Record<string, unknown>;
  priority: MaintenancePriority;
  status: 'queued' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  assignedAt?: string;
  completedAt?: string;
  estimatedDurationMin: number;
}

export interface MaintenanceRecord {
  id: string;
  robotId: string;
  type: MaintenanceType;
  priority: MaintenancePriority;
  description: string;
  partsReplaced: string[];
  technicianId: string;
  scheduledAt: string;
  completedAt?: string;
  downtimeMinutes: number;
  costUSD: number;
  notes?: string;
}

export interface DigitalTwin {
  id: string;
  robotId: string;
  model: Record<string, unknown>;
  simulatedState: Record<string, unknown>;
  realWorldState: Record<string, unknown>;
  syncStatus: TwinSyncStatus;
  lastSyncedAt: string;
  divergenceScore: number;
}

// ─── Fleet Manager ───────────────────────────────────────────────

export function createFleetManager() {
  const robots = new Map<string, Robot>();
  const tasks: FleetTask[] = [];

  return {
    /** Đăng ký robot mới vào fleet */
    registerRobot(robot: Robot): Robot {
      robots.set(robot.id, { ...robot });
      return { ...robot };
    },

    /** Cập nhật trạng thái robot */
    updateStatus(robotId: string, status: RobotStatus): { ok: boolean; robot?: Robot } {
      const robot = robots.get(robotId);
      if (!robot) return { ok: false };
      robot.status = status;
      return { ok: true, robot: { ...robot } };
    },

    /** Giao task cho robot phù hợp nhất */
    assignTask(task: FleetTask): { ok: boolean; assignedRobotId?: string; reason?: string } {
      const available = [...robots.values()].filter(r => r.status === 'idle' && r.batteryLevel > 20);
      if (available.length === 0) return { ok: false, reason: 'No idle robots with sufficient battery' };
      // Chọn robot gần nhất (placeholder coords 0,0)
      const robot = available[0];
      task.robotId = robot.id;
      task.status = 'assigned';
      task.assignedAt = new Date().toISOString();
      tasks.push({ ...task });
      robot.status = 'active';
      return { ok: true, assignedRobotId: robot.id };
    },

    /** Theo dõi sức khoẻ fleet */
    getFleetHealth(): { total: number; byStatus: Record<RobotStatus, number>; utilizationPct: number; lowBatteryCount: number } {
      const all = [...robots.values()];
      const byStatus = {} as Record<RobotStatus, number>;
      for (const r of all) byStatus[r.status] = (byStatus[r.status] ?? 0) + 1;
      const active = byStatus['active'] ?? 0;
      const utilizationPct = all.length === 0 ? 0 : Math.round((active / all.length) * 100);
      const lowBatteryCount = all.filter(r => r.batteryLevel < 20).length;
      return { total: all.length, byStatus, utilizationPct, lowBatteryCount };
    },

    /** Lấy danh sách robots cần bảo trì */
    getRobotsNeedingMaintenance(): Robot[] {
      const now = new Date().toISOString();
      return [...robots.values()].filter(r => r.nextMaintenanceDue <= now || r.status === 'maintenance');
    },

    /** Cập nhật sensor reading lên robot */
    applyTelemetry(robotId: string, readings: SensorReading[]): { ok: boolean; alerts: string[] } {
      const robot = robots.get(robotId);
      if (!robot) return { ok: false, alerts: [] };
      const alerts: string[] = [];
      for (const r of readings) {
        if (r.type === 'temperature' && r.value > 85) alerts.push(`Robot ${robotId}: High temperature ${r.value}°C`);
        if (r.type === 'vibration' && r.value > 10) alerts.push(`Robot ${robotId}: Excessive vibration ${r.value}g`);
        if (r.type === 'current' && r.value > 50) alerts.push(`Robot ${robotId}: Overcurrent ${r.value}A`);
      }
      return { ok: true, alerts };
    },

    getRobot: (id: string) => robots.get(id) ? { ...robots.get(id)! } : null,
    listRobots: () => [...robots.values()],
    listTasks: () => [...tasks],
  };
}

// ─── Maintenance Scheduler ───────────────────────────────────────

export function createMaintenanceScheduler() {
  const records: MaintenanceRecord[] = [];
  const partsInventory = new Map<string, number>();

  return {
    /** Lên lịch bảo trì dự phòng */
    schedulePreventive(robotId: string, intervalHours: number, lastMaintenanceAt: string, costUSD: number = 200): MaintenanceRecord {
      const scheduledAt = new Date(new Date(lastMaintenanceAt).getTime() + intervalHours * 3600000).toISOString();
      const record: MaintenanceRecord = {
        id: `maint_${Date.now()}_${robotId}`,
        robotId,
        type: 'preventive',
        priority: 'normal',
        description: `Preventive maintenance every ${intervalHours}h`,
        partsReplaced: [],
        technicianId: '',
        scheduledAt,
        downtimeMinutes: 60,
        costUSD,
      };
      records.push(record);
      return { ...record };
    },

    /** Dự đoán bảo trì dựa trên sensor data */
    predictMaintenance(_robotId: string, readings: SensorReading[]): { required: boolean; priority: MaintenancePriority; reasons: string[] } {
      const reasons: string[] = [];
      let priority: MaintenancePriority = 'low';
      for (const r of readings) {
        if (r.type === 'vibration' && r.value > 8) { reasons.push(`Vibration anomaly: ${r.value}g`); priority = 'high'; }
        if (r.type === 'temperature' && r.value > 80) { reasons.push(`Temperature high: ${r.value}°C`); priority = 'high'; }
        if (r.type === 'current' && r.value > 45) { reasons.push(`Current spike: ${r.value}A`); priority = 'critical'; }
      }
      return { required: reasons.length > 0, priority, reasons };
    },

    /** Ghi nhận hoàn thành bảo trì */
    completeRecord(recordId: string, technicianId: string, partsReplaced: string[], notes?: string): { ok: boolean } {
      const rec = records.find(r => r.id === recordId);
      if (!rec) return { ok: false };
      rec.completedAt = new Date().toISOString();
      rec.technicianId = technicianId;
      rec.partsReplaced = partsReplaced;
      if (notes) rec.notes = notes;
      // Trừ parts khỏi inventory
      for (const part of partsReplaced) {
        const qty = partsInventory.get(part) ?? 0;
        partsInventory.set(part, Math.max(0, qty - 1));
      }
      return { ok: true };
    },

    /** Tính tổng thời gian downtime & chi phí theo robot */
    getRobotMaintenanceSummary(robotId: string): { totalDowntimeMin: number; totalCostUSD: number; recordCount: number } {
      const robotRecords = records.filter(r => r.robotId === robotId && r.completedAt);
      return {
        totalDowntimeMin: robotRecords.reduce((sum, r) => sum + r.downtimeMinutes, 0),
        totalCostUSD: robotRecords.reduce((sum, r) => sum + r.costUSD, 0),
        recordCount: robotRecords.length,
      };
    },

    /** Kiểm tra tồn kho phụ tùng */
    checkPartsInventory(parts: string[]): { available: Record<string, number>; shortages: string[] } {
      const available: Record<string, number> = {};
      const shortages: string[] = [];
      for (const part of parts) {
        const qty = partsInventory.get(part) ?? 0;
        available[part] = qty;
        if (qty === 0) shortages.push(part);
      }
      return { available, shortages };
    },

    addPartsStock: (part: string, qty: number) => partsInventory.set(part, (partsInventory.get(part) ?? 0) + qty),
    listRecords: () => [...records],
  };
}

// ─── Digital Twin Engine ─────────────────────────────────────────

export function createDigitalTwinEngine() {
  const twins = new Map<string, DigitalTwin>();

  return {
    /** Tạo digital twin model cho robot */
    createTwin(robotId: string, initialModel: Record<string, unknown>): DigitalTwin {
      const twin: DigitalTwin = {
        id: `twin_${robotId}`,
        robotId,
        model: { ...initialModel },
        simulatedState: { ...initialModel },
        realWorldState: {},
        syncStatus: 'stale',
        lastSyncedAt: new Date().toISOString(),
        divergenceScore: 0,
      };
      twins.set(robotId, twin);
      return { ...twin };
    },

    /** Đồng bộ trạng thái thực tế vào twin */
    syncRealWorldState(robotId: string, realState: Record<string, unknown>): { ok: boolean; divergenceScore: number } {
      const twin = twins.get(robotId);
      if (!twin) return { ok: false, divergenceScore: -1 };
      twin.realWorldState = { ...realState };
      twin.lastSyncedAt = new Date().toISOString();
      // Tính divergence: số keys có giá trị khác nhau / tổng keys
      const allKeys = new Set([...Object.keys(twin.simulatedState), ...Object.keys(realState)]);
      let diverged = 0;
      for (const key of allKeys) {
        if (JSON.stringify(twin.simulatedState[key]) !== JSON.stringify(realState[key])) diverged++;
      }
      twin.divergenceScore = allKeys.size === 0 ? 0 : Math.round((diverged / allKeys.size) * 100);
      twin.syncStatus = twin.divergenceScore === 0 ? 'synced' : twin.divergenceScore > 50 ? 'diverged' : 'stale';
      return { ok: true, divergenceScore: twin.divergenceScore };
    },

    /** Chạy simulation scenario trên twin (không ảnh hưởng real world) */
    runSimulation(robotId: string, scenario: Record<string, unknown>): { outcome: Record<string, unknown>; riskFlags: string[] } {
      const twin = twins.get(robotId);
      if (!twin) return { outcome: {}, riskFlags: ['Twin not found'] };
      const simulatedOutcome = { ...twin.simulatedState, ...scenario };
      const riskFlags: string[] = [];
      if ((simulatedOutcome['temperature'] as number) > 85) riskFlags.push('Overheating risk in simulation');
      if ((simulatedOutcome['batteryLevel'] as number) < 10) riskFlags.push('Battery depletion risk');
      if ((simulatedOutcome['vibration'] as number) > 10) riskFlags.push('Mechanical stress risk');
      return { outcome: simulatedOutcome, riskFlags };
    },

    /** Cập nhật simulated state (cho simulation runs) */
    updateSimulatedState(robotId: string, updates: Record<string, unknown>): { ok: boolean } {
      const twin = twins.get(robotId);
      if (!twin) return { ok: false };
      twin.simulatedState = { ...twin.simulatedState, ...updates };
      return { ok: true };
    },

    /** Lấy tất cả twins đang diverged */
    getDivergedTwins(threshold: number = 30): DigitalTwin[] {
      return [...twins.values()].filter(t => t.divergenceScore >= threshold);
    },

    getTwin: (robotId: string) => twins.get(robotId) ? { ...twins.get(robotId)! } : null,
    listTwins: () => [...twins.values()],
  };
}
