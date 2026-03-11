/**
 * Mission Complexity Classifier Tests — 始計 Ch.1 (Laying Plans)
 * Tests 風林火山 routing: GIÓ (simple) / RỪNG (medium) / LỬA (complex)
 */
import { describe, it, expect, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// Mock dependencies
vi.mock('../lib/brain-logger', () => ({ log: vi.fn() }));

const {
    classifyComplexity,
    classifyContentTimeout,
    getTimeoutForComplexity,
    detectIntent,
} = require('../lib/mission-complexity-classifier');

const config = require('../config');

describe('Mission Complexity Classifier', () => {
    describe('classifyComplexity', () => {
        it('should return explicit complexity when provided', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'anything', complexity: 'complex' }, 'well')).toBe('complex');
            expect(classifyComplexity({ id: 'test', cmd: 'anything', complexity: 'simple' }, 'well')).toBe('simple');
            expect(classifyComplexity({ id: 'test', cmd: 'anything', complexity: 'strategic' }, 'well')).toBe('strategic');
        });

        it('should classify "refactor" as complex', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Refactor the auth module' }, 'well')).toBe('complex');
        });

        it('should classify "security audit" as complex', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Run security audit on the API' }, 'well')).toBe('complex');
        });

        it('should classify "feature" as medium', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Add a new feature for user profiles' }, 'well')).toBe('medium');
        });

        it('should classify "implement" as medium', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Implement dark mode toggle' }, 'well')).toBe('medium');
        });

        it('should classify unknown keywords as simple', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Fix typo in readme' }, 'well')).toBe('simple');
        });

        it('should classify "migrate" as complex', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Migrate from REST to GraphQL' }, 'well')).toBe('complex');
        });

        it('should classify "deep scan" as complex', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Deep scan all code for bugs' }, 'well')).toBe('complex');
        });

        it('should classify "testing" as medium', () => {
            expect(classifyComplexity({ id: 'test', cmd: 'Add testing for auth module' }, 'well')).toBe('medium');
        });
    });

    describe('classifyContentTimeout', () => {
        it('should return simple complexity for basic text', () => {
            const result = classifyContentTimeout('Fix typo in header');
            expect(result.complexity).toBe('simple');
            expect(result.timeout).toBe(config.TIMEOUT_SIMPLE);
        });

        it('should return complex complexity for refactoring', () => {
            const result = classifyContentTimeout('Refactor entire auth architecture');
            expect(result.complexity).toBe('complex');
            expect(result.timeout).toBe(config.TIMEOUT_COMPLEX);
        });

        it('should return medium complexity for feature work', () => {
            const result = classifyContentTimeout('Implement new api endpoint');
            expect(result.complexity).toBe('medium');
            expect(result.timeout).toBe(config.TIMEOUT_MEDIUM);
        });

        it('should handle empty string', () => {
            const result = classifyContentTimeout('');
            expect(result.complexity).toBe('simple');
            expect(result.timeout).toBe(config.TIMEOUT_SIMPLE);
        });

        it('should be case-insensitive', () => {
            const result = classifyContentTimeout('SECURITY AUDIT needed');
            expect(result.complexity).toBe('complex');
        });
    });

    describe('getTimeoutForComplexity', () => {
        it('should return TIMEOUT_SIMPLE for simple', () => {
            expect(getTimeoutForComplexity('simple')).toBe(config.TIMEOUT_SIMPLE);
        });

        it('should return TIMEOUT_MEDIUM for medium', () => {
            expect(getTimeoutForComplexity('medium')).toBe(config.TIMEOUT_MEDIUM);
        });

        it('should return TIMEOUT_COMPLEX for complex', () => {
            expect(getTimeoutForComplexity('complex')).toBe(config.TIMEOUT_COMPLEX);
        });

        it('should default to TIMEOUT_SIMPLE for unknown complexity', () => {
            expect(getTimeoutForComplexity('unknown')).toBe(config.TIMEOUT_SIMPLE);
        });
    });

    describe('detectIntent', () => {
        it('should detect BUILD intent for generic tasks', () => {
            expect(detectIntent('Create a new dashboard page')).toBe('BUILD');
        });

        it('should detect FIX intent for bug reports', () => {
            expect(detectIntent('Fix the login bug')).toBe('FIX');
        });

        it('should detect REVIEW intent for audits', () => {
            expect(detectIntent('Review the code quality')).toBe('REVIEW');
        });

        it('should detect RESEARCH intent', () => {
            expect(detectIntent('Research best practices for caching')).toBe('RESEARCH');
        });

        it('should detect PLAN intent', () => {
            expect(detectIntent('Plan the new dashboard layout')).toBe('PLAN');
        });

        it('should detect DEBUG intent for investigation', () => {
            expect(detectIntent('Investigate why the API is slow')).toBe('DEBUG');
        });

        it('should detect STRATEGIC intent for architecture', () => {
            expect(detectIntent('Architecture redesign for microservices')).toBe('STRATEGIC');
        });

        it('should detect MULTI_FIX when multiple bug words present', () => {
            expect(detectIntent('Fix the bug and error handling')).toBe('MULTI_FIX');
        });

        it('should detect Vietnamese keywords', () => {
            expect(detectIntent('Sửa lỗi đăng nhập')).toBe('FIX');
            expect(detectIntent('Tìm hiểu về caching')).toBe('RESEARCH');
            expect(detectIntent('Kế hoạch mới')).toBe('PLAN');
        });

        it('should handle empty string', () => {
            expect(detectIntent('')).toBe('BUILD');
        });
    });
});
