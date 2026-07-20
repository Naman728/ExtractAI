"""URL validation and SSRF protection utilities."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

from app.core.constants import ALLOWED_URL_SCHEMES
from app.core.exceptions import InvalidUrlError, SsrfBlockedError


def normalize_url(url: str) -> str:
    """Normalize a URL for storage and comparison."""
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        raise InvalidUrlError(f"Unsupported URL scheme: {parsed.scheme}")
    if not parsed.netloc:
        raise InvalidUrlError("URL must include a host")

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    # Drop fragments; keep query
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_public_url(url: str) -> str:
    """
    Validate URL and block SSRF targets (private/link-local/metadata hosts).

    Returns normalized URL.
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = parsed.hostname
    if not host:
        raise InvalidUrlError("URL host is required")

    blocked_hosts = {
        "localhost",
        "metadata.google.internal",
        "metadata.google",
    }
    if host.lower() in blocked_hosts or host.lower().endswith(".localhost"):
        raise SsrfBlockedError(f"Host is not allowed: {host}")

    if host.lower() == "169.254.169.254":
        raise SsrfBlockedError("Cloud metadata endpoint is blocked")

    try:
        addr_infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise InvalidUrlError(f"Unable to resolve host: {host}") from exc

    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _is_private_ip(ip):
            raise SsrfBlockedError(f"Resolved address is not publicly routable: {ip_str}")

    return normalized
