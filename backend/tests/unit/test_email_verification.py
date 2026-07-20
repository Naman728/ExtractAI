"""Mail / verification helpers."""

from app.services.auth_service import _hash_verify_token


def test_verify_token_hash_stable() -> None:
    a = _hash_verify_token("abc123")
    b = _hash_verify_token("abc123")
    assert a == b
    assert len(a) == 64
    assert a != _hash_verify_token("other")
