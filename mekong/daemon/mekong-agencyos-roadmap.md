# Mekong CLI × AgencyOS — Roadmap to True 100/100
*Unification Blueprint: Open Source Engine + Commercial RaaS*

---

## Diagnosis: Tại sao chưa thực sự 100/100

Repo hiện tại tự chấm 100/100 theo **production readiness** (doc + code + security + test + CI + DX = 60/60) và AGI 97.6/100 theo **subsystem scoring** — nhưng đây là self-reported metrics. True 100/100 cần đo bằng **external validation**:

| Dimension | Hiện tại | True 100/100 |
|---|---|---|
| OSS Traction | 0 stars, 1 fork | 100+ stars, active community |
| Code Health | Self-assessed | CI green, coverage ≥80%, no `:any` types |
| RaaS Revenue | Documented, not live | Paying tenants, monthly MRR |
| AGI Subsystems | 9/9 wired, runtime score | Real-world task success rate ≥90% |
| Repo Structure | Messy (personal paths committed) | Clean, standard OSS layout |
| Integration | Mekong ↔ AgencyOS documented | Live API bridge, end-to-end tested |

---

## Architecture: Unified Model

```
┌─────────────────────────────────────────────────────┐
│                   USER LAYER                        │
│  Non-tech user (AgencyOS UI)  │  Developer (CLI/API) │
└──────────────┬────────────────┴──────────┬───────────┘
               │                           │
┌──────────────▼───────────────────────────▼───────────┐
│              AGENCYOS (Commercial SaaS)               │
│  Dashboard │ Credit billing │ Multi-tenant │ Webhooks │
└──────────────────────────┬───────────────────────────┘
                           │ REST/WebSocket API
┌──────────────────────────▼───────────────────────────┐
│           MEKONG CLI ENGINE (Open Source)             │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Planner  │→│ Executor │→│    Verifier      │   │
│  │  (NLU)   │  │(5 modes) │  │ (quality gates)  │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  9 AGI Subsystems (Memory│Reflection│WorldModel│...)  │
│  EventBus (22 events) │ Auto-Recipe │ Telemetry       │
└───────────────────────────────────────────────────────┘
```

**Nguyên tắc phân tách:**
- **Mekong CLI** = OSS engine, MIT, community-driven, pip installable
- **AgencyOS** = Proprietary SaaS layer, billing, UI, enterprise features
- **Bridge** = REST API + SDK — Mekong expose, AgencyOS consume

---

## GAP ANALYSIS chi tiết

### Gap 1: Repo Structure Mess 🔴
Personal path `Users/macbookprom1/...` đã commit vào repo. Folder rác: `tmp/`, `tasks_paused/`, `doanh-trai-tom-hum/`, `newsletter-saas/`. Không có contributor onboarding rõ ràng.

### Gap 2: AGI Subsystems — Wired but not Validated 🟡
9 subsystems exist nhưng chưa có **integration tests** chứng minh chúng thực sự cải thiện task success rate. Score engine tự report, không có external benchmark.

### Gap 3: Mekong ↔ AgencyOS Bridge Chưa Live 🔴
`docs/unified-business-model.md` chỉ là docs. Chưa có:
- AgencyOS gọi Mekong API thực tế
- SDK typed cho third-party RaaS builders
- Webhook event schema chuẩn

### Gap 4: No Real-world Benchmark 🟡
Không có public dataset để test "mekong cook X" → success rate. Community không thể verify claims.

### Gap 5: Plugin Marketplace Chưa Tồn Tại 🔴
Roadmap mention "Plugin marketplace" nhưng zero implementation. Đây là key moat cho cả OSS và RaaS.

---

## ROADMAP — 4 Sprint để True 100/100

---

### SPRINT 1: CLEAN HOUSE (1 tuần)
*Priority: Credibility. Không ai contribute vào repo messy.*

**Task 1.1 — Repo Cleanup**
```bash
# Remove personal paths, tmp files, rác
git filter-repo --path-glob 'Users/*' --invert-paths
git filter-repo --path-glob 'tmp/*' --invert-paths

# Restructure về standard OSS layout
mekong-cli/
├── src/                    # Core engine (KEEP)
├── agents/                 # Agent definitions (KEEP)
├── tests/                  # Tests (KEEP)
├── docs/                   # Documentation (CLEAN)
├── examples/               # Code examples (KEEP)
├── recipes/                # Built-in recipes (KEEP)
├── .github/                # CI/CD, issue templates (KEEP)
└── agencyos/               # RaaS bridge layer (NEW — hoặc separate repo)
```

