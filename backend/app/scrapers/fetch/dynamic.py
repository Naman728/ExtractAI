"""Dynamic browser fetch engine (Playwright) — used when plan says playwright."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.scrapers.fetch.base import FetchEngine, FetchResult
from app.scrapers.headers import BROWSER_USER_AGENT
from app.utils.url import assert_public_url

logger = get_logger(__name__)


class DynamicFetchEngine(FetchEngine):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def id(self) -> str:
        return "playwright"

    def fetch(self, url: str, *, options: dict[str, Any] | None = None) -> FetchResult:
        opts = options or {}
        safe = assert_public_url(url)
        timeout_ms = int(opts.get("timeout_ms", self._settings.playwright_timeout_ms))
        scroll_rounds = int(opts.get("scroll_rounds") or 0)
        scroll_pause_ms = int(opts.get("scroll_pause_ms") or 500)
        wait_ms = int(opts.get("wait_ms") or 0)
        user_agent = str(opts.get("user_agent") or BROWSER_USER_AGENT)
        start = time.perf_counter()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return FetchResult(
                url=safe,
                final_url=safe,
                status_code=0,
                html="",
                raw_bytes=b"",
                elapsed_ms=(time.perf_counter() - start) * 1000,
                error_code="FETCH_FAILED",
                error_message=f"Playwright not installed: {exc}",
                diagnostics={"engine": self.id()},
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=bool(opts.get("headless", True)),
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1365, "height": 900},
                    locale="en-US",
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                page = context.new_page()
                page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                page.set_default_timeout(timeout_ms)
                response = page.goto(safe, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10_000))
                except Exception:
                    pass
                if wait_ms > 0:
                    page.wait_for_timeout(wait_ms)

                for _ in range(max(0, scroll_rounds)):
                    page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.92))")
                    page.wait_for_timeout(scroll_pause_ms)
                    try:
                        page.wait_for_load_state("networkidle", timeout=scroll_pause_ms + 1500)
                    except Exception:
                        pass

                html = page.content()
                status = response.status if response else 0
                final = page.url
                browser.close()

            elapsed = (time.perf_counter() - start) * 1000
            raw = html.encode("utf-8", errors="replace")[: self._settings.max_html_bytes]
            html = raw.decode("utf-8", errors="replace")

            error_code = error_message = None
            lower = html.lower()
            if "cf-browser-verification" in lower or "challenge-platform" in lower:
                error_code, error_message = "CLOUDFLARE", "Cloudflare challenge page detected"
            elif "bot or not" in lower or "robot or human" in lower:
                error_code, error_message = "CAPTCHA", "CAPTCHA challenge detected"
            elif "captcha" in lower and ("hcaptcha" in lower or "recaptcha" in lower or "px-captcha" in lower):
                error_code, error_message = "CAPTCHA", "CAPTCHA challenge detected"
            elif status == 404:
                error_code, error_message = "HTTP_404", "Page not found"
            elif status == 403:
                error_code, error_message = "HTTP_403", "Access forbidden"
            elif not html.strip():
                error_code, error_message = "EMPTY_PAGE", "Empty document returned"

            return FetchResult(
                url=safe,
                final_url=final,
                status_code=status,
                html=html,
                raw_bytes=raw,
                elapsed_ms=elapsed,
                error_code=error_code,
                error_message=error_message,
                diagnostics={
                    "engine": self.id(),
                    "scroll_rounds": scroll_rounds,
                    "wait_ms": wait_ms,
                },
            )
        except Exception as exc:
            msg = str(exc).lower()
            code = "TIMEOUT" if "timeout" in msg else "FETCH_FAILED"
            if "ssl" in msg:
                code = "SSL_ERROR"
            logger.warning("fetch.playwright_failed", url=safe, error=str(exc))
            return FetchResult(
                url=safe,
                final_url=safe,
                status_code=0,
                html="",
                raw_bytes=b"",
                elapsed_ms=(time.perf_counter() - start) * 1000,
                error_code=code,
                error_message=str(exc),
                diagnostics={"engine": self.id()},
            )
