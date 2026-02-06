# Implementation Plan: Vibe Analytics (DevOps Metrics)

**Status:** Draft
**Priority:** High
**Context:** `vibe-analytics`
**Goal:** Implement a lightweight engineering metrics engine (DORA, Cycle Time) for the `vibe-dev` ecosystem.

## Phases

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1** | [Setup & Infrastructure](./phase-1-setup-and-infrastructure.md) | Pending |
| **Phase 2** | [GitHub GraphQL Client](./phase-2-github-graphql-client.md) | Pending |
| **Phase 3** | [Metrics Calculation Engine](./phase-3-metrics-calculation-engine.md) | Pending |
| **Phase 4** | [CLI Integration & Reporting](./phase-4-cli-integration-and-reporting.md) | Pending |

## Dependencies
- `octokit`
- `@octokit/plugin-paginate-graphql`
- `zod` (for schema validation)
- `commander` (for CLI, likely inherited from `vibe-dev`)

## Key Features
- **DORA Metrics**: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Time to Restore.
- **Velocity Metrics**: Cycle Time, PR Pickup Time, PR Merge Time, PR Size.
- **CLI Command**: `vibe metrics`
- **Output**: JSON & Console Table.
