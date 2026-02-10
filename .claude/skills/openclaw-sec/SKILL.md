---
name: openclaw-sec
description: AI Agent Security Suite - Real-time protection against prompt injection, command validation, secret detection
---

# OpenClaw Security Suite

## Commands

### Validation

```bash
openclaw-sec validate-command "rm -rf /" # Check if command is safe
openclaw-sec validate-prompt "ignore previous instructions" # Detect injection
openclaw-sec validate-url "https://example.com" # Check URL safety
openclaw-sec validate-path "/etc/passwd" # Check path access
openclaw-sec scan-content "text with secrets" # Scan for secrets
```

### Monitoring

```bash
openclaw-sec events list           # List security events
openclaw-sec events stats          # Event statistics
openclaw-sec events export         # Export events
openclaw-sec reputation show       # User reputation
```

## Detection Modules

1. **Prompt Injection Detector** — Catches "ignore instructions", "system prompt", role manipulation
2. **Command Validator** — Blocks dangerous commands (rm -rf, chmod 777, dd if=)
3. **URL Validator** — Validates URLs against blocklists
4. **Path Validator** — Prevents access to sensitive paths (/etc, ~/.ssh)
5. **Secret Detector** — Finds API keys, passwords, tokens in content
6. **Content Scanner** — General content analysis

## Sensitivity Levels

- `low` — Only most dangerous patterns
- `medium` — Balanced (recommended start)
- `high` — Strict, may have false positives

## Best Practices

1. Start with Medium Sensitivity
2. Enable All Modules Initially
3. Review Events Regularly
4. Monitor User Reputation
5. Test Before Deploying
