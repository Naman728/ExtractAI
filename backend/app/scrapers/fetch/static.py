"""Static HTTP fetch engine (httpx)."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.scrapers.fetch.base import FetchEngine, FetchResult
from app.scrapers.headers import BROWSER_HEADERS
from app.utils.url import assert_public_url
from app.website_intelligence.probe import DEFAULT_HEADERS

logger = get_logger(__name__)


class StaticFetchEngine(FetchEngine):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def id(self) -> str:
        return "requests_http"

    def fetch(self, url: str, *, options: dict[str, Any] | None = None) -> FetchResult:
        opts = options or {}
        safe = assert_public_url(url)
        timeout = float(opts.get("timeout", self._settings.http_timeout_seconds))
        max_bytes = int(opts.get("max_bytes", self._settings.max_html_bytes))
        max_redirects = int(opts.get("max_redirects", self._settings.max_redirects))
        use_browser = bool(opts.get("browser_headers", True))
        headers = dict(BROWSER_HEADERS if use_browser else DEFAULT_HEADERS)
        if opts.get("headers") and isinstance(opts["headers"], dict):
            headers.update({str(k): str(v) for k, v in opts["headers"].items()})
        start = time.perf_counter()

        try:
            with httpx.Client(
                headers=headers,
                follow_redirects=True,
                timeout=timeout,
                max_redirects=max_redirects,
                verify=True,
            ) as client:
                response = client.get(safe)
                body = response.content[:max_bytes]
                text = body.decode(response.encoding or "utf-8", errors="replace")
                elapsed = (time.perf_counter() - start) * 1000
                error_code = None
                error_message = None
                if response.status_code == 404:
                    error_code, error_message = "HTTP_404", "Page not found"
                elif response.status_code == 403:
                    error_code, error_message = "HTTP_403", "Access forbidden"
                elif response.status_code >= 500:
                    error_code, error_message = "HTTP_5XX", f"Server error {response.status_code}"

                return FetchResult(
                    url=safe,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    html=text,
                    raw_bytes=body,
                    headers={k.lower(): v for k, v in response.headers.items()},
                    elapsed_ms=elapsed,
                    error_code=error_code,
                    error_message=error_message,
                    diagnostics={"engine": self.id(), "redirects": len(response.history)},
                )
        except httpx.TimeoutException as exc:
            return self._error(safe, "TIMEOUT", str(exc), start)
        except httpx.HTTPError as exc:
            msg = str(exc).lower()
            code = "SSL_ERROR" if "ssl" in msg or "certificate" in msg else "FETCH_FAILED"
            return self._error(safe, code, str(exc), start)
        except Exception as exc:
            return self._error(safe, "FETCH_FAILED", str(exc), start)

    def _error(self, url: str, code: str, message: str, start: float) -> FetchResult:
        logger.warning("fetch.static_failed", url=url, code=code, error=message)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            raw_bytes=b"",
            elapsed_ms=(time.perf_counter() - start) * 1000,
            error_code=code,
            error_message=message,
            diagnostics={"engine": self.id()},
        )
