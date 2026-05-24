import pytest
from jose import jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("my-secret-password")
    assert hashed != "my-secret-password"
    assert verify_password("my-secret-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_returns_false_for_invalid_hash():
    assert verify_password("password", "not-a-bcrypt-hash") is False


def test_create_access_token_includes_role_and_exp():
    token = create_access_token({"sub": "abc", "jti": "jti-1"}, role="student")
    payload = decode_access_token(token)
    assert payload["sub"] == "abc"
    assert payload["jti"] == "jti-1"
    assert payload["role"] == "student"
    assert "exp" in payload


def test_create_access_token_admin_role():
    token = create_access_token({"sub": "admin1"}, role="admin")
    payload = decode_access_token(token)
    assert payload["role"] == "admin"


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token({"sub": "x", "jti": "y"}, role="student")
    with pytest.raises(jwt.JWTError):
        decode_access_token(token + "tampered")
