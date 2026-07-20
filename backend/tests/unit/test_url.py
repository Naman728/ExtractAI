"""Unit tests for URL validation / SSRF guard."""

import pytest

from app.core.exceptions import InvalidUrlError, SsrfBlockedError
from app.utils.url import assert_public_url, normalize_url


def test_normalize_https_url() -> None:
    assert normalize_url("HTTPS://Example.COM/Path?q=1#frag") == "https://example.com/Path?q=1"


def test_reject_ftp() -> None:
    with pytest.raises(InvalidUrlError):
        normalize_url("ftp://example.com/file")


def test_block_localhost() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_public_url("http://localhost/admin")


def test_block_metadata_ip() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_public_url("http://169.254.169.254/latest/meta-data")


def test_block_loopback_literal() -> None:
    with pytest.raises(SsrfBlockedError):
        assert_public_url("http://127.0.0.1/")
