# Infrastructure Hardening Guide

> Securing and hardening Mekong CLI production deployments

**Last Updated**: 2026-06-21  
**Target Version**: Mekong CLI v6.0+  
**Migration Type**: Progressive security hardening with compliance validation

---

## Overview

Infrastructure hardening secures Mekong CLI deployments against threats, ensures compliance with security standards (PCI DSS, GDPR), and establishes operational resilience. This guide consolidates security best practices, deployment hardening, and monitoring setup.

### What Gets Hardened

| Component | Hardening Actions |
|-----------|-------------------|
| **Gateway API** | Authentication, rate limiting, input validation, CORS, security headers |
| **Database** | Encryption at rest, connection pooling, backup strategy, access controls |
| **LLM Provider** | API key rotation, audit logging, cost controls, provider failover |
| **File System** | Permission tightening, secure temp dirs, log rotation, secret management |
| **Network** | TLS enforcement, firewall rules, VPC isolation, DDoS protection |
| **Observability** | Audit logging, metrics, tracing, alerting, anomaly detection |
| **Deployment** | Immutable artifacts, rollback procedures, CI/CD security gates |

### Hardening Phases

```
┌─────────────────────────────────────┐
│  Phase 1: Security Audit            │
│  - Run security scans               │
│  - Identify vulnerabilities         │
│  - Create remediation plan         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 2: Access Controls           │
│  - JWT configuration hardening     │
│  - API key rotation                │
│  - Principle of least privilege    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 3: Input Validation          │
│  - Schema enforcement              │
│  - Injection prevention            │
│  - Rate limiting per endpoint      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 4: Observability             │
│  - Audit logging enabled           │
│  - Metrics collection              │
│  - Alert rules configured          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 5: Compliance Validation     │
│  - PCI DSS scope review            │
│  - GDPR data mapping               │
│  - SOC 2 controls assessment       │
└─────────────────────────────────────┘
```

---

## Pre-Hardening Checklist

### 1. Baseline Security Assessment

```bash
# Run comprehensive security scan
mekong audit/security --scan all --report pdf

# Output: security-audit-YYYYMMDD.pdf
# Review findings and prioritize by severity

# Run AST (Application Security Testing)
# See: .github/workflows/ast-security-scan.yml
```

### 2. Backup Current State

```bash
# Backup database
sqlite3 ~/.mekong/main.db ".backup ~/backup/main-$(date +%Y%m%d).db"

# Backup settings
cp ~/.mekong/settings.json ~/backup/settings-$(date +%Y%m%d).json

# Backup gateway config
sudo launchctl list | grep mekong > ~/backup/gateway-status-$(date +%Y%m%d).txt
```

### 3. Verify Deployment Method

Hardening steps vary by deployment:

| Deployment | Hardening Focus |
|------------|-----------------|
| **Local Development** | Basic auth, local firewall, dev secrets |
| **Cloudflare Workers** | Edge security, KV/D1 encryption, WAF |
| **Docker/Kubernetes** | Pod security policies, network policies, secrets management |
| **VM (VPS)** | OS hardening, fail2ban, firewall, SSH keys |

---

## Phase 1: Security Audit & Baseline

### Run Full Security Audit

```bash
# Comprehensive security audit
mekong audit/security --type all --report html --output ~/reports/security-audit.html

# Audit categories:
# - Authentication & Authorization
# - Data Protection
# - Input Validation
# - Secrets Management
# - Dependency Security
# - Infrastructure Security
```

### AST Scanning

The repository includes GitHub Actions workflows for:

1. **Dependency scanning** (dependabot, npm audit, pip-audit)
2. **SAST** (Semgrep, CodeQL)
3. **Secrets scanning** (GitGuardian, truffleHog)
4. **Container scanning** (Trivy)

Check the Security tab in GitHub Actions for latest scan results.

### Penetration Testing

Before production deployment, consider:
- External pen test (for customer-facing deployments)
- Internal red team exercise (for enterprise)
- Automated pen testing tools (OWASP ZAP, Burp Suite)

---

## Phase 2: Access Controls

### JWT Configuration Hardening

Edit `~/.mekong/settings.json`:

