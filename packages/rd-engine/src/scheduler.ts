export class RdScheduler {
  private timerId: ReturnType<typeof setInterval> | null = null;
  private running = false;

  /**
   * Start the scheduler. Runs the callback immediately, then on every interval.
   * @param intervalMs - Interval in milliseconds between scans
   * @param callback   - Async scan function to invoke on each tick
   */
  start(intervalMs: number, callback: () => Promise<void>): void {
    if (this.running) {
      throw new Error("RdScheduler is already running. Call stop() first.");
    }

    this.running = true;

    // Run immediately on start
    void callback().catch((err: unknown) => {
      console.error("[rd-scheduler] Initial scan failed:", err);
    });

    this.timerId = setInterval(() => {
      void callback().catch((err: unknown) => {
        console.error("[rd-scheduler] Scheduled scan failed:", err);
      });
    }, intervalMs);
  }

  stop(): void {
    if (this.timerId !== null) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
    this.running = false;
  }

  isRunning(): boolean {
    return this.running;
  }
}
