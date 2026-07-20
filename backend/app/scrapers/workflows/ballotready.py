"""BallotReady / CivicEngine — address → civic center → office holders."""

from __future__ import annotations

import re
import time
from urllib.parse import urlparse

from app.core.logging import get_logger
from app.scrapers.workflows.base import BrowserWorkflow, WorkflowResult
from app.scrapers.workflows.officials import parse_officials_from_text

logger = get_logger(__name__)


class BallotReadyOfficialsWorkflow(BrowserWorkflow):
    def id(self) -> str:
        return "ballotready_officials"

    def can_handle(self, url: str, inputs: dict[str, str]) -> bool:
        if not (inputs.get("address") or "").strip():
            return False
        host = urlparse(url).netloc.lower()
        return "ballotready.org" in host or "civicengine.com" in host

    def run(
        self,
        url: str,
        inputs: dict[str, str],
        *,
        timeout_ms: int = 60_000,
    ) -> WorkflowResult:
        address = (inputs.get("address") or "").strip()
        steps: list[dict] = []
        start = time.perf_counter()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return WorkflowResult(
                success=False,
                final_url=url,
                html="",
                error_code="FETCH_FAILED",
                error_message=f"Playwright not installed: {exc}",
                steps=steps,
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1100},
                    user_agent=(
                        "Mozilla/5.0 (compatible; ExtractAI/1.0; +https://extractai.local)"
                    ),
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1200)
                steps.append({"step": "open", "ok": True, "url": page.url})

                addr = page.locator('input[name="address"]').first
                if addr.count() == 0:
                    browser.close()
                    return WorkflowResult(
                        success=False,
                        final_url=page.url,
                        html=page.content(),
                        error_code="WORKFLOW_FAILED",
                        error_message="Address input not found",
                        steps=steps,
                    )

                addr.fill(address)
                page.wait_for_timeout(1000)
                try:
                    page.locator('[role="option"], .pac-item').first.click(timeout=4000)
                    steps.append({"step": "autocomplete", "ok": True})
                except Exception:
                    steps.append({"step": "autocomplete", "ok": False})

                try:
                    with page.expect_navigation(timeout=timeout_ms, wait_until="domcontentloaded"):
                        page.locator('input[type="submit"]').first.click()
                except Exception:
                    page.locator('input[type="submit"]').first.click()
                    page.wait_for_timeout(4000)

                try:
                    page.wait_for_selector("text=Your Civic Center", timeout=45_000)
                except Exception:
                    page.wait_for_timeout(3000)
                page.wait_for_timeout(1500)
                civic_text = page.inner_text("body")
                m = re.search(r"Your address:\s*(.+?)(?:\s*\.|$)", civic_text)
                normalized = m.group(1).strip() if m else None
                steps.append(
                    {
                        "step": "civic_center",
                        "ok": True,
                        "url": page.url,
                        "address_normalized": normalized,
                    }
                )

                try:
                    page.locator('a[href="/office_holders"]').first.click(timeout=10_000)
                except Exception:
                    page.goto(
                        "https://app.ballotready.org/office_holders",
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                steps.append({"step": "office_holders_nav", "ok": True})

                try:
                    page.wait_for_selector(
                        '[data-testid="spinner"]', state="detached", timeout=90_000
                    )
                except Exception:
                    pass

                for needle in (
                    "Senator",
                    "Representative",
                    "Governor",
                    "Commissioner",
                    "Sheriff",
                    "School Board",
                ):
                    try:
                        page.wait_for_selector(f"text={needle}", timeout=10_000)
                        break
                    except Exception:
                        continue
                page.wait_for_timeout(2500)

                body = page.inner_text("body")
                if len(body.strip()) < 80:
                    page.reload(wait_until="domcontentloaded")
                    try:
                        page.wait_for_selector(
                            '[data-testid="spinner"]', state="detached", timeout=90_000
                        )
                    except Exception:
                        pass
                    page.wait_for_timeout(4000)
                    body = page.inner_text("body")

                html = page.content()
                final_url = page.url
                title = page.title()
                officials = parse_officials_from_text(body)
                browser.close()

                success = officials["total"] > 0
                steps.append(
                    {
                        "step": "extract_officials",
                        "ok": success,
                        "total": officials["total"],
                        "counts": officials["counts"],
                    }
                )
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(
                    "workflow.ballotready_officials",
                    success=success,
                    total=officials["total"],
                    ms=round(elapsed, 1),
                )
                return WorkflowResult(
                    success=success,
                    final_url=final_url,
                    html=html,
                    title=title,
                    structured={
                        "officials": officials,
                        "address_input": address,
                        "address_normalized": normalized,
                        "workflow": self.id(),
                    },
                    steps=steps,
                    error_code=None if success else "EMPTY_PAGE",
                    error_message=None if success else "No officials extracted",
                    diagnostics={"elapsed_ms": elapsed, "body_chars": len(body)},
                )
        except Exception as exc:
            logger.warning("workflow.ballotready_failed", error=str(exc))
            return WorkflowResult(
                success=False,
                final_url=url,
                html="",
                error_code="WORKFLOW_FAILED",
                error_message=str(exc)[:2000],
                steps=steps,
            )
