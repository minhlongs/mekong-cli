/**
 * Task Tracker type definitions — tasks, statuses, dependencies.
 */

export type TaskStatus = "todo" | "in_progress" | "done";

export type TaskPriority = "low" | "medium" | "high" | "critical";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  /** Username of task owner */
  owner: string;
  /** MCU cost estimate */
  mcuCost: number;
  /** IDs of tasks that block this task */
  blockedBy: string[];
  /** IDs of tasks this task blocks */
  blocks: string[];
  /** ISO timestamp */
  createdAt: string;
  updatedAt: string;
}

export interface SessionHistoryEntry {
  taskId: string;
  timestamp: string;
  action: string;
  agent: string;
}

export type KanbanColumn = {
  status: TaskStatus;
  label: string;
  tasks: Task[];
};
