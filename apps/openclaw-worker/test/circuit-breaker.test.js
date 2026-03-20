/**
 * Circuit Breaker Tests — 軍形 Ch.4 (Tactical Dispositions)
 * Tests state machine: CLOSED → OPEN → HALF_OPEN → CLOSED
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// Mock brain-logger to prevent log noise
vi.mock('../lib/brain-logger', () => ({ log: vi.fn() }));

const { isOpen, recordSuccess, recordFailure, getState } = require('../lib/circuit-breaker');

describe('Circuit Breaker', () => {
    let name;
    beforeEach(() => {
        name = `test-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    });

    describe('Initial State', () => {
        it('should start in CLOSED state', () => {
            expect(getState(name)).toBe('CLOSED');
        });

        it('should NOT be open initially', () => {
            expect(isOpen(name)).toBe(false);
        });
    });

    describe('CLOSED → OPEN after 3 failures', () => {
        it('should remain CLOSED after 1 failure', () => {
            recordFailure(name);
            expect(getState(name)).toBe('CLOSED');
            expect(isOpen(name)).toBe(false);
        });

        it('should remain CLOSED after 2 failures', () => {
            recordFailure(name);
            recordFailure(name);
            expect(getState(name)).toBe('CLOSED');
        });

        it('should transition CLOSED → OPEN after 3 failures (FAILURE_THRESHOLD)', () => {
            recordFailure(name);
            recordFailure(name);
            recordFailure(name);
            expect(getState(name)).toBe('OPEN');
            expect(isOpen(name)).toBe(true);
        });
    });

    describe('HALF_OPEN → CLOSED on success', () => {
        it('should not close OPEN breaker on success (only HALF_OPEN → CLOSED)', () => {
            recordFailure(name);
            recordFailure(name);
            recordFailure(name);
            expect(getState(name)).toBe('OPEN');
            // Success on OPEN state only resets failureCount, not state
            recordSuccess(name);
            expect(getState(name)).toBe('OPEN');
        });
    });

    describe('Reset failure count on success', () => {
        it('should reset failure count so next 3 failures are needed again', () => {
            recordFailure(name);
            recordFailure(name);
            recordSuccess(name);
            expect(getState(name)).toBe('CLOSED');
            // Only 1 failure after reset — should stay CLOSED
            recordFailure(name);
            expect(getState(name)).toBe('CLOSED');
        });
    });

    describe('Independent breakers', () => {
        it('should maintain separate state per name', () => {
            const a = `breaker-a-${Date.now()}`;
            const b = `breaker-b-${Date.now()}`;

            recordFailure(a);
            recordFailure(a);
            recordFailure(a);

            expect(getState(a)).toBe('OPEN');
            expect(getState(b)).toBe('CLOSED');
            expect(isOpen(a)).toBe(true);
            expect(isOpen(b)).toBe(false);
        });
    });

    describe('Additional failures while OPEN', () => {
        it('should stay OPEN after more failures', () => {
            recordFailure(name);
            recordFailure(name);
            recordFailure(name);
            expect(getState(name)).toBe('OPEN');
            recordFailure(name);
            expect(getState(name)).toBe('OPEN');
        });
    });
});
