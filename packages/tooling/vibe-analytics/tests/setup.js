"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/**
 * Vitest Test Setup
 */
const vitest_1 = require("vitest");
// Mock global window object for jsdom
(0, vitest_1.beforeAll)(() => {
    // Mock sessionStorage
    const sessionStorageMock = {
        getItem: vitest_1.vi.fn(),
        setItem: vitest_1.vi.fn(),
        removeItem: vitest_1.vi.fn(),
        clear: vitest_1.vi.fn(),
    };
    Object.defineProperty(globalThis, 'sessionStorage', {
        value: sessionStorageMock,
        writable: true,
    });
    // Mock fetch
    Object.defineProperty(globalThis, 'fetch', {
        value: vitest_1.vi.fn(),
        writable: true,
    });
});
(0, vitest_1.afterAll)(() => {
    vitest_1.vi.restoreAllMocks();
});
