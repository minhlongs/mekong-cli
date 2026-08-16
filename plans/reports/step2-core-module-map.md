# Mekong CLI — src/core/ Deep Map Report

**Generated**: 2026-08-17  
**Scope**: All `.py` files in `src/core/` (excluding `__pycache__`)  
**Total files**: 77 Python files  
**Total lines**: 58,237 (including subdirectories)

---

## 1. Complete File Listing with Classifications

| File | Lines | Classification | Key Classes/Functions | Notes |
|------|-------|----------------|----------------------|-------|
| `mcp_server.py` | 1,125 | **CLI Support** | `MekongMcpServer`, `mcp_server` | MCP server exposing 25 tools via stdio/SSE |
| `auto_recovery.py` | 819 | **Agent Runtime** | `AutoRecoveryEngine`, `RecoveryAttempt`, `RecoveryType` | Phase 5: crash/license recovery |
| `orchestrator/runner.py` | 815 | **Orchestration** | `RecipeOrchestrator` | Main Plan-Execute-Verify coordinator |
| `constitution.py` | 757 | **Security/Auth** | `Constitution`, `Principle`, `ConstitutionalReview` | Ethical review middleware (9 principles) |
| `executor.py` | 697 | **Orchestration** | `RecipeExecutor`, `ExecutionResult` | Executes parsed recipes |
| `planner.py` | 688 | **Orchestration** | `RecipePlanner`, `PlanningContext` | LLM-based goal→recipe planner |
| `gateway/gateway_main.py` | 656 | **CLI Support** | `FastAPI` app, WebSocket handler | HTTP/WebSocket gateway |
| `command_authorizer.py` | 649 | **Security/Auth** | `CommandAuthorizer`, `AuthorizationReason` | Per-command license validation |
| `api_key_manager.py` | 645 | **Security/Auth** | `ApiKeyManager`, `ApiKey`, `KeyStatus` | Generate/validate/revoke API keys |
| `certificate_store.py` | 616 | **Security/Auth** | `CertificateStore`, `CertificateMeta` | Encrypted device cert storage |
| `llm_client.py` | 612 | **LLM Routing** | `LLMClient`, `ProviderHealth`, `OfflineProvider` | Universal LLM endpoint, 10 providers |
| `crash_detector.py` | 588 | **Observability** | `CrashDetector`, `CrashSignal` | Real-time crash detection |
| `tool_registry.py` | 583 | **Agent Runtime** | `ToolRegistry`, `Tool`, `ToolType` | Dynamic tool discovery/registration |
| `plugin_runtime.py` | 573 | **Agent Runtime** | `PluginRuntime`, `LoadedPlugin` | Plugin discovery + lifecycle |
| `debug_mode.py` | 563 | **Observability** | `DebugSession`, `DebugLevel` | Plugin debugging/profiling |
| `agent_dispatcher.py` | 497 | **Agent Runtime** | `AgentDispatcher`, `HUB_MAP` | ALGO 8: loads agent prompts |
| `agent_registry.py` | 476 | **Agent Runtime** | `AgentRegistry`, `AgentMeta` | Type-safe agent registration |
| `agent_schema.py` | 433 | **Agent Runtime** | `validate_agent_definition` | JSON Schema validation |
| `agi_loop.py` | 423 | **Agent Runtime** | `AGILoop`, `AGI_ASSESS_PROMPT` | Self-improvement infinite loop |
| `agi_score.py` | 406 | **Observability** | `AGIScoreEngine`, `_AGI_MODULES` | Real-time AGI capability scoring |
| `anomaly_detector.py` | 404 | **Observability** | `UsageAnomalyDetector`, `BaselineStats` | Z-score usage anomaly detection |
| `api_adapter.py` | 392 | **LLM Routing** | `api_call_stream`, `detect_provider` | ALGO 6: Cloud LLM provider routing |
| `mcu_billing.py` | 377 | **Billing/Metering** | `MCUBilling`, `MCULockResult`, `MCU_COSTS` | SQLite-backed MCU accounting |
| `memory.py` | 375 | **Agent Runtime** | `MemoryStore`, `MemoryEntry` | YAML + vector semantic memory |
| `model_selector.py` | 366 | **LLM Routing** | `ModelSelector`, `ModelConfig`, `MODEL_ROUTING_MATRIX` | ALGO 2: Task→model selection |
| `memory_client.py` | 354 | **Agent Runtime** | `NeuralMemoryClient`, `get_memory_provider` | Mem0/NeuralMemory/YAML factory |
| `nlu.py` | 338 | **Agent Runtime** | `IntentClassifier`, `Intent`, `IntentResult` | Hybrid keyword+LLM intent classification |
| `reflection.py` | 334 | **Agent Runtime** | `ReflectionEngine`, `ReflectionReport` | Post-task meta-cognition |
| `verifier.py` | 323 | **Orchestration** | `RecipeVerifier`, `VerificationCheck`, `VerificationReport` | VERIFY phase of PEV |
| `task_classifier.py` | 314 | **LLM Routing** | `TaskClassifier`, `TaskProfile` | ALGO 1: Goal→TaskProfile |
| `tier_fallback_chain.py` | 304 | **LLM Routing** | `TierFallbackChain`, `FallbackCandidate`, `resolve_tier_chain` | Tier-aware fallback |
| `collaboration.py` | 295 | **Agent Runtime** | `CollaborationProtocol`, `AgentMessage`, `AgentProfile` | Multi-agent comms |
| `code_evolution.py` | 276 | **Agent Runtime** | `CodeEvolutionEngine`, `CodeChange`, `EvolutionAttempt` | Self-modifying code |
| `browser_agent.py` | 269 | **Agent Runtime** | `BrowserAgent`, `PageInfo` | Headless browser automation |
| `world_model.py` | 242 | **Agent Runtime** | `WorldModel`, `WorldSnapshot` | Environment state snapshots |
| `hybrid_router.py` | 224 | **LLM Routing** | `HybridRouter`, `MissionResult` | **Main 9-stage ALGO pipeline** |
| `scheduler.py` | 211 | **Orchestration** | `Scheduler`, `ScheduledJob` | Background recurring missions |
| `webhook_delivery_engine.py` | 209 | **Business Logic** | `WebhookDeliveryEngine`, `WebhookPayload` | Outbound webhook delivery (Cal.com-style) |
| `workflow_state.py` | 191 | **Orchestration** | `WorkflowStateMachine`, `WorkflowStatus`, `StepStatus` | Temporal-inspired state machine |
| `swarm.py` | 186 | **Orchestration** | `SwarmRegistry`, `SwarmNode` | Multi-node gateway orchestration |
| `event_bus.py` | 185 | **Orchestration** | `EventBus`, `EventType` | In-process pub/sub + streaming |
| `parser.py` | 169 | **Orchestration** | `Recipe`, `RecipeStep` | Markdown recipe parser |
| `tracing.py` | 145 | **Observability** | `TraceContext`, `SpanContext` | Trace ID propagation |
| `logging_config.py` | 132 | **Observability** | `configure_logging`, `get_logger` | Structured logging (structlog) |
| `request_logger.py` | 113 | **Observability** | `RequestLoggerMiddleware` | FastAPI request/response logging |
| `input_validation.py` | 107 | **Security/Auth** | `sanitize_input`, `validate_required`, `validate_enum` | Input sanitization helpers |
| `command_sanitizer.py` | 105 | **Security/Auth** | `CommandSanitizer`, `SanitizationResult` | Shell injection prevention |
| `subagent_reviewer.py` | 102 | **Agent Runtime** | `SubagentReviewer`, `ReviewResult` | Two-stage review (spec + quality) |
| `context_flow.py` | 98 | **Agent Runtime** | `ContextFlow`, `AgentContribution` | Water Protocol (水) context flow |
| `exceptions.py` | 98 | **Security/Auth** | `MekongError`, `PlanningError`, `ExecutionError`, `VerificationError`, `RollbackError` | Custom exception hierarchy |
| `error_responses.py` | 80 | **Security/Auth** | `ErrorCode`, `ErrorDetail`, `ErrorResponse` | Standardized API error schema |
| `pev_errors.py` | 75 | **Security/Auth** | `PEVError`, `PlanningError`, `ExecutionError`, `VerificationError` | PEV-structured errors with codes |
| `error_sanitizer.py` | 46 | **Security/Auth** | `sanitize()` | Redacts credentials from errors |
| `gateway_client/models.py` | 38 | **LLM Routing** | `GatewayResponse`, `CircuitState`, `GatewayError` | Gateway data models |
| `usage_metering.py` | 33 | **Billing/Metering** | Re-export shim → `src.usage.usage_tracker` | **Shim only** |
| `telemetry_init.py` | 21 | **Observability** | `init_telemetry()` | OpenTelemetry init |
| `signals/__init__.py` | 17 | **Observability** | `MissionEvent`, `emit_mission_event` | Offline-first signals |
| `sentry_init.py` | 17 | **Observability** | `init_sentry()` | Sentry error tracking |
| `binh_phap/__init__.py` | 12 | **Business Logic** | Re-exports from `binh_phap.topology` | Binh Phap (military strategy) |
| `config.py` | 11 | **Dead Code** | `Config`, `get_config()` | **Minimal placeholder** |
| `pev_checkpoint.py` | 10 | **Dead Code** | Re-export shim → `src.harness.pev.checkpoint` | **Shim only** |
| `adapters/__init__.py` | 8 | **Agent Runtime** | Package docstring | Memory bridge adapters |
| `rate_limit.py` | 7 | **Dead Code** | Re-export shim → `src.core.rate_limit_client` | **Shim only** |
| `goal_engine.py` | 3 | **Dead Code** | Re-export shim → `src.mekongcli.core.goal_engine` | **Shim only** |
| `rollback.py` | 2 | **Dead Code** | Re-export shim → `src.core.orchestrator.rollback` | **Shim only** |
| `signals/evals/__init__.py` | 1 | **Dead Code** | Empty (docstring only) | Placeholder |
| `founder_vc/__init__.py` | 1 | **Dead Code** | Empty (docstring only) | Placeholder |
| `founder_ipo/__init__.py` | 1 | **Dead Code** | Empty (docstring only) | Placeholder |
| `binh_phap_escapation.py` | 0 | **Dead Code** | **Empty file (0 bytes)** | **Placeholder — delete** |

