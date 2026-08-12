# Plan A: Refactor src/core God-Module

## Context
src/core has 165+ top-level Python modules in one directory.
Hotspots and graph clusters show it as a dense hub with mixed domain/infra concerns.
Import fan-in is high, but organizational boundaries are missing.

## Observations
- src/core mixes auth, billing, planner, executor, verifier, raas, telemetry, memory, signals, governance, webhooks.
- No clear folder or code ownership boundary between core and raas.
- src/core/core_dna.py is a feature gate, not a structural boundary marker.
- Graph clustering already shows core as a dense hub with low separation of concerns.

## Proposal: Splits, not libraries
1. core/orchestrator - planner, executor, verifier, pipeline orchestrator runners.
2. core/agents - agent_base, registry, dispatcher, swarm, binh_phap dispatcher.
3. core/billing - billing, credits, quota, cost estimator/tracker, usage metering.
4. core/memory - memory store adapters, vector memory, memory bridge, memory scope.
5. core/signals - signal emitter, events, feature flags, local store, posthog sink.
6. core/webhooks - webhook delivery, events, schema.
7. core/security - certificate store, device certificate, attestation, command sanitizer.
8. core/config - config, feature gates, core_dna boundary.

Keep src/core as a thin facade or namespace shell if needed for import compatibility.
Existing imports should change slowly; prefer re-exporting from new subpackages first.

## Safety Rails
- No new runtime behavior changes.
- No new DB tables.
- No changes to src/raas, src/api, src/cli initially after the core split.
- Only move modules inside src/core.
- Add __init__.py re-exports to preserve imports.

## Boundaries and Contracts
- core/orchestrator depends on core/memory and core/signals; no direct core/security import.
- core/webhooks depends on core/events.
- core/billing depends on core/config and db.
- core/agents depends on core/orchestrator, not the other way around.
> Created: 2026-07-12
