"""Framework and library detection from HTML/headers/cookies."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.website_intelligence.types import ConfidentValue, TechnologyHit


@dataclass(frozen=True, slots=True)
class _Pattern:
    name: str
    category: str
    patterns: tuple[str, ...]
    confidence: float
    is_framework: bool = False
    is_cms: bool = False


# Confidence guide:
# 0.95–1.0 definitive markers (__NEXT_DATA__, wp-content generator)
# 0.80–0.94 strong markers (CDN paths, meta generators)
# 0.60–0.79 moderate heuristics (script bundles, class names)
# <0.60 weak hints only

_PATTERNS: tuple[_Pattern, ...] = (
    _Pattern("nextjs", "framework", (r"__NEXT_DATA__", r"/_next/static/", r"next-route-announcer"), 0.95, True),
    _Pattern("react", "framework", (r"data-reactroot", r"react-root", r"__REACT_DEVTOOLS"), 0.75, True),
    _Pattern("nuxt", "framework", (r"__NUXT__", r"/_nuxt/", r"data-n-head"), 0.95, True),
    _Pattern("vue", "framework", (r"data-v-[a-f0-9]{5,}", r"Vue\.version", r"__VUE__"), 0.70, True),
    _Pattern("angular", "framework", (r"ng-version", r"ng-app", r"_ngcontent-", r"angular\.js"), 0.90, True),
    _Pattern("svelte", "framework", (r"svelte-", r"__svelte"), 0.75, True),
    _Pattern("astro", "framework", (r"astro-island", r"data-astro-", r"/_astro/"), 0.92, True),
    _Pattern(
        "wordpress",
        "cms",
        (r"wp-content/", r"wp-includes/", r"name=\"generator\"[^>]*WordPress", r"/wp-json/"),
        0.95,
        is_cms=True,
    ),
    _Pattern(
        "shopify",
        "cms",
        (r"cdn\.shopify\.com", r"Shopify\.theme", r"myshopify\.com", r"shopify-section"),
        0.95,
        is_cms=True,
    ),
    _Pattern(
        "magento",
        "cms",
        (r"Magento_", r"/static/version\d+/", r"mage/cookies", r"magento"),
        0.85,
        is_cms=True,
    ),
    _Pattern("wix", "cms", (r"static\.wixstatic\.com", r"X-Wix-", r"wix\.com"), 0.93, is_cms=True),
    _Pattern(
        "squarespace",
        "cms",
        (r"squarespace\.com", r"static\.squarespace", r"squarespace-cdn"),
        0.93,
        is_cms=True,
    ),
    _Pattern(
        "webflow",
        "cms",
        (r"webflow\.com", r"wf-page", r"data-wf-", r"webflow\.js"),
        0.93,
        is_cms=True,
    ),
    _Pattern("drupal", "cms", (r"Drupal\.settings", r"/sites/default/files/", r"name=\"Generator\"[^>]*Drupal"), 0.92, is_cms=True),
    _Pattern("laravel", "server", (r"laravel_session", r"XSRF-TOKEN"), 0.80),
    _Pattern("django", "server", (r"csrfmiddlewaretoken", r"django"), 0.70),
    _Pattern("flask", "server", (r"Werkzeug", r"flask"), 0.55),
    _Pattern("rails", "server", (r"X-Runtime", r"rails", r"csrf-param"), 0.70),
    _Pattern("express", "server", (r"X-Powered-By:\s*Express", r"express"), 0.70),
)


def detect_technologies(
    html: str,
    headers: dict[str, str],
    cookies: dict[str, str],
) -> tuple[ConfidentValue[str | None], ConfidentValue[str | None], ConfidentValue[list[TechnologyHit]]]:
    """Detect frameworks, CMS, and related technologies."""
    blob = "\n".join(
        [
            html,
            "\n".join(f"{k}:{v}" for k, v in headers.items()),
            "\n".join(f"{k}={v}" for k, v in cookies.items()),
        ]
    )

    hits: list[TechnologyHit] = []
    framework: TechnologyHit | None = None
    cms: TechnologyHit | None = None

    for pattern in _PATTERNS:
        evidence: list[str] = []
        for rx in pattern.patterns:
            if re.search(rx, blob, re.IGNORECASE):
                evidence.append(rx)
        if not evidence:
            continue
        hit = TechnologyHit(
            name=pattern.name,
            category=pattern.category,
            confidence=min(0.99, pattern.confidence + 0.02 * (len(evidence) - 1)),
            evidence=evidence[:5],
        )
        hits.append(hit)
        if pattern.is_framework and (framework is None or hit.confidence > framework.confidence):
            # Prefer more specific frameworks (nextjs over react)
            if framework and framework.name == "react" and pattern.name in {"nextjs"}:
                framework = hit
            elif framework is None or hit.confidence >= framework.confidence:
                if not (framework and framework.name == "nextjs" and pattern.name == "react"):
                    framework = hit
        if pattern.is_cms and (cms is None or hit.confidence > cms.confidence):
            cms = hit

    # Next.js implies React
    if framework and framework.name == "nextjs":
        if not any(h.name == "react" for h in hits):
            hits.append(
                TechnologyHit(
                    name="react",
                    category="framework",
                    confidence=0.9,
                    evidence=["implied_by_nextjs"],
                )
            )

    # Header-based server
    powered = headers.get("x-powered-by") or headers.get("server")
    if powered:
        hits.append(
            TechnologyHit(
                name=powered.split("/")[0].strip().lower()[:64],
                category="server",
                confidence=0.85,
                evidence=[f"header:{powered[:120]}"],
            )
        )

    fw_value = ConfidentValue(
        value=framework.name if framework else None,
        confidence=framework.confidence if framework else 0.0,
        evidence=framework.evidence if framework else [],
    )
    cms_value = ConfidentValue(
        value=cms.name if cms else None,
        confidence=cms.confidence if cms else 0.0,
        evidence=cms.evidence if cms else [],
    )
    tech_value = ConfidentValue(
        value=hits,
        confidence=max((h.confidence for h in hits), default=0.0),
        evidence=[h.name for h in hits[:10]],
    )
    return fw_value, cms_value, tech_value
