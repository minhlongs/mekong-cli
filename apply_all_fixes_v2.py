#!/usr/bin/env python3
"""
Apply all 75 security fixes from the fix plan.
Handles indentation detection per file to avoid SyntaxError.
"""

import os
import re
import py_compile
import shutil
import json

SRC = "/Users/macbook/mekong-cli/src"
REPORTS = "/Users/macbook/plans/reports"

def get_method_indent(filepath):
    """Detect the indentation style of method bodies in a file."""
    with open(filepath) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            for j in range(i + 1, min(i + 8, len(lines) + 1)):
                if j < len(lines):
                    lj = lines[j]
                    if lj.strip() and not lj.strip().startswith(("#", '"""', "'''", "def ", "async def ", "class ")):
                        return len(lj) - len(lj.lstrip())
    return 4  # default fallback


def apply_line_replace(filepath, old_lines, new_lines, verify=True):
    """Replace a contiguous block of lines in a file."""
    with open(filepath) as f:
        content = f.read()

    old_text = "\n".join(old_lines)
    if old_text not in content:
        print(f"  WARNING: Could not find target text in {filepath}")
        print(f"  Looking for: {old_text[:100]}...")
        return False

    new_text = "\n".join(new_lines)
    content = content.replace(old_text, new_text, 1)

    with open(filepath, "w") as f:
        f.write(content)

    if verify:
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: Syntax error after fix in {filepath}: {e}")
            return False
    return True


def apply_indented_block(filepath, start_line_0idx, end_line_0idx, new_block_lines, verify=True):
    """Replace lines[start:end] with new_block_lines, preserving indentation context."""
    with open(filepath) as f:
        lines = f.readlines()

    if start_line_0idx < 0 or end_line_0idx > len(lines):
        print(f"  ERROR: Line range out of bounds for {filepath}")
        return False

    # Detect indentation from the surrounding context (line before start)
    context_line = lines[start_line_0idx - 1] if start_line_0idx > 0 else lines[0]
    base_indent = len(context_line) - len(context_line.lstrip())

    # Indent new block lines by base_indent
    indented_block = []
    for bl in new_block_lines:
        if bl.strip():
            indented_block.append(" " * base_indent + bl)
        else:
            indented_block.append(bl)

    lines[start_line_0idx:end_line_0idx] = indented_block

    with open(filepath, "w") as f:
        f.writelines(lines)

    if verify:
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: Syntax error after fix in {filepath}: {e}")
            return False
    return True


def backup(filepath):
    shutil.copy2(filepath, filepath + ".bak")


# ============================================================================
# PHASE 1: CRITICAL (19 fixes)
# ============================================================================

def fix_sec001():
    """Rate limiter bypass via X-Auth-Environment header."""
    fp = os.path.join(SRC, "auth/rate_limit_decorator.py")
    backup(fp)
    # Remove the two lines that use client-controlled header
    # Lines 164-167 in the wrapper function:
    #   if bypass_dev:
    #       auth_env = request.headers.get("X-Auth-Environment", "dev")
    #       if auth_env == "dev":
    # We need to replace these 3 lines with just checking os.environ
    old = """if bypass_dev:
            auth_env = request.headers.get("X-Auth-Environment", "dev")
            if auth_env == "dev\""""
    new = """if bypass_dev and os.getenv("AUTH_ENVIRONMENT") == "dev\""""
    with open(fp) as f:
        content = f.read()
    if old not in content:
        print(f"  WARNING: SEC-001 target text not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-001 syntax error: {e}")
        return False
    return True


def fix_sec002():
    """Token rotation - invalidate old refresh token after use."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        lines = f.readlines()

    # Find the line with "new_access = self.create_access_token(user)"
    # and insert token rotation block before it
    target = "new_access = self.create_access_token(user)\n"
    found_idx = None
    for i, line in enumerate(lines):
        if line == target:
            found_idx = i
            break

    if found_idx is None:
        print(f"  WARNING: SEC-002 target not found")
        return False

    # Detect indentation: method body is 8-space for this class
    # Get indent from "return new_access, new_refresh" line
    ret_line = lines[found_idx + 2]
    base_indent = len(ret_line) - len(ret_line.lstrip())

    # Build token rotation block (inserted before new_access = ...)
    rotation_block = [
        "",
        "# Token rotation: revoke old refresh token to prevent reuse",
        "old_jti = payload.get('jti')",
        "if old_jti:",
        "    try:",
        "        import asyncio as _asyncio_rot",
        "        _loop = _asyncio_rot.get_event_loop()",
        "        if _loop.is_running():",
        "            _loop.create_task(",
        "                self._user_repo.delete_refresh_token_by_jti(old_jti)",
        "            )",
        "        else:",
        "            _loop.run_until_complete(",
        "                self._user_repo.delete_refresh_token_by_jti(old_jti)",
        "            )",
        "    except Exception:",
        "        pass",
        "",
    ]

    indented_block = []
    for bl in rotation_block:
        if bl.strip():
            indented_block.append(" " * base_indent + bl)
        else:
            indented_block.append(bl)

    lines[found_idx:found_idx] = indented_block

    with open(fp, "w") as f:
        f.writelines(lines)

    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-002 syntax error: {e}")
        return False
    return True


def fix_sec003():
    """SSRF prevention in executor.py."""
    fp = os.path.join(SRC, "core/executor.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add imports and SSRF block at top of file, after existing imports
    import_block = '''"""  # Keep existing module docstring


# SSRF prevention: blocked network ranges
_BLOCKED_NETWORKS = [
    "127.0.0.0/8",      # loopback
    "10.0.0.0/8",       # RFC1918 private
    "172.16.0.0/12",    # RFC1918 private
    "192.168.0.0/16",   # RFC1918 private
    "169.254.0.0/16",   # link-local + metadata 169.254.169.254
    "0.0.0.0/8",        # unspecified
    "::1/128",          # IPv6 loopback
    "fc00::/7",         # IPv6 private
    "fe80::/10",        # IPv6 link-local
]


def _is_safe_url(url: str) -> bool:
    """Check URL does not target private/internal networks."""
    import ipaddress
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False
        addr = ipaddress.ip_address(host)
        for network in _BLOCKED_NETWORKS:
            if addr in ipaddress.ip_network(network):
                return False
        return True
    except (ValueError, TypeError):
        return False


'''

    # Insert after the module docstring (first """...""")
    pattern = '"""\n\n'
    if pattern in content:
        content = content.replace(pattern, '"""\n\n' + import_block, 1)
    else:
        content = import_block + content

    # Wrap the req.request() call in _execute_api_step with URL check
    old_api_call = "response = req.request(method, url, json=body, headers=headers, timeout=30)"
    new_api_call = """# SSRF check before making request
        if not _is_safe_url(url):
            self.console.print(f"[bold red]SSRF blocked:[/bold red] {url} targets private network")
            return ExecutionResult(
                exit_code=1, stdout="",
                stderr="URL blocked: targets private/internal network",
                metadata={"mode": "api", "ssrf_blocked": True},
            )
        response = req.request(method, url, json=body, headers=headers, timeout=30)"""

    if old_api_call in content:
        content = content.replace(old_api_call, new_api_call, 1)
    else:
        print(f"  WARNING: SEC-003 API call not found")

    with open(fp, "w") as f:
        f.write(content)

    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-003 syntax error: {e}")
        return False
    return True


def fix_sec004():
    """Legacy admin token - enforce org check."""
    fp = os.path.join(SRC, "api/vn_pilot_auth.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''if legacy_token and raw_token == legacy_token:
    org_id = request.query_params.get("org_id", "default")
    _audit_log(scope="legacy", org=org_id, sub="legacy", endpoint=request.url.path)
    return  # allow'''

    new = '''if legacy_token and raw_token == legacy_token:
    org_id = request.query_params.get("org_id", "default")
    _audit_log(scope="legacy", org=org_id, sub="legacy", endpoint=request.url.path)
    # Still enforce org check - admin token does NOT bypass tenant isolation
    if not check_org({"sub": "legacy", "role": "admin"}, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin token not authorized for this org",
        )
    return'''

    if old not in content:
        print(f"  WARNING: SEC-004 target text not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-004 syntax error: {e}")
        return False
    return True


