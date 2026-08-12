# Plugin Security Hardening Guide

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Production Ready
**Audience**: Plugin developers, security reviewers, operators

---

## Table of Contents

- [Overview](#overview)
- [Threat Model](#threat-model)
- [Secure Development](#secure-development)
- [Permissions](#permissions)
- [Secrets Management](#secrets-management)
- [Isolation & Sandboxing](#isolation--sandboxing)
- [Dependencies](#dependencies)
- [Code Signing](#code-signing)
- [Runtime Security](#runtime-security)
- [Supply Chain Security](#supply-chain-security)
- [Compliance](#compliance)
- [Incident Response](#incident-response)
- [Security Testing](#security-testing)
- [Hardening Checklists](#hardening-checklists)

---

## Overview

This guide defines security requirements for Mekong CLI plugins. The plugin system implements **defense-in-depth** with:

1. **Manifest validation** - Schema + security policy enforcement
2. **Permission boundaries** - Capability-based access control
3. **Process isolation** - Worker/container/WASM sandboxing
4. **Runtime monitoring** - Audit logs + constitutional review
5. **Supply chain verification** - Code signing + registry validation

All plugins **must** pass validation before registration:

```bash
# Validate plugin before submission
python3 -m src.core.plugin_validator validate --manifest plugin.json

# Or use Mekong CLI
mekong plugin validate ./my-plugin
```

---

## Threat Model

### Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| User credentials (API keys, tokens) | Critical | Account takeover, data breach |
| Plugin marketplace integrity | High | Widespread supply chain attack |
| MCU billing system | High | Financial loss, fraud |
| User data (PII, business data) | Critical | Privacy violation, GDPR fines |
| Mekong CLI host system | Critical | System compromise, lateral movement |
| Command execution context | High | Privilege escalation |

### Adversary Capabilities

| Threat | Capability | Mitigation |
|--------|------------|------------|
| Malicious plugin author | Write plugin with hidden payload | Code review, sandboxing, permissions |
| Compromised dependency | Inject malware via npm/PyPI | SBOM, pinned versions, integrity checks |
| Man-in-the-middle | Tamper plugin download | HTTPS-only, signature verification |
| Privilege escalation | Escape sandbox | Minimal permissions, seccomp/AppArmor |
| Data exfiltration | Steal credentials, PII | DLP, encrypted storage, audit logs |
| Denial of service | Resource exhaustion | CPU/memory limits, timeout enforcement |

### Attack Surfaces

```
┌─────────────────────────────────────────────────────────────┐
│                    Attack Surfaces                         │
├─────────────────────────────────────────────────────────────┤
│  1. Plugin Manifest (metadata, dependencies)              │
│  2. Plugin Code (arbitrary code execution)                │
│  3. Dependency Tree (transitive vulnerabilities)          │
│  4. Configuration (injection, path traversal)             │
│  5. IPC/API (command injection, auth bypass)              │
│  6. Runtime (sandbox escape, resource abuse)              │
│  7. Distribution (tampering, impersonation)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Secure Development

### Development Environment

```bash
# Use isolated development environment
python3 -m venv .venv
source .venv/bin/activate

# Enable security scanning in dev
pip install bandit safety semgrep
bandit -r src/
safety check
```

### Code Quality Gates

All plugins **must**:

1. **No hardcoded secrets** - Scan before commit:
   ```bash
   git-secrets --scan-history
   gitleaks detect
   trufflehog --regex --entropy=False
   ```

2. **Type safety** - Enable strict type checking:
   ```python
   # mypy config
   strict = true
   warn_return_any = true
   disallow_untyped_defs = true
   ```

3. **Error handling** - Catch and log exceptions:
   ```python
   try:
       result = external_api_call()
   except requests.RequestException as e:
       logger.error("API call failed", extra={"error": str(e)})
       raise PluginError("Service unavailable") from e
   ```

4. **Input validation** - Validate all user inputs:
   ```python
   from pydantic import BaseModel, validator

   class CreateUserInput(BaseModel):
       email: EmailStr
       name: str = Field(min_length=1, max_length=100)

       @validator('name')
       def strip_whitespace(cls, v):
           return v.strip()
   ```

### Secure Patterns

**✅ DO:**

```python
# Use environment variables for configuration
api_key = os.getenv("PLUGIN_API_KEY")
if not api_key:
    raise ConfigurationError("API key not configured")

# Validate permissions before operations
if "file:write" not in plugin.permissions:
    raise PermissionError("Write permission required")

# Log security events
logger.info("plugin_action", {
    "plugin": plugin.id,
    "action": "user_create",
    "user_id": user_id,
    "ip": request.remote_addr,
})
```

**❌ DON'T:**

```python
# DON'T: Hardcode secrets
api_key = "sk_live_1234567890"  # BLOCKED

# DON'T: Use eval/exec
result = eval(user_input)  # BLOCKED

# DON'T: Disable SSL verification
requests.post(url, verify=False)  # BLOCKED

# DON'T: Log sensitive data
logger.debug(f"Processing payment: {credit_card}")  # BLOCKED
```

---

## Permissions

### Permission Model

Plugins declare required permissions in `plugin.json`:

```json
{
  "id": "com.example.stripe",
  "permissions": {
    "network": ["outbound:https://api.stripe.com/*"],
    "file": ["read:./data/*", "write:./output/*"],
    "env": ["STRIPE_API_KEY"],
    "child_processes": false,
    "database": ["read:users", "write:logs"]
  }
}
```

### Permission Types

| Permission | Description | Example |
|------------|-------------|---------|
| `network` | Outbound network access | `outbound:https://api.example.com/*` |
| `file` | Filesystem access | `read:/etc/allowed.conf`, `write:./output/` |
| `env` | Environment variable access | `read:API_KEY`, `write:TEMP_DIR` |
| `child_processes` | Spawn subprocesses | `true` (all), `["bash", "python"]` (limited) |
| `database` | Database access | `read:users`, `write:logs` |
| `mcu` | Billing operations | `consume`, `read_balance` |
| `cli` | Mekong CLI operations | `command:execute`, `hook:register` |

### Least Privilege Principle

```json
{
  "permissions": {
    "network": ["outbound:https://api.stripe.com/v1/*"],
    "file": ["read:./config/", "write:./cache/"],
    "env": ["STRIPE_SECRET_KEY"]
  }
}
```

**NOT**:

```json
{
  "permissions": {
    "network": ["*"],          // Overly broad
    "file": ["read:*"],        // Too permissive
    "child_processes": true    // Unnecessary
  }
}
```

### Permission Enforcement

The plugin runner enforces permissions at runtime:

```python
# PluginRunner checks before execution
def check_permission(plugin: PluginManifest, action: str, resource: str) -> bool:
    required = f"{action}:{resource}"
    for perm_type, allowed in plugin.permissions.items():
        if perm_matches(required, allowed):
            return True
    raise PermissionError(f"Missing permission: {required}")
```

---

## Secrets Management

### Never Store Secrets in Code

**Secure approach** - Use environment variables or encrypted config:

```python
import os
from mekong.config import get_secret

# Method 1: Environment variables (preferred)
api_key = os.getenv("PLUGIN_API_KEY")
if not api_key:
    raise ConfigurationError("PLUGIN_API_KEY not set")

# Method 2: Encrypted config store
api_key = get_secret("my-plugin", "api_key")
```

**Insecure approach** - **NEVER**:

```python
# BAD: Hardcoded secret
API_KEY = "sk_live_abc123"  # COMMIT RISK

# BAD: Config file in git
config = {
    "api_key": "secret123"  # EXPOSED
}

# BAD: Logging secrets
logger.info(f"Using API key: {api_key}")  # LOG LEAK
```

### Secret Rotation

Design for secret rotation:

```python
import time
from functools import lru_cache

class SecretAwareClient:
    def __init__(self):
        self._last_refresh = 0
        self._cache_ttl = 300  # 5 minutes

    @lru_cache(maxsize=1)
    def _get_api_key(self) -> str:
        # Called at most once per TTL
        return os.getenv("PLUGIN_API_KEY")

    def _should_refresh(self) -> bool:
        return time.time() - self._last_refresh > self._cache_ttl
```

### Config Encryption

For persistent plugin configuration:

```bash
# Encrypt config
mekong plugin config encrypt --plugin com.example.myplugin --file config.json

# Decrypt at runtime (automatic in plugin runner)
from mekong.config import get_plugin_config
config = get_plugin_config("com.example.myplugin")
```

Storage location: `~/.mekong/plugins/<plugin-id>/config.json.enc` (mode 600)

---

## Isolation & Sandboxing

### Loading Modes

| Mode | Isolation | Performance | Use Case |
|------|-----------|-------------|----------|
| `in-process` | None | Fastest | Trusted core plugins |
| `worker` | Thread/worker pool | Fast | Standard plugins |
| `process` | Separate process | Medium | Untrusted plugins |
| `wasm` | WebAssembly sandbox | Slower | Maximum security |

### Sandbox Configuration

```json
{
  "sandbox": {
    "enabled": true,
    "v8Isolate": true,
    "allowedModules": ["os", "path", "logging"],
    "blockedModules": ["subprocess", "socket", "ctypes"],
    "allowedHosts": ["https://api.example.com/*"],
    "maxMemory": 256,
    "maxCpuTime": 30000,
    "timeout": 60000
  }
}
```

### Resource Limits

```python
# Enforced by PluginRunner
RESOURCE_LIMITS = {
    "memory_mb": {
        "default": 256,
        "max": 1024,
        "enforcement": "cgroup (Linux) / rlimit (Unix)"
    },
    "cpu_time_ms": {
        "default": 30000,
        "max": 300000,
        "enforcement": "setrlimit(RLIMIT_CPU)"
    },
    "wall_time_sec": {
        "default": 60,
        "max": 600,
        "enforcement": "SIGALRM / asyncio timeout"
    },
    "disk_quota_mb": {
        "default": 100,
        "max": 1000,
        "enforcement": "quota system / tempdir cleanup"
    }
}
```

### File System Restrictions

Plugins run with restricted filesystem access:

```python
class FileSandbox:
    def __init__(self, plugin_id: str):
        self.base_dir = Path(f"~/.mekong/plugins/{plugin_id}").expanduser()
        self.allowed_paths = [self.base_dir / "data", self.base_dir / "cache"]

    def resolve_path(self, requested: str) -> Path:
        target = (self.base_dir / requested).resolve()

        # Check path traversal
        if not str(target).startswith(str(self.base_dir)):
            raise SecurityError(f"Path traversal blocked: {requested}")

        # Check allowed pattern
        if not any(target.is_relative_to(p) for p in self.allowed_paths):
            raise SecurityError(f"Access denied: {requested}")

        return target
```

---

## Dependencies

### Dependency Security

1. **Pin exact versions** - No floating ranges:

   ```json
   {
     "dependencies": {
       "python": ["requests==2.31.0", "pydantic==2.5.0"],
       "node": ["axios@1.6.0"]
     }
   }
   ```

2. **Generate SBOM** - Software Bill of Materials:

   ```bash
   # Python
   pip install cyclonedx-bom
   cyclonedx-py environment --output bom.xml

   # Node
   npm install --save-dev @cyclonedx/cyclonedx-npm
   npx cyclonedx-npm --output-file bom.xml
   ```

3. **Scan for vulnerabilities**:

   ```bash
   # Python
   safety check --json

   # Node
   npm audit --audit-level=high

   # Combined
   trivy fs --security-checks vuln .
   ```

4. **Minimize dependencies** - Each additional dependency is attack surface:

   ```python
   # Use stdlib when possible
   import json  # ✅ Standard library
   # vs
   import simplejson  # ❌ Extra dependency
   ```

### Dependency Pinning in Manifest

```json
{
  "id": "com.example.api-client",
  "dependencies": {
    "python": [
      "requests==2.31.0",
      "urllib3>=1.26.0,<2.0",
      "certifi>=2023.7.0"
    ]
  },
  "dependencyConfidence": {
    "requests": "pinned",
    "urllib3": "upper-bounded",
    "certifi": "upper-bounded"
  }
}
```

---

## Code Signing

### Plugin Signing

Verified plugins include a signature block:

```json
{
  "id": "com.example.verified",
  "name": "Verified Plugin",
  "version": "1.0.0",
  "signature": {
    "algorithm": "ed25519",
    "keyId": "abc123def456",
    "signature": "base64-encoded-signature-of-manifest",
    "timestamp": "2026-06-20T12:00:00Z"
  }
}
```

### Signature Verification

```python
import ed25519
import hashlib

def verify_signature(manifest_path: str, signature: dict) -> bool:
    # Load manifest excluding signature field
    manifest = load_manifest_excluding_signature(manifest_path)

    # Hash manifest
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode()
    manifest_hash = hashlib.sha256(manifest_bytes).digest()

    # Fetch public key from registry
    public_key_bytes = registry.get_public_key(signature["keyId"])
    public_key = ed25519.VerifyingKey(public_key_bytes)

    # Verify signature
    try:
        public_key.verify(
            manifest_hash,
            base64.b64decode(signature["signature"])
        )
        return True
    except ed25519.BadSignatureError:
        return False
```

### Registry Verification

Verified plugins from marketplace include:

```
plugins.mekongmind.com/api/v1/plugins/com.example.verified
→ Includes: signature, publisher info, audit status, scan results
```

---

## Runtime Security

### Audit Logging

All plugin actions must be audited:

```python
import structlog

logger = structlog.get_logger()

class AuditLogger:
    @staticmethod
    def log_plugin_action(
        plugin_id: str,
        action: str,
        user_id: str | None,
        parameters: dict,
        result: dict,
        duration_ms: float
    ):
        logger.info("plugin.action", **{
            "plugin_id": plugin_id,
            "action": action,
            "user_id": user_id,
            "parameters": redact_secrets(parameters),
            "result_status": result.get("status"),
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": get_current_request_id(),
        })
```

### Constitutional Review

Plugins triggering sensitive operations invoke constitutional review:

```python
from src.core.constitution import get_constitution

constitution = get_constitution()

review = constitution.review(
    action=f"plugin:{plugin_id}:{command_name}",
    context={
        "user_id": user_id,
        "plugin_id": plugin_id,
        "permissions": plugin.permissions,
    },
    parameters=redact_secrets(parameters),
    metadata={
        "source": "plugin",
        "mcu_cost": command.mcu_cost,
    }
)

if not review.passed and constitution.mode == "enforce":
    raise ConstitutionalViolationError(review.failed_principles)
```

### Resource Monitoring

```python
import resource
import psutil

class ResourceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime

    def check_limits(self, limits: dict) -> None:
        # Check memory
        mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
        if mem_mb > limits["memory_mb"]:
            raise ResourceExhaustedError(f"Memory limit exceeded: {mem_mb}MB")

        # Check CPU time
        cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        if cpu_time - self.start_cpu > limits["cpu_time_ms"] / 1000:
            raise ResourceExhaustedError("CPU time limit exceeded")

        # Check wall time
        if time.time() - self.start_time > limits["wall_time_sec"]:
            raise ResourceExhaustedError("Timeout exceeded")
```

---

## Supply Chain Security

### Plugin Discovery

Only install from trusted sources:

```bash
# Marketplace (verified)
mekong plugin install com.example.verified

# Local development
mekong plugin install ./local-plugin --local

# Git (with signature verification)
mekong plugin install git+https://github.com/trusted/plugin.git
```

### Dependency Pinning

Always pin dependencies to specific versions:

```json
{
  "dependencies": {
    "python": [
      "requests==2.31.0",        // ✅ Specific version
      "pydantic>=2.5.0,<3.0.0",  // ✅ Bounded range
      "urllib3>=1.26.0,<2.0"     // ✅ Upper bound
    ]
  }
}
```

### Integrity Verification

Plugins distributed via marketplace include checksums:

```python
def verify_plugin_integrity(plugin_path: Path, expected_sha256: str) -> bool:
    actual = hashlib.sha256(plugin_path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise IntegrityError(
            f"Plugin checksum mismatch: expected {expected_sha256}, "
            f"got {actual}"
        )
    return True
```

---

## Compliance

### Data Protection

Plugins handling personal data **must**:

1. **Encrypt at rest**:
   ```python
   from cryptography.fernet import Fernet

   def save_sensitive_data(data: dict, key: bytes):
       fernet = Fernet(key)
       encrypted = fernet.encrypt(json.dumps(data).encode())
       file_path.write_bytes(encrypted)
   ```

2. **Encrypt in transit**:
   ```python
   # Always use HTTPS
   response = requests.post("https://api.example.com/endpoint", ...)  # ✅
   response = requests.post("http://api.example.com/endpoint", ...)  # ❌
   ```

3. **Implement data retention**:
   ```python
   @scheduled_task("daily")
   def cleanup_old_data():
       cutoff = datetime.utcnow() - timedelta(days=30)
       db.query(UserData).filter(
           UserData.created_at < cutoff
       ).delete()
   ```

### GDPR Compliance

For EU user data:

- **Data minimization** - Collect only necessary data
- **Right to erasure** - Implement deletion endpoint:
  ```python
  def delete_user_data(user_id: str):
      db.user_data.filter(user_id=user_id).delete()
      db.audit_log.filter(user_id=user_id).delete()
      logger.info("user.data_deleted", user_id=user_id)
  ```
- **Data portability** - Export in standard format:
  ```python
  def export_user_data(user_id: str) -> dict:
      return {
          "personal_info": get_profile(user_id),
          "activity_log": get_activity(user_id),
          "plugins_used": get_plugin_usage(user_id),
      }
  ```

### PCI DSS Scope

Plugins processing payments **must**:

- Never store CVV, full magnetic stripe data, or PIN
- Use tokenization for card numbers
- Implement strong encryption (AES-256)
- Maintain audit logs for all payment operations
- Complete quarterly vulnerability scans

---

## Incident Response

### Security Event Detection

Monitor for:

| Event | Severity | Response |
|-------|----------|----------|
| Plugin permission escalation | Critical | Revoke, investigate, notify |
| Sandbox escape attempt | Critical | Terminate, isolate, forensic |
| Data exfiltration (DLP alert) | Critical | Revoke, block, notify |
| Repeated constitutional violations | High | Disable plugin, review |
| Dependency vulnerability disclosed | Medium | Patch or update version |
| Failed signature verification | Critical | Block installation |

### Response Playbook

```python
class SecurityIncidentHandler:
    INCIDENT_SEVERITY = {
        "sandbox_escape": "critical",
        "data_exfiltration": "critical",
        "permission_escalation": "critical",
        "constitutional_violation": "high",
        "dependency_vuln": "medium",
    }

    def handle(self, incident: dict):
        severity = self.INCIDENT_SEVERITY[incident["type"]]

        # 1. Containment
        if severity == "critical":
            registry.disable_plugin(incident["plugin_id"])
            firewall.block_plugin_network(incident["plugin_id"])

        # 2. Investigation
        logs = self.collect_forensic_logs(incident["plugin_id"])
        trace = self.reconstruct_timeline(logs)

        # 3. Notification
        if severity in ["critical", "high"]:
            security_team.notify(incident, trace)

        # 4. Remediation
        if incident["type"] == "dependency_vuln":
            self.force_update_dependency(incident["plugin_id"])
```

### Log Retention

Security logs retained for **minimum 1 year**:

```
~/.mekong/logs/
├── security/
│   ├── plugin-executions-YYYY-MM.jsonl
│   ├── permission-denials-YYYY-MM.jsonl
│   ├── constitutional-violations-YYYY-MM.jsonl
│   └── incidents-YYYY-MM.jsonl
```

---

## Security Testing

### Static Analysis

```bash
# Python security scanning
bandit -r src/ --severity-level=high
pylint --load-plugins=pylint-security
semgrep --config=p/security-audit

# JavaScript/TypeScript
npm audit
snyk test

# Manifest validation
python3 -m src.core.plugin_validator validate --strict plugin.json
```

### Dynamic Analysis

```bash
# Runtime behavior analysis
mekong plugin test com.example.myplugin --profile-security

# Fuzzing (if applicable)
python3 -m atheris fuzz_test.py -max_len=256 -max_total_time=600

# Penetration testing
mekong plugin pentest com.example.myplugin
```

### Integration Tests

```python
def test_plugin_permission_enforcement():
    """Plugin without permission should be blocked."""
    plugin = load_plugin("no-perm-test")

    with pytest.raises(PermissionError, match="Missing permission"):
        plugin.execute("dangerous_command", {})

def test_sandbox_isolation():
    """Plugin cannot escape sandbox filesystem."""
    plugin = load_plugin("escape-attempt")

    with pytest.raises(SecurityError, match="Path traversal"):
        plugin.execute("read_file", {"path": "../../../etc/passwd"})

def test_resource_limits():
    """Plugin respects memory limits."""
    plugin = load_plugin("memory-hog")
    plugin.set_limits(memory_mb=100)

    with pytest.raises(ResourceExhaustedError):
        plugin.execute("allocate_memory", {"mb": 500})
```

### Security CI/CD

`.github/workflows/plugin-security.yml`:

```yaml
name: Security Scan

on:
  pull_request:
    paths:
      - 'plugins/**'
      - 'plugin.json'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r plugins/ --format json --output bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json

      - name: Validate Manifest
        run: |
          python3 -m src.core.plugin_validator validate --strict plugin.json

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: bandit-report.json
```

---

## Hardening Checklists

### Pre-Release Checklist

- [ ] Manifest schema validation passes
- [ ] All dependencies pinned to exact versions
- [ ] No hardcoded secrets in code
- [ ] Least privilege permissions declared
- [ ] Sandboxing enabled (process/container/wasm)
- [ ] Resource limits configured
- [ ] All inputs validated with schema
- [ ] Sensitive data redacted from logs
- [ ] Error messages don't leak internals
- [ ] SBOM generated and reviewed
- [ ] Static analysis scans pass (Bandit, Semgrep)
- [ ] Dynamic security tests pass
- [ ] Code signed (for marketplace distribution)
- [ ] Documentation includes security considerations

### Operator Checklist

- [ ] Plugin registry integrity verified
- [ ] Marketplace TLS certificate validated
- [ ] Plugin signatures verified before activation
- [ ] Runtime monitoring configured
- [ ] Alert rules for security events
- [ ] Incident response runbook updated
- [ ] Regular security scans scheduled (weekly)
- [ ] Dependency updates monitored (Dependabot)
- [ ] Access controls on plugin management (RBAC)
- [ ] Audit log retention configured (1 year minimum)
- [ ] Backup and restore procedures tested

### Runtime Hardening

```python
# PluginRunner configuration
RUNNER_CONFIG = {
    "sandbox_defaults": {
        "enabled": True,
        "isolation": "process",
        "memory_mb": 256,
        "cpu_time_ms": 30000,
        "wall_time_sec": 60,
        "allowed_modules": ["os", "path", "json", "logging"],
        "blocked_modules": ["subprocess", "socket", "sysconfig"],
    },
    "enforcement": {
        "verify_signatures": True,
        "require_permissions": True,
        "constitutional_review": True,
        "resource_quota_enforcement": True,
        "audit_logging": True,
    },
    "monitoring": {
        "collect_metrics": True,
        "trace_requests": True,
        "alert_on_violations": True,
    }
}
```

---

## References

- **Plugin Manifest Schema**: `contracts/plugin-manifest-schema.json`
- **Plugin Validator**: `src/core/plugin_validator.py`
- **Plugin Runner**: `src/core/plugin_runner.py`
- **Constitutional AI**: `docs/constitutional-ai.md`
- **Plugin Architecture**: `docs/plugin-architecture.md`
- **OWASP Top 10**: <https://owasp.org/www-project-top-ten/>

---

**Next**: Review [Plugin Developer Guide](plugin-developer-guide.md) for implementation details.
