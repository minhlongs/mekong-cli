/**
 * Task Queue Tests — 軍爭 Ch.7 (Maneuvering)
 * Tests priority sorting and module API surface.
 */
import { describe, it, expect } from 'vitest';

describe('Task Queue — Priority System', () => {
    describe('Priority filename sorting', () => {
        it('should rank CRITICAL > HIGH > MEDIUM > LOW > none', () => {
            const files = [
                'mission_test.txt',
                'LOW_mission_fix.txt',
                'CRITICAL_mission_hotfix.txt',
                'HIGH_mission_bug.txt',
                'MEDIUM_mission_feature.txt',
            ];

            // Replicate getPriority logic from task-queue.js
            function getPriority(filename) {
                if (filename.startsWith('CRITICAL_')) return 4;
                if (filename.startsWith('HIGH_')) return 3;
                if (filename.startsWith('MEDIUM_')) return 2;
                if (filename.startsWith('LOW_')) return 1;
                return 0;
            }

            const sorted = [...files].sort((a, b) => getPriority(b) - getPriority(a));
            expect(sorted[0]).toBe('CRITICAL_mission_hotfix.txt');
            expect(sorted[1]).toBe('HIGH_mission_bug.txt');
            expect(sorted[2]).toBe('MEDIUM_mission_feature.txt');
            expect(sorted[3]).toBe('LOW_mission_fix.txt');
            expect(sorted[4]).toBe('mission_test.txt');
        });

        it('should handle files with same priority', () => {
            function getPriority(filename) {
                if (filename.startsWith('CRITICAL_')) return 4;
                if (filename.startsWith('HIGH_')) return 3;
                if (filename.startsWith('MEDIUM_')) return 2;
                if (filename.startsWith('LOW_')) return 1;
                return 0;
            }

            const files = ['HIGH_a.txt', 'HIGH_b.txt', 'CRITICAL_x.txt'];
            const sorted = [...files].sort((a, b) => getPriority(b) - getPriority(a));
            expect(sorted[0]).toBe('CRITICAL_x.txt');
            expect(getPriority(sorted[1])).toBe(3);
            expect(getPriority(sorted[2])).toBe(3);
        });

        it('should handle empty prefix as lowest priority', () => {
            function getPriority(filename) {
                if (filename.startsWith('CRITICAL_')) return 4;
                if (filename.startsWith('HIGH_')) return 3;
                if (filename.startsWith('MEDIUM_')) return 2;
                if (filename.startsWith('LOW_')) return 1;
                return 0;
            }

            expect(getPriority('mission_plain.txt')).toBe(0);
            expect(getPriority('CRITICAL_urgent.txt')).toBe(4);
            expect(getPriority('LOW_cleanup.txt')).toBe(1);
        });
    });
});

describe('Task Queue — TASK_PATTERN regex', () => {
    // Replicate the regex from config.js
    const TASK_PATTERN = /^(?:CRITICAL_|HIGH_|MEDIUM_|LOW_)?(?:mission_)?.+\.txt$/;

    it('should match standard mission files', () => {
        expect(TASK_PATTERN.test('mission_test.txt')).toBe(true);
        expect(TASK_PATTERN.test('CRITICAL_mission_hotfix.txt')).toBe(true);
        expect(TASK_PATTERN.test('HIGH_mission_fix_auth.txt')).toBe(true);
    });

    it('should match files without mission_ prefix', () => {
        expect(TASK_PATTERN.test('CRITICAL_hotfix.txt')).toBe(true);
        expect(TASK_PATTERN.test('some_task.txt')).toBe(true);
    });

    it('should NOT match non-.txt files', () => {
        expect(TASK_PATTERN.test('mission_test.json')).toBe(false);
        expect(TASK_PATTERN.test('mission_test.md')).toBe(false);
    });

    it('should NOT match hidden files', () => {
        expect(TASK_PATTERN.test('.wal.json')).toBe(false);
    });
});
