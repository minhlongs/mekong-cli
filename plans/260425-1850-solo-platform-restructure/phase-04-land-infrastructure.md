# Phase 04: Đất (Land — Infrastructure Platform)

> **Ưu tiên:** MEDIUM | **Thời gian:** Tháng 3+  
> **Mục tiêu:** Self-serve, revenue machine, "The Signals Loop"

## Components

### 4.1 Temporal.io (PaperClip Supervisor)

```python
# Thay thế Redis simple queue bằng Temporal workflows
# Benefit: durable execution, retry, rollback, long-running (30+ phút)
# Use case: "Xây dựng toàn bộ SaaS product từ ý tưởng"
```

### 4.2 Agent Marketplace (Clipmart — đã có!)

```
clipmart/           ← Existing PaperClip templates
# Add: template marketplace UI
# User chọn: "CTO AI", "CMO AI", "Data Analyst AI"
# Platform spawn agent với persona đó
```

### 4.3 AI-Native CI/CD (5 Gates)

```yaml
# .github/workflows/ai-native-ci.yml
gates:
  1-validation: python validate_logic.py
  2-security:   python scan_secrets.py && npm audit
  3-quality:    python quality_check.py  # coverage, complexity
  4-dependency: safety check && pip-audit
  5-deployment: python smoke_test.py $PROD_URL
```

### 4.4 Feedback Loop ("The Signals Loop")

```python
# Integration: PostHog (đã có trong STRATEGY.md!)
# Track: task_submitted, task_completed, task_failed, user_satisfied
# Weekly: AI phân tích → propose improvements → A/B test
# Stack: PostHog events → SQL analysis → Anthropic API → action items
```

### 4.5 Observability (Harness Engineering)

```yaml
# observability/ đã có Prometheus + Grafana + OTel!
# Cần wire vào agent execution:
# - Track: agent_think_time, tool_call_duration, memory_recall_hits
# - Alert: agent_failure_rate > 5%
# - Dashboard: "Agent Health" panel trong Grafana
```

### 4.6 One-Click "Create Company" Onboarding

```
1. User đăng ký → Polar.sh checkout
2. Webhook → auto-provision: user_id, memory namespace, credits
3. User nhập "tầm nhìn công ty" → CEO Agent tạo org structure
4. Done: User có team AI sẵn sàng làm việc
```

## Files cần tạo/sửa

| File | Hành động |
|------|-----------|
| `.github/workflows/ai-native-ci.yml` | Tạo mới |
| `observability/agent-metrics.py` | Tạo mới |
| `apps/api/src/routes/onboarding.py` | Tạo mới |
| `clipmart/marketplace-api.py` | Tạo mới |
| `feedback/signals_loop.py` | Tạo mới |

## Revenue Model Validation

```
Hiện tại: $49/$149/$499 tiers (Polar.sh)
Target: 100 Starter users = $4,900 MRR
Path: 
  - Phase 01-02 (seed+tree): dogfood internally
  - Phase 03 (forest): invite 10 beta users
  - Phase 04 (land): public launch, paid tier enforcement
```

## Success Criteria

```
✅ User đăng ký → có AI team trong 60 giây
✅ Task thực thi → log trong Grafana
✅ Agent fail → alert + auto-retry
✅ Weekly: AI gợi ý 3 cải tiến dựa trên usage data
✅ Revenue: $4,900 MRR (100 Starter)
```

## Câu hỏi Chưa giải quyết

1. Temporal.io vs Prefect — cái nào nhẹ hơn cho M1 Max?
2. PostHog self-hosted hay cloud? (Data privacy)
3. Agent Marketplace monetization — take rate bao nhiêu %?
