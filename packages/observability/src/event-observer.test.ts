/**
 * Tests for event observer.
 */
import { describe, it, expect, vi } from 'vitest';
import { EventObserver, observeEvents } from '../src/event-observer.js';
import { logger } from '../src/logger.js';

describe('EventObserver', () => {
  it('should create observer with default config', () => {
    const observer = new EventObserver();
    expect(observer).toBeDefined();
  });

  it('should accept custom logger', () => {
    const customLogger = logger.child('test');
    const observer = new EventObserver({ logger: customLogger });
    expect(observer).toBeDefined();
  });

  it('should attach to event bus', () => {
    const observer = new EventObserver();
    const mockEventBus = {
      on: vi.fn(),
    };
    const cleanup = observer.attach(mockEventBus);
    expect(mockEventBus.on).toHaveBeenCalled();
    expect(cleanup).toBeDefined();
  });

  it('should categorize failed events as warn level', () => {
    const observer = new EventObserver();
    // @ts-expect-error - testing private method
    expect(observer.getLogLevel('agent:failed')).toBe('warn');
  });

  it('should categorize completed events as debug level', () => {
    const observer = new EventObserver();
    // @ts-expect-error - testing private method
    expect(observer.getLogLevel('task:completed')).toBe('debug');
  });

  it('should categorize started events as info level', () => {
    const observer = new EventObserver();
    // @ts-expect-error - testing private method
    expect(observer.getLogLevel('engine:started')).toBe('info');
  });
});

describe('observeEvents', () => {
  it('should create and attach observer', () => {
    const mockEventBus = {
      on: vi.fn(),
    };
    const cleanup = observeEvents(mockEventBus);
    expect(mockEventBus.on).toHaveBeenCalled();
    expect(cleanup).toBeDefined();
  });
});