**Task 1.2 — GitHub Hygiene**
- Issue templates: Bug Report, Feature Request, New Agent
- CONTRIBUTING.md với setup guide < 5 phút
- CHANGELOG.md cập nhật đúng semantic versioning
- `.github/CODEOWNERS` để route reviews

**Task 1.3 — CI Hard Gates**
```yaml
# .github/workflows/ci.yml additions
- name: No personal paths
  run: |
    if git ls-files | grep -E "Users/|/tmp/|tasks_paused"; then
      echo "Personal paths detected!" && exit 1
    fi
- name: Type coverage
  run: mypy src/ --disallow-any-expr # Zero `:any`
- name: Coverage gate
  run: pytest --cov=src --cov-fail-under=80
```

---

### SPRINT 2: AGI VALIDATION (2 tuần)
*Priority: Prove the score, don't just claim it.*

**Task 2.1 — Benchmark Suite**

Tạo `tests/benchmarks/` với public test cases:

```python
# tests/benchmarks/test_agi_tasks.py
BENCHMARK_TASKS = [
    # Simple (1 credit)
    {"goal": "Create a Python function to reverse a string with tests",
     "expected_files": ["reverse.py", "test_reverse.py"],
     "expected_tests_pass": True},
    
    # Standard (3 credits)  
    {"goal": "Create FastAPI endpoint GET /users with SQLite",
     "expected_files": ["main.py", "database.py"],
     "expected_endpoint": "/users"},
    
    # Complex (5 credits)
    {"goal": "Create JWT auth system: register/login/refresh",
     "expected_files": ["auth.py", "models.py", "test_auth.py"],
     "expected_coverage": 70},
]

def test_task_success_rate():
    results = run_benchmark(BENCHMARK_TASKS)
    assert results.success_rate >= 0.85  # 85% minimum
    assert results.avg_retry_count <= 2   # Max 2 retries per task
```

**Task 2.2 — Self-Healing Metrics**
```python
# src/core/telemetry.py additions
@dataclass
class SubsystemHealth:
    subsystem: str
    activation_count: int      # Bao nhiêu lần được gọi
    success_contribution: float  # Improve success rate bao nhiêu %
    avg_latency_ms: float

# Expose via: mekong agi benchmark --tasks tests/benchmarks/
```

**Task 2.3 — AGI Score thực sự**

Thay vì self-report, tính từ benchmark results:

```python
# Scoring formula mới (transparent)
agi_score = (
    task_success_rate * 40 +      # 40pts: Core delivery
    self_healing_rate * 20 +       # 20pts: Recovery ability  
    recipe_reuse_rate * 15 +       # 15pts: Learning/memory
    avg_quality_score * 15 +       # 15pts: Output quality
    subsystem_coverage * 10        # 10pts: All 9 active
) / 100
```

---

### SPRINT 3: UNIFICATION BRIDGE (2 tuần)
*Priority: Mekong CLI trở thành engine. AgencyOS consume nó.*

**Task 3.1 — Clean API Contract**

```python
# src/gateway.py — Public API cho AgencyOS
@app.post("/v1/missions")
async def create_mission(
    goal: str,
    tenant_id: str,
    webhook_url: Optional[str],
    priority: Literal["low", "normal", "high"] = "normal"
) -> MissionResponse:
    """
    Unified mission endpoint.
    AgencyOS calls this, Mekong executes, webhook receives result.
    """

@app.get("/v1/missions/{mission_id}/stream")
async def stream_mission(mission_id: str):
    """
    SSE stream for real-time progress.
    AgencyOS dashboard subscribes to this.
    """

@app.post("/v1/webhook/test")
async def test_webhook(tenant_id: str) -> dict:
    """Test webhook connectivity before going live."""
```

**Task 3.2 — Python SDK (pip install mekong-sdk)**

```python
# packages/sdk/mekong_sdk/client.py
class MekongClient:
    def __init__(self, api_key: str, base_url: str = "https://api.mekong.run"):
        ...
    
    def cook(self, goal: str, **kwargs) -> Mission:
        """Sync wrapper cho common use case."""
    
    async def cook_async(self, goal: str, **kwargs) -> AsyncIterator[MissionEvent]:
        """Async streaming cho real-time UI."""
    
    def subscribe(self, event: str, handler: Callable) -> None:
        """Webhook handler registration."""

# AgencyOS sử dụng:
from mekong_sdk import MekongClient
client = MekongClient(api_key=settings.MEKONG_API_KEY)
mission = client.cook("Deploy landing page", tenant_id=tenant.id)
```

