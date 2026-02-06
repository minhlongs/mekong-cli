---
title: "Design Vibe Analytics Architecture"
description: "Architecture design and implementation plan for vibe-analytics CLI tool"
status: pending
priority: P2
effort: 3d
branch: master
tags: [architecture, cli, analytics, dora-metrics]
created: 2026-02-06
---

# Vibe Analytics Architecture Plan

## Context
`vibe-analytics` currently exists as a telemetry library. We are expanding it into a CLI tool (or CLI plugin) to track engineering metrics (DORA). This plan outlines the architecture and implementation steps.

## Objectives
- transform `vibe-analytics` into a CLI tool.
- Implement DORA metrics collection (Deployment Freq, Lead Time, Failure Rate, MTTR) + Cycle Time.
- Integrate with GitHub GraphQL API.
- Store data locally for trend analysis.

## Reports
- [Architecture Design](reports/architecture-design.md)

## Phased Implementation Plan

### Phase 1: Foundation & Structure
- [ ] Initialize CLI structure in `vibe-analytics` (bin entry, commander setup).
- [ ] Add necessary dependencies (`commander`, `chalk`, `inquirer`, `ora`).
- [ ] Set up TypeScript configuration for CLI output.
- [ ] Create shared/common utilities (reuse `vibe-dev` patterns where possible).

### Phase 2: Data & Storage Layer
- [ ] Implement `JsonStorageAdapter` (compatible with `vibe-dev`).
- [ ] Define data schema interfaces (Snapshots, Metrics).
- [ ] Create `AnalyticsStorageService` to handle read/write of `.vibe-analytics/data.json`.

### Phase 3: GitHub Integration (Data Ingestion)
- [ ] Port/Import `GitHubClient` from `vibe-dev`.
- [ ] Implement `GitHubIngestionService`.
- [ ] Create GraphQL queries for:
    - Pull Requests (Cycle Time, Lead Time).
    - Releases/Tags (Deployment Frequency).
    - Issues (Incidents/Failures).

### Phase 4: Metrics Engine
- [ ] Implement `MetricsCalculator` class.
- [ ] Logic for **Cycle Time** (Commit to Merge).
- [ ] Logic for **Lead Time for Changes** (Merge/Tag to Deploy).
- [ ] Logic for **Deployment Frequency** (Count per day/week).
- [ ] Logic for **Change Failure Rate** (Incident count / Deploy count).
- [ ] Logic for **MTTR** (Incident Open to Close duration).

### Phase 5: CLI Commands & UI
- [ ] Implement `vibe analytics init` (Config wizard).
- [ ] Implement `vibe analytics sync` (Fetch & Process).
- [ ] Implement `vibe analytics report` (Table/JSON output).
- [ ] Add visualization (basic ASCII charts or simple tables).

### Phase 6: Testing & Polish
- [ ] Unit tests for `MetricsCalculator`.
- [ ] Integration tests for `GitHubIngestionService` (mocked).
- [ ] Documentation update (README.md).

## Unresolved Questions
- Should this strictly be a standalone `vibe-analytics` CLI or a plugin loaded by `vibe-dev`? (Current assumption: Standalone CLI that *can* be called `vibe-analytics`, potentially wrapped by `vibe-dev` later).
