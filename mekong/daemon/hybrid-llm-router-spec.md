# HYBRID LLM ROUTER — ALGORITHM SPEC
# Target: Opus CC CLI implementation
# Stack: Python 3.11+ · FastAPI · Ollama · Anthropic SDK · Google Generative AI
# File: src/core/hybrid_router.py (+ supporting modules)

---

## MODULE MAP

```
src/
├── core/
│   ├── hybrid_router.py        # MAIN: routing engine
│   ├── task_classifier.py      # ALGO 1: classify task → tier
│   ├── model_selector.py       # ALGO 2: select model per agent+tier
│   ├── cost_estimator.py       # ALGO 3: estimate cost before exec
│   ├── mcu_gate.py             # ALGO 4: MCU check/lock/confirm/refund
│   ├── local_adapter.py        # ALGO 5: Ollama local inference
│   ├── api_adapter.py          # ALGO 6: Claude/Gemini/GPT API
│   ├── fallback_chain.py       # ALGO 7: fallback khi model fail
│   └── agent_dispatcher.py     # ALGO 8: dispatch task to agent
agents/
├── cto.md                      # CTO agent prompt
├── cmo.md
├── coo.md
├── cfo.md
├── cs.md
├── sales.md
├── editor.md
└── data.md
```

---

## ALGO 1 — TASK CLASSIFIER
### File: `src/core/task_classifier.py`

**Input:** `goal: str`, `context: dict`
**Output:** `TaskProfile` dataclass

```python
@dataclass
class TaskProfile:
    complexity: Literal["simple", "standard", "complex", "bulk"]
    domain: Literal["code", "creative", "ops", "analysis", "sales", "support"]
    agent_role: Literal["cto", "cmo", "coo", "cfo", "cs", "sales", "editor", "data"]
    requires_reasoning: bool      # True → frontier model
    requires_creativity: bool     # True → không dùng local ops model
    data_sensitivity: Literal["public", "internal", "sensitive"]
    estimated_tokens: int
    mcu_cost: int                 # 1 / 3 / 5 / custom
    preferred_tier: Literal["local", "api_cheap", "api_mid", "api_best"]
```

### Thuật toán phân loại:

```
FUNCTION classify_task(goal, context) → TaskProfile:

  STEP 1 — DOMAIN DETECTION (keyword + embedding match)
  ─────────────────────────────────────────────────────
  domain_signals = {
    "code":     ["code", "implement", "fix", "deploy", "bug", "api", "function",
                 "class", "test", "refactor", "build", "script", "database"],
    "creative": ["write", "content", "blog", "email", "copy", "post", "announce",
                 "marketing", "social", "newsletter", "landing", "viết"],
    "ops":      ["monitor", "check", "status", "health", "backup", "cron",
                 "alert", "restart", "log", "metrics", "uptime"],
    "analysis": ["report", "analyze", "chart", "revenue", "usage", "trend",
                 "summary", "dashboard", "insight", "data", "stats"],
    "sales":    ["upsell", "churn", "follow-up", "lead", "convert", "offer",
                 "trial", "upgrade", "retention", "email sequence"],
    "support":  ["ticket", "user report", "error message", "help", "faq",
                 "refund", "complaint", "không hiểu", "lỗi"],
  }
  domain = argmax(count_signals(goal, domain_signals))

  STEP 2 — AGENT ROLE ASSIGNMENT
  ──────────────────────────────
  domain_to_agent = {
    "code":     "cto",
    "creative": "cmo",    # or "editor" if doc/changelog
    "ops":      "coo",
    "analysis": "data",
    "sales":    "sales",  # or "cfo" if revenue-specific
    "support":  "cs",
  }
  # Override rules:
  IF "changelog" OR "docs" OR "tutorial" IN goal → agent = "editor"
  IF "revenue" OR "polar" OR "invoice" IN goal → agent = "cfo"
  IF "marketing" AND "email" IN goal → agent = "cmo"

  STEP 3 — COMPLEXITY SCORING
  ────────────────────────────
  complexity_score = 0

  # Token estimation heuristic
  word_count = len(goal.split())
  IF word_count < 15:  complexity_score += 1
  IF word_count 15-40: complexity_score += 2
  IF word_count > 40:  complexity_score += 3

  # File scope signals
  IF any(["file", "module", "system", "architecture"] in goal): score += 2
  IF "multiple" OR "several" OR "all" in goal: score += 1

  # Domain weight
  IF domain == "code": score += 2       # code always heavier
  IF domain == "ops":  score -= 1       # ops usually simple
  IF domain == "analysis": score += 1

  # Map score → complexity
  complexity_map = {
    0-2:  "simple",    # 1 MCU
    3-4:  "standard",  # 3 MCU
    5-6:  "complex",   # 5 MCU
    7+:   "complex"    # 5 MCU (hard cap, no "epic" billing)
  }

  STEP 4 — REASONING + CREATIVITY FLAGS
  ───────────────────────────────────────
  requires_reasoning = (
    domain in ["code", "sales"] OR
    complexity in ["complex"] OR
    any(["design", "architecture", "strategy", "why"] in goal)
  )
  requires_creativity = (
    domain in ["creative", "sales"] OR
    any(["engaging", "compelling", "creative", "catchy"] in goal)
  )

  STEP 5 — DATA SENSITIVITY
  ──────────────────────────
  IF any(["password", "secret", "key", "token", "private", "confidential"] in goal):
    data_sensitivity = "sensitive"  → FORCE local tier
  ELIF any(["customer", "user data", "tenant", "billing"] in goal):
    data_sensitivity = "internal"   → prefer local, allow api if needed
  ELSE:
    data_sensitivity = "public"

  STEP 6 — MCU COST ASSIGNMENT
  ─────────────────────────────
  mcu_map = { "simple": 1, "standard": 3, "complex": 5 }
  mcu_cost = mcu_map[complexity]

  RETURN TaskProfile(
    complexity, domain, agent_role,
    requires_reasoning, requires_creativity,
    data_sensitivity, estimated_tokens, mcu_cost,
    preferred_tier  # set in ALGO 2
  )
```