```json
{
  "auth": {
    "jwt": {
      "algorithm": "HS256",
      "access_token_ttl_minutes": 15,
      "refresh_token_ttl_days": 30,
      "refresh_token_reuse_detection": true,
      "failed_login_delay_ms": 2000,
      "max_concurrent_sessions_per_user": 5,
      "require_https": true,
      "issuer": "mekong-cli",
      "audience": "mekong-api"
    }
  }
}
```

**Key Hardening:**
- Short access token TTL (15 min)
- Refresh token rotation with reuse detection
- HTTPS enforcement
- Session limits per user

### API Key Management

```bash
# Generate strong API keys
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Rotate existing keys periodically
# Store in: ~/.mekong/api_keys/ (chmod 600)
```

Configure in settings:

```json
{
  "api_keys": {
    "key_rotation_days": 90,
    "allow_key_reuse": false,
    "min_key_length": 32,
    "hash_algorithm": "argon2id"
  }
}
```

### Principle of Least Privilege

Review command permissions:

```bash
# List all commands with their required permissions
mekong admin permissions list --format json | jq '.[] | {name, permissions}'
```

Restrict dangerous commands:

```json
{
  "permissions": {
    "deny": ["admin:shutdown", "db:drop", "billing:charge"],
    "ask": ["deploy:prod", "plugin:install", "user:delete"]
  }
}
```

---

## Phase 3: Input Validation & Rate Limiting

### Schema Validation

All API endpoints use Pydantic validation. Ensure schemas are strict:

```python
# Example: strict validation in FastAPI
from pydantic import BaseModel, Field, field_validator

class CreateCommand(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    layer: str = Field(..., pattern="^(founder|business|product|engineering|ops)$")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Name must be lowercase alphanumeric with hyphens')
        return v
```

### Rate Limiting

Configure tier-based rate limiting:

```json
{
  "rate_limiting": {
    "enabled": true,
    "strategy": "token_bucket",
    "tiers": {
      "starter": {
        "requests_per_minute": 60,
        "burst_capacity": 10
      },
      "growth": {
        "requests_per_minute": 300,
        "burst_capacity": 50
      },
      "pro": {
        "requests_per_minute": 1000,
        "burst_capacity": 100
      }
    },
    "bypass_tiers": ["trusted_ip"],
    "storage": "redis"
  }
}
```

### Input Sanitization

- All user input sanitized before processing
- HTML escaping in logs and responses
- SQL parameterized queries only (no string concatenation)
- Command injection prevention via subprocess wrappers

---

## Phase 4: Observability & Monitoring

### Enable Audit Logging

```bash
# In settings.json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "audit_enabled": true,
    "audit_events": [
      "auth.login",
      "auth.logout",
      "command.execute",
      "plugin.install",
      "billing.charge",
      "admin.action"
    ]
  }
}
```

Audit logs written to: `~/.mekong/logs/audit.jsonl`

### Metrics Collection

The gateway exposes Prometheus metrics at `/metrics`:

```bash
# Scrape metrics
curl http://localhost:8000/metrics

# Key metrics to monitor:
# - mekong_requests_total
# - mekong_request_duration_seconds
# - mekong_errors_total
# - mekong_credits_consumed
# - mekong_plugin_executions
```

### Alerting Rules

Example Prometheus alert rules:

```yaml
groups:
  - name: mekong.alerts
    rules:
      - alert: HighErrorRate
        expr: rate(mekong_errors_total[5m]) > 0.05
        for: 2m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(mekong_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "95th percentile latency > 2s"
```

### Tracing

