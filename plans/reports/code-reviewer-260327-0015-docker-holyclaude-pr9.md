# Code Review: PR #9 — feat(docker): containerize Mekong CLI using HolyClaude patterns

**Branch:** `claude/holyclaude-mekong-fusion-ePJNS` -> `main`
**Files:** 19 changed (+659 / -2)
**Verdict:** REQUEST_CHANGES (1 critical, 3 high, 4 medium)

---

## Critical Issues

### 1. [CRITICAL] Wrong gateway module path — service will crash on start

**File:** `docker/s6-overlay/s6-rc.d/mekong-gateway/run` (line 7)

```sh
python3 -m uvicorn src.core.gateway:app --host 0.0.0.0 --port 8000
```

The actual `app` object lives at `src.core.gateway.gateway_main:app`. The `__init__.py` imports models/functions but does NOT re-export `app`. This service will fail with `AttributeError` on every start and s6-overlay will restart-loop it.

**Fix:**
```sh
python3 -m uvicorn src.core.gateway.gateway_main:app --host 0.0.0.0 --port 8000
```

---

## High Priority

### 2. [HIGH] Security: `bypassPermissions` in settings.json

**File:** `docker/config/settings.json` (line 3)

```json
"defaultMode": "bypassPermissions"
```

This disables all Claude Code permission prompts. While acceptable for a trusted dev container, this should be explicitly documented as a security trade-off. If this image is ever published to a registry, any user running it gets full unsandboxed execution. Consider using `"acceptEdits"` as a safer default, or at minimum add a warning comment in README.

### 3. [HIGH] Security: Excessive capabilities in docker-compose

**Files:** `docker/docker-compose.yaml` (lines 20-23), `docker/docker-compose.full.yaml` (lines 17-22)

```yaml
cap_add:
  - SYS_ADMIN
  - SYS_PTRACE
security_opt:
  - seccomp=unconfined
```

`SYS_ADMIN` + `seccomp=unconfined` essentially gives the container root-equivalent host access. `SYS_ADMIN` is needed for Chromium sandbox, but `seccomp=unconfined` is overkill.

**Fix:** Remove `seccomp=unconfined`. If Chromium needs it, use a targeted seccomp profile or keep `--no-sandbox` (already set via `CHROMIUM_FLAGS`). Since `--no-sandbox` is already configured, neither `SYS_ADMIN` nor `seccomp=unconfined` should be needed.

### 4. [HIGH] bootstrap.sh silently ignored on failure

**File:** `docker/scripts/entrypoint.sh` (line 35)

```bash
/usr/local/bin/bootstrap.sh || echo "[mekong] WARNING: bootstrap failed"
```

If bootstrap fails (e.g., permission error on chown), the container starts without settings.json, CLAUDE.md, or git config. Services will run in a broken state. Should either fail hard (`set -e` + no `||`) or implement proper health checks.

**Fix:** At minimum, verify sentinel creation after bootstrap:
```bash
/usr/local/bin/bootstrap.sh
if [ ! -f "$SENTINEL" ]; then
    echo "[mekong] FATAL: bootstrap failed, sentinel not created"
    exit 1
fi
```

---

## Medium Priority

### 5. [MEDIUM] Claude Code install via piped curl — no hash verification

**File:** `docker/Dockerfile` (line 91)

```dockerfile
RUN curl -fsSL https://claude.ai/install.sh | bash
```

Standard practice for dev tools, but no integrity check. A MITM or CDN compromise would inject arbitrary code. Consider pinning a known-good version or verifying a checksum.

### 6. [MEDIUM] `pip install --break-system-packages` used 3 times

**File:** `docker/Dockerfile` (lines 103, 112, 120)

Using `--break-system-packages` bypasses PEP 668 protection. In a container this is acceptable, but creating a venv would be cleaner and avoid potential conflicts between system Python packages and pip-installed ones. Low risk given container isolation.

### 7. [MEDIUM] No `.dockerignore` referenced or created

The `.gitignore` is modified to un-ignore `docker/`, but no `.dockerignore` exists. The build context is `..` (repo root), so ALL repo files (including `.env`, `apps/`, node_modules, .git) get sent to the Docker daemon. This slows builds and risks leaking secrets into build context.

**Fix:** Create `docker/.dockerignore` or a root `.dockerignore`:
```
.env
.env.*
.git
node_modules
apps/
*.log
```

### 8. [MEDIUM] notify.py swallows all exceptions silently

**File:** `docker/scripts/notify.py` (lines 46-47)

```python
except Exception:
    pass
```

Notification failures are completely silent. At minimum log to stderr so `docker logs` shows the issue.

**Fix:**
```python
except Exception as e:
    print(f"[notify] Failed: {e}", file=sys.stderr)
```

---

## Low Priority

### 9. [LOW] claude-memory.md references features that may not exist

**File:** `docker/config/claude-memory.md`

- References `mekong memory search` (vector semantic search) -- verify this command exists
- References `mekong collab debate` -- verify
- Lists "CTO Daemon" as a running service but no s6 service definition for it
- Credits section references `binhphap.io` domain -- verify it resolves

### 10. [LOW] Hardcoded MEKONG_VERSION=3.2.0

**File:** `docker/Dockerfile` (line 23)

```dockerfile
MEKONG_VERSION=3.2.0
```

This will drift from actual installed version. Consider reading from `pyproject.toml` or removing if unused.

### 11. [LOW] s6 services missing `dependencies` declarations

CloudCLI and mekong-gateway have no dependency on xvfb. If mekong-gateway uses Playwright/Chromium, it should depend on xvfb being up first. s6-rc supports `dependencies.d/` for this.

---

## Positive Observations

- Clean s6-overlay architecture, correct `longrun` service types
- Sentinel-based idempotent bootstrap -- good pattern
- UID/GID remapping for host bind-mount compatibility
- Multi-arch support via TARGETARCH
- Full/slim variant pattern via build arg
- Apprise notification integration is well-designed with opt-in flag file
- Compose files are well-structured with clear comments

---

## Public Repo Safety Check

- No `.env` files in diff
- No `apps/` directory content leaked
- No `mekong/daemon/` content leaked
- No API keys or secrets hardcoded (env vars are empty placeholders)
- `BAILIAN_API_KEY=` and `POLAR_WEBHOOK_SECRET=` are empty -- SAFE

---

## Recommended Actions (Priority Order)

1. **Fix gateway module path** in s6 run script (`gateway.gateway_main:app`)
2. **Remove `seccomp=unconfined`** from both compose files (redundant with `--no-sandbox`)
3. **Add `.dockerignore`** to prevent context bloat and secret leakage
4. **Fail hard on bootstrap error** or add post-bootstrap verification
5. **Document `bypassPermissions`** risk in README
6. **Add stderr logging** to notify.py exception handler

---

## Metrics

| Metric | Value |
|--------|-------|
| Files reviewed | 19 |
| Lines added | 659 |
| Critical issues | 1 |
| High issues | 3 |
| Medium issues | 4 |
| Low issues | 3 |
| Security concerns | 3 (caps, bypass perms, curl pipe) |

---

## Unresolved Questions

1. Does `src.core.gateway.__init__.py` re-export `app`? Verified it does NOT -- only models/functions are imported. This confirms the critical bug.
2. Is `@siteboon/claude-code-ui` a trusted package? No npm audit data available for review.
3. Are the CloudCLI plugins (`cloudcli-plugin-starter`, `cloudcli-plugin-terminal`) from a trusted org? They're cloned from GitHub without hash pinning.