**Task 3.3 — Webhook Event Schema chuẩn**

```python
# Tất cả events AgencyOS nhận từ Mekong
WEBHOOK_EVENTS = {
    "mission.created": MissionCreatedPayload,
    "mission.planning": PlanPayload,          # Plan steps generated
    "mission.step.started": StepStartPayload,
    "mission.step.completed": StepDonePayload,
    "mission.step.failed": StepFailPayload,   # Include retry info
    "mission.completed": MissionDonePayload,  # Include files, metrics
    "mission.failed": MissionFailPayload,     # Include error + refund trigger
    "credits.low": CreditsLowPayload,         # Tenant balance < 10
}
```

**Task 3.4 — Separate Repos Strategy**

```
longtho638-jpg/mekong-cli      # OSS engine (current, cleaned)
longtho638-jpg/mekong-sdk      # Python + JS SDK (new)
longtho638-jpg/agencyos        # Commercial RaaS UI (private or public)
longtho638-jpg/mekong-recipes  # Community recipe registry (new)
```

AgencyOS repo có thể private, nhưng `mekong-sdk` phải public để ecosystem build on top.

---

### SPRINT 4: COMMUNITY & FLYWHEEL (ongoing)
*Priority: OSS flywheel → AgencyOS leads.*

**Task 4.1 — Plugin Marketplace Foundation**

```python
# Plugin interface (minimal, extensible)
class MekongPlugin:
    name: str
    version: str
    description: str
    
    def register_agents(self) -> list[AgentBase]: ...
    def register_recipes(self) -> list[Recipe]: ...
    def register_tools(self) -> list[Tool]: ...

# Install flow:
# mekong plugin install github:user/my-plugin
# mekong plugin install pypi:mekong-plugin-database
```

**Task 4.2 — Community Recipe Registry**

Repo `mekong-recipes` riêng, community submit via PR:
```
recipes/
├── web/
│   ├── fastapi-crud.md
│   ├── nextjs-landing.md
├── data/
│   ├── pandas-pipeline.md
├── devops/
│   ├── docker-compose.md
└── INDEX.json  # Searchable registry
```

CLI command: `mekong search "fastapi auth"` → list community recipes

**Task 4.3 — Contributor Revenue Sharing (Live)**

Hiện tại chỉ documented. Để live cần:
- Polar.sh integration live, test với 1 real payout
- Attribution tracking: recipe đã dùng để generate bao nhiêu revenue
- Monthly transparency report tự động generate

**Task 4.4 — AgencyOS as Demo**

AgencyOS phải là **public demo** của Mekong CLI sức mạnh:
- Landing page: "Submit a task, watch Mekong execute it live"
- Free tier: 10 credits để try
- Conversion funnel: Free → Pro → Enterprise

---

## SCORE TRACKER — True 100/100

| Dimension | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|---|---|---|---|---|
| Repo clean | ✅ | ✅ | ✅ | ✅ |
| CI green (80% cov) | ✅ | ✅ | ✅ | ✅ |
| Benchmark suite | — | ✅ | ✅ | ✅ |
| Task success ≥85% | — | ✅ | ✅ | ✅ |
| SDK published | — | — | ✅ | ✅ |
| Webhook schema | — | — | ✅ | ✅ |
| Plugin foundation | — | — | — | ✅ |
| Community recipes | — | — | — | ✅ |
| Paying tenants | — | — | — | ✅ |
| **Score** | **60** | **75** | **88** | **100** |

---

## QUICK WINS — Làm ngay hôm nay

Thứ tự ưu tiên nếu chỉ có 1 ngày:

1. **Xóa personal paths** khỏi git history — 30 phút, impact lớn cho credibility
2. **Viết benchmark 5 tasks** đơn giản với assert success rate — 2 giờ, proves the claims
3. **Tạo `mekong-sdk` skeleton** với `MekongClient.cook()` — 3 giờ, unblocks AgencyOS integration
4. **Tách `agencyos/` thành separate concern** trong codebase — define interface boundary rõ ràng

---

## JIDOKA TRIGGERS — Stop nếu gặp

- Test success rate < 70% → Fix core PEV engine trước, đừng build features
- API contract thay đổi breaking change → Bump major version, maintain backward compat 1 version
- Security scan fail → Stop everything, fix trước khi merge

---

*Mekong CLI × AgencyOS Unification Roadmap v1.0*
*"Build the engine open. Monetize the platform."*