---

## ALGO 2 — MODEL SELECTOR
### File: `src/core/model_selector.py`

**Input:** `TaskProfile`, `system_state: SystemState`
**Output:** `ModelConfig` (model_id, provider, max_tokens, temperature)

```python
@dataclass
class SystemState:
    local_available: bool         # Ollama đang chạy?
    local_models: list[str]       # Models đã pull
    api_keys: dict[str, bool]     # anthropic/google/openai → có key không
    local_load: float             # 0.0-1.0, VRAM usage
    tenant_tier: str              # "starter" | "growth" | "premium"

@dataclass
class ModelConfig:
    model_id: str
    provider: Literal["ollama", "anthropic", "google", "openai"]
    max_tokens: int
    temperature: float
    context_window: int
    cost_per_mtok_input: float    # $0 nếu local
    cost_per_mtok_output: float
```

### Routing matrix (CORE LOGIC):

```
MODEL_ROUTING_MATRIX = {
  # (agent_role, complexity, requires_reasoning, data_sensitivity) → model

  # ── CTO: CODE ──
  ("cto", "simple",   False, "public"):    "gemini-2.0-flash",
  ("cto", "simple",   False, "sensitive"): "ollama:deepseek-coder-v2:16b",
  ("cto", "standard", True,  "public"):    "claude-sonnet-4-6",
  ("cto", "standard", True,  "sensitive"): "ollama:deepseek-coder-v2:33b",
  ("cto", "complex",  True,  "public"):    "claude-opus-4-6",
  ("cto", "complex",  True,  "sensitive"): "ollama:deepseek-coder-v2:33b",

  # ── CMO/EDITOR: CREATIVE ──
  ("cmo", "simple",   False, "*"):         "gemini-2.0-flash",
  ("cmo", "standard", True,  "*"):         "gemini-2.0-flash",
  ("cmo", "complex",  True,  "*"):         "gemini-2.0-pro",
  ("editor", "*",     False, "*"):         "gemini-2.0-flash",

  # ── COO: OPS (luôn local nếu available) ──
  ("coo", "*",        False, "*"):         "ollama:llama3.2:3b",   # lightweight
  # Fallback nếu local down:               "gemini-2.0-flash-lite"

  # ── CFO/DATA: ANALYSIS ──
  ("cfo", "*",        False, "sensitive"): "ollama:qwen2.5:7b",
  ("cfo", "*",        False, "public"):    "gemini-2.0-flash-lite",
  ("data", "*",       False, "sensitive"): "ollama:qwen2.5:7b",
  ("data", "*",       False, "public"):    "gemini-2.0-flash-lite",

  # ── CS: SUPPORT ──
  ("cs", "simple",    False, "*"):         "ollama:mistral:7b",
  ("cs", "standard",  False, "*"):         "claude-haiku-4-5",
  ("cs", "complex",   True,  "*"):         "claude-haiku-4-5",

  # ── SALES ──
  ("sales", "simple",   False, "*"):       "claude-haiku-4-5",
  ("sales", "standard", True,  "*"):       "claude-sonnet-4-6",
  ("sales", "complex",  True,  "*"):       "claude-sonnet-4-6",
}

FUNCTION select_model(profile: TaskProfile, state: SystemState) → ModelConfig:

  STEP 1 — LOOKUP matrix key
  ───────────────────────────
  key = (profile.agent_role, profile.complexity,
         profile.requires_reasoning, profile.data_sensitivity)

  # "*" wildcard matching: try exact first, then relax sensitivity
  model_id = MATRIX.get(key) or MATRIX.get(key_with_wildcard_sensitivity)

  STEP 2 — AVAILABILITY CHECK
  ────────────────────────────
  IF model_id starts with "ollama:":
    IF NOT state.local_available:
      model_id = fallback_to_api(profile)   # ALGO 7
    ELIF state.local_load > 0.85:
      # VRAM pressure: downgrade to smaller model
      model_id = downgrade_local(model_id)
    ELIF model_id.split(":")[1] NOT IN state.local_models:
      model_id = fallback_to_api(profile)   # model not pulled

  IF model_id is API model:
    provider = detect_provider(model_id)
    IF NOT state.api_keys.get(provider):
      model_id = fallback_chain(profile, exclude=provider)  # ALGO 7

  STEP 3 — TENANT TIER OVERRIDE
  ──────────────────────────────
  # Starter tier: không được dùng Opus
  IF state.tenant_tier == "starter" AND model_id == "claude-opus-4-6":
    model_id = "claude-sonnet-4-6"

  # Starter tier: local preferred để giảm cost
  IF state.tenant_tier == "starter" AND state.local_available:
    IF profile.domain NOT IN ["code", "sales"]:   # không downgrade critical
      model_id = best_local_for_domain(profile.domain)

  STEP 4 — BUILD ModelConfig
  ───────────────────────────
  temp_map = {
    "code": 0.2, "ops": 0.1, "analysis": 0.3,
    "creative": 0.8, "sales": 0.7, "support": 0.4
  }
  RETURN ModelConfig(
    model_id=model_id,
    provider=detect_provider(model_id),
    max_tokens=context_window_map[model_id] * 0.75,  # 75% safety cap
    temperature=temp_map[profile.domain],
    cost_per_mtok_input=COST_TABLE[model_id]["input"],
    cost_per_mtok_output=COST_TABLE[model_id]["output"],
  )
```

