"""Network Discovery Engine — discover & rank public data sources (no extraction)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.network.capture import ConventionProbe
from app.network.classifier import ApiClassifier
from app.network.html_analyzer import HtmlScriptAnalyzer
from app.network.playwright_capture import PlaywrightNetworkCapture
from app.network.profiler import ApiProfiler
from app.network.ranker import DataSourceRanker
from app.network.types import (
    ApiEndpointProfile,
    CapturedRequestMeta,
    NetworkProfile,
)
from app.utils.url import assert_public_url
from app.website_intelligence.profile import WebsiteProfile

logger = get_logger(__name__)


class NetworkDiscoveryEngine:
    """
    Observe public network/data signals and produce a NetworkProfile.

    Does not extract entities via APIs. Does not bypass auth or robots.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._classifier = ApiClassifier()
        self._profiler = ApiProfiler()
        self._ranker = DataSourceRanker()
        self._html = HtmlScriptAnalyzer()
        self._conventions = ConventionProbe(self._settings)
        self._playwright = PlaywrightNetworkCapture(self._settings)

    def discover(
        self,
        profile: WebsiteProfile,
        *,
        website_profile_id: str,
        strategy_analysis_id: str | None = None,
        use_playwright: bool | None = None,
    ) -> NetworkProfile:
        t0 = time.perf_counter()
        timings: dict[str, float] = {}
        diagnostics: dict[str, Any] = {}

        base = profile.final_url or profile.url
        try:
            assert_public_url(base)
        except Exception as exc:
            diagnostics["url_error"] = str(exc)

        # 1) HTML / script analysis (re-fetch page lightly)
        t_html = time.perf_counter()
        html = self._fetch_html(base)
        html_metas, signals = self._html.analyze(html, base)
        timings["html_analysis_ms"] = (time.perf_counter() - t_html) * 1000

        # Seed from intelligence profile hints
        seed_metas = self._from_profile_hints(profile)

        # 2) Convention probes (allowlist)
        t_conv = time.perf_counter()
        framework = profile.framework.value
        cms = profile.cms.value
        fw_hints = [framework] if framework else []
        cms_hints = [cms] if cms else []
        for tag in signals.get("framework", []):
            fw_hints.append(tag)
        robots = profile.robots.value if isinstance(profile.robots.value, dict) else None
        convention_metas = self._conventions.probe(
            base,
            robots=robots,
            framework_hints=fw_hints,
            cms_hints=cms_hints,
        )
        timings["convention_probe_ms"] = (time.perf_counter() - t_conv) * 1000

        # 3) Optional Playwright capture
        should_pw = use_playwright
        if should_pw is None:
            should_pw = bool(
                profile.javascript_required.value
                or (profile.rendering_mode.value or "") in {"csr_heavy", "hybrid"}
            )
        pw_metas: list[CapturedRequestMeta] = []
        if should_pw and getattr(self._settings, "network_playwright_capture", True):
            t_pw = time.perf_counter()
            pw_metas = self._playwright.capture(base)
            timings["playwright_capture_ms"] = (time.perf_counter() - t_pw) * 1000
            diagnostics["playwright_used"] = True
        else:
            diagnostics["playwright_used"] = False

        all_metas = self._dedupe_metas(seed_metas + html_metas + convention_metas + pw_metas)
        diagnostics["raw_candidates"] = len(all_metas)

        # 4) Classify + profile
        t_cls = time.perf_counter()
        endpoints: list[ApiEndpointProfile] = []
        rejected = 0
        for meta in all_metas:
            classification = self._classifier.classify(meta)
            if classification.endpoint_type in {"media", "static_asset"}:
                # Keep low-value for filtering UI but mark rejected for metrics
                rejected += 1
            fw_hint = self._framework_for(meta.url, signals, framework, cms)
            endpoints.append(self._profiler.profile(meta, classification, framework_hint=fw_hint))
        timings["classification_ms"] = (time.perf_counter() - t_cls) * 1000

        endpoints.sort(key=lambda e: e.estimated_value * e.confidence, reverse=True)

        # 5) Rank / recommend
        recommendation = self._ranker.recommend(
            endpoints,
            html_baseline_reliability=float(profile.overall_confidence or 0.7),
        )
        buckets = self._ranker.partition(endpoints)
        useful = [
            e
            for e in endpoints
            if e.endpoint_type in DataSourceRanker._USEFUL_TYPES
            and not e.authentication_required
            and e.estimated_value >= 50
        ]

        timings["discovery_total_ms"] = (time.perf_counter() - t0) * 1000
        diagnostics["endpoints_found"] = len(endpoints)
        diagnostics["useful_endpoints"] = len(useful)
        diagnostics["rejected_endpoints"] = rejected

        return NetworkProfile(
            website_profile_id=website_profile_id,
            strategy_analysis_id=strategy_analysis_id,
            final_url=base,
            discovered_at=datetime.now(UTC),
            discovery_version=getattr(self._settings, "network_version", "1.0.0"),
            endpoints=endpoints[:100],
            rest_endpoints=buckets["rest"][:40],
            graphql_endpoints=buckets["graphql"][:20],
            json_feeds=buckets["json_feed"][:40],
            xml_feeds=buckets["xml_feed"][:20],
            xhr_candidates=buckets["xhr"][:40],
            nextjs_signals=list(dict.fromkeys(signals.get("nextjs", [])))[:20],
            shopify_signals=list(dict.fromkeys(signals.get("shopify", [])))[:20],
            wordpress_signals=list(dict.fromkeys(signals.get("wordpress", [])))[:20],
            websocket_detected=bool(signals.get("websocket")),
            sse_detected=bool(signals.get("sse")),
            recommendation=recommendation,
            timings={k: round(v, 2) for k, v in timings.items()},
            diagnostics=diagnostics,
            captured_request_count=len(all_metas),
        )

    def _fetch_html(self, url: str) -> str:
        try:
            safe = assert_public_url(url)
            with httpx.Client(
                headers={
                    "User-Agent": "ExtractAI-Network/1.0 (+https://extractai.local)",
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
                timeout=self._settings.http_timeout_seconds,
                verify=True,
            ) as client:
                resp = client.get(safe)
                return resp.text[: self._settings.max_html_bytes]
        except Exception as exc:
            logger.warning("network.html_fetch_failed", error=str(exc))
            return ""

    def _from_profile_hints(self, profile: WebsiteProfile) -> list[CapturedRequestMeta]:
        metas: list[CapturedRequestMeta] = []
        for hint in profile.discovered_apis.value or []:
            metas.append(
                CapturedRequestMeta(
                    url=hint.url,
                    method=getattr(hint, "method", "GET") or "GET",
                    content_type=getattr(hint, "content_type", None),
                    source="probe",
                    resource_type="api",
                )
            )
        for hint in profile.discovered_graphql.value or []:
            metas.append(
                CapturedRequestMeta(
                    url=hint.url,
                    method="POST",
                    content_type="application/json",
                    source="probe",
                    resource_type="graphql",
                )
            )
        for feed in profile.rss_urls.value or []:
            metas.append(
                CapturedRequestMeta(
                    url=feed,
                    method="GET",
                    content_type="application/rss+xml",
                    source="probe",
                    resource_type="xml_feed",
                )
            )
        return metas

    def _dedupe_metas(self, metas: list[CapturedRequestMeta]) -> list[CapturedRequestMeta]:
        seen: set[str] = set()
        out: list[CapturedRequestMeta] = []
        for m in metas:
            key = f"{m.method.upper()}:{m.url.split('#')[0]}"
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
        return out

    def _framework_for(
        self,
        url: str,
        signals: dict[str, list[str]],
        framework: str | None,
        cms: str | None,
    ) -> str | None:
        path = urlparse(url).path.lower()
        if "wp-json" in path or signals.get("wordpress"):
            return "wordpress"
        if "products.json" in path or "collections.json" in path or signals.get("shopify"):
            return "shopify"
        if "/_next/data" in path or signals.get("nextjs"):
            return "nextjs"
        if signals.get("nuxt"):
            return "nuxt"
        return framework or cms