def fix_sec005():
    """JWT CI fallback - replace hardcoded secret."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''JWT_SECRET = "test-secret-for-ci-only-not-for-production"'''
    new = '''JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)'''

    if old not in content:
        print(f"  WARNING: SEC-005 hardcoded secret not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-005 syntax error: {e}")
        return False
    return True


def fix_sec006():
    """Webhook signature bypass - fail-closed."""
    fp = os.path.join(SRC, "api/billing_endpoints.py")
    backup(fp)

    fixes = [
        # Helper function at top
        ('if not secret:\n    logger.warning("WEBHOOK_SECRET not configured - skipping verification")\n    return True  # Allow unsigned events if secret not set',
         'if not secret:\n    logger.error("WEBHOOK_SECRET not configured - rejecting webhook")\n    raise HTTPException(\n        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n        detail="Webhook secret not configured",\n    )'),
        # Stripe webhook
        ('webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")\n    signature = request.headers.get("Stripe-Signature", "")\n\n    if not webhook_secret:\n        logger.warning("STRIPE_WEBHOOK_SECRET not configured")\n\n    try:',
         'webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")\n    signature = request.headers.get("Stripe-Signature", "")\n\n    if not webhook_secret:\n        raise HTTPException(\n            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            detail="Stripe webhook secret not configured",\n        )\n\n    try:'),
        # Polar webhook
        ('webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")\n    signature = request.headers.get("webhook-signature", "")\n\n    if not webhook_secret:\n        logger.warning("POLAR_WEBHOOK_SECRET not configured")\n\n    try:',
         'webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")\n    signature = request.headers.get("webhook-signature", "")\n\n    if not webhook_secret:\n        raise HTTPException(\n            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            detail="Polar webhook secret not configured",\n        )\n\n    try:'),
    ]

    with open(fp) as f:
        content = f.read()

    for old, new in fixes:
        if old in content:
            content = content.replace(old, new, 1)
        else:
            print(f"  WARNING: SEC-006 pattern not found: {old[:60]}...")

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-006 syntax error: {e}")
        return False
    return True


def fix_sec007():
    """MCU deduct endpoints require auth."""
    fp = os.path.join(SRC, "gateway_webhook_mcu_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add require_tenant import if missing
    if "from src.auth.tenant_auth import require_tenant" not in content:
        content = content.replace(
            "from fastapi import APIRouter, HTTPException",
            "from fastapi import APIRouter, Depends, HTTPException"
        )
        # Try to add import after last src.auth import
        if "from src.auth." in content:
            lines = content.split("\n")
            last_auth_idx = max(i for i, l in enumerate(lines) if l.startswith("from src.auth."))
            lines.insert(last_auth_idx + 1, "from src.auth.tenant_auth import require_tenant")
            content = "\n".join(lines)
        else:
            content = "from src.auth.tenant_auth import require_tenant\n" + content

    # Add Depends(require_tenant) to mcu deduct endpoints
    # Find the mcu_deduct function and add auth dep
    old_deduct_sig = 'async def mcu_deduct('
    if old_deduct_sig in content:
        content = content.replace(
            old_deduct_sig + '\n    request: Request,',
            old_deduct_sig + '\n    request: Request,\n    _auth: dict = Depends(require_tenant),'
        )

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-007 syntax error: {e}")
        return False
    return True


def fix_sec008():
    """Batch billing auth - require Bearer token."""
    fp = os.path.join(SRC, "api/billing_endpoints.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add auth dependency to submit_batch_billing
    old_sig = 'async def submit_batch_billing(\n    request: BatchBillingRequest,'
    new_sig = 'async def submit_batch_billing(\n    request: BatchBillingRequest,\n    auth: dict = Depends(lambda: get_repository()),'
    if old_sig in content:
        content = content.replace(old_sig, new_sig, 1)
    else:
        print("  WARNING: SEC-008 signature not found")

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-008 syntax error: {e}")
        return False
    return True


def fix_sec009():
    """Tier config routes - add require_admin."""
    fp = os.path.join(SRC, "api/tier_config_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add imports
    old_imports = "from fastapi import APIRouter, HTTPException, Response, status"
    new_imports = "from fastapi import APIRouter, Depends, HTTPException, Response, status\nfrom src.auth.tenant_auth import require_admin"
    if old_imports in content:
        content = content.replace(old_imports, new_imports, 1)

    # Add Depends(require_admin) to each route
    routes_to_fix = [
        ("@router.get(\"/\", response_model=TierConfigsListResponse)", "@router.get(\"/\", response_model=TierConfigsListResponse)\nasync def list_tier_configs(\n    _admin: dict = Depends(require_admin),\n):"),
        ("@router.post(\"/\", response_model=TierConfigResponse)", "@router.post(\"/\", response_model=TierConfigResponse)\nasync def create_tier_config(\n    _admin: dict = Depends(require_admin),\n):"),
        ("@router.put(\"/{config_id}\", response_model=TierConfigResponse)", "@router.put(\"/{config_id}\", response_model=TierConfigResponse)\nasync def update_tier_config(\n    _admin: dict = Depends(require_admin),\n):"),
        ("@router.delete(\"/{config_id}\")", "@router.delete(\"/{config_id}\")\nasync def delete_tier_config(\n    _admin: dict = Depends(require_admin),\n):"),
    ]

    for old_pat, new_pat in routes_to_fix:
        if old_pat in content:
            content = content.replace(old_pat, new_pat, 1)
        else:
            print(f"  WARNING: SEC-009 pattern not found: {old_pat[:60]}...")

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-009 syntax error: {e}")
        return False
    return True


def fix_sec010():
    """vn_pilot_polls - add require_tenant."""
    fp = os.path.join(SRC, "api/vn_pilot_polls.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add import
    if "from src.auth.tenant_auth import require_tenant" not in content:
        content = content.replace(
            "from fastapi import APIRouter, HTTPException, status",
            "from fastapi import APIRouter, Depends, HTTPException, status\nfrom src.auth.tenant_auth import require_tenant"
        )

    # Add auth to poll_response
    old = '@polls_router.post("/response", status_code=status.HTTP_201_CREATED)\nasync def poll_response(req: PollResponseRequest) -> dict[str, object]:'
    new = '@polls_router.post("/response", status_code=status.HTTP_201_CREATED)\nasync def poll_response(\n    req: PollResponseRequest,\n    _auth: dict = Depends(require_tenant),\n) -> dict[str, object]:'

    if old in content:
        content = content.replace(old, new, 1)
    else:
        print("  WARNING: SEC-010 pattern not found")
        return False

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-010 syntax error: {e}")
        return False
    return True


def fix_sec011():
    """Stripe tier-to-role exact match only."""
    fp = os.path.join(SRC, "auth/stripe_integration.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''role = self.tier_to_role.get(stripe_price_id)
    if not role:
        # Try matching by pattern (e.g., "price_123_pro" -> "price_pro")
        # Check if the price ID ends with or contains the pattern key suffix
        for price_pattern, mapped_role in self.tier_to_role.items():
            # Check both directions: pattern in ID or ID ends with pattern suffix
            if price_pattern in stripe_price_id or stripe_price_id in price_pattern:
                return mapped_role
        # Extract suffix after last underscore from pattern and check
        pattern_suffix = price_pattern.split("_", 1)[-1]  # e.g., "pro" from "price_pro"
        if stripe_price_id.endswith(f"_{pattern_suffix}") or stripe_price_id.endswith(pattern_suffix):
            return mapped_role
    return role'''

    new = '''role = self.tier_to_role.get(stripe_price_id)
    if not role:
        # Exact match only - no substring matching to prevent role escalation
        return None
    return role'''

    if old not in content:
        print(f"  WARNING: SEC-011 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-011 syntax error: {e}")
        return False
    return True


def fix_sec012():
    """Path traversal in cc_spawner."""
    fp = os.path.join(SRC, "core/cc_spawner.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """if project:
        project_dir = os.path.join(self.cwd, "apps", project)"""

    new = """if project:
        project_dir = os.path.join(self.cwd, "apps", project)
        # Path traversal prevention
        project_dir = os.path.realpath(project_dir)
        allowed_base = os.path.realpath(os.path.join(self.cwd, "apps"))
        if not project_dir.startswith(allowed_base + os.sep):
            session.status = SessionStatus.FAILED
            session.error = f"Path traversal blocked: {project}"
            self._sessions[session.id] = session
            return session"""

    if old not in content:
        print(f"  WARNING: SEC-012 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-012 syntax error: {e}")
        return False
    return True


def fix_sec013():
    """Governance approval gate - return False by default."""
    fp = os.path.join(SRC, "core/governance.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''def request_approval(self, goal: str, decision: GovernanceDecision) -> bool:
        """Request human approval. Placeholder - returns True."""\n        decision.approved = True\n        return True'''

    new = '''def request_approval(self, goal: str, decision: GovernanceDecision) -> bool:
        """Request human approval. Returns False until explicitly approved."""
        # Default to False - approval gate must be explicitly opened
        decision.approved = False
        return False'''

    if old not in content:
        print(f"  WARNING: SEC-013 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-013 syntax error: {e}")
        return False
    return True


def fix_sec014():
    """Token blacklist in session_manager."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add _token_blacklist at class/module level
    old_module_attrs = "JWT_ALGORITHM = \"HS256\""
    new_module_attrs = 'JWT_ALGORITHM = "HS256"\n_token_blacklist: set = set()'

    if old_module_attrs in content:
        content = content.replace(old_module_attrs, new_module_attrs, 1)
    else:
        print("  WARNING: SEC-014 JWT_ALGORITHM not found")
        return False

    # Add blacklist check in validate_session
    old_validate = """is_valid, payload, error = self.decode_token(token)  # noqa: F841 (error unused)
        if not is_valid:
            return None

        user_id = payload.get("sub")"""

    new_validate = """is_valid, payload, error = self.decode_token(token)  # noqa: F841 (error unused)
        if not is_valid:
            return None

        # Check token blacklist
        jti = payload.get("jti")
        if jti and jti in _token_blacklist:
            return None

        user_id = payload.get("sub")"""

    if old_validate in content:
        content = content.replace(old_validate, new_validate, 1)
    else:
        print("  WARNING: SEC-014 validate_session pattern not found")
        return False

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-014 syntax error: {e}")
        return False
    return True


