# Báo cáo: Kiến trúc Solo Platform Target

> **Nguồn:** DeepSeek-Solo-Platform.pdf + a16z model + AI-First framework

## Tầm nhìn Tổng thể

**"Multi-Tenant AI Agent Factory SaaS"**  
Mỗi người dùng (solo founder) sở hữu một "đội ngũ AI" riêng biệt và an toàn.  
Platform là "hệ điều hành cho các công ty AI".

## Kiến trúc 4 Lớp (từ a16z)

```
[Lớp D: Con người]        Chỉ ra quyết định lớn, approve  
         ↕
[Lớp A: PaperClip]        CEO ảo — điều phối chiến lược, quản lý vòng lặp
         ↕
[Lớp B: OpenClaw]         Thực thi — nhận lệnh từ Telegram/Discord, dùng LLM
         ↕
[Lớp C: M1 Max]           Hạ tầng — Ollama/LM Studio chạy LLM cục bộ
```

Mekong-cli mapping:
- Lớp D = User qua mekongmind.com
- Lớp A = PEV Engine (Planner/Orchestrator)  
- Lớp B = `.claude/commands/` + agents
- Lớp C = `mekong/adapters/` (Ollama local)

## Tech Stack Target

### Phase 1 (Seed)
```
Ollama (local LLM)
SQLite + ChromaDB (memory)
Python 3.11 (seed/ layer)
Docker Compose (orchestration)
```

### Phase 2-3 (Tree → Forest)
```
FastAPI (gateway)
Redis 7 (task queue)
Docker (per-user containers)
JWT (auth)
```

### Phase 4 (Land)
```
Temporal.io (long-running workflows — "PaperClip Supervisor")
pgvector (personal tenant memory)
Milvus (shared knowledge memory)
OpenTelemetry + Prometheus + Grafana (Harness Engineering)
Amplitude/PostHog (Feedback Loop)
Statsig (A/B testing — "Signals Loop")
```

## 5 Enforcement Gates (AI-Native CI/CD)

```
Gate 1: Validation     — Xác thực logic code
Gate 2: Security       — Quét bảo mật (không leak API keys, XSS, etc.)
Gate 3: Quality        — Code quality thresholds
Gate 4: Dependency     — Kiểm tra phụ thuộc an toàn
Gate 5: Deployment     — Smoke test trước khi push production
```

## Feedback Loop Architecture ("The Signals Loop")

```
User Interaction → Analytics → Offline Evals → Online Evals → A/B Test → Product Decision
```

Cụ thể:
1. User gửi task → PostHog track event
2. AI xử lý → Log telemetry (thành công/thất bại)
3. Hàng tuần: Phân tích "task nào hay fail?" → Train/tune
4. Deploy improvement → A/B test với Statsig
5. Business metric impact → Next decision

## SDLC Scaffold (AI-First Pattern)

```
Specification → Design → Code → Test → Deploy → Monitor → Feedback
```

Mỗi bước:
- Có Agent chuyên biệt
- Có file ownership rõ ràng
- Có Gate kiểm tra output
- Có rollback nếu Gate fail

## Nguồn Tham khảo Kỹ thuật

- Microsoft Agent Framework (MAF): Multi-agent orchestration
- LangGraph: Stateful agent workflows  
- AutoGen: Agent conversation patterns
- CrewAI: Role-based multi-agent
- Temporal.io: Durable workflow execution
- Fly.io Machines: Isolated VM per execution

## Câu hỏi Chưa giải quyết

1. MAF vs LangGraph vs CrewAI — chọn cái nào cho Phase 4?
2. Fly.io vs Docker per-container — cost model trên M1 Max?
3. Milvus (heavy) hay ChromaDB (light) cho shared memory?
