"""Redact sensitive headers before persistence."""

from __future__ import annotations

_SENSITIVE = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
}


def redact_headers(headers: dict[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    out: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE:
            out[key] = "[redacted]"
        else:
            out[key] = value[:500] if isinstance(value, str) else str(value)[:500]
    return out
