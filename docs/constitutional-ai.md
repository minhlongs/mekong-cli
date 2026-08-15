# Constitutional AI

> Ethical guardrails for the ZenOS ecosystem — ensuring AI actions align with human-centric principles

**Last Updated**: 2026-06-18  
**Implementation**: `src/core/constitution.py`, `src/api/constitutional_middleware.py`  
**Related**: [`docs/economic-particles.md`](./economic-particles.md), [`docs/founder-genome.md`](./founder-genome.md)

---

## Overview

Constitutional AI embeds a **written constitution** into the AI decision-making process. Inspired by Anthropic's approach, ZenOS uses a rule-based + LLM-assisted review system that evaluates every significant action against 9 core principles before execution.

### The Review Process

```
┌─────────────────────────────────────────────────────────────┐
│                    CONDUCTUTIONAL REVIEW                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Action Request → Build Context → Extract Parameters      │
│         │                │                   │              │
│         ▼                ▼                   ▼              │
│  Evaluate 9 Principles (parallel)                         │
│    │    │    │    │    │    │    │    │    │             │
│         ▼                ▼                   ▼              │
│   Weighted Score Calculation                               │
│         │                                                  │
│         ▼                                                  │
│   Decision: APPROVE | MODIFY | REJECT | HUMAN_REVIEW      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The 9 Principles

Each principle is evaluated independently with a score of 0.0-1.0.

### 1. Safety (Weight: 1.2)

**Description**: No harm to users, systems, or data

**Evaluation**: Pattern matching for dangerous operations

```python
DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf /*", ":(){ :|:& };",  # Fork bomb
    "dd if=/dev/zero", "mkfs", "format",
    "> /dev/sda", "shutdown", "reboot",
    "kill -9 -1", "killall",
    "chmod -R 777", "sudo", "doas"
]
```

**Scoring**:
- `0.0` - Dangerous pattern detected (fork bomb, disk destruction)
- `0.0` - System shutdown commands
- `0.2` - Credentials in plaintext
- `0.3` - Destructive without `--force` flag
- `0.7` - Destructive with confirmation
- `1.0` - No safety concerns

### 2. Security (Weight: 1.1)

**Description**: Protection against unauthorized access

**Evaluation**: Credential exposure, protocol security

```python
CREDENTIAL_PATTERNS = [
    (r"password\s*=", "plaintext password"),
    (r"api[_-]?key\s*=", "plaintext API key"),
    (r"token\s*=", "plaintext token"),
    (r"secret\s*=", "plaintext secret")
]
```

**Scoring**:
- `0.1` - Credentials exposed in command
- `0.3` - TLS certificate validation disabled (`curl -k`)
- `0.5` - HTTP instead of HTTPS (no MITM protection)
- `0.85` - No security violations
- `1.0` - Encryption/secure protocols used

### 3. Privacy (Weight: 1.0)

**Description**: Personal data protection and consent

**Evaluation**: PII handling, logging of sensitive data

```python
PII_KEYWORDS = [
    "ssn", "social security", "passport", "driver license",
    "email", "phone", "address", "birth", "medical",
    "password", "token", "secret", "api_key"
]
```

**Scoring**:
- `0.3` - PII without encryption mention
- `0.2` - Credentials being logged
- `0.9` - No PII detected
- `1.0` - Explicit encryption/privacy protection

### 4. Fairness (Weight: 1.0)

**Description**: No discriminatory bias or unfair treatment

**Evaluation**: Sensitive attribute filtering, batch operations

**Scoring**:
- `0.2` - Filtering by race, gender, religion, age, etc.
- `0.6` - Large batch (>1000) without rate limiting
- `0.9` - No fairness concerns

### 5. Transparency (Weight: 0.9)

**Description**: Clear, explainable actions and decisions

**Evaluation**: Black-box operations, attribution requirements

**Scoring**:
- `0.6` - Internal/private operation (`_private_method`)
- `0.7` - Agent action without description metadata
- `0.6` - Generated content without source attribution
- `0.85` - Action is transparent

### 6. Accountability (Weight: 0.9)

**Description**: Clear responsibility for outcomes

**Evaluation**: User tracking, audit trails, irreversible operations

**Scoring**:
- `0.5` - No user context for accountability
- `0.7` - Action without explicit audit_id
- `0.6` - Irreversible operation without dry-run option
- `0.9` - Accountability mechanisms present

### 7. Human Oversight (Weight: 1.0)

**Description**: Humans in critical decision loops

**Evaluation**: High-risk actions require human approval

```python
HIGH_RISK_ACTIONS = [
    "financial_transaction", "payout", "delete_user",
    "deactivate", "legal", "compliance_violation",
    "data_breach", "shutdown"
]
```

**Scoring**:
- `0.2` - High-risk action without `human_approved` in context
- `0.5` - Fully automated with no review requirement
- `0.9` - Human oversight adequate

### 8. Beneficence (Weight: 0.8)

**Description**: Actions should benefit users/system

**Evaluation**: Intent clarity, cost-benefit analysis

**Scoring**:
- `0.7` - No explicit intent stated
- `0.4` - High resource cost (>100) for low benefit (<0.3)
- `0.6` - Purely destructive action (no constructive purpose)
- `0.9` - Action appears beneficial

### 9. Sustainability (Weight: 0.7)

**Description**: Resource-conscious, long-term viable

**Evaluation**: Resource limits, infinite loops, cleanup

**Scoring**:
- `0.1` - Potential infinite loop detected
- `0.4` - High memory usage (>4GB)
- `0.5` - Inefficient algorithm (bubble sort, factorial recursive)
- `0.95` - Resource cleanup operation
- `0.85` - Resource usage appears sustainable

---

## Overall Score Calculation

The overall constitutional score is a **weighted average**:

```python
# Principle weights
PRINCIPLE_WEIGHTS = {
    SAFETY: 1.2,
    SECURITY: 1.1,
    PRIVACY: 1.0,
    FAIRNESS: 1.0,
    HUMAN_OVERSIGHT: 1.0,
    ACCOUNTABILITY: 0.9,
    TRANSPARENCY: 0.9,
    BENEFICENCE: 0.8,
    SUSTAINABILITY: 0.7,
}

total_weight = sum(PRINCIPLE_WEIGHTS.values())
weighted_sum = sum(
    result.score * PRINCIPLE_WEIGHTS[result.principle]
    for result in principle_results
)
overall_score = weighted_sum / total_weight
```

### Thresholds

| Threshold | Meaning |
|-----------|---------|
| `≥ 0.7` | Compliant (allowed in ENFORCE mode) |
| `0.3 - 0.7` | Modified required (warnings in AUDIT mode) |
| `< 0.3` | Critical failure (always blocked) |

---

## Operational Modes

### Monitor Mode

```python
from src.api.constitutional_middleware import (
    ConstitutionalReview,
    MiddlewareMode
)

config = MiddlewareConfig(
    mode=MiddlewareMode.MONITOR,
    constitution=constitution
)
```

- Logs all reviews
- Never blocks requests
- Used for baseline data collection

### Audit Mode

```python
config = MiddlewareConfig(
    mode=MiddlewareMode.AUDIT,
    constitution=constitution
)
```

- Adds `X-Constitutional-Score` header to responses
- Adds per-principle headers: `X-Constitutional-Safety`, etc.
- Logs failures at WARNING level
- Used for compliance reporting

### Enforce Mode

```python
config = MiddlewareConfig(
    mode=MiddlewareMode.ENFORCE,
    constitution=constitution,
    minimum_score=0.7
)
```

- Blocks non-compliant requests with HTTP 403
- Returns detailed failure reasons
- Used in production

---

## API Integration

### FastAPI Middleware

```python
from fastapi import FastAPI
from src.api.constitutional_middleware import setup_constitutional_middleware

app = FastAPI()

# Add constitutional review middleware
setup_constitutional_middleware(
    app=app,
    mode="enforce",  # "monitor", "audit", "enforce"
    minimum_score=0.7
)
```

### Manual Review

```python
from src.core.constitution import get_constitution

constitution = get_constitution()

review = constitution.review(
    action="api:post:/v1/finance/invoice/create",
    context={
        "user_id": "opc_001_abc123",
        "particle_id": "particle_xyz",
        "has_auth": True
    },
    parameters={
        "amount": 5000000,
        "client": "Acme Corp",
        "currency": "VND"
    },
    metadata={
        "agent": "finance-agent",
        "intent": "create-invoice-for-client",
        "priority": "normal"
    }
)

print(f"Score: {review.overall_score}")
print(f"Passed: {review.passed}")
print(f"Blocked: {review.blocked}")

for result in review.principle_results:
    print(f"  {result.principle.value}: {result.score} - {result.reason}")
```

---

## LLM-Assisted Evaluation

For nuanced principles, the system can optionally use an LLM:

```python
from src.core.constitution import Constitution

constitution = Constitution(llm_client=my_llm_client)

# The LLM assists with:
# - Beneficence: Is this action actually beneficial?
# - Transparency: Is the explanation clear?
# - Fairness: Subtle bias detection
```

**Fallback behavior**: If LLM unavailable, rule-based evaluators handle all principles.

---

## Configuration

### Constitution Definition

The runtime reviewer is defined in `src/core/constitution.py` and exposed through `get_constitution()`. The default mode is `audit`: reviews are logged and response headers are added, but requests are not blocked.

```json
{
  "version": "1.0",
  "name": "ZenOS Constitution",
  "description": "Constitutional framework for Economic Particles",
  "principles": [
    {
      "id": "safety",
      "priority": 1,
      "description": "Human wellbeing takes precedence over efficiency and profit",
      "weight": 1.2,
      "evaluator": "rule_based"
    },
    {
      "id": "human_oversight",
      "priority": 2,
      "description": "AI systems serve humans, not the reverse",
      "weight": 1.0,
      "evaluator": "rule_based"
    },
    {
      "id": "transparency",
      "priority": 3,
      "description": "All decisions affecting the particle must be explainable",
      "weight": 0.9,
      "evaluator": "rule_based"
    }
  ],
  "amendment_process": {
    "proposal_threshold": 0.1,
    "voting_period_days": 30,
    "quorum": 0.3,
    "pass_threshold": 0.666,
    "cooling_period_days": 7
  }
}
```

### Per-Particle Constitution Override

Particle-specific constitutions should be injected into the constitutional middleware or orchestrator at runtime. The reviewer accepts a custom `Constitution` instance:

```python
from src.api.constitutional_middleware import ConstitutionalReview, MiddlewareConfig, MiddlewareMode
from src.core.constitution import Constitution

particle_constitution = Constitution()
review = ConstitutionalReview(
    MiddlewareConfig(
        mode=MiddlewareMode.AUDIT,
        constitution=particle_constitution,
    )
)
```

Custom principles can be added in future by extending `src/core/constitution.py` with rule-based evaluators that return `(passed, score, reason, details)`.

---

## Response Headers

In AUDIT mode, responses include:

```
HTTP/1.1 200 OK
X-Constitutional-Score: 0.85
X-Constitutional-Passed: true
X-Constitutional-Duration-Ms: 12.3
X-Constitutional-Safety: 0.95
X-Constitutional-Security: 0.90
X-Constitutional-Privacy: 0.85
...
```

### Blocked Response (ENFORCE mode)

```json
{
  "error": "constitutional_violation",
  "message": "Request blocked by Constitutional AI review",
  "details": {
    "overall_score": 0.45,
    "minimum_required": 0.7,
    "failed_principles": [
      {
        "principle": "safety",
        "score": 0.0,
        "reason": "Potentially dangerous pattern: sudo"
      },
      {
        "principle": "security",
        "score": 0.3,
        "reason": "Credential exposed in command: password="
      }
    ]
  },
  "suggestions": [
    "Review command for dangerous operations",
    "Ensure credentials are passed via environment, not command line"
  ]
}
```

---

## Logging

Constitutional reviews are logged with structured data:

```json
{
  "timestamp": "2025-06-18T15:30:00Z",
  "path": "/v1/finance/invoice/create",
  "method": "POST",
  "overall_score": 0.85,
  "passed": true,
  "blocked": false,
  "duration_ms": 12.3,
  "principles": [
    {
      "principle": "safety",
      "score": 0.95,
      "passed": true
    },
    // ...
  ]
}
```

Log level:
- `INFO` - Passing reviews (if `log_all_reviews=True`)
- `WARNING` - Failing reviews (always logged)
- `ERROR` - Evaluation errors

---

## Testing

### Unit Tests

```python
from src.core.constitution import Constitution, Principle

def test_safety_evaluation():
    constitution = Constitution()

    # Dangerous command should fail
    review = constitution.review(
        action="shell",
        parameters={"command": "rm -rf /"}
    )
    assert not review.principle_results[Principle.SAFETY].passed
    assert review.principle_results[Principle.SAFETY].score == 0.0

def test_safe_command():
    review = constitution.review(
        action="shell",
        parameters={"command": "ls -la"}
    )
    assert review.principle_results[Principle.SAFETY].passed
    assert review.principle_results[Principle.SAFETY].score > 0.8
```

### Integration Tests

```bash
# Test API with constitutional middleware
python3 -m pytest tests/api/test_constitutional_middleware.py -v

# Test enforcement mode blocking
python3 -m pytest tests/api/test_constitutional_enforce.py -v

# Test particle constitutional alignment
python3 -m pytest tests/zenos/test_constitutional_particles.py -v
```

---

## Custom Principles

### Adding a New Principle

1. Add to `Principle` enum in `src/core/constitution.py`:

```python
class Principle(Enum):
    SUSTAINABILITY = "sustainability"
    // Add:
    vietnamese_labor_law = "vietnamese_labor_law"
```

2. Implement evaluator:

```python
def _evaluate_vietnamese_labor_law(
    self, action: str, context: Dict, parameters: Dict, metadata: Dict
) -> Tuple[bool, float, str, Optional[Dict]]:
    """Check compliance with Vietnamese Labor Code."""

    # Check for probation period violations
    if "probation" in parameters.get("contract_type", ""):
        probation_months = parameters.get("probation_duration", 0)
        if probation_months > 2:
            return False, 0.3, "Probation exceeds 60-day limit", {"months": probation_months}

    # Check overtime compliance
    overtime_hours = parameters.get("overtime_hours", 0)
    if overtime_hours > 16:
        return False, 0.2, "Monthly overtime exceeds legal limit", {"hours": overtime_hours}

    return True, 0.9, "Labor law compliant", None
```

3. Add to evaluator map:

```python
evaluator_map = {
    # ... existing
    Principle.VIETNAMESE_LABOR_LAW: self._evaluate_vietnamese_labor_law,
}
```

4. Add weight to `PRINCIPLE_WEIGHTS`:

```python
PRINCIPLE_WEIGHTS = {
    # ...
    Principle.VIETNAMESE_LABOR_LAW: 1.0,
}
```

---

## Constitutional Amendments

Particles can propose amendments to their constitution using Ostrom governance principles:

### Amendment Process

1. **Proposal**: Particle with trust_score ≥ 70 can propose
2. **Deliberation**: 14-day comment period
3. **Monitoring**: 30-day observation of effects
4. **Vote**: 2/3 majority + 30% quorum
5. **Cooling**: 7-day waiting period
6. **Enactment**: Version bump, old version archived

### CLI Command

```bash
# Propose amendment
mekong constitution propose-amendment \
  --particle particle_abc \
  --principle safety \
  --change "Add prohibition on remote data deletion without backup"

# Vote on amendment
mekong constitution vote \
  --amendment amd_123 \
  --vote yes \
  --reason "Safety improvement"

# Check amendment status
mekong constitution amendment-status --amendment amd_123
```

### Amendment Record

```json
{
  "id": "amd_001",
  "constitution_id": "zenos_v1",
  "proposer_particle": "particle_abc",
  "principle_id": "safety",
  "proposed_change": "Add pattern: 'drop database' to dangerous patterns",
  "proposed_at": "2025-06-18T15:00:00Z",
  "deliberation_end": "2025-06-22T15:00:00Z",
  "vote_opens": "2025-06-22T15:00:00Z",
  "vote_closes": "2025-07-22T15:00:00Z",
  "status": "voting",
  "votes": {
    "yes": 15,
    "no": 3,
    "abstain": 2
  },
  "quorum": 0.35,
  "result": null
}
```

---

## Troubleshooting

### False Positives

If legitimate actions are blocked:

```bash
# Temporarily adjust threshold
export CONSTITUTIONAL_MIN_SCORE=0.6

# Or add exception in metadata
metadata = {
    "const_exception": "safe_delete_with_backup",
    "const_exception_reason": "Backup verified before deletion"
}
```

### Performance Overhead

Constitutional review adds ~10-50ms per request. To optimize:

1. Cache review results for identical requests
2. Run in MONITOR mode and sample ENFORCE (1% of requests)
3. Exclude health checks: `exclude_paths=["/health", "/metrics"]`

### LLM Timeouts

If using LLM-assisted evaluation and hitting timeouts:

```python
# Increase timeout
config = MiddlewareConfig(
    llm_timeout_ms=5000,  # Default: 2000
    llm_fallback_to_rules=True  # Always fall back
)
```

---

## Monitoring & Observability

### Metrics to Track

| Metric | Target | Alert |
|--------|--------|-------|
| `constitutional_review_duration_ms` | < 50ms | > 100ms |
| `constitutional_score_avg` | > 0.85 | < 0.75 |
| `constitutional_blocked_requests` | N/A | > 5/min |
| `constitutional_principle_failures{principle}` | N/A | Spike > 200% |

### Grafana Dashboard

See `observability/dashboards/constitutional-ai.json` for pre-built dashboard with:

- Score distribution histogram
- Principle failure breakdown
- Block rate by endpoint
- Review latency percentiles

---

## References

- **Anthropic Constitutional AI**: <https://www.anthropic.com/news/constitutional-ai>
- **Implementation**: `src/core/constitution.py`
- **Middleware**: `src/api/constitutional_middleware.py`
- **Tests**: `tests/zenos/test_constitutional_ai.py`
- **Migration**: [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md)

---

**Next**: Learn about [`docs/founder-genome.md`](./founder-genome.md) to understand founder profiling.
