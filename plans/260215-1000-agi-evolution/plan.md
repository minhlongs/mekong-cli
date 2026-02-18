# AGI Evolution Plan - Phase 1: Perception

> **"Tướng thông cửu biến chi lợi"** — He who masters adaptation, controls the battlefield.

## Context
Based on `AGI_EVOLUTION_PLAN.md`, this plan focuses on **Phase 1: PERCEPTION**. The goal is to make the system UNDERSTAND itself and its environment through self-awareness engines and context intelligence.

## 1. Perception Engine (Week 1-2)

### 1.1 Codebase Self-Awareness Engine
- [x] **Auto-Indexer**: Scan monorepo → build dependency graph (Implemented in `packages/core/perception`)
- [x] **Health Dashboard**: Real-time build status, test coverage (Implemented in `packages/core/perception`)
- [x] **Impact Analyzer**: Predict change impact (Implemented in `packages/core/perception`)

### 1.2 Context Intelligence
- [x] **Session Memory**: Persist conversation context (Implemented in `packages/core/perception`)
- [x] **Mission History DB**: Store mission results and error patterns (Implemented in `packages/core/perception`)
- [ ] **Pattern Recognition**: Auto-detect recurring errors (Pending Phase 2)

## Architecture
Target directory: `packages/core/perception/` (New structure)

## Execution Steps

### Step 1: Foundation Setup
- [x] Create `packages/core/perception/` directory structure
- [x] Initialize TypeScript configuration for the new module

### Step 2: Auto-Indexer Implementation
- [x] Implement `indexer.ts` to scan the monorepo
- [x] specific focus on `apps/` and `packages/` dependencies

### Step 3: Health Monitor
- [x] Implement `health-monitor.ts` to check build status and TS errors
- [x] Implement `dashboard.ts` to aggregate data from Indexer and HealthMonitor

### Step 4: Context & Memory
- [x] Implement `session-memory.ts` and `mission-history.ts`

### Step 5: Integration
- [x] Create CLI script to display Health Dashboard (`scripts/agi-dashboard.js`)
- [ ] Integrate Session Memory and Mission History into `openclaw-worker`

## Success Criteria
- [x] Perception engine can generate a dependency graph of the current monorepo
- [x] Health dashboard reports current status of all projects
- [x] Session memory persists across CLI restarts
