/**
 * Integration tests for events.ts with observability.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { eventBus, emit, on, attachObservability } from './events.js';

describe('Events with Observability', () => {
  beforeEach(() => {
    // Clean event bus before each test
    eventBus.removeAllListeners();
  });

  afterEach(() => {
    eventBus.removeAllListeners();
  });

  it('should emit events successfully', () => {
    const handler = vi.fn();
    on('engine:started', handler);
    emit('engine:started', { providers: ['openai'] });
    expect(handler).toHaveBeenCalledWith({ providers: ['openai'] });
  });

  it('should handle multiple event types', () => {
    const events: string[] = [];
    const handler = (event: string) => (data?: unknown) => {
      events.push(event);
    };

    on('task:created', handler('task:created'));
    on('task:completed', handler('task:completed'));

    emit('task:created', { id: '1' });
    emit('task:completed', { id: '1' });

    expect(events).toEqual(['task:created', 'task:completed']);
  });

  it('should attach observability without errors', () => {
    expect(() => attachObservability()).not.toThrow();
  });

  it('should log events after attaching observability', () => {
    attachObservability();

    const handler = vi.fn();
    on('agent:spawned', handler);
    emit('agent:spawned', { agentId: 'test-agent' });

    expect(handler).toHaveBeenCalledWith({ agentId: 'test-agent' });
  });
});