---

## ALGO 3 — COST ESTIMATOR
### File: `src/core/cost_estimator.py`

**Input:** `TaskProfile`, `ModelConfig`
**Output:** `CostEstimate`

```python
@dataclass
class CostEstimate:
    mcu_required: int             # MCU cần deduct
    usd_llm_cost: float           # actual LLM cost
    usd_infra_cost: float         # ~$0.001 per task (Fly.io)
    total_usd: float
    margin_usd: float             # revenue - cost
    margin_pct: float

COST_TABLE = {
  # $/MTok (input, output)
  "claude-opus-4-6":          (15.0,  75.0),
  "claude-sonnet-4-6":         (3.0,  15.0),
  "claude-haiku-4-5":          (0.25,  1.25),
  "gemini-2.0-flash":          (0.075, 0.30),
  "gemini-2.0-flash-lite":     (0.02,  0.08),
  "gemini-2.0-pro":            (1.25,  5.0),
  "gpt-4o-mini":               (0.15,  0.60),
  "ollama:*":                  (0.0,   0.0),   # local = free
}

MCU_REVENUE_TABLE = {
  # MCU → USD revenue (blended across tiers)
  1: 0.049,   # simple task
  3: 0.045,   # standard (Growth bundle rate)
  5: 0.50,    # complex (overage)
}

FUNCTION estimate_cost(profile: TaskProfile, model: ModelConfig) → CostEstimate:

  # Token estimation từ complexity
  token_est = {
    "simple":   {"input": 800,   "output": 400},
    "standard": {"input": 2000,  "output": 1500},
    "complex":  {"input": 5000,  "output": 3000},
  }[profile.complexity]

  # LLM cost
  (c_in, c_out) = COST_TABLE.get(model.model_id, (0, 0))
  usd_llm = (token_est["input"] / 1e6 * c_in +
             token_est["output"] / 1e6 * c_out)

  # Revenue từ MCU
  revenue = MCU_REVENUE_TABLE[profile.mcu_cost]

  # Margin
  margin = revenue - usd_llm - 0.001  # 0.001 infra

  RETURN CostEstimate(
    mcu_required=profile.mcu_cost,
    usd_llm_cost=round(usd_llm, 6),
    usd_infra_cost=0.001,
    total_usd=round(usd_llm + 0.001, 6),
    margin_usd=round(margin, 6),
    margin_pct=round(margin / revenue * 100, 1) if revenue > 0 else 100.0
  )
```

