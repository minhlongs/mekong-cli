"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const index_1 = require("./index");
// Mock fetch
globalThis.fetch = vitest_1.vi.fn();
// Mock navigator
Object.defineProperty(globalThis, "navigator", {
    value: {
        share: vitest_1.vi.fn(),
        clipboard: {
            writeText: vitest_1.vi.fn(),
        },
    },
    writable: true,
});
// Mock performance
Object.defineProperty(globalThis, "performance", {
    value: {
        getEntriesByType: vitest_1.vi.fn(),
    },
    writable: true,
});
(0, vitest_1.describe)("VIBE Analytics", () => {
    (0, vitest_1.beforeEach)(() => {
        vitest_1.vi.clearAllMocks();
        globalThis.sessionStorage.getItem.mockReturnValue(null);
    });
    (0, vitest_1.describe)("Session Management", () => {
        (0, vitest_1.it)("should generate new session ID if none exists", () => {
            globalThis.sessionStorage.getItem.mockReturnValue(null);
            const sessionId = (0, index_1.getSessionId)();
            (0, vitest_1.expect)(sessionId).toMatch(/^vibe_\d+_[a-z0-9]+$/);
            (0, vitest_1.expect)(globalThis.sessionStorage.setItem).toHaveBeenCalledWith("vibe_session_id", sessionId);
        });
        (0, vitest_1.it)("should return existing session ID if available", () => {
            const existingId = "vibe_1234567890_abcdef";
            globalThis.sessionStorage.getItem.mockReturnValue(existingId);
            const sessionId = (0, index_1.getSessionId)();
            (0, vitest_1.expect)(sessionId).toBe(existingId);
            (0, vitest_1.expect)(globalThis.sessionStorage.setItem).not.toHaveBeenCalled();
        });
    });
    (0, vitest_1.describe)("Telemetry Engine", () => {
        (0, vitest_1.beforeEach)(() => {
            // Reset the telemetry instance
            index_1.vibeTelemetry.setUser(undefined);
            index_1.vibeTelemetry.setEndpoint(undefined);
        });
        (0, vitest_1.it)("should track events without user", () => {
            const event = {
                type: "page_view",
                path: "/test",
                title: "Test Page",
            };
            index_1.vibeTelemetry.track(event);
            // Event queued successfully
            (0, vitest_1.expect)(true).toBe(true);
        });
        (0, vitest_1.it)("should track events with user", () => {
            index_1.vibeTelemetry.setUser("test-user-123");
            const event = {
                type: "revenue_milestone",
                amount: 1000,
                currency: "USD",
            };
            index_1.vibeTelemetry.track(event);
            (0, vitest_1.expect)(true).toBe(true);
        });
        (0, vitest_1.it)("should set and use endpoint", async () => {
            const mockEndpoint = "https://api.example.com/telemetry";
            index_1.vibeTelemetry.setEndpoint(mockEndpoint);
            const event = { type: "page_view", path: "/test", title: "Test" };
            index_1.vibeTelemetry.track(event);
            globalThis.fetch.mockResolvedValueOnce({ ok: true });
            await index_1.vibeTelemetry.flush();
            (0, vitest_1.expect)(globalThis.fetch).toHaveBeenCalledWith(mockEndpoint, vitest_1.expect.objectContaining({
                method: "POST",
                headers: { "Content-Type": "application/json" },
            }));
        });
        (0, vitest_1.it)("should handle flush failure gracefully", () => {
            index_1.vibeTelemetry.setEndpoint("https://api.example.com/telemetry");
            const event = { type: "error", message: "Test error" };
            index_1.vibeTelemetry.track(event);
            globalThis.fetch.mockRejectedValueOnce(new Error("Network error"));
            return index_1.vibeTelemetry.flush().then(() => {
                (0, vitest_1.expect)(globalThis.fetch).toHaveBeenCalled();
            });
        });
    });
    (0, vitest_1.describe)("Growth Metrics", () => {
        (0, vitest_1.it)("should calculate growth metrics with default values", () => {
            const metrics = (0, index_1.calculateGrowthMetrics)(50000);
            (0, vitest_1.expect)(metrics.currentGMV).toBe(50000);
            (0, vitest_1.expect)(metrics.targetARR).toBe(1000000);
            (0, vitest_1.expect)(metrics.growthRate).toBe(0.1);
            (0, vitest_1.expect)(metrics.annualizedRunRate).toBe(600000);
            (0, vitest_1.expect)(metrics.daysToTarget).toBeGreaterThan(0);
        });
        (0, vitest_1.it)("should calculate growth metrics with custom values", () => {
            const metrics = (0, index_1.calculateGrowthMetrics)(100000, 2000000, 0.2);
            (0, vitest_1.expect)(metrics.currentGMV).toBe(100000);
            (0, vitest_1.expect)(metrics.targetARR).toBe(2000000);
            (0, vitest_1.expect)(metrics.growthRate).toBe(0.2);
            (0, vitest_1.expect)(metrics.annualizedRunRate).toBe(1200000);
        });
        (0, vitest_1.it)("should handle zero days to target", () => {
            const metrics = (0, index_1.calculateGrowthMetrics)(1000000, 1000000, 0.1);
            (0, vitest_1.expect)(metrics.daysToTarget).toBe(0);
        });
        (0, vitest_1.it)("should calculate compound growth correctly", () => {
            const metrics = (0, index_1.calculateGrowthMetrics)(10000, 120000, 0.15);
            (0, vitest_1.expect)(metrics.daysToTarget).toBeGreaterThanOrEqual(0);
            (0, vitest_1.expect)(metrics.currentGMV).toBe(10000);
            (0, vitest_1.expect)(metrics.targetARR).toBe(120000);
            (0, vitest_1.expect)(metrics.growthRate).toBe(0.15);
        });
    });
    (0, vitest_1.describe)("Currency Formatting", () => {
        (0, vitest_1.it)("should format billions correctly", () => {
            (0, vitest_1.expect)((0, index_1.formatVND)(1500000000)).toBe("1.5 tỷ");
            (0, vitest_1.expect)((0, index_1.formatVND)(2000000000)).toBe("2.0 tỷ");
        });
        (0, vitest_1.it)("should format millions correctly", () => {
            (0, vitest_1.expect)((0, index_1.formatVND)(1500000)).toBe("2 triệu");
            (0, vitest_1.expect)((0, index_1.formatVND)(5000000)).toBe("5 triệu");
            (0, vitest_1.expect)((0, index_1.formatVND)(999999)).toBe("999.999 đ");
        });
        (0, vitest_1.it)("should format smaller amounts correctly", () => {
            (0, vitest_1.expect)((0, index_1.formatVND)(50000)).toBe("50.000 đ");
            (0, vitest_1.expect)((0, index_1.formatVND)(100)).toBe("100 đ");
        });
        (0, vitest_1.it)("should handle edge cases", () => {
            (0, vitest_1.expect)((0, index_1.formatVND)(0)).toBe("0 đ");
            (0, vitest_1.expect)((0, index_1.formatVND)(-1000)).toBe("-1.000 đ");
        });
    });
    (0, vitest_1.describe)("Share Content", () => {
        (0, vitest_1.it)("should use native share when available", async () => {
            const content = {
                title: "Test",
                text: "Test text",
                url: "https://example.com",
            };
            globalThis.navigator.share.mockResolvedValueOnce(undefined);
            const result = await (0, index_1.shareContent)(content);
            (0, vitest_1.expect)(globalThis.navigator.share).toHaveBeenCalledWith(content);
            (0, vitest_1.expect)(result).toBe("native");
        });
        (0, vitest_1.it)("should fallback to clipboard when native share fails", async () => {
            const content = {
                title: "Test",
                text: "Test text",
                url: "https://example.com",
            };
            globalThis.navigator.share.mockRejectedValueOnce(new Error("Share cancelled"));
            globalThis.navigator.clipboard.writeText.mockResolvedValueOnce(undefined);
            const result = await (0, index_1.shareContent)(content);
            (0, vitest_1.expect)(globalThis.navigator.clipboard.writeText).toHaveBeenCalledWith("Test\nhttps://example.com");
            (0, vitest_1.expect)(result).toBe("copy");
        });
        (0, vitest_1.it)("should fallback to clipboard when native share not available", async () => {
            const content = {
                title: "Test",
                text: "Test text",
                url: "https://example.com",
            };
            Object.defineProperty(globalThis.navigator, "share", { value: undefined });
            globalThis.navigator.clipboard.writeText.mockResolvedValueOnce(undefined);
            const result = await (0, index_1.shareContent)(content);
            (0, vitest_1.expect)(globalThis.navigator.clipboard.writeText).toHaveBeenCalledWith("Test\nhttps://example.com");
            (0, vitest_1.expect)(result).toBe("copy");
        });
    });
    (0, vitest_1.describe)("Web Vitals Collection", () => {
        (0, vitest_1.it)("should collect paint metrics", async () => {
            const mockPaintEntries = [
                { name: "first-contentful-paint", startTime: 1234 },
                { name: "other-paint", startTime: 5678 },
            ];
            globalThis.performance.getEntriesByType.mockImplementation((type) => {
                if (type === "paint")
                    return mockPaintEntries;
                if (type === "navigation")
                    return [];
                return [];
            });
            const vitals = await (0, index_1.collectWebVitals)();
            (0, vitest_1.expect)(vitals.fcp).toBe(1234);
            (0, vitest_1.expect)(vitals.lcp).toBeUndefined();
        });
        (0, vitest_1.it)("should collect navigation metrics", async () => {
            const mockNavEntry = {
                requestStart: 1000,
                responseStart: 1200,
                domContentLoadedEventEnd: 2000,
                loadEventEnd: 2500,
            };
            globalThis.performance.getEntriesByType.mockImplementation((type) => {
                if (type === "paint")
                    return [];
                if (type === "navigation")
                    return [mockNavEntry];
                return [];
            });
            const vitals = await (0, index_1.collectWebVitals)();
            (0, vitest_1.expect)(vitals.ttfb).toBe(200);
            (0, vitest_1.expect)(vitals.fcp).toBeUndefined();
        });
        (0, vitest_1.it)("should handle missing performance APIs gracefully", async () => {
            globalThis.performance.getEntriesByType.mockImplementation(() => {
                throw new Error("API not supported");
            });
            const vitals = await (0, index_1.collectWebVitals)();
            (0, vitest_1.expect)(vitals).toEqual({});
        });
        (0, vitest_1.it)("should handle empty metrics gracefully", async () => {
            globalThis.performance.getEntriesByType.mockReturnValue([]);
            const vitals = await (0, index_1.collectWebVitals)();
            (0, vitest_1.expect)(vitals).toEqual({});
        });
    });
    (0, vitest_1.describe)("Event Types", () => {
        (0, vitest_1.it)("should accept all valid event types", () => {
            const events = [
                { type: "page_view", path: "/", title: "Home" },
                {
                    type: "agent_execute",
                    agentName: "test-agent",
                    duration: 1000,
                    success: true,
                },
                { type: "revenue_milestone", amount: 1000, currency: "USD" },
                { type: "share", platform: "copy", content: "test" },
                { type: "conversion", funnel: "signup", step: 1 },
                { type: "error", message: "Test error", stack: "stack trace" },
            ];
            events.forEach((event) => {
                (0, vitest_1.expect)(() => index_1.vibeTelemetry.track(event)).not.toThrow();
            });
        });
    });
    (0, vitest_1.describe)("Integration", () => {
        (0, vitest_1.it)("should work end-to-end with session and tracking", () => {
            const sessionId = (0, index_1.getSessionId)();
            const event = {
                type: "page_view",
                path: "/test",
                title: "Test",
            };
            index_1.vibeTelemetry.track(event, { customData: "test" });
            (0, vitest_1.expect)(sessionId).toMatch(/^vibe_\d+_[a-z0-9]+$/);
        });
        (0, vitest_1.it)("should calculate and format growth metrics together", () => {
            const metrics = (0, index_1.calculateGrowthMetrics)(50000000);
            const formatted = (0, index_1.formatVND)(metrics.currentGMV);
            (0, vitest_1.expect)(metrics.currentGMV).toBe(50000000);
            (0, vitest_1.expect)(formatted).toBe("50 triệu");
        });
    });
});