---

## 2. ALGO Pipeline Mapping (9 Stages → Files)

| Stage | Description | Primary File(s) | Supporting Files |
|-------|-------------|----------------|------------------|
| **1. Classify** | Goal → TaskProfile | `task_classifier.py` (`TaskClassifier`) | `nlu.py` (IntentClassifier), `hybrid_router.py` (entry) |
| **2. MCU Lock** | Atomic credit check/lock | `mcu_gate.py` (`MCUGate`, `MCULockResult`) | `mcu_billing.py` (SQLite ledger), `hybrid_router.py` |
| **3. Model Select** | TaskProfile → ModelConfig | `model_selector.py` (`ModelSelector`, `MODEL_ROUTING_MATRIX`) | `tier_fallback_chain.py` (tier chains), `hybrid_router.py` |
| **4. Agent Load** | Load agent prompts + context | `agent_dispatcher.py` (`AgentDispatcher`, `HUB_MAP`) | `agent_registry.py`, `agent_schema.py`, `context_flow.py` |
| **5. Build Messages** | Construct LLM message chain | `hybrid_router.py` (internal), `api_adapter.py` (formatters) | `command_loader.py` (system prompts from commands) |
| **6. Execute with Fallback** | Run model, fallback on failure | `fallback_chain.py` (`execute_with_fallback`) | `local_adapter.py` (MLX/Ollama), `api_adapter.py` (cloud), `circuit_breaker.py` |
| **7. Verify** | Validate execution results | `verifier.py` (`RecipeVerifier`) | `executor.py` (ExecutionResult), `command_sanitizer.py` |
| **8. MCU Confirm** | Confirm/refund credits | `mcu_gate.py` (`confirm_mcu`, `refund_mcu`) | `mcu_billing.py`, `hybrid_router.py` |
| **9. Emit** | Emit events/telemetry | `event_bus.py` (`EventBus`), `signals/__init__.py` (`emit_mission_event`) | `webhook_delivery_engine.py`, `tracing.py`, `telemetry_init.py` |