---

## ALGO 4 — MCU GATE
### File: `src/core/mcu_gate.py`

**Mục đích:** Check/lock/confirm/refund MCU trước và sau execution.
**Database:** SQLite table `mcu_ledger`

```python
# Schema
CREATE TABLE mcu_ledger (
  id          TEXT PRIMARY KEY,   -- UUID
  tenant_id   TEXT NOT NULL,
  mission_id  TEXT NOT NULL,
  amount      INTEGER NOT NULL,   -- positive=deduct, negative=refund
  type        TEXT NOT NULL,      -- "lock"|"confirm"|"refund"|"seed"|"purchase"
  status      TEXT DEFAULT "pending",  -- "pending"|"confirmed"|"cancelled"
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  confirmed_at DATETIME
);

CREATE TABLE mcu_balance (
  tenant_id   TEXT PRIMARY KEY,
  balance     INTEGER DEFAULT 0,
  locked      INTEGER DEFAULT 0,  -- MCU đang bị lock
  lifetime_used INTEGER DEFAULT 0
);
```

```
FUNCTION mcu_check_and_lock(tenant_id, mission_id, mcu_amount) → Result:
  # Atomic operation — dùng SQLite transaction

  BEGIN TRANSACTION:
    balance_row = SELECT balance, locked FROM mcu_balance
                  WHERE tenant_id = ? FOR UPDATE

    available = balance_row.balance - balance_row.locked

    IF available < mcu_amount:
      ROLLBACK
      RETURN Error(
        code="insufficient_mcu",
        available=available,
        required=mcu_amount,
        recharge_url=f"https://agencyos.network/billing?tenant={tenant_id}"
      )

    # Lock MCU
    INSERT INTO mcu_ledger (id, tenant_id, mission_id, amount, type, status)
    VALUES (uuid(), tenant_id, mission_id, mcu_amount, "lock", "pending")

    UPDATE mcu_balance
    SET locked = locked + mcu_amount
    WHERE tenant_id = tenant_id

  COMMIT
  RETURN Success(lock_id=..., locked_amount=mcu_amount)


FUNCTION mcu_confirm(lock_id, actual_tokens_used, model_config) → Result:
  # Sau khi task xong — confirm actual cost

  # Tính actual MCU dựa trên actual tokens (có thể khác estimate)
  actual_mcu = recalculate_mcu(actual_tokens_used, model_config)
  lock_row = SELECT * FROM mcu_ledger WHERE id = lock_id

  BEGIN TRANSACTION:
    IF actual_mcu < lock_row.amount:
      # Refund difference
      refund = lock_row.amount - actual_mcu
      INSERT mcu_ledger (..., amount=-refund, type="refund", status="confirmed")

    UPDATE mcu_ledger SET status="confirmed" WHERE id=lock_id
    UPDATE mcu_balance SET
      balance  = balance - actual_mcu,
      locked   = locked  - lock_row.amount,    # release lock
      lifetime_used = lifetime_used + actual_mcu
    WHERE tenant_id = lock_row.tenant_id

  COMMIT
  RETURN Success(
    charged=actual_mcu,
    refunded=(lock_row.amount - actual_mcu)
  )


FUNCTION mcu_refund_full(lock_id, reason) → Result:
  # Mission failed hoàn toàn — refund 100%
  lock_row = SELECT * FROM mcu_ledger WHERE id = lock_id

  BEGIN TRANSACTION:
    INSERT mcu_ledger (..., amount=-lock_row.amount, type="refund", ...)
    UPDATE mcu_balance SET
      balance = balance,              # không trừ
      locked  = locked - lock_row.amount
    WHERE tenant_id = lock_row.tenant_id
    UPDATE mcu_ledger SET status="cancelled" WHERE id=lock_id

  COMMIT
  emit_event("mission.failed", {tenant_id, mission_id, reason, refunded=lock_row.amount})
  RETURN Success(refunded=lock_row.amount)
```

