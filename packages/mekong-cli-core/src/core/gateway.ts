/**
 * Gateway — routes CLI commands to registered handlers or falls back to engine.run().
 * Supports ROIaaS 5-level command hierarchy: studio → cto → pm → dev → worker
 */
import type { MekongEngine } from './engine.js';

export type CommandHandler = (args: string[], engine: MekongEngine) => Promise<string>;

/** ROIaaS command level definitions — each level can delegate to the level below */
export const ROIAAS_LEVELS = {
  studio: { cascades_to: 'cto', chapter: '始計 — Portfolio', icon: '🏛️' },
  cto: { cascades_to: 'pm', chapter: '地形 — Terrain', icon: '🧠' },
  pm: { cascades_to: 'dev', chapter: '謀攻 — Stratagem', icon: '📋' },
  dev: { cascades_to: 'worker', chapter: '軍爭 — Contention', icon: '⚙️' },
  worker: { cascades_to: null, chapter: '九變 — Atomic', icon: '⚡' },
} as const;

export type RoiaasLevel = keyof typeof ROIAAS_LEVELS;

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

  /**
   * Delegate a command to a lower level in the ROIaaS hierarchy.
   * e.g., delegateDown('studio', 'cto:review', ['--project', 'mekong-cli'])
   */
  async delegateDown(fromLevel: RoiaasLevel, targetCommand: string, args: string[] = []): Promise<string> {
    const levelDef = ROIAAS_LEVELS[fromLevel];
    if (!levelDef.cascades_to) {
      throw new Error(`Level "${fromLevel}" is atomic — cannot delegate further`);
    }
    const targetLevel = targetCommand.split(':')[0] as RoiaasLevel;
    if (targetLevel !== levelDef.cascades_to) {
      throw new Error(`Level "${fromLevel}" can only delegate to "${levelDef.cascades_to}", not "${targetLevel}"`);
    }
    return this.dispatch(targetCommand, args);
  }

  /** Get the cascade target for a given level */
  getCascadeTarget(level: RoiaasLevel): RoiaasLevel | null {
    return ROIAAS_LEVELS[level]?.cascades_to ?? null;
  }

  /** Parse a namespaced command like "studio:audit" into { level, command } */
  parseCommand(input: string): { level: RoiaasLevel | null; command: string } {
    const colonIdx = input.indexOf(':');
    if (colonIdx > 0) {
      const level = input.substring(0, colonIdx) as RoiaasLevel;
      if (level in ROIAAS_LEVELS) {
        return { level, command: input };
      }
    }
    return { level: null, command: input };
  }

  /** List all registered route names */
  listRoutes(): string[] {
    return Array.from(this.routes.keys());
  }

  /** List routes filtered by ROIaaS level */
  listRoutesByLevel(level: RoiaasLevel): string[] {
    const prefix = `${level}:`;
    return this.listRoutes().filter(r => r.startsWith(prefix));
  }

  has(command: string): boolean {
    return this.routes.has(command);
  }
}
