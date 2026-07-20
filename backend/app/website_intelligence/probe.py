"""HTTP probe client for Website Intelligence (analysis only — no extraction)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.utils.url import assert_public_url
from app.website_intelligence.types import RedirectHop

logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "ExtractAI-Intelligence/1.0 (+https://extractai.local; research/analysis; "
        "respectful crawler)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(slots=True)
class ProbeResult:
    """Raw HTTP probe output for a single URL fetch."""

    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    cookies: dict[str, str]
    body: bytes
    text: str
    elapsed_ms: float
    redirect_chain: list[RedirectHop] = field(default_factory=list)
    error: str | None = None


class ProbeClient:
    """
    Lightweight HTTP client for intelligence probing.

    Uses httpx only — Playwright is reserved for later strategy execution.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def fetch(self, url: str, *, max_bytes: int | None = None) -> ProbeResult:
        """Fetch a URL following redirects within caps. SSRF-checked."""
        safe_url = assert_public_url(url)
        limit = max_bytes or self._settings.max_html_bytes
        timeout = self._settings.http_timeout_seconds
        max_redirects = self._settings.max_redirects

        redirect_chain: list[RedirectHop] = []
        current = safe_url
        start = time.perf_counter()

        try:
            with httpx.Client(
                headers=DEFAULT_HEADERS,
                follow_redirects=False,
                timeout=timeout,
                verify=True,
            ) as client:
                response: httpx.Response | None = None
                for _ in range(max_redirects + 1):
                    # Re-validate each hop against SSRF
                    assert_public_url(current)
                    response = client.get(current)
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            break
                        next_url = urljoin(current, location)
                        redirect_chain.append(
                            RedirectHop(url=current, status_code=response.status_code)
                        )
                        current = next_url
                        continue
                    break

                assert response is not None
                body = response.content[:limit]
                # Prefer charset from headers; fallback utf-8/replace
                text = body.decode(response.encoding or "utf-8", errors="replace")
                elapsed_ms = (time.perf_counter() - start) * 1000
                cookies = {k: v for k, v in response.cookies.items()}
                headers = {k.lower(): v for k, v in response.headers.items()}

                return ProbeResult(
                    requested_url=safe_url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    headers=headers,
                    cookies=cookies,
                    body=body,
                    text=text,
                    elapsed_ms=elapsed_ms,
                    redirect_chain=redirect_chain,
                )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.warning("probe.failed", url=safe_url, error=str(exc))
            return ProbeResult(
                requested_url=safe_url,
                final_url=safe_url,
                status_code=0,
                headers={},
                cookies={},
                body=b"",
                text="",
                elapsed_ms=elapsed_ms,
                redirect_chain=redirect_chain,
                error=str(exc),
            )

    def fetch_text(self, base_url: str, path: str) -> ProbeResult:
        """Fetch a same-origin path (robots.txt, sitemap, etc.)."""
        absolute = urljoin(base_url if base_url.endswith("/") else base_url + "/", path.lstrip("/"))
        # Prefer origin root for well-known paths
        parsed = urlparse(base_url)
        if path.startswith("/"):
            absolute = f"{parsed.scheme}://{parsed.netloc}{path}"
        return self.fetch(absolute, max_bytes=min(self._settings.max_html_bytes, 2_000_000))