---

## ALGO 5 — LOCAL ADAPTER (Ollama)
### File: `src/core/local_adapter.py`

```python
class OllamaAdapter:

  BASE_URL = "http://localhost:11434"

  QUANTIZATION_MAP = {
    # model → recommended quant cho VRAM budget
    "llama3.3:70b":          "q4_K_M",   # ~40GB VRAM
    "deepseek-coder-v2:33b": "q4_K_M",   # ~20GB
    "deepseek-coder-v2:16b": "q5_K_M",   # ~10GB
    "llama3.2:3b":           "q8_0",     # ~2GB — always full
    "qwen2.5:7b":            "q6_K",     # ~5GB
    "mistral:7b":            "q5_K_M",   # ~5GB
  }


  FUNCTION health_check() → bool:
    TRY:
      GET http://localhost:11434/api/tags timeout=2s
      RETURN True
    EXCEPT ConnectionError:
      RETURN False


  FUNCTION get_vram_load() → float:
    # Dùng nvidia-smi hoặc ollama ps
    result = run("ollama ps --json")
    IF no models running: RETURN 0.0
    total_vram = sum(m.size for m in result.models)
    RETURN total_vram / GPU_TOTAL_VRAM


  ASYNC FUNCTION generate(model, messages, config) → AsyncIterator[str]:
    # Ensure model is pulled
    IF model NOT IN pulled_models_cache:
      AWAIT pull_model(model)

    payload = {
      "model": model,
      "messages": messages,
      "stream": True,
      "options": {
        "temperature": config.temperature,
        "num_predict": config.max_tokens,
        "num_ctx": 4096,                    # context window
        "num_thread": os.cpu_count(),
      }
    }

    ASYNC FOR chunk IN http_stream("POST", "/api/chat", payload):
      IF chunk.done: BREAK
      YIELD chunk.message.content


  ASYNC FUNCTION pull_model(model_id) → None:
    # Background pull — không block main flow
    quant = QUANTIZATION_MAP.get(model_id, "q4_K_M")
    AWAIT run_background(f"ollama pull {model_id}:{quant}")
    pulled_models_cache.add(model_id)
```

---

## ALGO 6 — API ADAPTER
### File: `src/core/api_adapter.py`

```python
class APIAdapter:

  PROVIDERS = {
    "anthropic": AnthropicClient(api_key=env.ANTHROPIC_API_KEY),
    "google":    genai.Client(api_key=env.GOOGLE_API_KEY),
    "openai":    OpenAI(api_key=env.OPENAI_API_KEY),
  }

  ASYNC FUNCTION generate(model_config: ModelConfig, messages, system_prompt) → AsyncIterator[str]:

    provider = detect_provider(model_config.model_id)

    IF provider == "anthropic":
      ASYNC WITH anthropic.messages.stream(
        model=model_config.model_id,
        max_tokens=model_config.max_tokens,
        temperature=model_config.temperature,
        system=system_prompt,
        messages=messages
      ) AS stream:
        ASYNC FOR text IN stream.text_stream:
          YIELD text

    ELIF provider == "google":
      model = genai.GenerativeModel(model_config.model_id)
      response = model.generate_content(
        contents=format_for_gemini(messages, system_prompt),
        generation_config=genai.types.GenerationConfig(
          max_output_tokens=model_config.max_tokens,
          temperature=model_config.temperature,
        ),
        stream=True
      )
      FOR chunk IN response:
        IF chunk.text: YIELD chunk.text

    ELIF provider == "openai":
      ASYNC FOR chunk IN openai.chat.completions.create(
        model=model_config.model_id,
        messages=format_for_openai(messages, system_prompt),
        max_tokens=model_config.max_tokens,
        temperature=model_config.temperature,
        stream=True
      ):
        IF chunk.choices[0].delta.content:
          YIELD chunk.choices[0].delta.content


FUNCTION detect_provider(model_id: str) → str:
  IF "claude" in model_id:   RETURN "anthropic"
  IF "gemini" in model_id:   RETURN "google"
  IF "gpt" in model_id:      RETURN "openai"
  IF model_id.startswith("ollama:"): RETURN "ollama"
  RAISE ValueError(f"Unknown provider for model: {model_id}")
```

