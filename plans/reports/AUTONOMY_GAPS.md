# Mekong CLI — Autonomy Gaps

**Date:** 2026-08-17
**Scope:** Missing interfaces for Buzz + MCP + x402/MPP + autonomous runtime
**Author:** docs-manager

## Summary

The Mekong CLI has built significant autonomous execution infrastructure — a 9-stage LLM routing pipeline, a PEV (Plan-Execute-Verify) orchestrator, AGI self-improvement loop, and swarm node management — but lacks the adapter interfaces required for the target autonomous agent runtime architecture. The target runtime (Buzz → MekongRuntimeAdapter → MekongCore → Goal → Context → Plan → Delegate → Execute → Observe → Verify → Repair → Remember → Commit) cannot be assembled without defining missing contracts. Critical gaps include: no MekongCoreContract interface, no MekongRuntimeAdapter, missing lifecycle primitives (Goal, Context, Delegate, Observe, Repair, Remember, Commit), no approval gates on the AGI self-improvement loop, hardcoded Cloudflare deployment logic, and no standardized payment abstraction. Additionally, duplicate implementations across `src/core/`, `src/harness/`, and `src/daemon/` create maintenance risk and inconsistent behavior.

## Buzz Integration Gaps
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| MekongRuntimeAdapter interface | Does not exist | Must be implemented to bridge Buzz runtime to Mekong Core | No adapter interface found in any report or code scan |
| MekongCoreContract interface | Does not exist | Must define the contract Buzz calls into | No contract interface found in any report or code scan |
| Goal primitive | Not implemented | Required as entry point for autonomous cycles | Missing from PEV lifecycle (step2 report) |
| Context primitive | Partial (memory systems exist) | Must expose unified context interface | 4 memory systems exist but no Buzz-facing state contract |
| Plan primitive | Implemented (PEV orchestrator) | Already exists, needs contract alignment | `src/core/orchestrator/runner.py` has Plan phase |
| Delegate primitive | Not implemented | Required for multi-agent orchestration | No Delegate primitive found in codebase |
| Execute primitive | Implemented (PEV orchestrator) | Already exists | `src/core/orchestrator/runner.py` has Execute phase |
| Observe primitive | Not implemented | Required for runtime monitoring | No Observe primitive found |
| Verify primitive | Implemented (PEV orchestrator) | Already exists | `src/core/orchestrator/runner.py` has Verify phase |
| Repair primitive | Not implemented | Required for failure recovery | Partial in AutoRecoveryEngine but not part of lifecycle |
| Remember primitive | Partial (memory systems exist) | Must expose unified memory interface | `src/core/memory.py` + `src/core/memory_store.py` exist |
| Commit primitive | Not implemented | Required for persisting decisions/state | No Commit primitive found in codebase |

## MCP Gap
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| Standard MCP tool schema | Custom implementation in `src/core/mcp_server.py` (25 tools, stdio/SSE) | Standard JSON-RPC MCP protocol compliance | `mcp_server.py` is custom — no verification of MCP 2025 spec compliance |
| MCP resource protocol | Unknown | Required for capability bus integration | `mcp_server.py` has no evident resource protocol implementation |
| MCP as canonical capability bus | Not established | All tool execution should flow through MCP | Tool execution currently uses `src/core/tool_registry.py` directly, not MCP |

## x402/MPP Gap
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| Payment protocol abstraction | 3 parallel billing implementations (MCU, Engine Billing, Engine Payments) with 5+ Tier enum definitions | Single x402/MPP-compatible abstraction layer | `src/core/mcu_billing.py` (LIVE), `engine/billing/` (DORMANT), `engine/payments/` (PARTIAL) — step8 report confirms fragmentation |
| Stablecoin rail support | Not implemented | Required for economic bus | VietQR/PayOS NOT IMPLEMENTED (step8 report) |
| Unified Tier enum | 5+ parallel Tier definitions | Single canonical `TierKey` enum | `src/seed/config/tiers.py` TierKey is closest to canonical but not enforced |
| Usage metering unification | 2 parallel systems (SQLite CLI vs PostgreSQL RaasLicenseGate) | Single source of truth | step8 report confirms split between `src/usage/usage_tracker.py` and `engine/payments/usage_metering_service.py` |

## Autonomous Execution Gaps
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| Approval gates for high-risk actions | Missing from AGI loop | Required for autonomous safety | `src/core/agi_loop.py` has no approval gate — infinite self-improvement loop with only MAX_CONSECUTIVE_FAILURES=3 and optional MAX_ITERATIONS |
| Risk scoring for decisions | Missing | Required for autonomous safety | No risk scoring module found in codebase |
| Rollback interfaces | Missing from orchestrator | Required for safe execution | `src/core/exceptions.py` defines `RollbackError` but no rollback implementation found in orchestrator |
| agi_loop.py self-improvement | No human approval gate | Must require human approval before spawning CC CLI sessions | `src/core/agi_loop.py` line 211: `_execute(improvement)` spawns CC CLI without gate |
| swarm.py node management | No auth on registration/dispatch | Must require authentication | `src/core/swarm.py` register_node() and dispatch_goal() have no auth checks |
| Blacklist for AGI improvements | Partial (improvement blacklist exists) | Must be enforceable at runtime | `src/core/agi_loop.py` has `_is_blacklisted()` but no external management interface |

