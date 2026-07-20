"""Pipeline conductor — wires intelligence → strategy → fetch → extract → store."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# on_progress(stage, progress_pct, message, details)
ProgressFn = Callable[[str, int, str, dict[str, Any]], None]

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.normalization.engine import NormalizationEngine
from app.observability import metrics, set_job_id, span
from app.plugins.registry import PluginRegistry, get_plugin_registry
from app.scrapers.cleaner import HtmlCleaner
from app.scrapers.fetch import FetchEngineRegistry, create_fetch_registry
from app.scrapers.pagination import (
    discover_next_url,
    merge_plugin_payloads,
    merge_section_confidence,
)
from app.scrapers.site_profiles import profile_to_crawl, resolve_site_profile
from app.storage import StorageBackend, create_storage_backend
from app.strategy.engine import StrategyEngine
from app.strategy.types import ExecutionPlan
from app.utils.url import normalize_url
from app.validation.engine import ValidationEngine
from app.website_intelligence.engine import WebsiteIntelligenceEngine
from app.website_intelligence.profile import WebsiteProfile

logger = get_logger(__name__)


@dataclass
class PipelineTimings:
    intelligence_ms: float = 0.0
    strategy_ms: float = 0.0
    fetch_ms: float = 0.0
    clean_ms: float = 0.0
    plugins_ms: float = 0.0
    normalize_ms: float = 0.0
    validate_ms: float = 0.0
    persist_ms: float = 0.0
    total_ms: float = 0.0
    plugin_timings: dict[str, float] = field(default_factory=dict)


@dataclass
class PipelineResult:
    success: bool
    profile: WebsiteProfile | None
    plan: ExecutionPlan | None
    raw_html: str
    clean_html: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    validation_report: dict[str, Any]
    section_confidence: dict[str, float]
    timings: PipelineTimings
    error_code: str | None = None
    error_message: str | None = None
    raw_storage_path: str | None = None
    clean_storage_path: str | None = None
    content_hash: str | None = None
    discovery: dict[str, Any] = field(default_factory=dict)
    strategy_ranking: dict[str, Any] = field(default_factory=dict)
    pagination: dict[str, Any] = field(default_factory=dict)
    pages_fetched: int = 1


class ExtractionPipeline:
    """
    Full traditional extraction pipeline.

    Stages are replaceable via injected engines/registries.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        intelligence: WebsiteIntelligenceEngine | None = None,
        strategy: StrategyEngine | None = None,
        fetchers: FetchEngineRegistry | None = None,
        cleaner: HtmlCleaner | None = None,
        plugins: PluginRegistry | None = None,
        normalizer: NormalizationEngine | None = None,
        validator: ValidationEngine | None = None,
        storage: StorageBackend | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._intelligence = intelligence or WebsiteIntelligenceEngine(self._settings)
        self._strategy = strategy or StrategyEngine(settings=self._settings)
        self._fetchers = fetchers or create_fetch_registry(self._settings)
        self._cleaner = cleaner or HtmlCleaner()
        self._plugins = plugins or get_plugin_registry()
        self._normalizer = normalizer or NormalizationEngine()
        self._validator = validator or ValidationEngine()
        self._storage = storage or create_storage_backend(self._settings)

    @staticmethod
    def _fetch_needs_browser_retry(fetched: Any) -> bool:
        """True when static/HTTP fetch is blocked or empty and Playwright may help."""
        code = (getattr(fetched, "error_code", None) or "").upper()
        if code in {"HTTP_403", "CLOUDFLARE", "CAPTCHA", "EMPTY_PAGE", "HTTP_401"}:
            return True
        status = int(getattr(fetched, "status_code", 0) or 0)
        if status in {401, 403, 429}:
            return True
        html = (getattr(fetched, "html", None) or "").strip()
        if not html:
            return True
        lower = html.lower()
        if "access denied" in lower[:2000] or "just a moment" in lower[:2000]:
            return True
        if "cf-browser-verification" in lower or "challenge-platform" in lower:
            return True
        return False

    def run(
        self,
        url: str,
        *,
        job_id: str | None = None,
        inputs: dict[str, Any] | None = None,
        workflow: str | None = None,
        crawl: dict[str, Any] | None = None,
        on_progress: ProgressFn | None = None,
    ) -> PipelineResult:
        timings = PipelineTimings()
        total_start = time.perf_counter()
        if job_id:
            set_job_id(job_id)

        def report(stage: str, progress: int, message: str, **details: Any) -> None:
            if on_progress is None:
                return
            try:
                on_progress(stage, progress, message, details)
            except Exception as exc:  # progress reporting must never break the pipeline
                logger.warning("pipeline.progress_report_failed", error=str(exc))

        job_inputs = {
            str(k): str(v)
            for k, v in (inputs or {}).items()
            if v is not None and str(v).strip()
        }

        with span("pipeline.run", url=url):
            # 1. Intelligence
            report("intelligence", 12, "Profiling site — headers, framework & metadata")
            t0 = time.perf_counter()
            profile, _report, discovery = self._intelligence.analyze(url)
            timings.intelligence_ms = (time.perf_counter() - t0) * 1000
            _fw = (getattr(profile, "framework", None) or getattr(profile, "cms", None) or "unknown")
            report(
                "intelligence",
                22,
                f"Site profiled — {_fw} · {len(getattr(discovery, 'endpoints', []) or [])} endpoints found",
                framework=str(_fw),
            )

            # Attach job context so BrowserAgentStrategy can score itself
            if job_inputs:
                profile.diagnostics = {
                    **(profile.diagnostics or {}),
                    "job_inputs": job_inputs,
                    "workflow": workflow,
                }

            # 2. Strategy
            report("strategy", 30, "Scoring extraction strategies & choosing engine")
            t0 = time.perf_counter()
            plan, ranking, _reasoning = self._strategy.decide(profile)
            # Ensure inputs always reach the fetch engine when provided
            if job_inputs:
                plan.options = {
                    **(plan.options or {}),
                    "inputs": job_inputs,
                    "workflow": workflow or (plan.options or {}).get("workflow"),
                }
                # Prefer browser_agent when interactive inputs were supplied
                if plan.fetch_engine != "browser_agent" and job_inputs:
                    from app.strategy.strategies.browser_agent import BrowserAgentStrategy

                    agent = BrowserAgentStrategy()
                    if agent.can_handle(profile):
                        plan = agent.build_execution_plan(profile)
                        plan.options = {
                            **(plan.options or {}),
                            "inputs": job_inputs,
                            "workflow": workflow,
                        }
            timings.strategy_ms = (time.perf_counter() - t0) * 1000

            # Apply site profile + crawl overrides (force engine, scroll, etc.)
            crawl_opts = crawl if isinstance(crawl, dict) else {}
            site_profile = resolve_site_profile(url)
            profile_crawl = profile_to_crawl(
                site_profile,
                overrides={
                    k: crawl_opts.get(k)
                    for k in (
                        "follow_pagination",
                        "max_pages",
                        "force_engine",
                        "scroll_rounds",
                        "scroll_pause_ms",
                        "wait_ms",
                        "timeout_ms",
                        "browser_headers",
                    )
                    if k in crawl_opts
                },
            )
            # Explicit crawl keys win over profile defaults
            for k, v in crawl_opts.items():
                if v is not None:
                    profile_crawl[k] = v

            force_engine = profile_crawl.get("force_engine")
            if force_engine in {"requests_http", "playwright", "browser_agent"}:
                plan.fetch_engine = str(force_engine)
                if force_engine == "playwright":
                    plan.strategy_id = "dynamic_browser"
                elif force_engine == "browser_agent":
                    plan.strategy_id = "browser_agent"
                elif force_engine == "requests_http":
                    plan.strategy_id = plan.strategy_id or "static_html"

            plan.options = {
                **(plan.options or {}),
                "browser_headers": bool(profile_crawl.get("browser_headers", True)),
                "scroll_rounds": int(profile_crawl.get("scroll_rounds") or 0),
                "scroll_pause_ms": int(profile_crawl.get("scroll_pause_ms") or 500),
                "wait_ms": int(profile_crawl.get("wait_ms") or 0),
                "timeout_ms": int(
                    profile_crawl.get("timeout_ms")
                    or (plan.options or {}).get("timeout_ms")
                    or self._settings.playwright_timeout_ms
                ),
            }

            report(
                "strategy",
                38,
                f"Strategy: {plan.strategy_id} · fetch via {plan.fetch_engine}"
                + (f" · profile={site_profile.id}" if site_profile.id != "generic" else ""),
                strategy=plan.strategy_id,
                fetch_engine=plan.fetch_engine,
                site_profile=site_profile.id,
            )

            # 3. Fetch via plan.fetch_engine (registry lookup — no if/else chains)
            report("fetch", 45, f"Fetching page content via {plan.fetch_engine}…")
            t0 = time.perf_counter()
            fetcher = self._fetchers.get(plan.fetch_engine)
            fetched = fetcher.fetch(profile.final_url or url, options=plan.options)
            timings.fetch_ms = (time.perf_counter() - t0) * 1000
            metrics.observe("pipeline.fetch_ms", timings.fetch_ms, engine=fetcher.id())

            # Soft-prod cascade: static/WAF blocks → one Playwright retry (UI jobs too)
            cascade = profile_crawl.get("cascade")
            if cascade is None:
                cascade = self._settings.fetch_cascade_retry
            if (
                cascade
                and plan.fetch_engine != "playwright"
                and self._fetch_needs_browser_retry(fetched)
            ):
                report(
                    "fetch",
                    52,
                    f"Retrying with Playwright after {fetched.error_code or fetched.status_code}…",
                    prior_engine=plan.fetch_engine,
                    prior_error=fetched.error_code,
                )
                plan.fetch_engine = "playwright"
                plan.strategy_id = "dynamic_browser"
                plan.options = {
                    **(plan.options or {}),
                    "scroll_rounds": max(int((plan.options or {}).get("scroll_rounds") or 0), 3),
                    "wait_ms": max(int((plan.options or {}).get("wait_ms") or 0), 1000),
                    "timeout_ms": max(
                        int((plan.options or {}).get("timeout_ms") or 0),
                        self._settings.playwright_timeout_ms,
                    ),
                }
                t1 = time.perf_counter()
                fetcher = self._fetchers.get("playwright")
                fetched = fetcher.fetch(profile.final_url or url, options=plan.options)
                timings.fetch_ms += (time.perf_counter() - t1) * 1000
                metrics.observe("pipeline.fetch_ms", timings.fetch_ms, engine=fetcher.id())
                logger.info(
                    "pipeline.fetch_cascade_retry",
                    url=url,
                    error=fetched.error_code,
                    status=fetched.status_code,
                )

            _kb = round(len(fetched.raw_bytes or b"") / 1024, 1) if getattr(fetched, "raw_bytes", None) else round(len(fetched.html or "") / 1024, 1)
            report(
                "fetch",
                60,
                f"Fetched {_kb} KB · HTTP {getattr(fetched, 'status_code', '') or ''}".strip(),
                bytes_kb=_kb,
            )

            if fetched.error_code and not fetched.html:
                timings.total_ms = (time.perf_counter() - total_start) * 1000
                return PipelineResult(
                    success=False,
                    profile=profile,
                    plan=plan,
                    raw_html="",
                    clean_html="",
                    raw_payload={},
                    normalized_payload={},
                    validation_report={},
                    section_confidence={},
                    timings=timings,
                    error_code=fetched.error_code,
                    error_message=fetched.error_message,
                    discovery=discovery.model_dump(mode="json"),
                    strategy_ranking=ranking.model_dump(mode="json"),
                )

            # Bot protection on returned HTML
            lower = (fetched.html or "").lower()
            if "cf-browser-verification" in lower or "challenge-platform" in lower:
                if not fetched.error_code:
                    fetched.error_code = "CLOUDFLARE"
                    fetched.error_message = "Cloudflare challenge detected in content"

            # 4. Clean
            report("clean", 66, "Cleaning & de-noising HTML")
            t0 = time.perf_counter()
            clean_html = self._cleaner.clean(fetched.html)
            timings.clean_ms = (time.perf_counter() - t0) * 1000

            if not clean_html.strip() and not fetched.html.strip():
                timings.total_ms = (time.perf_counter() - total_start) * 1000
                return PipelineResult(
                    success=False,
                    profile=profile,
                    plan=plan,
                    raw_html=fetched.html,
                    clean_html=clean_html,
                    raw_payload={},
                    normalized_payload={},
                    validation_report={},
                    section_confidence={},
                    timings=timings,
                    error_code=fetched.error_code or "EMPTY_PAGE",
                    error_message=fetched.error_message or "Empty page after fetch/clean",
                    discovery=discovery.model_dump(mode="json"),
                    strategy_ranking=ranking.model_dump(mode="json"),
                )

            # 5. Plugins
            report("plugins", 72, "Running extraction plugins — links, emails, products, media…")
            t0 = time.perf_counter()
            plugin_out = self._plugins.run_all(
                url=url,
                final_url=fetched.final_url,
                html=clean_html or fetched.html,
            )
            timings.plugins_ms = (time.perf_counter() - t0) * 1000
            timings.plugin_timings = plugin_out["plugin_timings"]
            try:
                _counts = {
                    k: (len(v) if isinstance(v, (list, dict)) else (1 if v else 0))
                    for k, v in (plugin_out.get("payload") or {}).items()
                }
                _top = ", ".join(
                    f"{k}:{n}" for k, n in sorted(_counts.items(), key=lambda kv: kv[1], reverse=True)[:4] if n
                )
            except Exception:
                _top = ""
            report("plugins", 80, f"Extracted {_top}" if _top else "Extraction plugins complete", counts=_top)

            # Merge structured data from browser_agent workflows (officials, etc.)
            structured = (fetched.diagnostics or {}).get("structured") or {}
            if isinstance(structured, dict) and structured:
                if structured.get("officials"):
                    plugin_out["payload"]["officials"] = structured["officials"]
                    plugin_out["section_confidence"]["officials"] = 0.95
                plugin_out["payload"]["agent"] = {
                    "workflow": structured.get("workflow"),
                    "mode": structured.get("mode"),
                    "address_input": structured.get("address_input"),
                    "address_normalized": structured.get("address_normalized"),
                    "inputs_applied": structured.get("inputs_applied") or list(job_inputs.keys()),
                    "targets": structured.get("targets") or [],
                    "results": structured.get("results") or [],
                    "steps": (fetched.diagnostics or {}).get("steps") or [],
                    "fields_filled": structured.get("fields_filled"),
                    "body_preview": structured.get("body_preview"),
                }
                plugin_out["section_confidence"]["agent"] = 0.9

            # 5b. Follow pagination (same job, merge list sections)
            follow = profile_crawl.get("follow_pagination")
            if follow is None:
                follow = self._settings.pagination_enabled
            try:
                max_pages = int(
                    profile_crawl.get("max_pages") or self._settings.pagination_max_pages
                )
            except (TypeError, ValueError):
                max_pages = self._settings.pagination_max_pages
            max_pages = max(1, min(max_pages, 50))

            page_urls = [fetched.final_url or url]
            seen_pages: set[str] = set()
            for u in page_urls:
                try:
                    seen_pages.add(normalize_url(u))
                except Exception:
                    seen_pages.add(u.rstrip("/"))
            stopped_reason = "disabled" if not follow else "no_next"
            pages_fetched = 1

            if follow and max_pages > 1:
                page_html = clean_html or fetched.html or ""
                page_base = fetched.final_url or url
                # Subsequent pages: static fetch (avoid replaying browser-agent inputs)
                page_fetcher = self._fetchers.get("requests_http")
                page_opts = {
                    k: v
                    for k, v in (plan.options or {}).items()
                    if k not in {"inputs", "workflow"}
                }
                page_opts["browser_headers"] = True
                # Keep pagination pages lighter — no deep scroll by default
                page_opts["scroll_rounds"] = min(int(page_opts.get("scroll_rounds") or 0), 2)

                while pages_fetched < max_pages:
                    next_url = discover_next_url(page_html, page_base, seen=seen_pages)
                    if not next_url:
                        stopped_reason = "no_next"
                        break

                    report(
                        "fetch",
                        min(70, 60 + pages_fetched * 2),
                        f"Following pagination · page {pages_fetched + 1}/{max_pages}",
                        page=pages_fetched + 1,
                        url=next_url,
                    )
                    t_page = time.perf_counter()
                    page_fetched = page_fetcher.fetch(next_url, options=page_opts)
                    timings.fetch_ms += (time.perf_counter() - t_page) * 1000

                    if not page_fetched.html or page_fetched.error_code:
                        stopped_reason = "fetch_error"
                        logger.info(
                            "pagination.stopped",
                            reason=stopped_reason,
                            url=next_url,
                            error=page_fetched.error_code,
                        )
                        break

                    t_clean = time.perf_counter()
                    page_clean = self._cleaner.clean(page_fetched.html)
                    timings.clean_ms += (time.perf_counter() - t_clean) * 1000
                    page_html = page_clean or page_fetched.html
                    page_base = page_fetched.final_url or next_url

                    t_plug = time.perf_counter()
                    page_plugins = self._plugins.run_all(
                        url=next_url,
                        final_url=page_base,
                        html=page_html,
                    )
                    timings.plugins_ms += (time.perf_counter() - t_plug) * 1000
                    for name, ms in (page_plugins.get("plugin_timings") or {}).items():
                        timings.plugin_timings[name] = (
                            timings.plugin_timings.get(name, 0.0) + float(ms)
                        )

                    plugin_out["payload"] = merge_plugin_payloads(
                        plugin_out["payload"], page_plugins.get("payload") or {}
                    )
                    plugin_out["section_confidence"] = merge_section_confidence(
                        plugin_out.get("section_confidence") or {},
                        page_plugins.get("section_confidence") or {},
                    )

                    pages_fetched += 1
                    page_urls.append(page_base)
                    try:
                        seen_pages.add(normalize_url(page_base))
                    except Exception:
                        seen_pages.add(page_base.rstrip("/"))
                    stopped_reason = "max_pages" if pages_fetched >= max_pages else "no_next"

                if pages_fetched > 1:
                    report(
                        "plugins",
                        82,
                        f"Merged extraction across {pages_fetched} pages",
                        pages=pages_fetched,
                    )

            pagination_meta = {
                "enabled": bool(follow),
                "pages_crawled": pages_fetched,
                "page_urls": page_urls,
                "max_pages": max_pages,
                "stopped_reason": stopped_reason,
            }
            plugin_out["payload"]["pagination"] = pagination_meta
            plugin_out["section_confidence"]["pagination"] = 0.95 if pages_fetched > 1 else 0.5

            # 6. Normalize
            report("normalize", 86, "Mapping fields to canonical schema")
            t0 = time.perf_counter()
            normalized = self._normalizer.normalize(
                plugin_out["payload"], base_url=fetched.final_url
            )
            timings.normalize_ms = (time.perf_counter() - t0) * 1000

            # 7. Validate
            report("validate", 92, "Validating field quality & confidence")
            t0 = time.perf_counter()
            validated, validation_report = self._validator.validate(normalized)
            timings.validate_ms = (time.perf_counter() - t0) * 1000

            # 8. Store HTML artifacts
            report("persist", 97, "Storing artifacts & finalizing")
            t0 = time.perf_counter()
            raw_path = clean_path = None
            content_hash = hashlib.sha256(fetched.raw_bytes or b"").hexdigest()
            if job_id:
                raw_obj = self._storage.put_bytes(
                    f"jobs/{job_id}/raw.html",
                    (fetched.html or "").encode("utf-8", errors="replace"),
                    content_type="text/html",
                )
                clean_obj = self._storage.put_bytes(
                    f"jobs/{job_id}/clean.html",
                    clean_html.encode("utf-8", errors="replace"),
                    content_type="text/html",
                )
                raw_path, clean_path = raw_obj.path, clean_obj.path
            timings.persist_ms = (time.perf_counter() - t0) * 1000
            timings.total_ms = (time.perf_counter() - total_start) * 1000

            metrics.observe("pipeline.total_ms", timings.total_ms)
            logger.info(
                "pipeline.complete",
                job_id=job_id,
                strategy=plan.strategy_id,
                fetch=fetcher.id(),
                pages=pages_fetched,
                total_ms=round(timings.total_ms, 1),
            )

            return PipelineResult(
                success=True,
                profile=profile,
                plan=plan,
                raw_html=fetched.html,
                clean_html=clean_html,
                raw_payload=plugin_out["payload"],
                normalized_payload=validated,
                validation_report=validation_report,
                section_confidence=plugin_out["section_confidence"],
                timings=timings,
                error_code=fetched.error_code,
                error_message=fetched.error_message,
                raw_storage_path=raw_path,
                clean_storage_path=clean_path,
                content_hash=content_hash,
                discovery=discovery.model_dump(mode="json"),
                strategy_ranking=ranking.model_dump(mode="json"),
                pagination=pagination_meta,
                pages_fetched=pages_fetched,
            )