---

## ALGO 7 — FALLBACK CHAIN
### File: `src/core/fallback_chain.py`

```
FALLBACK_HIERARCHY = {
  # primary_fail → fallback_options (ordered by quality)
  "claude-opus-4-6":           ["claude-sonnet-4-6", "gemini-2.0-pro"],
  "claude-sonnet-4-6":         ["claude-haiku-4-5",  "gemini-2.0-flash"],
  "claude-haiku-4-5":          ["gemini-2.0-flash",  "gpt-4o-mini"],
  "gemini-2.0-pro":            ["claude-sonnet-4-6", "gpt-4o"],
  "gemini-2.0-flash":          ["gpt-4o-mini",       "claude-haiku-4-5"],
  "gemini-2.0-flash-lite":     ["gpt-4o-mini",       "ollama:llama3.2:3b"],
  "ollama:deepseek-coder-v2:33b": ["claude-sonnet-4-6", "gemini-2.0-flash"],
  "ollama:llama3.3:70b":       ["gemini-2.0-flash",  "gpt-4o-mini"],
  "ollama:llama3.2:3b":        ["gemini-2.0-flash-lite"],
  "ollama:qwen2.5:7b":         ["gemini-2.0-flash-lite"],
  "ollama:mistral:7b":         ["claude-haiku-4-5",  "gemini-2.0-flash"],
}

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = [1, 3, 9]   # exponential backoff

ASYNC FUNCTION execute_with_fallback(
  model_config: ModelConfig,
  messages,
  system_prompt,
  on_token_cb,         # callback stream token về UI
  profile: TaskProfile
) → ExecutionResult:

  attempted = []
  current_model = model_config.model_id

  FOR attempt IN range(MAX_RETRIES):
    TRY:
      attempted.append(current_model)
      tokens_used = 0

      # Chọn adapter
      IF current_model.startswith("ollama:"):
        adapter = OllamaAdapter()
        ASYNC FOR token IN adapter.generate(current_model, messages, model_config):
          AWAIT on_token_cb(token)
          tokens_used += 1  # rough count
      ELSE:
        api_adapter = APIAdapter()
        ASYNC FOR token IN api_adapter.generate(model_config, messages, system_prompt):
          AWAIT on_token_cb(token)
          tokens_used += 1

      # Success
      RETURN ExecutionResult(
        success=True,
        model_used=current_model,
        tokens_output=tokens_used,
        attempts=attempted
      )

    EXCEPT RateLimitError:
      log.warning(f"Rate limit: {current_model}")
      AWAIT sleep(RETRY_DELAY_SECONDS[attempt])
      # Don't switch model, just retry

    EXCEPT (ModelUnavailableError, ConnectionError, TimeoutError) AS e:
      log.warning(f"Model unavailable: {current_model} — {e}")
      fallbacks = FALLBACK_HIERARCHY.get(current_model, [])
      next_models = [m for m in fallbacks if m not in attempted]

      IF NOT next_models:
        BREAK  # all fallbacks exhausted

      # Sensitivity check: đừng fallback lên API nếu data sensitive
      IF profile.data_sensitivity == "sensitive":
        api_fallbacks = [m for m in next_models if not m.startswith("ollama:")]
        IF api_fallbacks:
          # emit warning, skip API fallbacks
          log.warning("Sensitive data: skipping API fallback")
          next_models = [m for m in next_models if m.startswith("ollama:")]

      IF next_models:
        current_model = next_models[0]
        # Rebuild model_config cho model mới
        model_config = rebuild_config(current_model, profile)
        log.info(f"Falling back to: {current_model}")
      ELSE:
        BREAK

  # All attempts failed
  RETURN ExecutionResult(
    success=False,
    model_used=None,
    error="all_models_failed",
    attempts=attempted
  )
```

---

## ALGO 8 — AGENT DISPATCHER + MAIN ORCHESTRATOR
### File: `src/core/agent_dispatcher.py` & `hybrid_router.py`