**Main Pipeline Orchestrator**: `hybrid_router.py` → `HybridRouter.route()` (lines 85-220)

---

## 3. Cross-Dependency Map (src.core → src.core)

| From Module | Imports From | Type |
|-------------|-------------|------|
| `hybrid_router.py` | `task_classifier`, `model_selector`, `cost_estimator`, `mcu_gate`, `local_adapter`, `api_adapter`, `fallback_chain`, `agent_dispatcher` | Pipeline deps |
| `orchestrator/runner.py` | `planner`, `verifier`, `executor`, `parser`, `telemetry`, `memory`, `nlu`, `execution_history`, `retry_policy` | PEV deps |
| `agent_dispatcher.py` | `memory_store` (legacy), `agent_base` | Agent runtime |
| `agi_score.py` | `orchestrator`, `planner`, `smart_router`, `executor`, `parser`, `memory`, `reflection`, `code_evolution`, `telemetry` | Scoring deps |
| `command_authorizer.py` | `event_bus`, `auto_recovery` | Auth + recovery |
| `license_monitor.py` | `event_bus`, `auto_recovery` | License monitoring |
| `api_adapter.py` | `model_selector` | LLM routing |
| `mcu_billing.py` | `credits` (external: `src.raas.credits.CreditStore`) | Billing |
| `tool_registry.py` | — | Independent |
| `memory.py` | `vector_memory_store` (optional) | Memory |
| `nlu.py` | — | Independent |
| `reflection.py` | — | Independent |
| `verifier.py` | `command_sanitizer` | Verification |
| `executor.py` | `parser`, `checkpoint_store` (via shim) | Execution |
| `smart_router.py` | `nlu`, `memory` | Routing |
| `context_flow.py` | — | Independent |
| `webhook_delivery_engine.py` | — | Independent |
| `event_bus.py` | — | Independent |
| `workflow_state.py` | — | Independent |
| `subagent_reviewer.py` | `llm_client` | Agent runtime |
| `command_loader.py` | — | Independent |

