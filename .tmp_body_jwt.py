from pathlib import Path

p = Path("src/auth/session_manager.py")
text = p.read_text(encoding="utf-8")

old = '''\
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

new = '''\
    if not JWT_SECRET:
        if _is_test_or_ci():
            JWT_SECRET = f"test-jwt-secret-{os.getpid()}"
            return JWT_SECRET
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
            "and add to your .env file."
        )
    if len(JWT_SECRET.encode()) < 32:
        raise RuntimeError(
            f"JWT_SECRET is too short: {len(JWT_SECRET.encode())} bytes. "
            "Minimum 32 bytes required for production security. "
            "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return JWT_SECRET'''

if old not in text:
    raise SystemExit("target not found")
text = text.replace(old, new, 1)
p.write_text(text, encoding="utf-8")
print("OK")
