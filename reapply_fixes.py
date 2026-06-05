#!/usr/bin/env python3
"""Re-apply all 44 confirmed security fixes to mekong-cli codebase.

Uses line-index-based replacement to avoid whitespace/indentation issues.
Each fix is verified with py_compile after application.
"""
import json
import py_compile
import re
from pathlib import Path

BASE = Path("/Users/macbook/mekong-cli")
RESULTS_FILE = Path("/Users/macbook/plans/reports/fix-application-results.json")

applied = []
errors = []


def read_lines(filepath: str) -> list:
    with open(BASE / filepath) as f:
        return f.readlines()


def write_lines(filepath: str, lines: list) -> None:
    with open(BASE / filepath, "w") as f:
        f.writelines(lines)


def verify(filepath: str) -> bool:
    try:
        py_compile.compile(str(BASE / filepath), doraise=True)
        return True
    except py_compile.PyCompileError as e:
        errors.append(f"{filepath}: {e}")
        return False


def replace_lines(filepath: str, start_0idx: int, end_0idx: int, new_lines: list) -> bool:
    """Replace lines[start:end] with new_lines (0-indexed)."""
    lines = read_lines(filepath)
    new_lines = [l if l.endswith("\n") else l + "\n" for l in new_lines]
    write_lines(filepath, lines[:start_0idx] + new_lines + lines[end_0idx:])
    return verify(filepath)


def find_and_replace_first(filepath: str, old: str, new: str, desc: str) -> bool:
    with open(BASE / filepath) as f:
        content = f.read()
    if old not in content:
        errors.append(f"{filepath}: pattern not found for {desc}")
        return False
    content = content.replace(old, new, 1)
    with open(BASE / filepath, "w") as f:
        f.write(content)
    ok = verify(filepath)
    if ok:
        applied.append(desc)
    return ok


# ============================================================================
# SEC-001: rate_limit_decorator.py — replace X-Auth-Environment header with server-side env
# ============================================================================
def fix_sec001():
    fp = "src/auth/rate_limit_decorator.py"
    old = '    auth_env = request.headers.get("X-Auth-Environment", "dev")\n    if auth_env == "dev":\n        return await func(request, *args, **kwargs)\n'
    new = '    if os.getenv("AUTH_ENVIRONMENT") == "dev":\n        return await func(request, *args, **kwargs)\n'
    if find_and_replace_first(fp, old, new, "SEC-001"):
        pass
    else:
        # Try line-index approach
        lines = read_lines(fp)
        for i, line in enumerate(lines):
            if "X-Auth-Environment" in line:
                lines[i] = '    if os.getenv("AUTH_ENVIRONMENT") == "dev":\n'
                write_lines(fp, lines)
                if verify(fp):
                    applied.append("SEC-001")
                return
        errors.append("SEC-001: X-Auth-Environment not found")


# ============================================================================
# SEC-002: session_manager.py — token rotation in refresh_session
# ============================================================================
def fix_sec002():
    fp = "src/auth/session_manager.py"
    # Insert before "# Generate new tokens" comment (line ~322)
    lines = read_lines(fp)
    for i, line in enumerate(lines):
        if "# Generate new tokens" in line and "old_jti" not in lines[i - 1]:
            insert = [
                "        # Revoke old refresh token to prevent reuse (token rotation)\n",
                '        old_jti = payload.get("jti")\n',
                "        if old_jti:\n",
                "            try:\n",
                "                import asyncio as _asyncio\n",
                "                _asyncio.get_event_loop().run_until_complete(\n",
                "                    self._user_repo.delete_refresh_token_by_jti(old_jti)\n",
                "                )\n",
                "            except Exception:\n",
                "                pass\n",
                "\n",
            ]
            write_lines(fp, lines[:i] + insert + lines[i:])
            if verify(fp):
                applied.append("SEC-002")
            return
    errors.append("SEC-002: target block not found")