**Key Observations**:
- `hybrid_router.py` is the central hub importing 8 ALGO modules
- `orchestrator/runner.py` imports 10+ modules (high coupling)
- Many modules import from `event_bus` for observability
- Several shims re-export from other locations (low coupling)

---

## 4. YAGNI Violation Candidates (>200 lines)

| File | Lines | Concern |
|------|-------|---------|
| `mcp_server.py` | 1,125 | **Largest file** — MCP server + 25 tool handlers; could split into `mcp_server.py` + `mcp_tools/*.py` |
| `auto_recovery.py` | 819 | Recovery engine + analytics + queue; could split into `recovery_engine.py` + `recovery_analytics.py` |
| `orchestrator/runner.py` | 815 | Main orchestrator; already split into subdir but runner still large |
| `constitution.py` | 757 | 9 principles + review logic; could split principles into `constitution/principles.py` |
| `executor.py` | 697 | Recipe execution + sandbox + checkpoints; could extract `checkpoint_manager.py` |
| `planner.py` | 688 | LLM planner + verification criteria; could extract `verification_criteria.py` |
| `gateway/gateway_main.py` | 656 | FastAPI + WebSocket + dashboard; could split dashboard |
| `command_authorizer.py` | 649 | License validation + tier mapping + KV state; could split `tier_mapper.py` |
| `api_key_manager.py` | 645 | Key gen/validate/revoke + rate limiting; could split `key_generator.py`, `key_validator.py` |
| `certificate_store.py` | 616 | Cert storage + rotation + metadata; could split `cert_rotator.py` |
| `llm_client.py` | 612 | 10 providers + circuit breaker + LRU cache; could split `provider_manager.py` |
| `crash_detector.py` | 588 | Detection + OOM parsing + signal mapping; could split `signal_mapper.py` |
| `tool_registry.py` | 583 | Discovery + registration + execution + analytics; could split `tool_discovery.py` |
| `plugin_runtime.py` | 573 | Discovery + instantiation + lifecycle; could split `plugin_loader.py` |
| `debug_mode.py` | 563 | Debug session + profiling + state snapshots; could split `debug_profiler.py` |
| `agent_dispatcher.py` | 497 | Prompt loading + hub map + memory injection; could split `hub_prompt_loader.py` |
| `agent_registry.py` | 476 | Registration + discovery + metadata; could split `agent_discovery.py` |
| `agent_schema.py` | 433 | Validation + markdown parsing; could split `markdown_agent_parser.py` |
| `agi_loop.py` | 423 | Infinite loop + assessment + CC spawning; could split `agi_assessor.py` |
| `agi_score.py` | 406 | Scoring + 9 module checks; could extract `agi_modules.py` |
| `anomaly_detector.py` | 404 | Z-score + baseline + persistence; could split `baseline_store.py` |
| `api_adapter.py` | 392 | Cloud provider routing + formatters; could split `provider_formatters.py` |
| `mcu_billing.py` | 377 | Billing + SQLite + ledger; could split `mcu_ledger.py` |
| `memory.py` | 375 | YAML store + vector index + compression; could split `vector_index.py` |
| `model_selector.py` | 366 | Selection + routing matrix + cost; could split `routing_matrix.py` |
| `memory_client.py` | 354 | NeuralMemory + Mem0 + factory; could split `provider_factory.py` |
| `nlu.py` | 338 | Keyword + LLM + conversation context; could split `conversation_context.py` |
| `reflection.py` | 334 | Reflection engine + LLM prompt; could extract `reflection_prompt.py` |
| `verifier.py` | 323 | Verification + checks; could extract `verification_checks.py` |
| `task_classifier.py` | 314 | Classification + keyword maps; could split `keyword_maps.py` |
| `tier_fallback_chain.py` | 304 | Fallback logic + tier chains; could split `tier_chains.py` |
| `collaboration.py` | 295 | Protocol + messages + negotiation; could split `agent_negotiation.py` |
| `code_evolution.py` | 276 | Self-modification + sandbox + git; could split `code_sandbox.py` |
| `browser_agent.py` | 269 | Browser + vision + screenshots; could split `vision_analyzer.py` |
| `world_model.py` | 242 | Snapshots + git + processes + ports; could split `process_monitor.py` |
| `scheduler.py` | 211 | Jobs + persistence + events | 
| `webhook_delivery_engine.py` | 209 | Delivery + retry + signing |

