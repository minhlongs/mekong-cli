# Báo cáo: Hiện trạng mekong-cli v6.0

> **Loại:** Brownfield Audit | **Ngày:** 2026-04-25

## Điểm mạnh (Giữ nguyên)

### Core Engine
- **PEV Engine** (`src/core/`): planner.py, executor.py, verifier.py, orchestrator.py — vòng lặp Plan→Execute→Verify đã hoạt động
- **443 commands** (`.claude/commands/`): Moat thực sự, không đối thủ nào có
- **LLM Router** (`mekong/adapters/llm-providers.yaml`): Universal 3-var endpoint, hỗ trợ Ollama/OpenRouter/Anthropic/DashScope/Gemini
- **PEV Engine** đang LIVE tại `api.cashclaw.cc` — thực sự serving requests

### Infrastructure Có Sẵn
- **Observability stack** (`observability/`): Prometheus + Grafana + OpenTelemetry collector — CHƯA fully wired nhưng code đã có
- **CI helpers** (`ci/`): config + helpers — cần extend thêm AI-specific gates
- **Docker** (`docker-compose.yml`, `Dockerfile`): Cơ sở để multi-tenant
- **Polar.sh billing**: Fully wired ($49/$149/$499 tiers), checkout LIVE

### Agent Layer  
- **22 departments** mapped to agent personas
- **Clipmart** (`clipmart/`): PaperClip-style marketplace templates — Phase 4 ready
- **packages/agents**: Agent definitions có thể reuse

### Production URLs
| Service | URL | Status |
|---------|-----|--------|
| API Gateway | https://api.cashclaw.cc | ✅ LIVE |
| Landing | https://mekongmind.com | ✅ LIVE |
| Starter Checkout | https://buy.polar.sh/... | ✅ 302 |

## Điểm yếu (Cần fix)

### Architectural Debt
- `apps/` directory: 40+ apps không liên quan tồn tại trong same monorepo — bloat
- Thiếu `seed/` layer: không có entry point độc lập, local-first
- Memory system chưa chuẩn: không có ChromaDB integration, không có vector search
- Không có task queue (Redis): requests xử lý synchronously

### Missing Pieces
- **Multi-tenant isolation**: Không có per-user Docker containers
- **Feedback loop**: Không có analytics integration (PostHog có trong STRATEGY.md nhưng chưa wired)
- **5 Enforcement Gates**: ci/ có helpers nhưng chưa có AI-specific gates
- **Temporal/Prefect**: Không có long-running workflow manager

## Kết luận

mekong-cli v6.0 = **Xuất sắc ở Build & Validate, thiếu Run & Optimize**

Đây chính xác là mô tả của bài viết Peter Pang về AI-First gap:
- ClaudeKit (Build & Validate): 9/10
- Run & Optimize: 3/10

**Bước tiếp theo:** Implement `seed/` layer là nền tảng đúng đắn nhất