```python
# Đây là entry point — FastAPI gọi vào đây

ASYNC FUNCTION route_and_execute(
  goal: str,
  tenant_id: str,
  mission_id: str,
  webhook_url: str | None,
  sse_queue: asyncio.Queue          # stream tokens về dashboard
) → MissionResult:

  # ── STAGE 1: CLASSIFY ──────────────────────────────────────────
  profile = classify_task(goal, context={
    "tenant_id": tenant_id,
    "history": get_recent_missions(tenant_id, limit=5)  # context memory
  })

  # ── STAGE 2: MCU CHECK + LOCK ──────────────────────────────────
  lock_result = mcu_check_and_lock(tenant_id, mission_id, profile.mcu_cost)
  IF lock_result.is_error:
    emit_sse(sse_queue, "error", {
      "code": "insufficient_mcu",
      "available": lock_result.available,
      "required": profile.mcu_cost,
      "recharge_url": lock_result.recharge_url
    })
    RETURN MissionResult(success=False, error="insufficient_mcu")
  lock_id = lock_result.lock_id

  # ── STAGE 3: MODEL SELECT ──────────────────────────────────────
  system_state = get_system_state()  # check Ollama + API keys
  model_config = select_model(profile, system_state)
  cost_est = estimate_cost(profile, model_config)

  emit_sse(sse_queue, "planning", {
    "agent": profile.agent_role,
    "model": model_config.model_id,
    "complexity": profile.complexity,
    "mcu_cost": profile.mcu_cost,
    "estimated_margin": f"{cost_est.margin_pct}%"
  })

  # ── STAGE 4: LOAD AGENT PROMPT ─────────────────────────────────
  agent_prompt = load_agent_prompt(profile.agent_role)
  # agents/{agent_role}.md → inject vào system prompt

  # ── STAGE 5: BUILD MESSAGE CHAIN ──────────────────────────────
  messages = [{"role": "user", "content": goal}]

  # Inject relevant context
  IF profile.domain == "code":
    # CTO gets codebase context
    messages = inject_codebase_context(messages, goal)
  ELIF profile.domain == "analysis":
    # Data agent gets metrics
    messages = inject_metrics_context(messages, tenant_id)

  # ── STAGE 6: EXECUTE WITH FALLBACK ─────────────────────────────
  async def on_token(token: str):
    emit_sse(sse_queue, "token", {"text": token})

  exec_result = AWAIT execute_with_fallback(
    model_config, messages, agent_prompt,
    on_token_cb=on_token,
    profile=profile
  )

  # ── STAGE 7: VERIFY OUTPUT ─────────────────────────────────────
  IF exec_result.success:
    verify_result = verify_output(
      output=collect_sse_buffer(sse_queue),
      profile=profile,
      goal=goal
    )
    IF NOT verify_result.passed:
      # Self-heal: retry với reflection hint
      IF verify_result.retry_count < 2:
        goal_with_hint = f"{goal}\n\nPREVIOUS ATTEMPT FAILED:\n{verify_result.failure_reason}\nPlease fix: {verify_result.suggested_fix}"
        RETURN AWAIT route_and_execute(goal_with_hint, tenant_id, mission_id, ...)
      ELSE:
        # Max retries → refund MCU
        mcu_refund_full(lock_id, reason=verify_result.failure_reason)
        emit_sse(sse_queue, "failed", {"reason": "max_retries_exceeded"})
        RETURN MissionResult(success=False, ...)

  # ── STAGE 8: MCU CONFIRM ───────────────────────────────────────
  mcu_confirm(lock_id, exec_result.tokens_output, model_config)

  # ── STAGE 9: EMIT COMPLETION ───────────────────────────────────
  emit_sse(sse_queue, "completed", {
    "model_used": exec_result.model_used,
    "mcu_charged": profile.mcu_cost,
    "output_preview": get_preview(sse_buffer)
  })

  IF webhook_url:
    AWAIT fire_webhook(webhook_url, "mission.completed", {
      "mission_id": mission_id,
      "tenant_id": tenant_id,
      "success": True,
      "model_used": exec_result.model_used,
      "mcu_charged": profile.mcu_cost,
      "output": get_full_output(sse_buffer)
    })

  RETURN MissionResult(success=True, model=exec_result.model_used, ...)
```

---

## VERIFY OUTPUT (Jidoka gate)
### Inline trong hybrid_router.py

