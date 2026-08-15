/**
 * Mission Types
 * RaaS UX Kit v2.1.79
 */

import { Robot } from './robot';
import { TelemetryStream } from './telemetry';

// ============================================
// Mission Core Types
// ============================================

export type MissionType = 'patrol' | 'inspection' | 'transport' | 'inventory' | 'charging' | 'custom';

export type MissionStatus = 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'aborted' | 'failed';

export type MissionPriority = 'low' | 'normal' | 'high' | 'critical';

export type WaypointStatus = 'pending' | 'active' | 'completed' | 'skipped' | 'failed';

export type ActionType = 'navigate' | 'scan' | 'pick' | 'place' | 'charge' | 'wait' | 'custom';

// ============================================
// Mission Interfaces
// ============================================

export interface Mission {
  id: string;
  name: string;
  type: MissionType;
  status: MissionStatus;
  priority: MissionPriority;
  robotId?: string;
  robot?: Robot;
  createdAt: Date;
  scheduledAt?: Date;
  startedAt?: Date;
  completedAt?: Date;
  waypoints: Waypoint[];
  actions: MissionAction[];
  batteryRequirement?: number; // percentage
  estimatedDuration?: number; // ms
  actualDuration?: number; // ms
  metadata?: Record<string, unknown>;
}

export interface Waypoint {
  id: string;
  name: string;
  order: number;
  position: Position3D;
  heading?: number; // degrees
  status: WaypointStatus;
  actions?: WaypointAction[];
  reachedAt?: Date;
  departedAt?: Date;
  metadata?: Record<string, unknown>;
}

export interface Position3D {
  x: number; // mm
  y: number; // mm
  z: number; // mm
}

export interface WaypointAction {
  id: string;
  type: ActionType;
  name: string;
  parameters?: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt?: Date;
  completedAt?: Date;
  result?: unknown;
}

export interface MissionAction {
  id: string;
  type: ActionType;
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
  trigger: 'on_waypoint_reach' | 'on_mission_start' | 'on_mission_complete' | 'manual';
  waypointId?: string;
}

// ============================================
// Mission Progress
// ============================================

export interface MissionProgress {
  percentage: number; // 0-100
  currentWaypoint: number; // index
  totalWaypoints: number;
  elapsedSeconds: number;
  estimatedRemainingSeconds?: number;
  completedWaypoints: number;
  failedWaypoints: number;
  skippedWaypoints: number;
}

// ============================================
// Mission Log Types
// ============================================

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'critical';

export interface MissionLog {
  id?: string;
  timestamp: Date;
  level: LogLevel;
  message: string;
  source?: string;
  data?: Record<string, unknown>;
  missionId?: string;
  robotId?: string;
}

export interface MissionLogFilter {
  levels?: LogLevel[];
  source?: string;
  timeRange?: {
    from: Date;
    to: Date;
  };
  search?: string;
}

// ============================================
// Mission Control Props
// ============================================

export interface MissionControlProps {
  robotId: string;
  missions: Mission[];
  activeMission?: Mission;
  onCreateMission: () => void;
  onLaunchMission: (missionId: string) => Promise<void>;
  onPauseMission: (missionId: string) => Promise<void>;
  onResumeMission: (missionId: string) => Promise<void>;
  onAbortMission: (missionId: string) => Promise<void>;
  isPlaying: boolean;
  isPaused: boolean;
  onPlayPauseToggle: () => void;
  onStop: () => void;
  progress: MissionProgress;
  logs: MissionLog[];
  logFilter?: LogLevel[];
  onLogsExport?: (format: 'txt' | 'json') => void;
  onLogsClear: () => void;
  statusFilter?: MissionStatus[];
  onStatusFilterChange?: (statuses: MissionStatus[]) => void;
  className?: string;
  compact?: boolean;
}

// ============================================
// Mission Templates
// ============================================

export interface MissionTemplate {
  id: string;
  name: string;
  type: MissionType;
  description?: string;
  waypoints: TemplateWaypoint[];
  actions: TemplateAction[];
  estimatedDuration?: number;
  batteryRequirement?: number;
  isDefault?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface TemplateWaypoint {
  order: number;
  name: string;
  position?: Position3D;
  heading?: number;
  actions?: TemplateAction[];
}

export interface TemplateAction {
  type: ActionType;
  name: string;
  parameters?: Record<string, unknown>;
}

// ============================================
// Mission WebSocket Events
// ============================================

export type MissionWebSocketEventType =
  | 'mission_started'
  | 'mission_paused'
  | 'mission_resumed'
  | 'mission_completed'
  | 'mission_aborted'
  | 'mission_failed'
  | 'waypoint_reached'
  | 'waypoint_departed'
  | 'action_started'
  | 'action_completed'
  | 'action_failed'
  | 'state_change'
  | 'progress_update'
  | 'log_entry';

export interface MissionWebSocketEvent {
  type: MissionWebSocketEventType;
  missionId: string;
  robotId?: string;
  timestamp: Date;
  data?: unknown;
}

export interface MissionUpdate {
  type: MissionWebSocketEventType;
  missionId: string;
  waypointIndex?: number;
  missionState?: MissionStatus;
  progress?: MissionProgress;
}

// ============================================
// Queued Action (Offline Support)
// ============================================

export type QueuedActionType = 'launch' | 'pause' | 'resume' | 'abort' | 'add_waypoint';

export type QueuedActionStatus = 'pending' | 'syncing' | 'completed' | 'failed';

export interface QueuedAction {
  id: string;
  type: QueuedActionType;
  missionId: string;
  payload?: unknown;
  queuedAt: Date;
  status: QueuedActionStatus;
  retryCount: number;
  error?: string;
}

// ============================================
// Mission Statistics
// ============================================

export interface MissionStatistics {
  totalMissions: number;
  completedMissions: number;
  failedMissions: number;
  abortedMissions: number;
  successRate: number; // percentage
  averageDuration: number; // ms
  totalDistance: number; // mm
  totalWaypoints: number;
  averageWaypointsPerMission: number;
}

// ============================================
// Mission Hooks
// ============================================

export interface UseMissionControlOptions {
  robotId: string;
  missionId?: string;
  autoConnect?: boolean;
  refreshInterval?: number;
}

export interface UseMissionControlReturn {
  activeMission: Mission | null;
  progress: MissionProgress;
  logs: MissionLog[];
  isConnected: boolean;
  isPlaying: boolean;
  isPaused: boolean;
  isLoading: boolean;
  error: string | null;
  launchMission: (missionId: string) => Promise<void>;
  pauseMission: () => Promise<void>;
  resumeMission: () => Promise<void>;
  abortMission: () => Promise<void>;
  addWaypoint: (waypoint: Waypoint) => Promise<void>;
  removeWaypoint: (waypointId: string) => Promise<void>;
  exportLogs: (format: 'txt' | 'json') => void;
  clearLogs: () => void;
  filterLogs: (filter: MissionLogFilter) => void;
}