Enable OpenTelemetry:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_RESOURCE_ATTRIBUTES="service.name=mekong-gateway"
```

---

## Phase 5: Compliance Validation

### PCI DSS Scope Review

If processing payments:

1. **Complete PCI DSS Scope Review** (`compliance/PCI-DSS-Scope-Review.md`)
2. **Implement required controls**:
   - Encrypt all cardholder data
   - Use TLS 1.2+ for all transmissions
   - Implement access controls and logging
   - Regular vulnerability scanning

3. **Validate compliance**:

```bash
# Run PCI DSS compliance check
mekong compliance pci-dss --check --report pdf
```

### GDPR Compliance

1. **Data Mapping** (`GDPR Phase 1`): Document all personal data processing
2. **Consent Management**: Implement consent tracking
3. **Data Subject Rights**: Build DSAR endpoints
4. **Privacy by Design**: Embed privacy into all features

See `compliance/` for full GDPR documentation.

### SOC 2 Type II Preparation

For enterprise customers:

- Document all security controls
- Implement change management procedures
- Establish incident response plan
- Regular third-party audits

---

## Deployment-Specific Hardening

### Cloudflare Workers

See [Cloudflare Deployment Guide](cloudflare-deployment-guide.md) for:

- D1 database encryption
- KV namespace security
- Worker secrets management
- WAF rules configuration

### Docker/Kubernetes

```yaml
# PodSecurityPolicy example
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: mekong-gateway
spec:
  privileged: false
  runAsNonRoot: true
  requireRunAsUser:
    - 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false  # Set true if possible
  volumes:
    - 'secret'
    - 'configMap'
```

### VM (Ubuntu/Debian)

```bash
# OS hardening
sudo apt update && sudo apt upgrade -y
sudo apt install -y ufw fail2ban auditd

# Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw enable

# SSH hardening (in /etc/ssh/sshd_config):
# PasswordAuthentication no
# PermitRootLogin no
# ClientAliveInterval 300
# ClientAliveCountMax 2
```

---

## Continuous Hardening

### Security Scanning in CI

The repository includes GitHub Actions workflows that run on every PR:

1. **dependabot.yml** - Dependency updates
2. **ast-security-scan.yml** - Static analysis
3. **container-scanning.yml** - Docker image vulnerabilities

Ensure all checks pass before merging.

### Regular Hardening Tasks

| Frequency | Task |
|-----------|------|
| Daily | Review security alerts |
| Weekly | Check failed login attempts, audit log review |
| Monthly | Rotate API keys, update dependencies, scan for secrets |
| Quarterly | Full security audit, penetration test, compliance review |
| Annually | Third-party security assessment, policy review |

---

## Rollback & Incident Response

### Incident Response Playbook

1. **Contain**: Isolate affected systems
2. **Investigate**: Determine scope and impact
3. **Eradicate**: Remove malicious presence
4. **Recover**: Restore from clean backups
5. **Post-mortem**: Document lessons learned

See [Operator Runbook](operator-runbook.md) for detailed procedures.

### Emergency Rollback

```bash
# Quick database rollback
sqlite3 ~/.mekong/main.db ".restore ~/backup/main-YYYYMMDD.db"

# Rollback configuration
cp ~/backup/settings-YYYYMMDD.json ~/.mekong/settings.json

# Restart gateway
sudo launchctl kickstart -k system/com.mekong.gateway
```

---

## Verification Checklist

Before declaring infrastructure hardened:

- [ ] All security scans pass with no high/critical findings
- [ ] JWT tokens use strong algorithms and short TTLs
- [ ] API keys are rotated and stored securely
- [ ] Rate limiting is enforced on all endpoints
- [ ] Audit logging captures all security events
- [ ] Metrics and alerts are configured
- [ ] TLS 1.2+ enforced for all external traffic
- [ ] Database is encrypted at rest
- [ ] Secrets managed via environment variables or vault (not in code)
- [ ] CI/CD includes security gates
- [ ] Incident response plan documented and tested
- [ ] Compliance reports generated (PCI DSS, GDPR as applicable)

---

## Related Documentation

- [Plugin Security Hardening](plugin-security-hardening.md) - Plugin-specific security
- [Deployment Guide](deployment-guide.md) - Platform-specific deployment instructions
- [Rollback Procedures](rollback-procedures.md) - Emergency rollback procedures
- [Operator Runbook](operator-runbook.md) - Day-to-day operations
- [Compliance Overview](compliance/) - PCI DSS, GDPR documentation
- [Security ADRs](./architecture/adrs/) - Security-related architecture decisions

---

**Hardening Complete?** → Your infrastructure now meets security best practices and compliance requirements. Continue regular security assessments to maintain security posture.
