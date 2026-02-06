# Phase 3: Metrics Calculation Engine

**Priority:** High
**Status:** Pending

## Overview
Implement the core logic to transform raw GitHub data into DORA and Velocity metrics. This is a pure transformation layer (Data -> Metrics).

## Requirements
- Calculate **DORA Metrics**:
  - Deployment Frequency (Daily/Weekly)
  - Lead Time for Changes (Commit to Merge/Release)
  - Change Failure Rate (Approximate via hotfix conventions)
  - Time to Restore (Approximate via incident conventions)
- Calculate **Velocity Metrics**:
  - Cycle Time (Pickup + Review + Merge)
  - PR Size
- Support aggregation by time periods (e.g., Last 30 days).

## Architecture
- **`src/lib/metrics-engine.ts`**: Core calculation logic.
- **`src/lib/dora.ts`**: Specific DORA calculators.
- **`src/lib/velocity.ts`**: Specific Velocity calculators.
- **`src/types/metrics.ts`**: Metric result definitions.

## Implementation Steps

1.  **Define Metric Interfaces**
    - `MetricResult`: `{ value: number, unit: string, label: string }`.
    - `Report`: `{ period: DateRange, dora: DoraMetrics, velocity: VelocityMetrics }`.

2.  **Implement Velocity Logic**
    - `calculatePickupTime(pr)`: `firstReview.createdAt` - `pr.createdAt`.
    - `calculateReviewTime(pr)`: `mergedAt` - `firstReview.createdAt`.
    - `calculateCycleTime(pr)`: `mergedAt` - `firstCommit.committedDate`.

3.  **Implement DORA Logic**
    - `calculateDeploymentFrequency(releases, period)`: Count / Days.
    - `calculateLeadTime(prs)`: Median of `mergedAt` - `firstCommit`.
    - `calculateFailureRate(releases)`: (Hotfixes / Total Releases) * 100.

4.  **Unit Testing**
    - Create fixtures of raw GitHub data.
    - Write comprehensive tests to verify calculations (e.g., ensure weekend handling if relevant, though strictly time-based is simpler first).

## Success Criteria
- Correctly calculates metrics for a given set of mock data.
- Handles edge cases (e.g., PR with no reviews, PR merged without commits).