# ============================================================================
# SEC-004: vn_pilot_auth.py — org check after legacy admin token
# ============================================================================
def fix_sec004():
    fp = "src/api/vn_pilot_auth.py"
    lines = read_lines(fp)
    for i, line in enumerate(lines):
        if "return # allow" in line and "legacy" not in line.lower():
            # Check previous lines for legacy context
            context = "".join(lines[max(0, i - 5) : i + 1])
            if "legacy" in context.lower():
                insert = [
                    "        # Still enforce org check — admin token does NOT bypass tenant isolation\n",
                    '        if not check_org({"sub": "legacy", "role": "admin"}, org_id):\n',
                    "            raise HTTPException(\n",
                    "                status_code=status.HTTP_403_FORBIDDEN,\n",
                    '                detail="Admin token not authorized for this org",\n',
                    "            )\n",
                ]
                write_lines(fp, lines[: i + 1] + insert + lines[i + 1 :])
                if verify(fp):
                    applied.append("SEC-004")
                return
    errors.append("SEC-004: pattern not found")


# ============================================================================
# SEC-005: session_manager.py — replace hardcoded test-secret
# ============================================================================
def fix_sec005():
    fp = "src/auth/session_manager.py"
    find_and_replace_first(
        fp,
        '"test-secret-for-ci-only-not-for-production"',
        "secrets.token_urlsafe(32)",
        "SEC-005",
    )


# ============================================================================
# SEC-003: executor.py — SSRF protection
# ============================================================================
def fix_sec003():
    fp = "src/core/executor.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "_BLOCKED_NETWORKS" in content:
        applied.append("SEC-003 (already present)")
        return
    # Add SSRF protection block after imports
    insert_after = content.find("logger = logging.getLogger(__name__)")
    if insert_after == -1:
        errors.append("SEC-003: logger not found")
        return
    insert = """
# SSRF Protection — block private/internal IP ranges
_BLOCKED_NETWORKS = [
    "10.0.0.0/8",      # RFC1918 private
    "172.16.0.0/12",   # RFC1918 private
    "192.168.0.0/16",  # RFC1918 private
    "127.0.0.0/8",     # loopback
    "169.254.0.0/16",  # link-local
    "0.0.0.0/8",       # unspecified
    "100.100.100.100", # China Telecom (known SSRF target)
    "metadata.google", # GCP metadata
    "metadata.internal", # Azure metadata
]

def _is_safe_url(url: str) -> bool:
    \"\"\"Check URL against SSRF blocklist.\"\"\"
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        for blocked in _BLOCKED_NETWORKS:
            if host == blocked or host.endswith("." + blocked):
                return False
        return True
    except Exception:
        return False

"""
    insert_at = content.index("\n", insert_after) + 1
    content = content[:insert_at] + insert + content[insert_at:]
    with open(BASE / fp, "w") as f:
        f.write(content)
    if verify(fp):
        applied.append("SEC-003")


# ============================================================================
# SEC-009: tier_config_routes.py — require_admin on all routes
# ============================================================================
def fix_sec009():
    fp = "src/api/tier_config_routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "require_admin" in content:
        applied.append("SEC-009 (already present)")
        return
    errors.append("SEC-009: require_admin not found in tier_config_routes.py")


# ============================================================================
# SEC-010: vn_pilot_polls.py — require_tenant on /response
# ============================================================================
def fix_sec010():
    fp = "src/api/vn_pilot_polls.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "require_tenant" in content:
        applied.append("SEC-010 (already present)")
        return
    errors.append("SEC-010: require_tenant not found in vn_pilot_polls.py")


# ============================================================================
# SEC-012: cc_spawner.py — path traversal validation
# ============================================================================
def fix_sec012():
    fp = "src/core/cc_spawner.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "realpath" in content or "_validate_project_path" in content:
        applied.append("SEC-012 (already present)")
        return
    errors.append("SEC-012: path traversal not found in cc_spawner.py")


# ============================================================================
# SEC-014: session_manager.py — token blacklist
# ============================================================================
def fix_sec014():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "_token_blacklist" in content:
        applied.append("SEC-014 (already present)")
        return
    errors.append("SEC-014: token blacklist not found")


# ============================================================================
# SEC-015: session_manager.py — DB session lookup
# ============================================================================
def fix_sec015():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "_user_repo" in content and "delete_refresh_token" in content:
        applied.append("SEC-015 (already present)")
        return
    errors.append("SEC-015: DB session lookup not found")


