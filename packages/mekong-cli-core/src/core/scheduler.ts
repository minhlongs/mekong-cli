/**
 * Scheduler — manages recurring/periodic tasks (heartbeat, compaction, etc.)
 */
import { emit } from './events.js';

export interface ScheduledTask {
  id: string;
  name: string;
  intervalMs: number;
  handler: () => Promise<void>;
}

export class Scheduler {
  private tasks: Map<string, { task: ScheduledTask; timer: ReturnType<typeof setInterval> }> = new Map();

  /** Schedule a recurring task */
  schedule(task: ScheduledTask): void {
    if (this.tasks.has(task.id)) this.cancel(task.id);

    const timer = setInterval(async () => {
      try {
        await task.handler();
      } catch (error) {
        emit('engine:stopped', { error: String(error), taskId: task.id });
      }
    }, task.intervalMs);

    this.tasks.set(task.id, { task, timer });
  }

  /** Cancel a scheduled task */
  cancel(id: string): boolean {
    const entry = this.tasks.get(id);
    if (!entry) return false;
    clearInterval(entry.timer);
    this.tasks.delete(id);
    return true;
  }

  /** Cancel all scheduled tasks */
  cancelAll(): void {
    for (const [id] of this.tasks) this.cancel(id);
  }

  /** List active task definitions */
  list(): ScheduledTask[] {
    return Array.from(this.tasks.values()).map(e => e.task);
  }

  get size(): number {
    return this.tasks.size;
  }
}
