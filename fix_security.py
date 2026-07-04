#!/usr/bin/env python3
"""Apply security fixes to org_routes.py."""
import re

path = "/Users/macbook/mekong-cli/src/api/org_routes.py"

with open(path, "r") as f:
    content = f.read()

# Fix 1: Remove legacy admin token bypass from _extract_email_from_jwt
old1 = """ raw_token = authorization[len("Bearer "):].strip()

    # Allow legacy admin token through (returns a placeholder email)
    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")
    if legacy and raw_token == legacy:
        return "admin@legacy"
    try:
        claims = decode_jwt(raw_token, jwt_secret)"""

new1 = """ raw_token = authorization[len("Bearer "):].strip()

    # Require authenticated JWT — legacy admin token bypass removed
    try:
        claims = decode_jwt(raw_token, jwt_secret)"""

if old1 in content:
    content = content.replace(old1, new1)
    print("Fix 1 applied: _extract_email_from_jwt legacy bypass removed")
else:
    print("WARNING: Fix 1 pattern not found!")

# Fix 2: Remove legacy bypass from get_org_me — simplify to JWT-only
old2 = """ jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")

    if not jwt_secret and not legacy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth disabled — MEKONG_JWT_SECRET not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = authorization[len("Bearer "):].strip()

    # Legacy admin token bypasses org resolution restriction
    is_legacy = legacy and raw_token == legacy
    allowed_orgs: list[str] = []

    if not is_legacy:
        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWT auth disabled",
            )
        try:
            claims = decode_jwt(raw_token, jwt_secret)
        except JWTExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except JWTInvalidError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        allowed_orgs = claims.get("allowed_orgs", [])

    # Resolve org_id: from param, or auto-resolve for single-org JWTs
    resolved_org_id = org_id
    if resolved_org_id is None:
        if is_legacy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "org_id_required"},
            )
        if len(allowed_orgs) == 1:
            resolved_org_id = allowed_orgs[0]
        elif len(allowed_orgs) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "multi_org_jwt_specify_org_id"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "org_id_required"},
            )

    # Enforce org membership unless legacy token
    if not is_legacy and resolved_org_id not in allowed_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "org_not_in_allowed_orgs"},
        )"""

new2 = """ jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth disabled — MEKONG_JWT_SECRET not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = authorization[len("Bearer "):].strip()

    try:
        claims = decode_jwt(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    allowed_orgs = claims.get("allowed_orgs", [])

    # Resolve org_id: from param, or auto-resolve for single-org JWTs
    resolved_org_id = org_id
    if resolved_org_id is None:
        if len(allowed_orgs) == 1:
            resolved_org_id = allowed_orgs[0]
        elif len(allowed_orgs) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "multi_org_jwt_specify_org_id"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "org_id_required"},
            )

    # Enforce org membership
    if resolved_org_id not in allowed_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "org_not_in_allowed_orgs"},
        )"""

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied: get_org_me legacy bypass removed")
else:
    print("WARNING: Fix 2 pattern not found!")
    # Debug: find the area
    idx = content.find("jwt_secret = os.environ.get")
    if idx >= 0:
        print(f"Found jwt_secret at position {idx}")
        print(repr(content[idx:idx+100]))

with open(path, "w") as f:
    f.write(content)

print("org_routes.py written successfully")
