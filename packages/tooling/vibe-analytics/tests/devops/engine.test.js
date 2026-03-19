"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const metrics_engine_1 = require("../../src/devops/engine/metrics-engine");
(0, vitest_1.describe)("MetricsEngine", () => {
    const engine = new metrics_engine_1.MetricsEngine();
    // Mock Data
    const mockData = {
        pullRequests: [
            {
                number: 1,
                title: "Feature A",
                state: "MERGED",
                createdAt: "2023-10-01T10:00:00Z",
                mergedAt: "2023-10-02T10:00:00Z", // 24h cycle
                closedAt: "2023-10-02T10:00:00Z",
                additions: 100,
                deletions: 50,
                url: "http://github.com/owner/repo/pull/1",
                author: { login: "dev1" },
                commits: {
                    nodes: [
                        { commit: { committedDate: "2023-10-01T09:00:00Z" } } // 1h before PR creation
                    ]
                },
                reviews: {
                    nodes: [
                        { createdAt: "2023-10-01T12:00:00Z", state: "APPROVED", author: { login: "reviewer1" } } // 2h pickup
                    ]
                }
            },
            {
                number: 2,
                title: "Bug Fix B",
                state: "MERGED",
                createdAt: "2023-10-03T10:00:00Z",
                mergedAt: "2023-10-03T12:00:00Z", // 2h cycle
                closedAt: "2023-10-03T12:00:00Z",
                additions: 10,
                deletions: 5,
                url: "http://github.com/owner/repo/pull/2",
                author: { login: "dev2" },
                commits: {
                    nodes: [
                        { commit: { committedDate: "2023-10-03T09:30:00Z" } }
                    ]
                },
                reviews: {
                    nodes: [
                        { createdAt: "2023-10-03T10:30:00Z", state: "APPROVED", author: { login: "reviewer2" } }
                    ]
                }
            }
        ],
        releases: [
            {
                name: "v1.0.0",
                tagName: "v1.0.0",
                createdAt: "2023-10-02T12:00:00Z",
                publishedAt: "2023-10-02T12:00:00Z",
                isPrerelease: false,
                isDraft: false,
                url: "..."
            },
            {
                name: "v1.0.1-hotfix",
                tagName: "v1.0.1-hotfix",
                createdAt: "2023-10-04T12:00:00Z",
                publishedAt: "2023-10-04T12:00:00Z",
                isPrerelease: false,
                isDraft: false,
                url: "..."
            }
        ]
    };
    (0, vitest_1.it)("calculates deployment frequency correctly", () => {
        // 2 releases in 7 days = ~0.28/day
        const report = engine.calculate(mockData, 7);
        (0, vitest_1.expect)(report.dora.deploymentFrequency.value).toBeCloseTo(0.29, 2);
        (0, vitest_1.expect)(report.dora.deploymentFrequency.rating).toBe("High");
    });
    (0, vitest_1.it)("calculates lead time correctly", () => {
        // PR 1: Merge(Oct 2 10:00) - Commit(Oct 1 09:00) = 25 hours
        // PR 2: Merge(Oct 3 12:00) - Commit(Oct 3 09:30) = 2.5 hours
        // Median = (25 + 2.5) / 2 = 13.75 hours = 0.57 days
        const report = engine.calculate(mockData, 7);
        (0, vitest_1.expect)(report.dora.leadTimeForChanges.value).toBeCloseTo(0.57, 2);
        (0, vitest_1.expect)(report.dora.leadTimeForChanges.rating).toBe("Elite");
    });
    (0, vitest_1.it)("calculates change failure rate correctly", () => {
        // 1 hotfix out of 2 releases = 50%
        const report = engine.calculate(mockData, 7);
        (0, vitest_1.expect)(report.dora.changeFailureRate.value).toBe(50.00);
        (0, vitest_1.expect)(report.dora.changeFailureRate.rating).toBe("Low"); // > 15% is Low/Medium
    });
    (0, vitest_1.it)("calculates velocity metrics correctly", () => {
        const report = engine.calculate(mockData, 7);
        // Cycle Time: PR1 (25h), PR2 (2.5h) -> Median 13.75h
        (0, vitest_1.expect)(report.velocity.cycleTime.value).toBe(13.75);
        // Pickup Time:
        // PR1: 12:00 - 10:00 = 2h
        // PR2: 10:30 - 10:00 = 0.5h
        // Median = 1.25h
        (0, vitest_1.expect)(report.velocity.prPickupTime.value).toBe(1.25);
    });
});