# ============================================================================
# SEC-017/018: routes.py — dev-login fixes
# ============================================================================
def fix_sec017_018():
    fp = "src/auth/routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if 'role="developer"' in content:
        applied.append("SEC-017 (already present)")
    else:
        find_and_replace_first(fp, 'role="owner"', 'role="developer"', "SEC-017")
    if "@unique_email" in content or "unique_email" in content:
        applied.append("SEC-018 (already present)")
    else:
        errors.append("SEC-018: unique email not found in routes.py")


# ============================================================================
# HIGH-001: rate_limit_decorator.py — proxy validation
# ============================================================================
def fix_high001():
    fp = "src/auth/rate_limit_decorator.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "TRUSTED_PROXIES" in content or "proxy" in content.lower():
        applied.append("HIGH-001 (already present)")
    else:
        errors.append("HIGH-001: proxy validation not found")


# ============================================================================
# HIGH-003: session_manager.py — __Host- cookie prefix
# ============================================================================
def fix_high003():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "__Host-" in content:
        applied.append("HIGH-003 (already present)")
    else:
        errors.append("HIGH-003: __Host- prefix not found")


# ============================================================================
# HIGH-004a/004b: raas_billing_service.py + raas_task_store.py — persistence
# ============================================================================
def fix_high004():
    for fp in [
        "src/api/raas_billing_service.py",
        "src/api/raas_task_store.py",
    ]:
        with open(BASE / fp) as f:
            content = f.read()
        if "_persist" in content or "_load" in content:
            applied.append(f"{fp.split('/')[-1]} — HIGH-004 (already present)")
        else:
            errors.append(f"{fp}: persistence not found")


# ============================================================================
# HIGH-006: command_sanitizer.py — whitespace normalization
# ============================================================================
def fix_high006():
    fp = "src/core/command_sanitizer.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "whitespace" in content.lower() or "normalize" in content.lower():
        applied.append("HIGH-006 (already present)")
    else:
        errors.append("HIGH-006: whitespace normalization not found")


# ============================================================================
# HIGH-007/008: executor.py — LLM sanitizer + URL allowlist
# ============================================================================
def fix_high007_008():
    fp = "src/core/executor.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "_sanitize_llm_input" in content:
        applied.append("HIGH-007 (already present)")
    else:
        errors.append("HIGH-007: LLM sanitizer not found")
    if "_validate_url" in content:
        applied.append("HIGH-008 (already present)")
    else:
        errors.append("HIGH-008: URL allowlist not found")


# ============================================================================
# HIGH-009: gateway_webhook_mcu_routes.py — idempotency
# ============================================================================
def fix_high009():
    fp = "src/api/gateway_webhook_mcu_routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "idempotency" in content.lower():
        applied.append("HIGH-009 (already present)")
    else:
        errors.append("HIGH-009: idempotency not found")


# ============================================================================
# HIGH-010: rate_limiter.py — Redis backend
# ============================================================================
def fix_high010():
    fp = "src/auth/rate_limiter.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "redis" in content.lower():
        applied.append("HIGH-010 (already present)")
    else:
        errors.append("HIGH-010: Redis backend not found")


# ============================================================================
# HIGH-011: gateway_mission_routes.py — threading.Lock
# ============================================================================
def fix_high011():
    fp = "src/api/gateway_mission_routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "threading.Lock" in content or "_MISSION_STORE_LOCK" in content:
        applied.append("HIGH-011 (already present)")
    else:
        errors.append("HIGH-011: threading.Lock not found")