```
FUNCTION verify_output(output, profile, goal) → VerifyResult:

  checks = []

  IF profile.domain == "code":
    checks += [
      check_no_syntax_errors(output),
      check_imports_valid(output),
      check_no_placeholder_comments(output),   # "TODO:", "your code here"
      check_file_size_reasonable(output),       # < 300 lines per file
    ]

  IF profile.domain == "creative":
    checks += [
      check_length_adequate(output, min_words=100),
      check_no_lorem_ipsum(output),
      check_language_matches_goal(output, goal),
    ]

  IF profile.domain == "analysis":
    checks += [
      check_contains_numbers(output),           # report phải có số liệu
      check_structured_output(output),          # JSON hoặc markdown table
    ]

  # Universal checks
  checks += [
    check_not_empty(output),
    check_no_apology_pattern(output),   # "I cannot", "I'm sorry" → failure
    check_no_truncation(output),        # ends mid-sentence
  ]

  failures = [c for c in checks if not c.passed]

  IF failures:
    RETURN VerifyResult(
      passed=False,
      failure_reason="; ".join(f.reason for f in failures),
      suggested_fix=generate_fix_hint(failures[0]),
      retry_count=current_retry_count + 1
    )

  RETURN VerifyResult(passed=True)
```

---

## FASTAPI ENDPOINTS
### File: `src/core/gateway.py`

```python
POST /v1/missions
  Body: { goal, tenant_id, webhook_url? }
  → validate tenant API key (X-API-Key header)
  → mcu_check (quick, no lock yet)
  → return { mission_id, estimated_mcu, model_preview }
  → background task: route_and_execute(...)

GET /v1/missions/{mission_id}/stream
  → SSE stream: planning | token | completed | error | failed
  → heartbeat every 15s để giữ connection

GET /v1/mcu/balance?tenant_id=...
  → { balance, locked, lifetime_used }

POST /v1/mcu/deduct         # OpenClaw billing hook
  Body: { tenant_id, mission_id, amount, lock_id }
  → gọi mcu_check_and_lock hoặc mcu_confirm tuỳ type

POST /v1/billing/polar      # Polar.sh webhook
  Body: Polar event payload
  Header: polar-signature (verify HMAC)
  → subscription.created  → seed MCU
  → subscription.updated  → adjust tier
  → subscription.cancelled → mark tenant inactive
  → order.created         → one-time MCU pack
```

---

## ENVIRONMENT VARIABLES

```bash
# LLM APIs
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...       # optional

# Local
OLLAMA_URL=http://localhost:11434
GPU_TOTAL_VRAM_GB=24         # để tính load %

# Billing
POLAR_WEBHOOK_SECRET=whsec_...
POLAR_ORG_ID=...

# App
DATABASE_URL=~/.mekong/raas/tenants.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Tiered model access
ALLOW_OPUS_TIERS=growth,premium     # starter không dùng Opus
```

---

## IMPLEMENTATION ORDER CHO OPUS

```
Sprint A (ngày 1-2):
  1. task_classifier.py   ← ALGO 1 (không có dependency)
  2. cost_estimator.py    ← ALGO 3 (depends on 1)
  3. mcu_gate.py          ← ALGO 4 (SQLite, standalone)
  4. Tests: test_classifier.py, test_mcu_gate.py

Sprint B (ngày 3-4):
  5. local_adapter.py     ← ALGO 5 (Ollama)
  6. api_adapter.py       ← ALGO 6 (Anthropic + Google)
  7. model_selector.py    ← ALGO 2 (depends on 5+6)
  8. Tests: test_adapters.py

Sprint C (ngày 5-6):
  9.  fallback_chain.py   ← ALGO 7 (depends on 5+6)
  10. agent_dispatcher.py ← ALGO 8 (depends on all)
  11. hybrid_router.py    ← MAIN (wires everything)
  12. gateway.py          ← FastAPI endpoints
  13. Integration test: POST /v1/missions end-to-end

Sprint D (ngày 7):
  14. Load agents/*.md prompts
  15. Deploy Fly.io
  16. Smoke test từ agencyos dashboard
```

---

## DEFINITION OF DONE (Opus phải đạt trước merge)

```
□ pytest tests/ -v → 100% pass
□ POST /v1/missions với goal thực → mission complete trong 60s
□ MCU deducted đúng amount sau task
□ Fallback hoạt động: tắt Ollama → tự switch sang API
□ Data sensitive task → KHÔNG gọi API (chỉ local)
□ Starter tenant → KHÔNG được dùng claude-opus-4-6
□ Mission fail → MCU refund 100%
□ SSE stream phát token realtime (< 500ms first token)
□ /v1/mcu/balance trả đúng balance
□ Polar webhook → MCU seeded đúng theo tier
```
