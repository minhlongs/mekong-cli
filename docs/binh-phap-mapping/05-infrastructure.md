# Phần 5: Infrastructure — Cơ Sở Vận Hành

> Status: DRAFT

## 1. Brainstorm Contract (reuse P1)
Outcome: Infrastructure spec for dual-path auth, Jidoka self-healing, and PEV integration.
Constraints: (1) ZuneF gateway for team, dev fallback Anthropic (2) Zero local model execution (3) Single escalation.py entrypoint
Non-goals: (1) No local Ollama setup (2) No model caching layer
Acceptance: Auth flow diagram + Jidoka hook contract + PEV interface spec

## 2. Auth Architecture — Dual Path

### 2.1 Flow
```
create_provider_for_level(escalation_level)
        |
        v
  _resolve(slug, model)
        |
        +-- ZUNEF env set? --> ZuneF gateway (team token)
        |
        +-- No ZUNEF env --> direct Anthropic (dev's own key)
```

### 2.2 Env Vars (priority order)
FABLE:  ZUNEF_FABLE_BASE_URL > FABLE_BASE_URL > ANTHROPIC_BASE_URL
        ZUNEF_FABLE_MODEL > FABLE_MODEL > default "claude-fable-5"
OPUS:   ZUNEF_OPUS_BASE_URL > OPUS_BASE_URL > ANTHROPIC_BASE_URL
        ZUNEF_OPUS_MODEL > OPUS_MODEL > default "claude-opus-4-8"
KEY:    ZUNEF_API_KEY > ANTHROPIC_API_KEY

### 2.3 Load Balancing Strategy
Round-robin across ZuneF proxy instances via base_url config:
  ZUNEF_FABLE_BASE_URL=https://zunef1.v2/api/v1
  ZUNEF_OPUS_BASE_URL=https://zunef2.v2/api/v1

Provider name auto-detected: "zuneffable" vs "anthropic-fable" for observability.

## 3. Jidoka Self-Healing (src/daemon/jidoka.py)

### 3.1 Error Pattern Registry
{
  "breaking_test":    { severity: HIGH,    auto_fix: "npm test -- --updateSnapshot", rollback: null },
  "schema_change":    { severity: CRITICAL, auto_fix: null,                     rollback: "git revert HEAD" },
  "security_cve":     { severity: CRITICAL, auto_fix: "npm audit fix",          rollback: null },
  "build_failure":    { severity: HIGH,    auto_fix: "npm run build -- --fix",  rollback: null },
  "import_error":     { severity: MEDIUM,  auto_fix: "npm install",             rollback: null },
  "timeout":          { severity: MEDIUM,  auto_fix: "retry with backoff",      rollback: null }
}

### 3.2 Hook Points (3 in vertical chain)
1. POST-COOK:    scan -> auto_fix or escalate
2. POST-TEST:    scan -> auto_fix (snapshot) or escalate
3. POST-DEPLOY:  scan -> rollback or escalate

## 4. PEV Orchestrator Integration

### 4.1 Interface Contract (binh_phap_dispatcher.py)
class BinhPhapDispatcher:
    def next_action() -> dict:
        # returns: action, command, llm, needs_approval, chapter, dimension
    
    def report_result(command, success, output, error, duration_ms)
    
    def report_cycle_lesson(mrr, customers, lessons, adaptations)
    
    def handle_event(event_type, source, data) -> list[dict]

### 4.2 LLM Client Creation
dispatcher.create_llm_client_for_command(cmd)
    -> resolve_llm_provider(level)
    -> create_provider_for_level(level)
    -> LLMClient(providers=[provider])
    -> fallback: local_mlx (Ollama) -> disabled in Fable-only mode

## 5. Trade-off
| A: Direct API | B: Gateway proxy (REC) | C: Hybrid per-model |
|--------------|------------------------|---------------------|
| Simple | Team-controlled cost | Complex routing |
| Dev pays directly | ZuneF settles centrally | Maintainability risk |
| **REC: B** | | |

## 6. Recommendation
Gateway proxy (B) for team operations. Direct Anthropic as explicit dev fallback (opt-in). Round-robin across ZuneF instances for load balancing. Jidoka pattern registry extensible via YAML config.

## 7. Handoff to P6
Delivery: target file structure, migration checklist, acceptance criteria.