## Provider Agnosticism Gaps
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| Cloudflare hardcoding | `src/commands/deploy.py` hardcodes `wrangler deploy` subprocess calls and Cloudflare-specific status checks | Must be adapter-based | deploy.py:47 `deploy_cloudflare()` uses `subprocess(["wrangler", "deploy"])`; deploy.py:187 `check_cloudflare_status()` uses `subprocess(["wrangler", "deployments", "list"])` |
| Buzz hardcoding | None found | Must remain adapter-only | No Buzz references found in codebase — safe |
| LLM provider abstraction | 4 implementations (Claude/Qwen/DeepSeek/OpenAI-compatible) with 1 canonical provider layer | Single canonical adapter | `src/core/providers.py` is canonical; `src/harness/core/router.py` is duplicate |
| Capability provider abstraction | Custom tool registry + MCP server | Standard adapter pattern for MCP/local tools/Cloudflare/filesystem/shell/browser | No unified capability adapter interface |

## State Management Gaps
| Gap | Current State | Required State | Evidence |
|---|---|---|---|
| Canonical memory system | 9 implementations, 2 canonical (memory.py YAML+Vector, memory_store.py JSONL) unified via MemoryBridge | Single canonical MemoryStore interface | step9 report confirms 4 memory systems with 2 canonical backends |
| State interface for Buzz | Unknown | Required for runtime integration | No Buzz-facing state contract found |
| Duplicate telemetry collectors | Identical TelemetryCollector in core and harness | Single source | step9 report confirms `src/core/telemetry_hooks.py` (396 lines) duplicates harness telemetry |
| Duplicate health reporters | Identical HealthReporter in core and harness | Single source | step9 report confirms duplicate health.py implementations |

## Priority Gap List
| Priority | Gap | Effort | Impact |
|---|---|---|---|
| 1 | Define MekongCoreContract interface | LOW | CRITICAL — blocks all Buzz integration |
| 2 | Add approval gates to agi_loop.py | LOW | HIGH — prevents uncontrolled self-modification |
| 3 | Wrap existing billing in payment adapter | MEDIUM | HIGH — enables x402/MPP economic bus |
| 4 | Merge telemetry/health duplicates | LOW | MEDIUM — reduces maintenance burden |
| 5 | Standardize on single memory backend | MEDIUM | HIGH — enables Buzz state contract |
| 6 | Extract Cloudflare adapter from deploy.py | MEDIUM | HIGH — removes hardcoded provider |
| 7 | Add auth to swarm.py node operations | LOW | HIGH — prevents unauthorized swarm access |
| 8 | Define Delegate/Observe/Repair/Remember/Commit primitives | MEDIUM | CRITICAL — completes autonomous lifecycle |
| 9 | Standardize MCP tool schema compliance | MEDIUM | HIGH — enables MCP ecosystem integration |
| 10 | Merge 3 parallel orchestrator hierarchies | HIGH | CRITICAL — reduces divergence risk |

## Speculative Gaps (External Deps)
| Gap | Status | Notes |
|---|---|---|
| Buzz SDK/interface | SPECULATIVE | Buzz runtime contract not publicly available; integration points assumed from target architecture |
| x402/MPP standard | SPECULATIVE | Payment protocol standard still evolving; exact interface shape unknown |
| MCP 2025 spec | LOW CONFIDENCE | Current `mcp_server.py` may already be partially compatible — needs formal verification against spec |

## Confidence Level
HIGH for current-state gaps identified in step2/6/7/8/9/10 reports. LOW for speculative gaps based on assumed external interfaces (Buzz, x402/MPP, MCP 2025 spec). Step5 (CLI entrypoint trace) report was missing from `plans/reports/` — deploy.py was read directly to verify Cloudflare hardcoding.

## Cross-references
- `/Users/macbook/mekong-cli/plans/reports/step2-core-module-map.md` — core module classification
- `/Users/macbook/mekong-cli/plans/reports/step6-llm-router-trace.md` — LLM provider duplication
- `/Users/macbook/mekong-cli/plans/reports/step7-tool-execution-trace.md` — tool registry and security
- `/Users/macbook/mekong-cli/plans/reports/step8-billing-payment-map.md` — billing fragmentation
- `/Users/macbook/mekong-cli/plans/reports/step9-observability-state-map.md` — telemetry/health/memory duplicates
- `/Users/macbook/mekong-cli/plans/reports/step10-issue-classification.md` — issue severity classification
- `/Users/macbook/mekong-cli/src/commands/deploy.py` — Cloudflare hardcoding verification
- `/Users/macbook/mekong-cli/src/core/agi_loop.py` — approval gap verification
- `/Users/macbook/mekong-cli/src/core/swarm.py` — auth gap verification
- `/Users/macbook/mekong-cli/src/core/mcp_server.py` — MCP compliance verification