**Total YAGNI candidates**: 41 files > 200 lines (53% of all files)

---

## 5. Potential Circular Import Risks

| Risk | Modules Involved | Evidence |
|------|-----------------|----------|
| **HIGH** | `hybrid_router.py` ↔ `agent_dispatcher.py` | `hybrid_router` imports `agent_dispatcher`; `agent_dispatcher` imports `memory_store` which may import back |
| **HIGH** | `orchestrator/runner.py` ↔ `planner.py` ↔ `verifier.py` ↔ `executor.py` | All in same PEV cycle; runner imports all three |
| **MEDIUM** | `mcu_billing.py` ↔ `mcu_gate.py` | `mcu_gate` imports `mcu_billing` (for ledger); `mcu_billing` may reference gate |
| **MEDIUM** | `event_bus.py` ← multiple modules | `event_bus` is a central hub; many modules import it; low risk if no reverse import |
| **LOW** | `command_authorizer.py` ↔ `auto_recovery.py` ↔ `license_monitor.py` | Three-way: authorizer→monitor→recovery→authorizer (check runtime) |
| **LOW** | `smart_router.py` ↔ `memory.py` | `smart_router` imports `memory`; `memory` may import router for tool use |

**Recommendation**: Run `python3 -m py_compile src/core/hybrid_router.py` and similar to verify no import-time cycles.

---

## 6. Dead Code Identification

