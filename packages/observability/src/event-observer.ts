/**
 * Event observer - wires into Mekong event bus to log all events.
 */

import { logger, type Logger } from './logger.js';

export interface EventObserverConfig {
  logger?: Logger;
  logEvents?: boolean;
  logData?: boolean;
}

export class EventObserver {
  private logger: Logger;
  private logEvents: boolean;
  private logData: boolean;
  private cleanup?: () => void;

  constructor(config: EventObserverConfig = {}) {
    this.logger = config.logger || logger;
    this.logEvents = config.logEvents ?? true;
    this.logData = config.logData ?? false;
  }

  /**
   * Attach observer to event bus.
   * Returns cleanup function to detach.
   */
  attach(eventBus: {
    on: (event: string, handler: (data?: unknown) => void) => void;
  }): () => void {
    const handler = (event: string, data?: unknown) => {
      if (!this.logEvents) return;

      const meta: Record<string, unknown> = { event };
      if (this.logData && data) {
        meta.data = data;
      }

      // Categorize by event type
      const level = this.getLogLevel(event);
      this.log(level, `Event: ${event}`, meta);
    };

    // Attach to all Mekong events
    const events = [
      'engine:started', 'engine:stopped',
      'agent:spawned', 'agent:completed', 'agent:failed',
      'task:created', 'task:started', 'task:completed', 'task:failed',
      'tool:called', 'tool:result',
      'sop:started', 'sop:step_completed', 'sop:completed', 'sop:failed',
      'budget:warning', 'budget:exceeded',
      'constraint:violation',
      'memory:saved', 'memory:compacted',
    ];

    for (const event of events) {
      eventBus.on(event, (data) => handler(event, data));
    }

    this.cleanup = () => {
      // In practice, eventBus would need off() method
      this.logger.info('EventObserver detached');
    };

    return () => this.cleanup?.();
  }

  private getLogLevel(event: string): 'debug' | 'info' | 'warn' | 'error' {
    // Errors and failures → warn
    if (event.includes('failed') || event.includes('error') || event.includes('exceeded')) {
      return 'warn';
    }
    // Budget warnings → warn
    if (event.includes('warning')) {
      return 'warn';
    }
    // Completion events → debug (less noisy)
    if (event.includes('completed') || event.includes('stopped')) {
      return 'debug';
    }
    // Started/created events → info
    return 'info';
  }

  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string, meta?: Record<string, unknown>): void {
    switch (level) {
      case 'debug':
        this.logger.debug(message, meta);
        break;
      case 'info':
        this.logger.info(message, meta);
        break;
      case 'warn':
        this.logger.warn(message, meta);
        break;
      case 'error':
        this.logger.error(message, undefined, meta);
        break;
    }
  }
}

/** Create and attach event observer */
export function observeEvents(
  eventBus: { on: (event: string, handler: (data?: unknown) => void) => void },
  config?: EventObserverConfig
): () => void {
  const observer = new EventObserver(config);
  return observer.attach(eventBus);
}
