import { EventEmitter } from "node:events";

/** Stub WebSocket relay using EventEmitter pub/sub.
 *  Wire to `ws` package later by replacing emit/on with actual WS broadcast.
 */
export class WebSocketRelay {
  private emitter = new EventEmitter();
  private connectionCount = 0;

  /** Register a listener for a specific event. */
  on(event: string, listener: (data: unknown) => void): void {
    this.emitter.on(event, listener);
  }

  /** Remove a listener. */
  off(event: string, listener: (data: unknown) => void): void {
    this.emitter.off(event, listener);
  }

  /** Broadcast an event with payload to all subscribers. */
  broadcast(event: string, data: unknown): void {
    this.emitter.emit(event, data);
  }

  /** Simulate connection tracking (wire to real WS server later). */
  connect(): void {
    this.connectionCount++;
  }

  disconnect(): void {
    if (this.connectionCount > 0) this.connectionCount--;
  }

  getConnectionCount(): number {
    return this.connectionCount;
  }

  /** Remove all listeners and reset state. */
  destroy(): void {
    this.emitter.removeAllListeners();
    this.connectionCount = 0;
  }
}
