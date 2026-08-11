Execute SOP 'monitoring' (layer ops) according to its steps.

SOP content:
# SOP: Ops Monitoring & Observability
**Layer:** Ops | **Version:** 1.0.0 | **Owner:** OPS (Operations)

## Intent
Proactive monitoring with clear alerting thresholds and response playbooks.

## Dashboards
- `observability/dashboards/agent-performance.json` — agent metrics
- `observability/dashboards/cost-analysis.json` — LLM cost tracking
- `observability/dashboards/m1max-health.json` — system health

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Agent error rate | > 5% | > 15% |
| LLM token cost/day | > budget 80% | > budget 100% |
| CPU usage (M1 Max) | > 70% | > 90% |
| Disk usage | > 80% | > 95% |
| Response time p95 | > 5s | > 10s |

## Weekly Ops Review
- Review all alerts from past week
- Tune thresholds if false positive rate > 20%
- Check cost trends in Grafana
- Update this SOP if new monitoring needs identified

## Tools
- Prometheus: metrics collection
- Grafana: visualization
- OpenTelemetry: trace collection
- `/audit-trail`: audit log review
y resolution via monitoring
- Communicate status to stakeholders

### §5 — Post-Mortem (P1/P2 only)
- Timeline, root cause, impact
- Action items with owners and deadlines
- Post-mortem review within 5 business days

## Escalation
P1 not resolved in 1 hour → CEO emergency notification.
