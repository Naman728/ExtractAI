"""Website Intelligence Engine — analyze a URL into WebsiteProfile + report."""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.discovery.bundle import DiscoveryBundle
from app.discovery.engine import DiscoveryEngine
from app.observability import span
from app.utils.url import assert_public_url
from app.website_intelligence.detectors import (
    detect_auth_signals,
    detect_bot_protection,
    detect_cookies,
    detect_document_meta,
    detect_downloads,
    detect_forms,
    detect_rendering,
    detect_security_headers,
    detect_social_links,
    detect_technologies,
)
from app.website_intelligence.probe import ProbeClient
from app.website_intelligence.profile import IntelligenceReport, WebsiteProfile
from app.website_intelligence.report import build_intelligence_report, estimate_complexity
from app.website_intelligence.types import ConfidentValue, DiscoveredAsset

logger = get_logger(__name__)


class WebsiteIntelligenceEngine:
    """
    Orchestrates probe → detectors → discovery → profile → report.

    Does not extract products/emails/tables. Analysis only.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        probe: ProbeClient | None = None,
        discovery: DiscoveryEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._probe = probe or ProbeClient(self._settings)
        self._discovery = discovery or DiscoveryEngine(self._probe, self._settings)

    def analyze(self, url: str) -> tuple[WebsiteProfile, IntelligenceReport, DiscoveryBundle]:
        with span("intelligence.analyze", url=url):
            normalized = assert_public_url(str(url))
            page = self._probe.fetch(normalized)

            if page.error and page.status_code == 0:
                profile = self._error_profile(normalized, page.error, page.elapsed_ms)
                report = build_intelligence_report(profile)
                empty = DiscoveryBundle(discovery_version=self._settings.discovery_version)
                return profile, report, empty

            fw, cms, techs = detect_technologies(page.text, page.headers, page.cookies)
            rendering, js_required = detect_rendering(page.text, fw.value)
            bot, cloudflare, captcha = detect_bot_protection(
                page.text, page.headers, page.status_code
            )
            auth_signals = detect_auth_signals(page.text, page.status_code, page.headers)
            cookies_present, cookie_names = detect_cookies(page.cookies)
            forms = detect_forms(page.text)
            meta = detect_document_meta(page.text, page.final_url)
            social = detect_social_links(page.text, page.final_url)
            downloads = detect_downloads(page.text, page.final_url)
            security = detect_security_headers(page.headers)

            discovery = self._discovery.discover(page)

            # Merge discovery into profile fields where stronger
            sitemap = ConfidentValue(
                value=discovery.sitemap_urls,
                confidence=0.9 if discovery.sitemap_urls else 0.6,
                evidence=discovery.sitemap_urls[:5],
            )
            rss = ConfidentValue(
                value=discovery.rss_urls,
                confidence=0.9 if discovery.rss_urls else 0.6,
                evidence=discovery.rss_urls[:5],
            )
            robots_cv = ConfidentValue(
                value=discovery.robots,
                confidence=0.95 if discovery.robots.get("available") else 0.5,
                evidence=["robots.txt"],
            )
            if discovery.favicon_url and not meta["favicon"].value:
                meta["favicon"] = ConfidentValue(
                    value=discovery.favicon_url, confidence=0.7, evidence=["discovery"]
                )
            if discovery.open_graph:
                meta["open_graph"] = ConfidentValue(
                    value=discovery.open_graph, confidence=0.95, evidence=list(discovery.open_graph)[:5]
                )
            if discovery.twitter_cards:
                meta["twitter_cards"] = ConfidentValue(
                    value=discovery.twitter_cards,
                    confidence=0.95,
                    evidence=list(discovery.twitter_cards)[:5],
                )
            if discovery.schema_org_types:
                meta["schema_org_types"] = ConfidentValue(
                    value=discovery.schema_org_types,
                    confidence=0.95,
                    evidence=discovery.schema_org_types[:10],
                )
                meta["has_json_ld"] = ConfidentValue(
                    value=True, confidence=0.98, evidence=["discovery_json_ld"]
                )

            assets = list(discovery.downloads) + [
                DiscoveredAsset(url=a.url, kind=a.kind, confidence=a.confidence)
                for a in discovery.media[:15]
            ]
            if discovery.manifest_url:
                assets.append(
                    DiscoveredAsset(url=discovery.manifest_url, kind="manifest", confidence=0.9)
                )

            complexity, cx_evidence = estimate_complexity(
                {
                    "js_required": js_required.value,
                    "cloudflare": cloudflare.value,
                    "captcha": captcha.value,
                    "auth": bool(auth_signals.value),
                    "rendering_mode": rendering.value,
                    "tech_count": len(techs.value),
                }
            )

            confidences = [
                fw.confidence,
                cms.confidence,
                rendering.confidence,
                js_required.confidence,
                bot.confidence,
                meta["has_json_ld"].confidence,
                robots_cv.confidence,
            ]
            overall = mean([c for c in confidences if c > 0] or [0.5])

            content_type = page.headers.get("content-type")
            server = page.headers.get("server")

            profile = WebsiteProfile(
                url=page.requested_url,
                final_url=page.final_url,
                normalized_url=normalized,
                profile_version=self._settings.profile_version,
                probed_at=datetime.now(UTC),
                status_code=ConfidentValue(
                    value=page.status_code, confidence=1.0, evidence=["http_probe"]
                ),
                content_type=ConfidentValue(
                    value=content_type,
                    confidence=0.95 if content_type else 0.3,
                    evidence=["content-type"] if content_type else [],
                ),
                charset=meta["charset"],
                server=ConfidentValue(
                    value=server, confidence=0.9 if server else 0.3, evidence=["server"] if server else []
                ),
                response_time_ms=ConfidentValue(
                    value=round(page.elapsed_ms, 2), confidence=0.95, evidence=["probe_timing"]
                ),
                estimated_page_size_bytes=ConfidentValue(
                    value=len(page.body), confidence=0.9, evidence=["body_len"]
                ),
                redirect_chain=ConfidentValue(
                    value=page.redirect_chain,
                    confidence=1.0,
                    evidence=[h.url for h in page.redirect_chain[:5]],
                ),
                redirect_count=ConfidentValue(
                    value=len(page.redirect_chain), confidence=1.0, evidence=["redirects"]
                ),
                framework=fw,
                cms=cms,
                rendering_mode=rendering,
                javascript_required=js_required,
                technologies=techs,
                bot_protection=bot,
                cloudflare=cloudflare,
                captcha=captcha,
                auth_required=ConfidentValue(
                    value=bool(auth_signals.value),
                    confidence=auth_signals.confidence,
                    evidence=auth_signals.evidence,
                ),
                auth_signals=auth_signals,
                cookies_present=cookies_present,
                cookie_names=cookie_names,
                language=meta["language"],
                canonical_url=meta["canonical_url"],
                favicon=meta["favicon"],
                title=meta["title"],
                has_json_ld=meta["has_json_ld"],
                schema_org_types=meta["schema_org_types"],
                open_graph=meta["open_graph"],
                twitter_cards=meta["twitter_cards"],
                robots=robots_cv,
                sitemap_urls=sitemap,
                rss_urls=rss,
                discovered_apis=ConfidentValue(
                    value=discovery.rest_candidates + discovery.json_endpoints,
                    confidence=0.6 if discovery.rest_candidates else 0.5,
                    evidence=[a.url for a in discovery.rest_candidates[:5]],
                ),
                discovered_graphql=ConfidentValue(
                    value=discovery.graphql_candidates,
                    confidence=0.55 if discovery.graphql_candidates else 0.5,
                    evidence=[g.url for g in discovery.graphql_candidates[:5]],
                ),
                discovered_assets=ConfidentValue(
                    value=assets,
                    confidence=0.8 if assets else 0.5,
                    evidence=[a.kind for a in assets[:8]],
                ),
                social_links=social,
                downloads=ConfidentValue(
                    value=list(downloads.value) + list(discovery.downloads),
                    confidence=downloads.confidence,
                    evidence=downloads.evidence,
                ),
                forms_detected=forms,
                security_headers=security,
                estimated_complexity=ConfidentValue(
                    value=complexity, confidence=0.75, evidence=cx_evidence
                ),
                overall_confidence=round(float(overall), 3),
                diagnostics={
                    "probe_error": page.error,
                    "discovery": discovery.diagnostics,
                    "profile_version": self._settings.profile_version,
                    "discovery_version": self._settings.discovery_version,
                },
            )

            report = build_intelligence_report(profile)
            logger.info(
                "intelligence.complete",
                url=normalized,
                framework=fw.value,
                cms=cms.value,
                strategy=report.suggested_fetch_strategy,
                confidence=profile.overall_confidence,
            )
            return profile, report, discovery

    def _error_profile(self, normalized: str, error: str, elapsed_ms: float) -> WebsiteProfile:
        empty_str = ConfidentValue(value=None, confidence=0.0, evidence=[error])
        empty_bool = ConfidentValue(value=False, confidence=0.3, evidence=[error])
        empty_list: ConfidentValue[list] = ConfidentValue(value=[], confidence=0.0, evidence=[error])
        return WebsiteProfile(
            url=normalized,
            final_url=normalized,
            normalized_url=normalized,
            profile_version=self._settings.profile_version,
            probed_at=datetime.now(UTC),
            status_code=ConfidentValue(value=0, confidence=1.0, evidence=[error]),
            content_type=empty_str,
            charset=empty_str,
            server=empty_str,
            response_time_ms=ConfidentValue(value=elapsed_ms, confidence=0.8, evidence=["timing"]),
            estimated_page_size_bytes=ConfidentValue(value=0, confidence=1.0, evidence=[]),
            redirect_chain=ConfidentValue(value=[], confidence=1.0, evidence=[]),
            redirect_count=ConfidentValue(value=0, confidence=1.0, evidence=[]),
            framework=empty_str,
            cms=empty_str,
            rendering_mode=ConfidentValue(value="unknown", confidence=0.0, evidence=[error]),
            javascript_required=empty_bool,
            technologies=empty_list,
            bot_protection=ConfidentValue(value="none", confidence=0.0, evidence=[error]),
            cloudflare=empty_bool,
            captcha=empty_bool,
            auth_required=empty_bool,
            auth_signals=empty_list,
            cookies_present=empty_bool,
            cookie_names=empty_list,
            language=empty_str,
            canonical_url=empty_str,
            favicon=empty_str,
            title=empty_str,
            has_json_ld=empty_bool,
            schema_org_types=empty_list,
            open_graph=ConfidentValue(value={}, confidence=0.0, evidence=[]),
            twitter_cards=ConfidentValue(value={}, confidence=0.0, evidence=[]),
            robots=ConfidentValue(value={"available": False}, confidence=0.0, evidence=[]),
            sitemap_urls=empty_list,
            rss_urls=empty_list,
            discovered_apis=empty_list,
            discovered_graphql=empty_list,
            discovered_assets=empty_list,
            social_links=empty_list,
            downloads=empty_list,
            forms_detected=ConfidentValue(value=0, confidence=0.0, evidence=[]),
            security_headers=ConfidentValue(value={}, confidence=0.0, evidence=[]),
            estimated_complexity=ConfidentValue(value=0.0, confidence=0.0, evidence=[]),
            overall_confidence=0.0,
            diagnostics={"error": error},
        )
