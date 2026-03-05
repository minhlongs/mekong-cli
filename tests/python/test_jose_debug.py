#!/usr/bin/env python3
"""
Test JWT encoding/decoding with python-jose library.
Verifies JWT functionality works correctly.
"""

import pytest

# Skip if python-jose not installed
jose = pytest.importorskip("jose")


def test_jose_jwt_encode_decode():
    """Test JWT encoding and decoding with python-jose."""
    import jose.jwt

    key = "secret"
    payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}

    # Encode
    token = jose.jwt.encode(payload, key, algorithm="HS256")
    assert token is not None
    assert isinstance(token, str)

    # Decode
    decoded = jose.jwt.decode(token, key, algorithms=["HS256"])
    assert decoded is not None
    assert decoded["sub"] == "1234567890"
    assert decoded["name"] == "John Doe"


def test_jose_jwt_invalid_token():
    """Test JWT decoding with invalid token raises error."""
    import jose.jwt

    key = "secret"
    wrong_key = "wrong_secret"
    payload = {"sub": "1234567890"}

    # Encode with one key
    token = jose.jwt.encode(payload, key, algorithm="HS256")

    # Decode with wrong key should fail
    with pytest.raises(Exception):
        jose.jwt.decode(token, wrong_key, algorithms=["HS256"])


if __name__ == "__main__":
    test_jose_jwt_encode_decode()
    test_jose_jwt_invalid_token()
    print("✓ All JOSE JWT tests passed!")