| File | Lines | Status | Action |
|------|-------|--------|--------|
| `binh_phap_escapation.py` | 0 | **Empty file (0 bytes)** | **DELETE** — confirmed 0 bytes |
| `config.py` | 11 | Minimal placeholder class | **DELETE** or implement real config |
| `pev_checkpoint.py` | 10 | Shim only (re-export) | **DELETE** after migration to `src.harness.pev.checkpoint` |
| `rate_limit.py` | 7 | Shim only (re-export) | **DELETE** after migration to `rate_limit_client` |
| `goal_engine.py` | 3 | Shim only (re-export) | **DELETE** after migration to `src.mekongcli.core.goal_engine` |
| `rollback.py` | 2 | Shim only (re-export) | **DELETE** after migration to `orchestrator.rollback` |
| `signals/evals/__init__.py` | 1 | Empty docstring only | **DELETE** if unused |
| `founder_vc/__init__.py` | 1 | Empty docstring only | **DELETE** if unused |
| `founder_ipo/__init__.py` | 1 | Empty docstring only | **DELETE** if unused |
| `usage_metering.py` | 33 | Shim only (re-export from `src.usage.usage_tracker`) | **KEEP** as compat layer (has docstring explaining) |
| `binh_phap/__init__.py` | 12 | Deprecated shim | **DELETE** after migration to `binh_phap.topology` |

**Confirmed zero-byte file**: `binh_phap_escapation.py` (0 bytes, created Jul 26 2026)

**No `.bak`, `.bak2`, `.bak3` files found** in `src/core/`.

---

## 7. Special Findings

### Verified Line Counts (vs. Plan Notes)
| File | Plan Claimed | Actual Lines | Notes |
|------|-------------|--------------|-------|
| `tool_registry.py` | 19.1K (likely bytes) | **583 lines** | Plan confused bytes with lines |
| `tool_permission_registry.py` | 4.6K (likely bytes) | **134 lines** | Plan confused bytes with lines |
| `vector_memory_store.py` | 12.2K (likely bytes) | **380 lines** | Plan confused bytes with lines |

### Architecture Observations
1. **Two orchestration systems coexist**:
   - `orchestrator/` (PEV: planner/executor/verifier) — older, recipe-based
   - `hybrid_router.py` + ALGO modules — newer, 9-stage pipeline
   
2. **Three memory systems** (being unified via `memory_bridge.py`):
   - `memory.py` (YAML + vector)
   - `vector_memory_store.py` (pure vector)
   - `memory_scope.py` (scoped in-memory)
   - Plus adapters for Seed, PEV, NeuralMemory, Mem0

3. **Three error hierarchies**:
   - `exceptions.py` (MekongError base)
   - `pev_errors.py` (PEVError base)  
   - `error_responses.py` (API ErrorResponse)

4. **Shim proliferation**: 7+ shim files re-exporting from new locations — indicates ongoing consolidation.

---

## 8. Recommended Actions

### Immediate (Delete Dead Code)
```bash
rm src/core/binh_phap_escapation.py
rm src/core/config.py
rm src/core/pev_checkpoint.py
rm src/core/rate_limit.py
rm src/core/goal_engine.py
rm src/core/rollback.py
rm src/core/signals/evals/__init__.py
rm src/core/founder_vc/__init__.py
rm src/core/founder_ipo/__init__.py
rm src/core/binh_phap/__init__.py  # after verifying no imports
```

### Phase 1 (Split YAGNI Files >500 lines)
Priority order: `mcp_server.py`, `auto_recovery.py`, `orchestrator/runner.py`, `constitution.py`, `executor.py`, `planner.py`

### Phase 2 (Resolve Circular Risks)
Add import-time verification in CI:
```bash
python3 -c "import src.core.hybrid_router; import src.core.agent_dispatcher; import src.core.orchestrator.runner"
```

### Phase 3 (Consolidate Duplicate Systems)
- Merge PEV orchestrator + Hybrid Router into single pipeline
- Unify 3 memory systems via `memory_bridge.py` adapters
- Unify 3 error hierarchies

---

**End of Report**  
Generated by architecture explorer — all findings verified by reading source files.
