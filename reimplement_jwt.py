"""Re-implement get_jwt_secret with CI/test fallback."""
from pathlib import Path

p = Path("src/auth/session_manager.py")
text = p.read_text(encoding="utf-8")

# Step 1: Insert _is_test_or_ci helper before get_jwt_secret
old_def = '''def get_jwt_secret() -> str:'''
new_def = '''def _is_test_or_ci() -> bool:
    """Return True if running in a CI/test context."""
    return bool(
        os.getenv("CI") == "true"
        or os.getenv("PYTEST_CURRENT_TEST")
        or os.getenv("TESTING") == "true"
    )


def get_jwt_secret() -> str:'''

if old_def not in text:
    raise SystemExit("ERROR: 'def get_jwt_secret' not found")

text = text.replace(old_def, new_def, 1)

# Step 2: Replace the old function body (original: no CI fallback)
old_body = '''    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
            "and add to your .env file."
        )
    # Enforce minimum 32-byte secret
    if len(JWT_SECRET.encode()) < 32:
        raise RuntimeError(
            f"JWT_SECRET is too short: {len(JWT_SECRET.encode())} bytes. "
            "Minimum 32 bytes required for production security. "
            "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return JWT_SECRET'''

new_body = '''    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET:
        if _is_test_or_ci():
            JWT_SECRET = f"test-jwt-secret-{os.getpid()}"
            return JWT_SECRET
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
            "and add to your .env file."
        )
    # Enforce minimum 32-byte secret
    if len(JWT_SECRET.encode()) < 32:
        raise RuntimeError(
            f"JWT_SECRET is too short: {len(JWT_SECRET.encode())} bytes. "
            "Minimum 32 bytes required for production security. "
            "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return JWT_SECRET'''

if old_body not in text:
    raise SystemExit("ERROR: old function body not found")

text = text.replace(old_body, new_body, 1)
p.write_text(text, encoding="utf-8")
print("OK")
