# Task: Architecture Audit — Mekong CLI → Autonomous Agent Runtime

## User Request

Perform a repository-wide architecture audit of the EXISTING Mekong CLI codebase.

**DO NOT** rewrite the project.
**DO NOT** create parallel architecture.
**DO NOT** add speculative features.
**DO NOT** delete working functionality.

**Mission**: Transform the EXISTING Mekong CLI into an autonomous agent runtime that can later plug into Buzz as a runtime/extended-arm, while Cloudflare becomes the preferred external execution/distribution layer and MCP + x402/MPP become capability/economic buses.

## Audit Requirements

### Read and Map These First
- AGENTS.md
- CLAUDE.md
- HARNESS.md
- README.md
- dna/
- agents/
- src/harness/
- engine/
- factory/
- cli/
- integrations/
- cloudflare-skills/
- recipes/cloudflare/
- workflows/
- observability/
- specs/
- tests/

### Trace Execution Paths
1. CLI entrypoint
2. Command dispatch
3. Harness
4. PEV
5. Agent registry
6. LLM router
7. Tool execution
8. Verification
9. Observability
10. Billing/payment

### Identify Issues
- duplicated orchestration systems
- dead code
- conflicting agent abstractions
- duplicated CLI surfaces
- duplicated billing/payment concepts
- Cloudflare code that should become adapters
- components that should become core primitives
- components that should be deprecated
- missing interfaces required for Buzz integration
- missing interfaces required for MCP
- missing abstraction required for x402/MPP
- unsafe autonomous execution paths
- missing approval/risk gates
- state/memory ownership problems

### Produce Deliverables
1. CURRENT_ARCHITECTURE.md
2. DEPENDENCY_MAP.md
3. DUPLICATION_MAP.md
4. DEPRECATION_MAP.md
5. AUTONOMY_GAPS.md
6. MEKONG_CORE_CONTRACT.md

**STOP after audit. Do not implement until explicitly instructed.**