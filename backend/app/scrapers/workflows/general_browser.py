"""General Browser Agent — one interactive workflow for every website.

Browserbase-style behavior:
  1. Open URL
  2. Perceive search/form fields on the page
  3. Fill user-provided inputs (query, search, address, topics, …)
  4. Submit / press Enter
  5. Capture resulting DOM for the normal extraction pipeline

No per-site Selenium scripts. BallotReady remains an optional specialized
fast-path in the workflow registry.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any
from urllib.parse import quote, urlparse

from app.core.logging import get_logger
from app.scrapers.workflows.base import BrowserWorkflow, WorkflowResult
from app.scrapers.workflows.input_normalize import (
    all_search_targets,
    normalize_agent_inputs,
    parse_list_value,
)

logger = get_logger(__name__)

_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Shared search-field selectors (site-agnostic)
_SEARCH_SELECTORS = [
    'input[type="search"]',
    'input[name="search"]',
    'input[name="q"]',
    'input[name="query"]',
    'input[id*="search" i]',
    'input[placeholder*="Search" i]',
    'input[aria-label*="Search" i]',
    'textarea[placeholder*="Search" i]',
    'input[type="text"]',
]

_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Search")',
    'button:has-text("Submit")',
    'button:has-text("Find")',
    'button:has-text("Go")',
    'button:has-text("Get started")',
    'button:has-text("Continue")',
    'button:has-text("Look up")',
    '[role="button"]:has-text("Search")',
]


class GeneralBrowserWorkflow(BrowserWorkflow):
    """Universal interactive agent used for any site when inputs are provided."""

    def id(self) -> str:
        return "general_browser"

    def can_handle(self, url: str, inputs: dict[str, str]) -> bool:
        return bool(normalize_agent_inputs(inputs))

    def run(
        self,
        url: str,
        inputs: dict[str, str],
        *,
        timeout_ms: int = 60_000,
    ) -> WorkflowResult:
        steps: list[dict[str, Any]] = []
        start = time.perf_counter()
        normalized = normalize_agent_inputs(inputs)
        targets = all_search_targets(normalized, max_items=10)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return WorkflowResult(
                success=False,
                final_url=url,
                html="",
                error_code="FETCH_FAILED",
                error_message=f"Playwright not installed: {exc}",
            )

        if not targets and not normalized:
            return WorkflowResult(
                success=False,
                final_url=url,
                html="",
                error_code="VALIDATION",
                error_message="general_browser requires non-empty inputs",
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    user_agent=_CHROME_UA,
                    locale="en-US",
                )
                page = context.new_page()

                # Fast path: Wikipedia / MediaWiki title → direct article URL or public API
                wiki_html, wiki_meta = self._try_wikipedia_direct(page, url, targets, steps, timeout_ms)
                if wiki_html:
                    browser.close()
                    return self._success(
                        url=url,
                        final_url=wiki_meta.get("final_url") or url,
                        html=wiki_html,
                        title=wiki_meta.get("title") or "",
                        body=wiki_meta.get("body") or "",
                        steps=steps,
                        start=start,
                        normalized=normalized,
                        targets=targets,
                        mode=wiki_meta.get("mode") or "wikipedia_direct",
                        collected=wiki_meta.get("collected") or [],
                    )

                # Public API fallback for Wikipedia (HTML often 403)
                api_html, api_meta = self._try_wikipedia_api(url, targets, steps)
                if api_html:
                    browser.close()
                    return self._success(
                        url=url,
                        final_url=api_meta.get("final_url") or url,
                        html=api_html,
                        title=api_meta.get("title") or "",
                        body=api_meta.get("body") or "",
                        steps=steps,
                        start=start,
                        normalized=normalized,
                        targets=targets,
                        mode="wikipedia_api",
                        collected=api_meta.get("collected") or [],
                    )

                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                self._settle(page)
                steps.append({"step": "open", "ok": True, "url": page.url})

                collected: list[dict[str, Any]] = []
                last_html = page.content()
                last_body = ""
                last_title = page.title()
                last_url = page.url

                # Multi-target: search each topic with the same general logic
                for index, target in enumerate(targets):
                    if index > 0:
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                            self._settle(page)
                        except Exception:
                            pass

                    filled = self._fill_best_field(page, normalized, target, steps)
                    if filled:
                        self._maybe_autocomplete(page, normalized, steps)
                        submitted = self._submit(page, timeout_ms, steps)
                        if not submitted:
                            # Press Enter on focused field
                            try:
                                page.keyboard.press("Enter")
                                steps.append({"step": "press_enter", "ok": True})
                                self._settle(page, wait_ms=2500)
                            except Exception as exc:
                                steps.append({"step": "press_enter", "ok": False, "error": str(exc)[:200]})
                        else:
                            self._settle(page, wait_ms=2000)

                        # If results list, try first meaningful result link
                        self._maybe_open_first_result(page, target, steps, timeout_ms)

                    html = page.content()
                    try:
                        body = page.inner_text("body")
                    except Exception:
                        body = ""
                    title = page.title()
                    final = page.url
                    collected.append(
                        {
                            "input": target,
                            "url": final,
                            "title": title,
                            "preview": (body or "")[:1500],
                            "filled": filled,
                        }
                    )
                    last_html, last_body, last_title, last_url = html, body, title, final

                    # Single-target sites: stop after first successful navigation
                    if len(targets) == 1:
                        break

                browser.close()
                success = len(last_html) > 400 and (
                    any(c.get("filled") for c in collected) or len(last_body) > 80
                )
                return self._success(
                    url=url,
                    final_url=last_url,
                    html=last_html,
                    title=last_title,
                    body=last_body,
                    steps=steps,
                    start=start,
                    normalized=normalized,
                    targets=targets,
                    mode="general_interact",
                    collected=collected,
                    success=success,
                )
        except Exception as exc:
            logger.warning("workflow.general_browser_failed", error=str(exc))
            return WorkflowResult(
                success=False,
                final_url=url,
                html="",
                error_code="WORKFLOW_FAILED",
                error_message=str(exc)[:2000],
                steps=steps,
            )

    # ── helpers ─────────────────────────────────────────────────────────

    def _success(
        self,
        *,
        url: str,
        final_url: str,
        html: str,
        title: str,
        body: str,
        steps: list[dict[str, Any]],
        start: float,
        normalized: dict[str, str],
        targets: list[str],
        mode: str,
        collected: list[dict[str, Any]],
        success: bool = True,
    ) -> WorkflowResult:
        elapsed = (time.perf_counter() - start) * 1000
        return WorkflowResult(
            success=success,
            final_url=final_url,
            html=html,
            title=title,
            structured={
                "workflow": self.id(),
                "mode": mode,
                "inputs_applied": list(normalized.keys()),
                "targets": targets,
                "results": collected,
                "body_preview": (body or "")[:2000],
            },
            steps=steps,
            error_code=None if success else "WORKFLOW_FAILED",
            error_message=None
            if success
            else "Could not interact with page using provided inputs",
            diagnostics={"elapsed_ms": elapsed, "body_chars": len(body or ""), "start_url": url},
        )

    def _settle(self, page: Any, wait_ms: int = 1500) -> None:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10_000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        try:
            page.wait_for_timeout(wait_ms)
        except Exception:
            pass

    def _try_wikipedia_direct(
        self,
        page: Any,
        url: str,
        targets: list[str],
        steps: list[dict[str, Any]],
        timeout_ms: int,
    ) -> tuple[str | None, dict[str, Any]]:
        """If host is Wikipedia, open article pages directly (no portal search)."""
        host = (urlparse(url).netloc or "").lower()
        if "wikipedia.org" not in host or not targets:
            return None, {}

        # Prefer English Wikipedia articles
        base = "https://en.wikipedia.org/wiki/"
        collected: list[dict[str, Any]] = []
        last_html = ""
        last_body = ""
        last_title = ""
        last_url = url

        for target in targets[:10]:
            slug = quote(target.replace(" ", "_"), safe="()_")
            article = f"{base}{slug}"
            try:
                page.goto(article, wait_until="domcontentloaded", timeout=timeout_ms)
                self._settle(page, wait_ms=800)
                # Soft-block detection
                html = page.content()
                if len(html) < 500 or "403" in page.title():
                    steps.append({"step": "wikipedia_direct", "ok": False, "url": article, "reason": "blocked_or_empty"})
                    continue
                body = ""
                try:
                    body = page.inner_text("body")
                except Exception:
                    pass
                title = page.title()
                collected.append(
                    {
                        "input": target,
                        "url": page.url,
                        "title": title,
                        "preview": body[:1500],
                        "filled": True,
                    }
                )
                last_html, last_body, last_title, last_url = html, body, title, page.url
                steps.append({"step": "wikipedia_direct", "ok": True, "url": page.url})
            except Exception as exc:
                steps.append({"step": "wikipedia_direct", "ok": False, "error": str(exc)[:200]})

        if not last_html:
            return None, {}
        return last_html, {
            "final_url": last_url,
            "title": last_title,
            "body": last_body,
            "collected": collected,
            "mode": "wikipedia_direct",
        }

    def _try_wikipedia_api(
        self,
        url: str,
        targets: list[str],
        steps: list[dict[str, Any]],
    ) -> tuple[str | None, dict[str, Any]]:
        """Use MediaWiki public API when HTML scraping is blocked."""
        host = (urlparse(url).netloc or "").lower()
        if "wikipedia.org" not in host or not targets:
            return None, {}

        try:
            import httpx
        except ImportError:
            return None, {}

        collected: list[dict[str, Any]] = []
        parts: list[str] = []
        last_title = ""
        last_url = "https://en.wikipedia.org/"

        for target in targets[:10]:
            try:
                with httpx.Client(timeout=20.0) as client:
                    resp = client.get(
                        "https://en.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "titles": target,
                            "prop": "extracts|info",
                            "exintro": True,
                            "explaintext": True,
                            "inprop": "url",
                            "redirects": 1,
                            "format": "json",
                        },
                        headers={"User-Agent": "ExtractAI/1.0 (website-understanding; research)"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                pages = (data.get("query") or {}).get("pages") or {}
                page = next(iter(pages.values()), {}) if pages else {}
                if not page or page.get("missing") is not None:
                    steps.append({"step": "wikipedia_api", "ok": False, "title": target})
                    continue
                title = str(page.get("title") or target)
                extract = str(page.get("extract") or "")
                fullurl = str(page.get("fullurl") or f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}")
                collected.append(
                    {
                        "input": target,
                        "url": fullurl,
                        "title": title,
                        "preview": extract[:1500],
                        "filled": True,
                    }
                )
                parts.append(f"<article data-title=\"{title}\"><h1>{title}</h1><p>{extract}</p></article>")
                last_title, last_url = title, fullurl
                steps.append({"step": "wikipedia_api", "ok": True, "title": title, "url": fullurl})
            except Exception as exc:
                steps.append({"step": "wikipedia_api", "ok": False, "error": str(exc)[:200]})

        if not parts:
            return None, {}

        html = (
            "<!DOCTYPE html><html><head><title>Wikipedia extracts</title></head><body>"
            + "\n".join(parts)
            + "</body></html>"
        )
        body = "\n\n".join(
            f"{c['title']}\n{c.get('preview') or ''}" for c in collected
        )
        return html, {
            "final_url": last_url,
            "title": last_title or "Wikipedia",
            "body": body,
            "collected": collected,
            "mode": "wikipedia_api",
        }

    def _fill_best_field(
        self,
        page: Any,
        inputs: dict[str, str],
        target: str,
        steps: list[dict[str, Any]],
    ) -> bool:
        """Fill the best matching field for this target value."""
        # 1) Key-specific selectors from provided input keys
        for key, value in inputs.items():
            if key == "topics":
                continue
            use_value = target if key in {"query", "q", "search", "topic", "keyword", "address", "addr"} else value
            selectors = self._selectors_for_key(key)
            if self._try_fill(page, selectors, use_value, key, steps):
                return True

        # 2) Generic search box with the target string
        if self._try_fill(page, _SEARCH_SELECTORS, target, "query", steps):
            return True

        # 3) First visible text input as last resort
        try:
            loc = page.locator('input[type="text"]:visible, textarea:visible').first
            if loc.count() > 0:
                loc.click(timeout=1500)
                loc.fill("")
                loc.fill(target)
                steps.append({"step": "fill", "key": "first_visible", "ok": True})
                return True
        except Exception:
            pass

        steps.append({"step": "fill", "key": "any", "ok": False, "value": target[:80]})
        return False

    def _selectors_for_key(self, key: str) -> list[str]:
        key = key.lower()
        selectors = [
            f'input[name="{key}"]',
            f'textarea[name="{key}"]',
            f'input[id*="{key}" i]',
            f'input[placeholder*="{key}" i]',
            f'input[aria-label*="{key}" i]',
            f'textarea[placeholder*="{key}" i]',
        ]
        if key in {"query", "q", "search", "topic", "keyword", "keywords", "term"}:
            selectors = _SEARCH_SELECTORS + selectors
        if key in {"address", "addr", "location"}:
            selectors = [
                'input[name="address"]',
                'input[placeholder*="Address" i]',
                'input[aria-label*="Address" i]',
                'input[autocomplete="street-address"]',
            ] + selectors
        if key in {"zip", "postal", "postcode"}:
            selectors = [
                'input[name="zip"]',
                'input[name="postal"]',
                'input[placeholder*="ZIP" i]',
                'input[placeholder*="Postal" i]',
            ] + selectors
        return selectors

    def _try_fill(
        self,
        page: Any,
        selectors: list[str],
        value: str,
        key: str,
        steps: list[dict[str, Any]],
    ) -> bool:
        for sel in selectors:
            loc = page.locator(sel).first
            try:
                if loc.count() > 0 and loc.is_visible(timeout=1200):
                    loc.click(timeout=1500)
                    loc.fill("")
                    loc.fill(str(value))
                    steps.append({"step": "fill", "key": key, "selector": sel, "ok": True})
                    return True
            except Exception:
                continue
        return False

    def _maybe_autocomplete(self, page: Any, inputs: dict[str, str], steps: list[dict[str, Any]]) -> None:
        if not any(k in inputs for k in ("address", "addr", "location")):
            return
        try:
            page.locator('[role="option"], .pac-item, .tt-suggestion').first.click(timeout=2500)
            steps.append({"step": "autocomplete", "ok": True})
        except Exception:
            steps.append({"step": "autocomplete", "ok": False})

    def _submit(self, page: Any, timeout_ms: int, steps: list[dict[str, Any]]) -> bool:
        for sel in _SUBMIT_SELECTORS:
            loc = page.locator(sel).first
            try:
                if loc.count() > 0 and loc.is_visible(timeout=1200):
                    try:
                        with page.expect_navigation(timeout=min(timeout_ms, 45_000), wait_until="domcontentloaded"):
                            loc.click()
                    except Exception:
                        loc.click()
                        page.wait_for_timeout(2000)
                    steps.append({"step": "submit", "ok": True, "selector": sel})
                    return True
            except Exception:
                continue
        steps.append({"step": "submit", "ok": False})
        return False

    def _maybe_open_first_result(
        self,
        page: Any,
        target: str,
        steps: list[dict[str, Any]],
        timeout_ms: int,
    ) -> None:
        """If still on a results list, click the best matching link."""
        try:
            # Avoid clicking nav chrome — prefer main content links containing the query
            needle = re.escape(target.split("(")[0].strip())
            if len(needle) < 3:
                return
            candidates = [
                f'main a:has-text("{target[:40]}")',
                f'#content a:has-text("{target[:40]}")',
                f'a:has-text("{target[:40]}")',
            ]
            for sel in candidates:
                loc = page.locator(sel).first
                try:
                    if loc.count() > 0 and loc.is_visible(timeout=1000):
                        href = loc.get_attribute("href") or ""
                        if href.startswith("#") or "javascript:" in href:
                            continue
                        try:
                            with page.expect_navigation(timeout=min(timeout_ms, 30_000), wait_until="domcontentloaded"):
                                loc.click()
                        except Exception:
                            loc.click()
                            page.wait_for_timeout(1500)
                        steps.append({"step": "open_result", "ok": True, "selector": sel})
                        self._settle(page, wait_ms=1000)
                        return
                except Exception:
                    continue
        except Exception as exc:
            steps.append({"step": "open_result", "ok": False, "error": str(exc)[:200]})