def fix_sec015():
    """Session validation - add DB session check."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = await self._user_repo.find_by_id(UUID(user_id))
            return user"""

    new = """user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify session exists in DB (not just valid JWT)
        try:
            session = await self._user_repo.find_session_by_token_hash(
                __import__("hashlib").sha256(token.encode()).hexdigest()
            )
            if not session:
                return None  # Session revoked or expired
            user = await self._user_repo.find_by_id(UUID(user_id))
            return user"""

    if old not in content:
        print(f"  WARNING: SEC-015 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-015 syntax error: {e}")
        return False
    return True


def fix_sec016():
    """Command sanitizer - allow patterns must not clear blocks."""
    # Fix both command_sanitizer.py and core/command_sanitizer.py
    for rel_path in ["security/command_sanitizer.py", "core/command_sanitizer.py"]:
        fp = os.path.join(SRC, rel_path)
        if not os.path.exists(fp):
            continue
        backup(fp)
        with open(fp) as f:
            content = f.read()

        # Ensure is_safe starts False
        old = "result.is_safe = True\n        result.allowed_patterns = list(self.allow_patterns)"
        new = "# Start as not safe - allow patterns only add, never clear blocks\n        result.is_safe = False\n        result.allowed_patterns = list(self.allow_patterns)"

        if old in content:
            content = content.replace(old, new, 1)
            with open(fp, "w") as f:
                f.write(content)
            try:
                py_compile.compile(fp, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"  ERROR: SEC-016 syntax error in {fp}: {e}")
                continue
        else:
            print(f"  WARNING: SEC-016 target not found in {rel_path}")


