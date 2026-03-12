/**
 * Gateway — routes CLI commands to registered handlers or falls back to engine.run().
 */
import type { MekongEngine } from './engine.js';

export type CommandHandler = (args: string[], engine: MekongEngine) => Promise<string>;

export class Gateway {
  private routes: Map<string, CommandHandler> = new Map();
  private engine: MekongEngine;

  constructor(engine: MekongEngine) {
    this.engine = engine;
  }

  /** Register a named command route */
  route(command: string, handler: CommandHandler): void {
    this.routes.set(command, handler);
  }

  /** Dispatch a command — uses registered handler or falls back to engine.run() */
  async dispatch(command: string, args: string[] = []): Promise<string> {
    const handler = this.routes.get(command);
    if (handler) {
      return handler(args, this.engine);
    }
    return this.engine.run([command, ...args].join(' '));
  }

  /** List all registered route names */
  listRoutes(): string[] {
    return Array.from(this.routes.keys());
  }

  has(command: string): boolean {
    return this.routes.has(command);
  }
}