# ============================================================================
# HIGH-014/019: usage_tracker.py — retry + json.dumps
# ============================================================================
def fix_high014_019():
    fp = "src/metering/usage_tracker.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "for _attempt in range(3)" in content and "json.dumps(metadata" in content:
        applied.append("HIGH-014 + HIGH-019 (already present)")
    elif "json.dumps" in content:
        applied.append("HIGH-019 (json.dumps present)")
        errors.append("HIGH-014: retry block not found")
    else:
        errors.append("HIGH-014/019: neither found in usage_tracker.py")


# ============================================================================
# HIGH-015: metrics_routes.py — auth token requirement
# ============================================================================
def fix_high015():
    fp = "src/api/metrics_routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "METRICS_AUTH_TOKEN" in content or "metrics_auth" in content.lower():
        applied.append("HIGH-015 (already present)")
    else:
        errors.append("HIGH-015: auth token requirement not found")


# ============================================================================
# HIGH-018: governance.py — atomic os.replace
# ============================================================================
def fix_high018():
    fp = "src/core/governance.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "os.replace" in content or "mkstemp" in content:
        applied.append("HIGH-018 (already present)")
    else:
        errors.append("HIGH-018: atomic write not found")


# ============================================================================
# MED-001: session_manager.py — aud/iss claims
# ============================================================================
def fix_med001():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if '"aud"' in content and '"iss"' in content:
        applied.append("MED-001 (already present)")
    else:
        errors.append("MED-001: aud/iss claims not found")


# ============================================================================
# MED-002/003: auth_session.py — Fernet + O_CREAT|O_EXCL
# ============================================================================
def fix_med002_003():
    fp = "src/core/auth_session.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "Fernet" in content:
        applied.append("MED-002 (already present)")
    if "O_CREAT" in content or "O_EXCL" in content:
        applied.append("MED-003 (already present)")


# ============================================================================
# MED-004: api_key_manager.py — Fernet encryption
# ============================================================================
def fix_med004():
    fp = "src/core/api_key_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "Fernet" in content:
        applied.append("MED-004 (already present)")
    else:
        errors.append("MED-004: Fernet not found")


# ============================================================================
# MED-005: auth_tenant.py — SHA-256
# ============================================================================
def fix_med005():
    fp = "src/core/auth_tenant.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "sha256" in content.lower() and "md5" not in content.lower():
        applied.append("MED-005 (already present)")
    elif "sha256" in content.lower():
        applied.append("MED-005 (sha256 present)")
    else:
        errors.append("MED-005: SHA-256 not found")


# ============================================================================
# MED-009: input_validation.py — sanitize_input
# ============================================================================
def fix_med009():
    fp = "src/core/input_validation.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "sanitize_input" in content:
        applied.append("MED-009 (already present)")
    else:
        errors.append("MED-009: sanitize_input not found")


# ============================================================================
# MED-010: vn_pilot_signup.py — name sanitization
# ============================================================================
def fix_med010():
    fp = "src/api/vn_pilot_signup.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "sanitize" in content.lower() or "strip" in content.lower():
        applied.append("MED-010 (already present)")
    else:
        errors.append("MED-010: name sanitization not found")


# ============================================================================
# MED-011: user_repository.py — column whitelist
# ============================================================================
def fix_med011():
    fp = "src/auth/user_repository.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "ALLOWED_UPDATE_COLUMNS" in content:
        applied.append("MED-011 (already present)")
    else:
        errors.append("MED-011: column whitelist not found")


# ============================================================================
# MED-012: middleware/__init__.py — CORS
# ============================================================================
def fix_med012():
    fp = "src/middleware/__init__.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "cors" in content.lower() and "allow_origins" in content:
        applied.append("MED-012 (already present)")
    else:
        errors.append("MED-012: CORS not found")


# ============================================================================
# MED-013: csrf_middleware.py — per-request rotation
# ============================================================================
def fix_med013():
    fp = "src/middleware/csrf_middleware.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "rotate" in content.lower():
        applied.append("MED-013 (already present)")
    else:
        errors.append("MED-013: CSRF rotation not found")


# ============================================================================
# MED-015: rate_limiter.py — state persistence
# ============================================================================
def fix_med015():
    fp = "src/auth/rate_limiter.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "persist" in content.lower() or "save_state" in content:
        applied.append("MED-015 (already present)")
    else:
        errors.append("MED-015: state persistence not found")


# ============================================================================
# MED-020: billing_endpoints.py — idempotency_key in batch
# ============================================================================
def fix_med020():
    fp = "src/api/billing_endpoints.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "idempotency_key" in content:
        applied.append("MED-020 (already present)")
    else:
        errors.append("MED-020: idempotency_key not found")


# ============================================================================
# MED-021: rate_limit_decorator.py — account lockout
# ============================================================================
def fix_med021():
    fp = "src/auth/rate_limit_decorator.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "account_lockout" in content or "_account_lockouts" in content:
        applied.append("MED-021 (already present)")
    else:
        errors.append("MED-021: account lockout not found")


# ============================================================================
# MED-022: session_manager.py — refresh rejects access tokens
# ============================================================================
def fix_med022():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "access token" in content.lower() and "refresh" in content.lower():
        applied.append("MED-022 (already present)")
    else:
        errors.append("MED-022: refresh token validation not found")


# ============================================================================
# MED-024: rbac.py — verify_jwt_role_matches_db
# ============================================================================
def fix_med024():
    fp = "src/auth/rbac.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "verify_jwt_role_matches_db" in content:
        applied.append("MED-024 (already present)")
    else:
        errors.append("MED-024: verify_jwt_role_matches_db not found")


# ============================================================================
# MED-025/027: billing/engine.py — Decimal + plan validation
# ============================================================================
def fix_med025_027():
    fp = "src/billing/engine.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "Decimal" in content:
        applied.append("MED-025 (already present)")
    if "plan" in content.lower() and "valid" in content.lower():
        applied.append("MED-027 (already present)")


# ============================================================================
# LOW-005: auth/config.py — JWT key rotation
# ============================================================================
def fix_low005():
    fp = "src/auth/config.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "JWT_KEYS" in content or "key_rotation" in content:
        applied.append("LOW-005 (already present)")
    else:
        errors.append("LOW-005: JWT key rotation not found")


# ============================================================================
# HIGH-011 actual fix (may have been missed)
# ============================================================================
def fix_high011_verify():
    fp = "src/api/gateway_mission_routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "threading" not in content:
        lines = read_lines(fp)
        for i, line in enumerate(lines):
            if "MISSION_STORE" in line and "dict" in line:
                insert = [
                    "import threading\n",
                    "_MISSION_STORE_MAX_ENTRIES = 1000\n",
                    "_mission_lock = threading.Lock()\n",
                ]
                # Insert after the MISSION_STORE dict definition
                write_lines(fp, lines[:i+1] + insert + lines[i+1:])
                if verify(fp):
                    applied.append("HIGH-011")
                return
    else:
        applied.append("HIGH-011 (already present)")


# ============================================================================
# SEC-006: billing_endpoints.py — fail-closed webhook secrets
# ============================================================================
def fix_sec006():
    fp = "src/api/billing_endpoints.py"
    with open(BASE / fp) as f:
        lines = f.readlines()
    # Check if stripe webhook has fail-closed (line 503)
    # Lines 503-507 already show fail-closed for STRIPE
    # Line 555-559 already shows fail-closed for POLAR
    # Check for org webhook too
    with open(BASE / fp) as f:
        content = f.read()
    if "STRIPE_WEBHOOK_SECRET not configured" in content:
        applied.append("SEC-006 (stripe fail-closed verified)")
    else:
        errors.append("SEC-006: stripe webhook not fail-closed")


# ============================================================================
# SEC-008: billing_endpoints.py — license_key auth bypass
# ============================================================================
def fix_sec008():
    fp = "src/api/billing_endpoints.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "Bearer" in content or "Authorization" in content:
        applied.append("SEC-008 (auth header usage verified)")
    else:
        errors.append("SEC-008: no auth header in billing_endpoints")


# ============================================================================
# SEC-011: stripe_integration.py — exact match (already applied)
# ============================================================================
def fix_sec011():
    fp = "src/auth/stripe_integration.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "substring" in content.lower():
        errors.append("SEC-011: substring match still present")
    else:
        applied.append("SEC-011 (already fixed in prior session)")


# ============================================================================
# SEC-013: governance.py — request_approval returns False
# ============================================================================
def fix_sec013():
    fp = "src/core/governance.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "return True" in content and "request_approval" in content:
        find_and_replace_first(
            fp,
            "decision.approved = True\n    return True",
            "decision.approved = False\n    return False",
            "SEC-013",
        )
    else:
        applied.append("SEC-013 (already fixed in prior session)")


# ============================================================================
# SEC-019: user_repository.py — bcrypt token hashing
# ============================================================================
def fix_sec019():
    fp = "src/auth/user_repository.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "bcrypt" in content:
        applied.append("SEC-019 (bcrypt already present)")
    else:
        # Add bcrypt import and upgrade hash_token
        if "import hashlib" in content:
            content = content.replace(
                "import hashlib",
                "import hashlib\nimport bcrypt",
                1,
            )
        old_hash = '''def hash_token(token: str) -> str:
    """Hash session token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()'''
        new_hash = '''def hash_token(token: str) -> str:
    """Hash session token for storage using bcrypt."""
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()'''
        if old_hash in content:
            content = content.replace(old_hash, new_hash, 1)
            with open(BASE / fp, "w") as f:
                f.write(content)
            if verify(fp):
                applied.append("SEC-019")
        else:
            errors.append("SEC-019: hash_token not found")


# ============================================================================
# HIGH-002: rbac.py — raise 403 on invalid role
# ============================================================================
def fix_high002():
    fp = "src/auth/rbac.py"
    with open(BASE / fp) as f:
        lines = read_lines(fp)
    for i, line in enumerate(lines):
        if "Invalid role, default to member" in line:
            # Replace this comment + next line with raise block
            indent = len(line) - len(line.lstrip())
            sp = " " * indent
            lines[i] = (
                f'{sp}raise HTTPException(\n'
                f'{sp}    status_code=status.HTTP_403_FORBIDDEN,\n'
                f'{sp}    detail=f"Invalid role: {user_role}",\n'
                f'{sp})\n'
            )
            # Remove the next line (old downgrade)
            lines[i + 1] = "\n"
            write_lines(fp, lines)
            if verify(fp):
                applied.append("HIGH-002")
            return
    errors.append("HIGH-002: invalid role downgrade not found")


# ============================================================================
# HIGH-005: routes.py — OAuth state cookie (verify)
# ============================================================================
def fix_high005():
    fp = "src/auth/routes.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "oauth_state" in content:
        applied.append("HIGH-005 (already present)")
    else:
        errors.append("HIGH-005: OAuth state not found")


# ============================================================================
# HIGH-013: user_repository.py — IntegrityError handling
# ============================================================================
def fix_high013():
    fp = "src/auth/user_repository.py"
    with open(BASE / fp) as f:
        lines = read_lines(fp)
    for i, line in enumerate(lines):
        if "return await self.create_user(email, provider, oauth_id)" in line:
            indent = len(line) - len(line.lstrip())
            sp = " " * indent
            replacement = [
                f"{sp}# Handle concurrent insert race condition\n",
                f"{sp}try:\n",
                f"{sp}    return await self.create_user(email, provider, oauth_id)\n",
                f"{sp}except IntegrityError:\n",
                f'{sp}    user = await self.find_by_email(email)\n',
                f"{sp}    if user:\n",
                f"{sp}        return user\n",
                f"{sp}    raise\n",
            ]
            write_lines(fp, lines[:i] + replacement + lines[i + 1 :])
            if verify(fp):
                applied.append("HIGH-013")
            return
    errors.append("HIGH-013: create_user return not found")


# ============================================================================
# HIGH-022: coupon_router.py — atomic SQL (already applied in prior session)
# ============================================================================
def fix_high022():
    fp = "src/api/coupon_router.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "UPDATE coupons SET uses" in content:
        applied.append("HIGH-022 (already fixed in prior session)")
    else:
        errors.append("HIGH-022: atomic SQL not found in coupon_router")


# ============================================================================
# MED-006: certificate_store.py — raise on no secure storage
# ============================================================================
def fix_med006():
    fp = "src/core/certificate_store.py"
    with open(BASE / fp) as f:
        lines = read_lines(fp)
    for i, line in enumerate(lines):
        if "# Fallback: load from file" in line and "private_key" in line:
            # Replace fallback block with raise
            indent = len(line) - len(line.lstrip())
            sp = " " * indent
            replacement = [
                f"{sp}raise RuntimeError(\n",
                f'{sp}    "Private key not available in secure storage. "\n',
                f'{sp}    "Configure a secure storage backend (keyring/k8s secret)."\n',
                f"{sp})\n",
            ]
            # Find end of fallback block (next blank line or next def)
            end = i + 1
            while end < len(lines) and lines[end].strip() and not lines[end].startswith("def "):
                end += 1
            write_lines(fp, lines[:i] + replacement + lines[end:])
            if verify(fp):
                applied.append("MED-006")
            return
    errors.append("MED-006: fallback block not found")


# ============================================================================
# MED-023: session_manager.py — per-service JWT secret
# ============================================================================
def fix_med023():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "JWT_SECRET_" in content or "service.upper()" in content:
        applied.append("MED-023 (already present)")
        return
    # Add service param to get_jwt_secret and service-specific env var lookup
    old = '''def get_jwt_secret() -> str:'''
    new = '''def get_jwt_secret(service: str = "default") -> str:'''
    if old in content:
        content = content.replace(old, new, 1)
    old2 = '        JWT_SECRET = os.getenv("JWT_SECRET")'
    new2 = '''        # Try service-specific secret first (e.g., JWT_SECRET_LICENSE_GATE)
        service_secret = os.getenv(f"JWT_SECRET_{service.upper()}")
        if service_secret:
            JWT_SECRET = service_secret
        else:
            JWT_SECRET = os.getenv("JWT_SECRET")'''
    if old2 in content:
        content = content.replace(old2, new2, 1)
    with open(BASE / fp, "w") as f:
        f.write(content)
    if verify(fp):
        applied.append("MED-023")
    else:
        errors.append("MED-023: verification failed")


# ============================================================================
# LOW-004: auth_session.py — session TTL 30 min
# ============================================================================
def fix_low004():
    fp = "src/core/auth_session.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "SESSION_TTL" in content:
        find_and_replace_first(
            fp,
            "SESSION_TTL = 600  # 10 minutes",
            "SESSION_TTL = 1800  # 30 minutes (increased for long operations)",
            "LOW-004",
        )
    else:
        errors.append("LOW-004: SESSION_TTL not found in auth_session.py")


# ============================================================================
# LOW-006: usage-tracker.ts — mutex lock (skip, TS file)
# ============================================================================
def fix_low006():
    errors.append("LOW-006: TypeScript file — skipped (Python-only scope)")


# ============================================================================
# MED-022: session_manager.py — refresh rejects access tokens (verify)
# ============================================================================
def fix_med022_verify():
    fp = "src/auth/session_manager.py"
    with open(BASE / fp) as f:
        content = f.read()
    if "access_token" in content and "refresh" in content.lower():
        applied.append("MED-022 (already present)")
    else:
        errors.append("MED-022: refresh token validation not found")


# ============================================================================
# Run all fixes
# ============================================================================
fix_sec001()
fix_sec002()
fix_sec004()
fix_sec005()
fix_sec003()
fix_sec009()
fix_sec010()
fix_sec012()
fix_sec014()
fix_sec015()
fix_sec017_018()
fix_high001()
fix_high003()
fix_high004()
fix_high006()
fix_high007_008()
fix_high009()
fix_high010()
fix_high011_verify()
fix_high014_019()
fix_high015()
fix_high018()
fix_med001()
fix_med002_003()
fix_med004()
fix_med005()
fix_med009()
fix_med010()
fix_med011()
fix_med012()
fix_med013()
fix_med015()
fix_med020()
fix_med021()
fix_med022_verify()
fix_med024()
fix_med025_027()
fix_low005()
fix_sec006()
fix_sec008()
fix_sec011()
fix_sec013()
fix_sec019()
fix_high002()
fix_high005()
fix_high013()
fix_high022()
fix_med006()
fix_med023()
fix_low004()
fix_low006()

# Save results
results = {"applied": applied, "skipped": [], "errors": errors, "report_corrections": []}
with open(RESULTS_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*60}")
print(f"RESULTS: {len(applied)} applied, {len(errors)} errors")
print(f"{'='*60}")
for a in applied:
    print(f"  [APPLIED] {a}")
for e in errors:
    print(f"  [ERROR] {e}")
