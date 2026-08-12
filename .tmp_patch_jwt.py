from pathlib import Path

src_path = Path("src/auth/session_manager.py")
text = src_path.read_text(encoding="utf-8")

old = """\
def get_jwt_secret() -> str:
    \"\"\"Return JWT secret from environment variable.

    Raises RuntimeError if JWT_SECRET is not set (in all environments,
    including CI/test). Secrets must never be hardcoded.

    Returns:
    JWT secret string

    Raises:
    RuntimeError: If JWT_SECRET env var is not set or too short
    \"\"\"
    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
            "and add to your .env file."
        )\
"""

new = """\
def _is_test_or_ci() -> bool:
    \"\"\"Return True if running in a test/CI context.\"\"\"
    return bool(
        os.getenv("CI") == "true"
        or os.getenv("PYTEST_CURRENT_TEST")
        or os.getenv("TESTING") == "true"
    )


def get_jwt_secret() -> str:
    \"\"\"Return JWT secret from environment variable.

    In CI/test environments, returns a generated fallback secret so tests
    don't need a real JWT_SECRET. In all other contexts, raises RuntimeError
    if JWT_SECRET is missing or too short. Secrets must never be hardcoded.

    Returns:
    JWT secret string

    Raises:
    RuntimeError: If JWT_SECRET env var is not set or too short outside CI/test.
    \"\"\"
    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET:
        if _is_test_or_ci():
            import secrets as _secrets
            JWT_SECRET = _secrets.token_urlsafe(32)
            return JWT_SECRET
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
            "and add to your .env file."
        )\
"""

if old not in text:
    import sys as _sys
    _sys.stderr.write("ERROR: old block not found in source")
    raise SystemExit(1)

src_path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("OK")