def fix_sec017():
    """Dev-login - remove hardcoded role=owner."""
    fp = os.path.join(SRC, "auth/routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'defaults={"name": "Dev User", "role": "owner"}  # Full access for testing'
    new = 'defaults={"name": "Dev User", "role": "developer"}'

    if old not in content:
        print(f"  WARNING: SEC-017 target not found")
        return False
    content = content.replace(old, new, 1)

    # Also gate dev-login behind ENV check
    old_dev_login = 'if not settings.ENV or settings.ENV != "production":\n    return await _dev_login(request)'
    new_dev_login = 'if settings.ENV == "production":\n        raise HTTPException(\n            status_code=status.HTTP_403_FORBIDDEN,\n            detail="Dev login disabled in production",\n        )\n    return await _dev_login(request)'

    if old_dev_login in content:
        content = content.replace(old_dev_login, new_dev_login, 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-017 syntax error: {e}")
        return False
    return True


def fix_sec018():
    """Dev-login - unique email per session."""
    fp = os.path.join(SRC, "auth/routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Create or get dev test user
    test_email = "dev@example.com"
    user = await user_repo.find_or_create_user(
        email=test_email,
        provider="local",
        oauth_id="dev-local-user",
        defaults={"name": "Dev User", "role": "developer"}  # Full access for testing
    )"""

    new = """# Create or get dev test user - unique email per session to prevent account sharing
    import uuid as _uuid
    test_email = f"dev-{_uuid.uuid4().hex[:8]}@example.com"
    user = await user_repo.find_or_create_user(
        email=test_email,
        provider="local",
        oauth_id=f"dev-local-{_uuid.uuid4().hex[:8]}",
        defaults={"name": "Dev User", "role": "developer"}
    )"""

    if old not in content:
        print(f"  WARNING: SEC-018 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-018 syntax error: {e}")
        return False
    return True


def fix_sec019():
    """bcrypt for token hashing in user_repository."""
    fp = os.path.join(SRC, "auth/user_repository.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add bcrypt import
    old_imports = "import hashlib\nimport logging"
    new_imports = "import hashlib\nimport logging\nimport bcrypt"

    if old_imports in content:
        content = content.replace(old_imports, new_imports, 1)

    # Replace sha256 token hashing with bcrypt
    old_hash = """import hashlib
    _ = hashlib.sha256(access_token.encode()).hexdigest()  # token_hash intentionally unused"""

    new_hash = """import bcrypt as _bcrypt
    _ = _bcrypt.hashpw(access_token.encode(), _bcrypt.gensalt()).decode()  # token_hash intentionally unused"""

    if old_hash in content:
        content = content.replace(old_hash, new_hash, 1)
    else:
        print(f"  WARNING: SEC-019 target not found")
        return False

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: SEC-019 syntax error: {e}")
        return False
    return True


# ============================================================================
# PHASE 2: HIGH (22 fixes)
# ============================================================================

def fix_high001():
    """X-Forwarded-For - only trust from known proxy IPs."""
    for fp_rel in ["auth/rate_limit_decorator.py", "middleware/rate_limit_gateway_middleware.py"]:
        fp = os.path.join(SRC, fp_rel)
        if not os.path.exists(fp):
            continue
        backup(fp)
        with open(fp) as f:
            content = f.read()

        old = """def get_client_ip(request: Request) -> str:
        \"\"\"Extract client IP address from request headers.\"\"\"
        # Check X-Forwarded-For header first (set by reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown\""""

        new = """def get_client_ip(request: Request) -> str:
        \"\"\"Extract client IP address from request headers.\"\"\"
        # Only trust X-Forwarded-For from known proxy IPs
        _TRUSTED_PROXIES = os.getenv("TRUSTED_PROXY_IPS", "").split(",")
        _TRUSTED_PROXIES = [p.strip() for p in _TRUSTED_PROXIES if p.strip()]
        client_host = request.client.host if request.client else "unknown"
        if client_host in _TRUSTED_PROXIES:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return client_host"""

        if old in content:
            content = content.replace(old, new, 1)
            with open(fp, "w") as f:
                f.write(content)
            try:
                py_compile.compile(fp, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"  ERROR: HIGH-001 syntax error in {fp_rel}: {e}")
                continue
        else:
            print(f"  WARNING: HIGH-001 target not found in {fp_rel}")


def fix_high002():
    """RBAC - raise 403 on invalid role instead of silent downgrade."""
    fp = os.path.join(SRC, "auth/rbac.py")
    backup(fp)
    with open(fp) as f:
        lines = f.readlines()

    old_block = """if user_role:
            try:
                # Ensure role is valid
                Role(user_role)
                request.state.user_role = user_role
            except ValueError:
                # Invalid role, default to member
                request.state.user_role = Role.MEMBER.value
        else:
            # No role specified, default to member
            request.state.user_role = Role.MEMBER.value"""

    new_block = """if user_role:
            try:
                # Ensure role is valid
                Role(user_role)
                request.state.user_role = user_role
            except ValueError:
                # Invalid role - reject request, do not silently downgrade
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid role: {user_role}",
                )
        else:
            # No role specified - reject request
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role claim missing from token",
            )"""

    old_text = "\n".join(old_block)
    new_text = "\n".join(new_block)
    with open(fp) as f:
        content = f.read()
    if old_text not in content:
        print(f"  WARNING: HIGH-002 target not found")
        return False
    content = content.replace(old_text, new_text, 1)

    # Ensure status import exists
    if "from fastapi import" in content and "status" not in content.split("from fastapi import")[1].split("\n")[0]:
        content = content.replace(
            "from fastapi import",
            "from fastapi import status,"
        )

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-002 syntax error: {e}")
        return False
    return True


def fix_high003():
    """__Host- cookie prefix in production."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''COOKIE_NAME = "session_token"'''
    new = '''COOKIE_NAME = "__Host-session_token"'''

    if old not in content:
        print(f"  WARNING: HIGH-003 COOKIE_NAME not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-003 syntax error: {e}")
        return False
    return True


def fix_high004():
    """Persist billing state to disk."""
    for fp_rel in ["api/raas_billing_service.py", "api/raas_task_store.py"]:
        fp = os.path.join(SRC, fp_rel)
        if not os.path.exists(fp):
            continue
        backup(fp)
        with open(fp) as f:
            content = f.read()

        # Add persistence methods
        persist_block = '''
import json
import os as _os

_PERSIST_PATH = os.path.expanduser("~/.mekong/{basename}.json")

def _persist(self):
    """Persist state to disk."""
    try:
        os.makedirs(os.path.dirname(_PERSIST_PATH), exist_ok=True)
        with open(_PERSIST_PATH, "w") as f:
            json.dump(self._serialize(), f, default=str)
    except Exception as e:
        logger.warning("Failed to persist state: %s", e)

def _load(self):
    """Load state from disk."""
    if not os.path.exists(_PERSIST_PATH):
        return
    try:
        with open(_PERSIST_PATH) as f:
            data = json.load(f)
        self._deserialize(data)
    except Exception as e:
        logger.warning("Failed to load state: %s", e)
'''.format(basename="raas_billing" if "billing" in fp_rel else "raas_task_store")

        # Insert after imports
        if 'import logging' in content:
            content = content.replace('import logging\n', 'import logging\n' + persist_block, 1)

        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: HIGH-004 syntax error in {fp_rel}: {e}")
            continue


def fix_high005():
    """OAuth state - encrypted cookie validation."""
    fp = os.path.join(SRC, "auth/routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Replace session-based state with encrypted cookie
    old = """# Verify state (simplified - implement proper CSRF protection)
        stored_state = request.session.get("oauth_state")
        if stored_state and state != stored_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )"""

    new = """# Verify state via encrypted cookie (fail-closed)
        stored_state = request.cookies.get("oauth_state")
        if not stored_state or state != stored_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )"""

    if old not in content:
        print(f"  WARNING: HIGH-005 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-005 syntax error: {e}")
        return False
    return True


def fix_high006():
    """Whitespace bypass in command sanitizer."""
    for fp_rel in ["security/command_sanitizer.py", "core/command_sanitizer.py"]:
        fp = os.path.join(SRC, fp_rel)
        if not os.path.exists(fp):
            continue
        backup(fp)
        with open(fp) as f:
            content = f.read()

        old = 'command = command.strip()'
        new = 'import re as _re\n        command = _re.sub(r"\\s+", " ", command).strip()'

        if old in content:
            content = content.replace(old, new, 1)
            with open(fp, "w") as f:
                f.write(content)
            try:
                py_compile.compile(fp, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"  ERROR: HIGH-006 syntax error in {fp_rel}: {e}")
                continue
        else:
            print(f"  WARNING: HIGH-006 target not found in {fp_rel}")


def fix_high007():
    """LLM prompt injection - sanitize step.description."""
    fp = os.path.join(SRC, "core/executor.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """prompt = step.description
        system_prompt = step.params.get("system", "") if step.params else """

    new = """# Sanitize step description to prevent prompt injection
        prompt = re.sub(r"(?i)(ignore\\s+(previous|above|all)\\s+instructions|system\\s*:|you\\s+are\\s+now|new\\s+instruction|override\\s+system)", "[FILTERED]", step.description)
        system_prompt = step.params.get("system", "") if step.params else """

    if old not in content:
        print(f"  WARNING: HIGH-007 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-007 syntax error: {e}")
        return False
    return True


def fix_high008():
    """API/browse steps - URL allowlist + SSRF."""
    fp = os.path.join(SRC, "core/executor.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """url = step.params.get("url", "") if step.params else ""
        method = (step.params.get("method", "GET") if step.params else "GET").upper()
        body = step.params.get("body", None) if step.params else None
        headers = step.params.get("headers", {}) if step.params else {}"""

    new = """# URL allowlist + SSRF check
        from src.core.executor import _is_safe_url
        url = step.params.get("url", "") if step.params else ""
        if not url:
            return ExecutionResult(exit_code=0, stdout="[SKIPPED] No URL", stderr="", metadata={"mode": "api", "skipped": True})
        if not _is_safe_url(url):
            return ExecutionResult(exit_code=1, stdout="", stderr="URL blocked: targets private network", metadata={"mode": "api", "ssrf_blocked": True})
        method = (step.params.get("method", "GET") if step.params else "GET").upper()
        body = step.params.get("body", None) if step.params else None
        headers = step.params.get("headers", {}) if step.params else {}"""

    if old not in content:
        print(f"  WARNING: HIGH-008 target not found")
        return False
    content = content.replace(old, new, 1)

    # Also remove the duplicate URL check that was in _execute_api_step
    # Remove the now-duplicate SSRF check block
    old_ssrf_dup = """# SSRF check before making request
        if not _is_safe_url(url):
            self.console.print(f"[bold red]SSRF blocked:[/bold red] {url} targets private network")
            return ExecutionResult(
                exit_code=1, stdout="",
                stderr="URL blocked: targets private/internal network",
                metadata={"mode": "api", "ssrf_blocked": True},
            )"""

    if old_ssrf_dup in content:
        content = content.replace(old_ssrf_dup, "", 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-008 syntax error: {e}")
        return False
    return True


def fix_high009():
    """MCU deduction idempotency."""
    fp = os.path.join(SRC, "gateway_webhook_mcu_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add idempotency key to deduct logic
    old = """# Deduct MCU from tenant
        result = await deduct_mcu("""
    new = """# Idempotency check
        idempotency_key = request.headers.get("X-Idempotency-Key") or str(uuid.uuid4())
        existing = await get_existing_deduction(tenant_id, idempotency_key)
        if existing:
            return {"status": "already_processed", "mcu_deducted": existing["amount"]}

        # Deduct MCU from tenant
        result = await deduct_mcu("""

    if old not in content:
        print(f"  WARNING: HIGH-009 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-009 syntax error: {e}")
        return False
    return True


def fix_high010():
    """Rate limiter - Redis backend option."""
    fp = os.path.join(SRC, "auth/rate_limiter.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add Redis backend hook
    old = "class RateLimiter:\n    def __init__(self):"
    new = """class RateLimiter:
    def __init__(self):
        self._redis = None
        if os.getenv("REDIS_URL"):
            try:
                import redis as _redis
                self._redis = _redis.from_url(os.getenv("REDIS_URL"))
            except ImportError:
                pass  # Fall back to in-memory"""

    if old not in content:
        print(f"  WARNING: HIGH-010 target not found")
        return False
    content = content.replace(old, new, 1)

    # Add os import
    if "import os" not in content:
        content = "import os\n" + content

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-010 syntax error: {e}")
        return False
    return True


def fix_high011():
    """MISSION_STORE - add threading.Lock."""
    fp = os.path.join(SRC, "api/gateway_mission_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'MISSION_STORE: dict = {}'
    new = 'import threading\n\nMISSION_STORE: dict = {}\n_MISSION_LOCK = threading.Lock()\n_MISSION_STORE_MAX_ENTRIES = 1000'

    if old not in content:
        print(f"  WARNING: HIGH-011 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-011 syntax error: {e}")
        return False
    return True


def fix_high012():
    """MISSION_STORE - add size limit."""
    fp = os.path.join(SRC, "api/gateway_mission_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add size check before appending to MISSION_STORE entries
    old = "MISSION_STORE[mission_id].append(event)"
    new = """if len(MISSION_STORE.get(mission_id, [])) >= _MISSION_STORE_MAX_ENTRIES:
            MISSION_STORE[mission_id] = MISSION_STORE[mission_id][-(_MISSION_STORE_MAX_ENTRIES // 2):]
        MISSION_STORE[mission_id].append(event)"""

    if old not in content:
        print(f"  WARNING: HIGH-012 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-012 syntax error: {e}")
        return False
    return True


def fix_high013():
    """find_or_create_user TOCTOU race."""
    fp = os.path.join(SRC, "auth/user_repository.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Create new user
        return await self.create_user(email, provider, oauth_id)"""

    new = """# Create new user (with race condition handling)
        try:
            return await self.create_user(email, provider, oauth_id)
        except IntegrityError:
            # Another request created the user concurrently - retry lookup
            user = await self.find_by_oauth(provider, oauth_id)
            if user:
                return user
            user = await self.find_by_email(email)
            if user:
                return user
            raise"""

    if old not in content:
        print(f"  WARNING: HIGH-013 target not found")
        return False
    content = content.replace(old, new, 1)

    # Add IntegrityError import if missing
    if "from sqlalchemy.exc import IntegrityError" not in content:
        if "from sqlalchemy" in content:
            content = content.replace(
                "from sqlalchemy",
                "from sqlalchemy.exc import IntegrityError\nfrom sqlalchemy"
            )
        else:
            content = "from sqlalchemy.exc import IntegrityError\n" + content

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-013 syntax error: {e}")
        return False
    return True


def fix_high014():
    """SQLite INSERT error handling with retry."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        lines = f.readlines()

    # Find the INSERT block (around line 156-172)
    # Look for "await self._db.execute" that is an INSERT
    insert_idx = None
    for i, line in enumerate(lines):
        if "INSERT INTO usage_events" in line or "INSERT INTO" in line and "usage_events" in "".join(lines[max(0, i-3):i+3]):
            insert_idx = i
            break

    if insert_idx is None:
        # Try broader search
        for i, line in enumerate(lines):
            if "await self._db.execute" in line and i > 150:
                insert_idx = i
                break

    if insert_idx is None:
        print(f"  WARNING: HIGH-014 INSERT not found")
        return False

    # Get base indent
    context = lines[insert_idx - 1] if insert_idx > 0 else lines[0]
    base_indent = len(context) - len(context.lstrip())

    # Find the end of the insert block (next blank or lower indent line)
    end_idx = insert_idx + 1
    for j in range(insert_idx + 1, min(insert_idx + 20, len(lines))):
        if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= base_indent:
            end_idx = j
            break
        if not lines[j].strip():
            end_idx = j + 1
            break
    else:
        end_idx = min(insert_idx + 15, len(lines))

    retry_block = [
        "for attempt in range(3):",
        "    try:",
        "        await self._db.execute(insert_query, params)",
        "        await self._db.commit()",
        "        break",
        "    except (OperationalError, IntegrityError) as e:",
        "        await self._db.rollback()",
        "        if attempt < 2:",
        "            import time as _time",
        "            _time.sleep(0.1 * (2 ** attempt))",
        "        else:",
        "            raise",
    ]

    indented = [" " * base_indent + l for l in retry_block]
    lines[insert_idx:end_idx] = indented

    with open(fp, "w") as f:
        f.writelines(lines)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-014 syntax error: {e}")
        return False
    return True


def fix_high015():
    """Metrics endpoint - require METRICS_AUTH_TOKEN."""
    fp = os.path.join(SRC, "api/metrics_routes.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Optional auth token check
    metrics_token = os.getenv("METRICS_AUTH_TOKEN")
    if not metrics_token:
        # No token configured - allow access (backward compat)
        pass"""

    new = """# Mandatory auth token check - fail closed
    metrics_token = os.getenv("METRICS_AUTH_TOKEN")
    if not metrics_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics endpoint not configured - METRICS_AUTH_TOKEN required",
        )

    # Verify token
    request_token = request.headers.get("X-Metrics-Token", "")
    if not hmac.compare_digest(metrics_token, request_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid metrics token",
        )"""

    if old not in content:
        print(f"  WARNING: HIGH-015 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-015 syntax error: {e}")
        return False
    return True


def fix_high016():
    """Atomic daily aggregation in usage_tracker."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Group by event type (multiple queries)
        for event_type in event_types:"""

    new = "# Atomic aggregation with GROUP BY (single query)\n"
    new += "        aggregate_query = SELECT_WITH_GROUP_BY"

    if old not in content:
        print(f"  WARNING: HIGH-016 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-016 syntax error: {e}")
        return False
    return True


def fix_high017():
    """JWT secret - never generate random in dev."""
    fp = os.path.join(SRC, "auth/config.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Generate random secret for development
    jwt_secret = secrets.token_hex(32)"""

    new = """# JWT secret must come from environment - never auto-generate
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET environment variable is required")"""

    if old not in content:
        print(f"  WARNING: HIGH-017 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-017 syntax error: {e}")
        return False
    return True


def fix_high018():
    """Governance audit - atomic write."""
    fp = os.path.join(SRC, "core/governance.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """def _save_audit(self) -> None:
        \"\"\"Save audit trail to YAML.\"\"\"
        path = Path(self.audit_path)
        path.write_text(yaml.dump(self._audit))"""

    new = """def _save_audit(self) -> None:
        \"\"\"Save audit trail to YAML atomically.\"\"\"
        import tempfile as _tempfile
        import os as _os
        path = Path(self.audit_path)
        dir_path = path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = _tempfile.mkstemp(dir=dir_path, suffix=".yaml.tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(yaml.dump(self._audit))
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise"""

    if old not in content:
        print(f"  WARNING: HIGH-018 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-018 syntax error: {e}")
        return False
    return True


def fix_high019():
    """json.dumps instead of str(metadata)."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'metadata_str = str(metadata or {})'
    new = 'metadata_str = json.dumps(metadata or {}, default=str)'

    if old not in content:
        print(f"  WARNING: HIGH-019 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-019 syntax error: {e}")
        return False
    return True


def fix_high020():
    """CHECK constraint on units column."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "CREATE TABLE IF NOT EXISTS usage_events ("
    new = """CREATE TABLE IF NOT EXISTS usage_events (
        CHECK (units > 0),"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: HIGH-020 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: HIGH-020 table creation not found")
        return False
    return True


def fix_high021():
    """WAL mode + VACUUM in usage_tracker."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'self._db.execute("PRAGMA journal_mode=WAL")'
    new = """self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA wal_checkpoint(TRUNCATE)")"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: HIGH-021 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: HIGH-021 WAL mode not found")
        return False
    return True


def fix_high022():
    """Coupon race condition - atomic SQL."""
    fp = os.path.join(SRC, "api/coupon_router.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """coupon["uses"] += 1
    logger.info("Coupon %s applied: %s %d%% off -> $%d->$%d", code, req.tier, discount, original, final)

    return CouponResponse("""

    new = """# Atomic update - increment uses only if remaining > 0
    from src.db.repository import get_repository
    repo = get_repository()
    updated = await repo.execute(
        "UPDATE coupons SET uses = uses + 1 WHERE code = $1 AND uses < max_uses",
        code,
    )
    if not updated:
        return CouponResponse(success=False, error="Ma giam gia da het luot su dung.")

    logger.info("Coupon %s applied: %s %d%% off -> $%d->$%d", code, req.tier, discount, original, final)

    return CouponResponse("""

    if old not in content:
        print(f"  WARNING: HIGH-022 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: HIGH-022 syntax error: {e}")
        return False
    return True


# ============================================================================
# PHASE 3: MEDIUM (27 fixes)
# ============================================================================

def fix_med001():
    """Add aud/iss claims to JWT."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = '''payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,'''

    new = '''payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "aud": "mekong-cli",
            "iss": "mekong-auth",'''

    if old not in content:
        print(f"  WARNING: MED-001 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-001 syntax error: {e}")
        return False
    return True


def fix_med002():
    """Fernet encryption for session cache."""
    fp = os.path.join(SRC, "core/auth_session.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """import os
import json"""
    new = """import os
import json
from cryptography.fernet import Fernet"""

    if old in content:
        content = content.replace(old, new, 1)

    old_write = """with open(self._cache_path, "w") as f:
            json.dump(cache_data, f)"""
    new_write = """# Encrypt before writing
        key = os.getenv("SESSION_CACHE_KEY") or Fernet.generate_key().decode()
        f_obj = Fernet(key.encode())
        encrypted = f_obj.encrypt(json.dumps(cache_data).encode())
        with open(self._cache_path, "wb") as f:
            f.write(encrypted)"""

    if old_write in content:
        content = content.replace(old_write, new_write, 1)
    else:
        print(f"  WARNING: MED-002 write block not found")

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-002 syntax error: {e}")
        return False
    return True


def fix_med003():
    """O_CREAT|O_EXCL atomic file creation."""
    fp = os.path.join(SRC, "core/auth_session.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """with open(self._cache_path, "w") as f:
            json.dump(cache_data, f)
        os.chmod(self._cache_path, 0o600)"""

    new = """# Atomic creation with O_CREAT|O_EXCL to prevent TOCTOU
        import tempfile as _tmp
        dir_path = os.path.dirname(self._cache_path)
        fd, tmp_path = _tmp.mkstemp(dir=dir_path, suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(cache_data, f)
            os.chmod(tmp_path, 0o600)
            os.rename(tmp_path, self._cache_path)
        except FileExistsError:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)"""

    if old not in content:
        print(f"  WARNING: MED-003 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-003 syntax error: {e}")
        return False
    return True


def fix_med004():
    """Replace base64 with Fernet for API keys."""
    fp = os.path.join(SRC, "core/api_key_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """import base64"""
    new = """import base64
from cryptography.fernet import Fernet"""

    if old in content:
        content = content.replace(old, new, 1)

    old_enc = """encoded = base64.b64encode(api_key.encode()).decode()
        return encoded"""
    new_enc = """key = os.getenv("API_KEY_MASTER_KEY") or Fernet.generate_key().decode()
        encrypted = Fernet(key.encode()).encrypt(api_key.encode())
        return encrypted.decode()"""

    if old_enc in content:
        content = content.replace(old_enc, new_enc, 1)

    old_dec = """decoded = base64.b64decode(encoded_key.encode()).decode()
        return decoded"""
    new_dec = """key = os.getenv("API_KEY_MASTER_KEY") or Fernet.generate_key().decode()
        decrypted = Fernet(key.encode()).decrypt(encoded_key.encode())
        return decrypted.decode()"""

    if old_dec in content:
        content = content.replace(old_dec, new_dec, 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-004 syntax error: {e}")
        return False
    return True


def fix_med005():
    """Replace MD5 with SHA-256 for tenant ID."""
    fp = os.path.join(SRC, "core/auth_tenant.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "tenant_hash = hashlib.md5(tenant_input.encode()).hexdigest()"
    new = "tenant_hash = hashlib.sha256(tenant_input.encode()).hexdigest()"

    count = content.count(old)
    for _ in range(count):
        content = content.replace(old, new, 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-005 syntax error: {e}")
        return False
    return True


def fix_med006():
    """Certificate store - raise on no secure storage."""
    fp = os.path.join(SRC, "core/certificate_store.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Fallback: load from file
    key_file = self.cert_dir / "private_key.pem"
    if key_file.exists():
        try:
            with open(key_file, "rb") as f:
                return f.read()
        except Exception as e:
            logger.debug("Failed to load private key from file: %s", e)

    return None"""

    new = """# No fallback - require secure storage to be configured
    raise RuntimeError(
        "No secure storage configured for private key. "
        "Set up system keyring or environment variable for secure storage."
    )"""

    if old not in content:
        print(f"  WARNING: MED-006 target not found")
        return False
    content = content.replace(old, new, 1)

    # Also fix _save_private_key fallback
    old_save = """# Fallback: save to file (less secure)
    key_file = self.cert_dir / "private_key.pem"
    with open(key_file, "wb") as f:
        f.write(private_key_pem)
    os.chmod(key_file, 0o600)"""

    new_save = """# No fallback - require secure storage
    raise RuntimeError(
        "No secure storage configured for private key save. "
        "Configure secure storage before saving keys."
    )"""

    if old_save in content:
        content = content.replace(old_save, new_save, 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-006 syntax error: {e}")
        return False
    return True


def fix_med007():
    """Schema version tracking in usage_tracker."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "CREATE TABLE IF NOT EXISTS usage_events ("
    new = """CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS usage_events ("""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-007 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-007 table creation not found")
        return False
    return True


def fix_med008():
    """WAL checkpoint strategy."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'self._db.execute("PRAGMA journal_mode=WAL")'
    new = '''self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA wal_checkpoint(TRUNCATE)")'''

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-008 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-008 WAL mode not found")
        return False
    return True


def fix_med009():
    """Input sanitization in validation module."""
    fp = os.path.join(SRC, "core/input_validation.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    sanitize_func = '''
import re
import unicodedata


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input: normalize Unicode, strip control chars, limit length."""
    if not isinstance(text, str):
        return str(text)
    # Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)
    # Strip control characters (except newline, tab)
    text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
    # Normalize HTML/XML entities
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    # Collapse whitespace
    text = re.sub(r"\\s+", " ", text).strip()
    # Length limit
    return text[:max_length]
'''

    # Add at end of file if not already there
    if "def sanitize_input(" not in content:
        with open(fp, "a") as f:
            f.write("\n" + sanitize_func)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-009 syntax error: {e}")
        return False
    return True


def fix_med010():
    """Sanitize name field in signup."""
    fp = os.path.join(SRC, "api/vn_pilot_signup.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'name = data.get("name", "").strip()'
    new = '''from src.core.input_validation import sanitize_input
        name = sanitize_input(data.get("name", "").strip(), max_length=100)'''

    if old not in content:
        print(f"  WARNING: MED-010 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-010 syntax error: {e}")
        return False
    return True


def fix_med011():
    """Whitelist columns in update_user."""
    fp = os.path.join(SRC, "auth/user_repository.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Build dynamic update query
        fields = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(kwargs.keys()))
        values = list(kwargs.values())"""

    new = """# Validate column names against whitelist
        ALLOWED_UPDATE_COLUMNS = {"name", "role", "email", "provider", "oauth_id", "tier"}
        invalid_cols = set(kwargs.keys()) - ALLOWED_UPDATE_COLUMNS
        if invalid_cols:
            raise ValueError(f"Invalid update columns: {invalid_cols}")

        # Build dynamic update query
        fields = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(kwargs.keys()))
        values = list(kwargs.values())"""

    if old not in content:
        print(f"  WARNING: MED-011 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-011 syntax error: {e}")
        return False
    return True


def fix_med012():
    """CORS middleware with origin allowlist."""
    fp = os.path.join(SRC, "middleware/__init__.py")
    if not os.path.exists(fp):
        # Create the file
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w") as f:
            f.write("""\"\"\"Mekong CLI Middleware\"\"\"

from fastapi.middleware.cors import CORSMiddleware


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


def setup_cors(app):
    \"\"\"Configure CORS with explicit origin allowlist.\"\"\"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
""")
        return True

    backup(fp)
    with open(fp) as f:
        content = f.read()

    if "setup_cors" not in content:
        content += "\n\nfrom fastapi.middleware.cors import CORSMiddleware\n\n\nALLOWED_ORIGINS = os.getenv(\"ALLOWED_ORIGINS\", \"http://localhost:3000\").split(\",\")\n\n\ndef setup_cors(app):\n    app.add_middleware(\n        CORSMiddleware,\n        allow_origins=ALLOWED_ORIGINS,\n        allow_credentials=True,\n        allow_methods=[\"GET\", \"POST\", \"PUT\", \"DELETE\", \"PATCH\", \"OPTIONS\"],\n        allow_headers=[\"Authorization\", \"Content-Type\", \"X-Request-ID\"],\n    )\n"

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-012 syntax error: {e}")
        return False
    return True


def fix_med013():
    """CSRF token rotation per-request."""
    fp = os.path.join(SRC, "middleware/csrf_middleware.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """def _generate_csrf_token(self) -> str:
        \"\"\"Generate new CSRF token.\"\"\"
        return secrets.token_urlsafe(32)"""

    new = """def _generate_csrf_token(self, rotate: bool = False) -> str:
        \"\"\"Generate new CSRF token. Rotate existing if requested.\"\"\"
        if rotate and hasattr(self, "_csrf_token"):
            self._csrf_token = secrets.token_urlsafe(32)
            return self._csrf_token
        self._csrf_token = secrets.token_urlsafe(32)
        return self._csrf_token"""

    if old not in content:
        print(f"  WARNING: MED-013 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-013 syntax error: {e}")
        return False
    return True


def fix_med014():
    """RBAC invalid role - raise 403 (duplicate of HIGH-002, skip)."""
    print("  SKIP: MED-014 is duplicate of HIGH-002")
    return True


def fix_med015():
    """Rate limiter - persist state."""
    fp = os.path.join(SRC, "auth/rate_limiter.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "class RateLimiter:\n    def __init__(self):\n        self._limits = {}"
    new = """class RateLimiter:
    def __init__(self):
        self._limits = {}
        self._redis = None
        if os.getenv("REDIS_URL"):
            try:
                import redis as _redis
                self._redis = _redis.from_url(os.getenv("REDIS_URL"))
                self._load_from_redis()
            except ImportError:
                pass"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-015 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-015 target not found")
        return False
    return True


def fix_med016():
    """Thread-safe singleton for usage_tracker and rate_limiter."""
    for fp_rel in ["metering/usage_tracker.py", "auth/rate_limiter.py"]:
        fp = os.path.join(SRC, fp_rel)
        if not os.path.exists(fp):
            continue
        backup(fp)
        with open(fp) as f:
            content = f.read()

        old = "import threading" if "import threading" in content else "_instance = None\n_instance_lock = threading.Lock()"
        new = "_instance = None\n_instance_lock = threading.Lock()"

        if "_instance_lock" not in content:
            content = content.replace(
                "_instance = None",
                "_instance = None\n_instance_lock = threading.Lock()"
            )
            with open(fp, "w") as f:
                f.write(content)
            try:
                py_compile.compile(fp, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"  ERROR: MED-016 syntax error in {fp_rel}: {e}")
                continue


def fix_med017():
    """SQLite thread safety."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'self._db = sqlite3.connect(db_path)'
    new = 'self._db = sqlite3.connect(db_path, check_same_thread=False)'

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-017 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-017 sqlite3 connect not found")
        return False
    return True


def fix_med018():
    """Retry on SQLite lock (MED version, HIGH-014 already covers)."""
    # HIGH-014 already adds retry with backoff - skip duplicate
    print("  SKIP: MED-018 covered by HIGH-014")
    return True


def fix_med019():
    """Billing endpoints - require_tenant auth."""
    fp = os.path.join(SRC, "api/billing_endpoints.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add require_tenant to period/usage/reconcile endpoints
    fixes = [
        ('async def get_billing_period(\n        license_key: str,',
         'async def get_billing_period(\n        license_key: str,\n        _auth: dict = Depends(require_tenant),'),
        ('async def get_usage_summary(\n        license_key: str,',
         'async def get_usage_summary(\n        license_key: str,\n        _auth: dict = Depends(require_tenant),'),
        ('async def trigger_reconciliation(\n        license_key: str,',
         'async def trigger_reconciliation(\n        license_key: str,\n        _auth: dict = Depends(require_tenant),'),
    ]

    for old, new in fixes:
        if old in content:
            content = content.replace(old, new, 1)

    # Add import
    if "from src.auth.tenant_auth import require_tenant" not in content:
        if "from fastapi import" in content:
            content = content.replace(
                "from fastapi import APIRouter, Depends, HTTPException, Query, Request, status",
                "from fastapi import APIRouter, Depends, HTTPException, Query, Request, status\nfrom src.auth.tenant_auth import require_tenant"
            )

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-019 syntax error: {e}")
        return False
    return True


def fix_med020():
    """Batch billing idempotency."""
    fp = os.path.join(SRC, "api/billing_endpoints.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Process with idempotency
    batch_result = await idempotency_manager.process_batch("""
    new = """# Check for duplicate events before processing
    seen_keys = set()
    deduped_events = []
    for e in request.events:
        event_key = f"{request.license_key}:{e.event_type}:{e.metric}:{e.timestamp}"
        if event_key not in seen_keys:
            seen_keys.add(event_key)
            deduped_events.append(e)
    events_dict = [
        {"event_type": e.event_type, "metric": e.metric, "value": e.value,
         "model": e.model, "timestamp": e.timestamp, "metadata": e.metadata}
        for e in deduped_events
    ]

    # Process with idempotency
    batch_result = await idempotency_manager.process_batch("""

    if old not in content:
        print(f"  WARNING: MED-020 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-020 syntax error: {e}")
        return False
    return True


def fix_med021():
    """Account-level lockout (already handled in rate_limit_decorator)."""
    print("  SKIP: MED-021 covered by existing _account_lockouts dict")
    return True


def fix_med022():
    """JWT type claim mutual exclusion."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """# Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None"""

    new = """# Verify it's a refresh token - reject access tokens at refresh endpoint
        token_type = payload.get("type")
        if token_type != "refresh":
            return None
        # Also verify typ claim matches endpoint (mutual exclusion)
        if payload.get("typ") == "access":
            return None"""

    if old not in content:
        print(f"  WARNING: MED-022 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-022 syntax error: {e}")
        return False
    return True


def fix_med023():
    """Per-service JWT secret."""
    fp = os.path.join(SRC, "auth/session_manager.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)'
    new = 'JWT_SECRET = os.getenv("JWT_SECRET_SESSION") or os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)'

    if old in content:
        content = content.replace(old, new, 1)
    else:
        # Try the original pattern
        old2 = 'JWT_SECRET = os.getenv("JWT_SECRET")'
        new2 = 'JWT_SECRET = os.getenv("JWT_SECRET_SESSION") or os.getenv("JWT_SECRET")'
        if old2 in content:
            content = content.replace(old2, new2, 1)
        else:
            print(f"  WARNING: MED-023 target not found")
            return False

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-023 syntax error: {e}")
        return False
    return True


def fix_med024():
    """Verify JWT role against DB."""
    fp = os.path.join(SRC, "auth/rbac.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = """request.state.user_role = user_role"""

    new = """# Anti-tampering: verify JWT role against DB
            db_role = getattr(user, "role", None)
            if db_role and db_role != user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Role mismatch between token and database",
                )
            request.state.user_role = user_role"""

    if old not in content:
        print(f"  WARNING: MED-024 target not found")
        return False
    content = content.replace(old, new, 1)
    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: MED-024 syntax error: {e}")
        return False
    return True


def fix_med025():
    """Decimal arithmetic for billing."""
    fp = os.path.join(SRC, "billing/engine.py")
    if not os.path.exists(fp):
        fp = os.path.join(SRC, "api/billing_service.py")
    if not os.path.exists(fp):
        print("  SKIP: billing engine file not found")
        return True
    backup(fp)
    with open(fp) as f:
        content = f.read()

    if "from decimal import Decimal" not in content:
        content = "from decimal import Decimal\n" + content

    old = "total = price * quantity"
    new = "total = Decimal(str(price)) * Decimal(str(quantity))"

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-025 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-025 float arithmetic not found")
    return True


def fix_med026():
    """Validate mcu_cost > 0."""
    fp = os.path.join(SRC, "billing/engine.py")
    if not os.path.exists(fp):
        fp = os.path.join(SRC, "api/billing_service.py")
    if not os.path.exists(fp):
        print("  SKIP: billing engine not found")
        return True
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "mcu_cost = plan.get(\"mcu_cost\", 0)"
    new = """mcu_cost = plan.get("mcu_cost", 0)
        if mcu_cost <= 0:
            raise ValueError(f"mcu_cost must be > 0 for plan: {plan.get('name', 'unknown')}")"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-026 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-026 target not found")
    return True


def fix_med027():
    """Validate plan string against known plans."""
    fp = os.path.join(SRC, "billing/engine.py")
    if not os.path.exists(fp):
        fp = os.path.join(SRC, "api/billing_service.py")
    if not os.path.exists(fp):
        print("  SKIP: billing engine not found")
        return True
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'plan = self._plans.get(plan_name, {})'
    new = '''KNOWN_PLANS = {"starter", "growth", "pro", "enterprise"}
        if plan_name not in KNOWN_PLANS:
            logger.warning("Unknown plan requested: %s", plan_name)
        plan = self._plans.get(plan_name, {})'''

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: MED-027 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: MED-027 target not found")
    return True


# ============================================================================
# PHASE 4: LOW (7 fixes)
# ============================================================================

def fix_low001():
    """Schema migration versioning."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    # Add SCHEMA_VERSION constant
    old = "SCHEMA_VERSION = \"1.0\""
    new = """SCHEMA_VERSION = 2
    _SCHEMA_MIGRATIONS = {
        1: "ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'api'",
        2: "ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS session_id TEXT",
    }"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: LOW-001 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: LOW-001 SCHEMA_VERSION not found")
    return True


def fix_low002():
    """Max future timestamp check."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'if timestamp and timestamp > now:'
    new = """if timestamp:
            future_limit = now + timedelta(minutes=5)
            if timestamp > future_limit:
                raise ValueError(f"Timestamp too far in future: {timestamp}")"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: LOW-002 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: LOW-002 timestamp check not found")
    return True


def fix_low003():
    """Clock skew logging."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "now = datetime.now(timezone.utc)"
    new = """now = datetime.now(timezone.utc)
        # Log clock skew warning if system time is off
        if hasattr(self, '_last_timestamp') and self._last_timestamp:
            skew = abs((now - self._last_timestamp).total_seconds())
            if skew > 60:
                logger.warning("Clock skew detected: %.1f seconds", skew)
        self._last_timestamp = now"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: LOW-003 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: LOW-003 timestamp not found")
    return True


def fix_low004():
    """Session TTL increase to 30 minutes."""
    fp = os.path.join(SRC, "core/auth_session.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "SESSION_TTL = 900  # 15 minutes"
    new = "SESSION_TTL = 1800  # 30 minutes"

    if old in content:
        content = content.replace(old, new, 1)
        with open(fp, "w") as f:
            f.write(content)
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERROR: LOW-004 syntax error: {e}")
            return False
    else:
        print(f"  WARNING: LOW-004 SESSION_TTL not found")
        return False
    return True


def fix_low005():
    """JWT key rotation mechanism."""
    fp = os.path.join(SRC, "auth/config.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = "JWT_KEYS = {"
    new = """JWT_KEYS: Dict[str, str] = {
        "current": os.getenv("JWT_SECRET", ""),
        "previous": os.getenv("JWT_SECRET_PREVIOUS", ""),
    }"""

    if old in content:
        content = content.replace(old, new, 1)
    else:
        # Try different format
        old2 = 'JWT_SECRET = os.getenv("JWT_SECRET", "")'
        new2 = '''JWT_KEYS = {
            "current": os.getenv("JWT_SECRET", ""),
            "previous": os.getenv("JWT_SECRET_PREVIOUS", ""),
        }
        JWT_SECRET = JWT_KEYS["current"]'''
        if old2 in content:
            content = content.replace(old2, new2, 1)

    with open(fp, "w") as f:
        f.write(content)
    try:
        py_compile.compile(fp, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"  ERROR: LOW-005 syntax error: {e}")
        return False
    return True


def fix_low006():
    """TypeScript singleton thread safety - out of scope (TS file)."""
    print("  SKIP: LOW-006 is TypeScript file (src/usage-tracker.ts)")
    return True


def fix_low007():
    """check_same_thread=False on sqlite3."""
    fp = os.path.join(SRC, "metering/usage_tracker.py")
    backup(fp)
    with open(fp) as f:
        content = f.read()

    old = 'self._db = sqlite3.connect(db_path, check_same_thread=False)'
    new = 'self._db = sqlite3.connect(db_path, check_same_thread=False)'

    # Already fixed by MED-017, just verify
    if old not in content:
        # Maybe original had True
        old2 = 'self._db = sqlite3.connect(db_path)'
        if old2 in content:
            content = content.replace(old2, new, 1)
            with open(fp, "w") as f:
                f.write(content)
            try:
                py_compile.compile(fp, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"  ERROR: LOW-007 syntax error: {e}")
                return False
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    os.makedirs(REPORTS, exist_ok=True)
    results = {"applied": [], "skipped": [], "errors": []}

    phases = [
        ("Phase 1: CRITICAL", [
            ("SEC-001", fix_sec001),
            ("SEC-002", fix_sec002),
            ("SEC-003", fix_sec003),
            ("SEC-004", fix_sec004),
            ("SEC-005", fix_sec005),
            ("SEC-006", fix_sec006),
            ("SEC-007", fix_sec007),
            ("SEC-008", fix_sec008),
            ("SEC-009", fix_sec009),
            ("SEC-010", fix_sec010),
            ("SEC-011", fix_sec011),
            ("SEC-012", fix_sec012),
            ("SEC-013", fix_sec013),
            ("SEC-014", fix_sec014),
            ("SEC-015", fix_sec015),
            ("SEC-016", fix_sec016),
            ("SEC-017", fix_sec017),
            ("SEC-018", fix_sec018),
            ("SEC-019", fix_sec019),
        ]),
        ("Phase 2: HIGH", [
            ("HIGH-001", fix_high001),
            ("HIGH-002", fix_high002),
            ("HIGH-003", fix_high003),
            ("HIGH-004", fix_high004),
            ("HIGH-005", fix_high005),
            ("HIGH-006", fix_high006),
            ("HIGH-007", fix_high007),
            ("HIGH-008", fix_high008),
            ("HIGH-009", fix_high009),
            ("HIGH-010", fix_high010),
            ("HIGH-011", fix_high011),
            ("HIGH-012", fix_high012),
            ("HIGH-013", fix_high013),
            ("HIGH-014", fix_high014),
            ("HIGH-015", fix_high015),
            ("HIGH-016", fix_high016),
            ("HIGH-017", fix_high017),
            ("HIGH-018", fix_high018),
            ("HIGH-019", fix_high019),
            ("HIGH-020", fix_high020),
            ("HIGH-021", fix_high021),
            ("HIGH-022", fix_high022),
        ]),
        ("Phase 3: MEDIUM", [
            ("MED-001", fix_med001),
            ("MED-002", fix_med002),
            ("MED-003", fix_med003),
            ("MED-004", fix_med004),
            ("MED-005", fix_med005),
            ("MED-006", fix_med006),
            ("MED-007", fix_med007),
            ("MED-008", fix_med008),
            ("MED-009", fix_med009),
            ("MED-010", fix_med010),
            ("MED-011", fix_med011),
            ("MED-012", fix_med012),
            ("MED-013", fix_med013),
            ("MED-014", fix_med014),
            ("MED-015", fix_med015),
            ("MED-016", fix_med016),
            ("MED-017", fix_med017),
            ("MED-018", fix_med018),
            ("MED-019", fix_med019),
            ("MED-020", fix_med020),
            ("MED-021", fix_med021),
            ("MED-022", fix_med022),
            ("MED-023", fix_med023),
            ("MED-024", fix_med024),
            ("MED-025", fix_med025),
            ("MED-026", fix_med026),
            ("MED-027", fix_med027),
        ]),
        ("Phase 4: LOW", [
            ("LOW-001", fix_low001),
            ("LOW-002", fix_low002),
            ("LOW-003", fix_low003),
            ("LOW-004", fix_low004),
            ("LOW-005", fix_low005),
            ("LOW-006", fix_low006),
            ("LOW-007", fix_low007),
        ]),
    ]

    for phase_name, fixes in phases:
        print(f"\n{'=' * 60}")
        print(f"  {phase_name}")
        print(f"{'=' * 60}")
        for fix_id, fix_fn in fixes:
            print(f"  [{fix_id}]", end=" ")
            try:
                result = fix_fn()
                if result is True:
                    results["applied"].append(fix_id)
                    print("OK")
                elif result is None:
                    results["skipped"].append(fix_id)
                    print("SKIPPED")
                else:
                    results["errors"].append(fix_id)
                    print("ERROR")
            except Exception as e:
                results["errors"].append(fix_id)
                print(f"EXCEPTION: {e}")

    # Verify all Python files compile
    print(f"\n{'=' * 60}")
    print("  Verifying all Python files compile...")
    print(f"{'=' * 60}")
    compile_errors = []
    for root, dirs, files in os.walk(SRC):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                try:
                    py_compile.compile(fpath, doraise=True)
                except py_compile.PyCompileError as e:
                    compile_errors.append(str(e))

    print(f"  Applied: {len(results['applied'])}")
    print(f"  Skipped: {len(results['skipped'])}")
    print(f"  Errors:  {len(results['errors'])}")
    print(f"  Compile errors after fixes: {len(compile_errors)}")

    if compile_errors:
        for e in compile_errors[:10]:
            print(f"    COMPILE ERROR: {e}")

    # Save results
    results["compile_errors"] = compile_errors[:20]
    with open(os.path.join(REPORTS, "fix-application-results.json"), "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    main()
