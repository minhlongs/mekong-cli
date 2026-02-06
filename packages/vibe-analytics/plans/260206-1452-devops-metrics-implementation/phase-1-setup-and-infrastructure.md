# Phase 1: Setup & Infrastructure (Updated)

**Priority:** Critical
**Status:** In Progress

## Overview
Update the existing `@agencyos/vibe-analytics` package to support DevOps metrics calculation. The package currently handles Growth Telemetry; we will add Engineering Metrics capabilities alongside it.

## Requirements
- Update `package.json` with new dependencies (`octokit`, `zod`, etc.).
- Update `tsconfig.json` if needed to support new features (target ES2022 preferred for top-level await if possible, but ES2020 is acceptable).
- Create directory structure for new modules, preferably namespaced to avoid confusion with growth analytics.

## Dependencies to Add
- `octokit`: For GitHub API interaction.
- `@octokit/plugin-paginate-graphql`: For efficient data fetching.
- `zod`: For schema validation (already in use in many modern stacks, good to add).
- `commander`: For CLI (check if already used or if we need to add it).
- `chalk`, `cli-table3`: For CLI output.

## Implementation Steps

1.  **Update `package.json`**
    - Add dependencies:
      - `octokit`
      - `@octokit/plugin-paginate-graphql`
      - `zod`
      - `commander`
      - `chalk`
      - `cli-table3`
      - `@types/octokit` (if needed, usually included)

2.  **Directory Structure**
    - We will organize the new features under `src/devops/` to keep them separate from existing `src/growth.ts`, `src/telemetry.ts` etc.
    - `src/devops/client/`: GitHub API client.
    - `src/devops/engine/`: Metrics calculation logic.
    - `src/devops/cli/`: CLI commands for devops metrics.
    - `src/devops/types/`: Types specific to devops metrics.

3.  **Configuration**
    - Verify `tsconfig.json` settings are compatible.

## Success Criteria
- `npm install` runs successfully with new dependencies.
- New directories created.
- Existing tests still pass.
