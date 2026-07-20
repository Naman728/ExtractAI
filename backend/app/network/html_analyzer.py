"""Extract API / data-source hints from HTML and inline scripts (public only)."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.network.types import CapturedRequestMeta

_FETCH_URL_RE = re.compile(
    r"""(?:fetch|axios\.(?:get|post)|XMLHttpRequest)\s*\(\s*["']([^"']+)["']""",
    re.I,
)
_JSON_URL_RE = re.compile(
    r"""["']((?:https?:)?//[^"' ]+\.json(?:\?[^"' ]*)?|/[^"' ]+\.json(?:\?[^"' ]*)?)["']""",
    re.I,
)
_API_URL_RE = re.compile(
    r"""["']((?:https?:)?//[^"' ]+/api/[^"' ]+|/api/[^"' ]+|/wp-json/[^"' ]+|[^"' ]*graphql[^"' ]*)["']""",
    re.I,
)
_WS_RE = re.compile(r"""["'](wss?://[^"' ]+)["']""", re.I)
_NEXT_BUILD_RE = re.compile(r"""/_next/data/([^/"']+)/""", re.I)


class HtmlScriptAnalyzer:
    """Find public endpoint references in page HTML / scripts — no fuzzing."""

    def analyze(self, html: str, base_url: str) -> tuple[list[CapturedRequestMeta], dict[str, list[str]]]:
        soup = BeautifulSoup(html or "", "lxml")
        metas: list[CapturedRequestMeta] = []
        signals: dict[str, list[str]] = {
            "nextjs": [],
            "nuxt": [],
            "shopify": [],
            "wordpress": [],
            "websocket": [],
            "sse": [],
            "framework": [],
        }

        # __NEXT_DATA__
        next_script = soup.find("script", id="__NEXT_DATA__")
        if next_script and next_script.string:
            signals["nextjs"].append("__NEXT_DATA__")
            signals["framework"].append("nextjs")
            try:
                payload = json.loads(next_script.string)
                build_id = payload.get("buildId")
                if build_id:
                    signals["nextjs"].append(f"buildId:{build_id}")
                    # Common Next.js data route pattern (not fetched here — just noted)
                    path = urlparse(base_url).path or "/"
                    candidate = urljoin(base_url, f"/_next/data/{build_id}{path}.json")
                    metas.append(
                        CapturedRequestMeta(
                            url=candidate,
                            method="GET",
                            content_type="application/json",
                            resource_type="next_data",
                            source="html_script",
                        )
                    )
            except (json.JSONDecodeError, TypeError):
                pass

        # Nuxt
        if "window.__NUXT__" in (html or "") or "__NUXT__" in (html or ""):
            signals["nuxt"].append("__NUXT__")
            signals["framework"].append("nuxt")

        # Shopify markers
        html_l = (html or "").lower()
        if "cdn.shopify.com" in html_l or "shopify" in html_l:
            signals["shopify"].append("shopify_marker")
            signals["framework"].append("shopify")

        if "wp-content" in html_l or "wp-includes" in html_l:
            signals["wordpress"].append("wp_assets")
            signals["framework"].append("wordpress")

        # Alternate JSON feeds
        for link in soup.find_all("link", href=True):
            typ = (link.get("type") or "").lower()
            href = link["href"]
            abs_url = urljoin(base_url, href)
            if "json" in typ or href.lower().endswith(".json"):
                metas.append(
                    CapturedRequestMeta(
                        url=abs_url,
                        method="GET",
                        content_type=typ or "application/json",
                        resource_type="json_feed",
                        source="html_script",
                    )
                )
            if "rss" in typ or "atom" in typ or "xml" in typ:
                metas.append(
                    CapturedRequestMeta(
                        url=abs_url,
                        method="GET",
                        content_type=typ or "application/xml",
                        resource_type="xml_feed",
                        source="html_script",
                    )
                )

        # Inline / external script text scan (limited size)
        script_text = " ".join(
            (s.string or "")[:20_000]
            for s in soup.find_all("script")
            if s.string
        )[:200_000]

        for pattern, resource in (
            (_FETCH_URL_RE, "fetch"),
            (_JSON_URL_RE, "json"),
            (_API_URL_RE, "api"),
        ):
            for match in pattern.finditer(script_text):
                raw = match.group(1)
                if raw.startswith("//"):
                    raw = "https:" + raw
                abs_url = urljoin(base_url, raw)
                if not abs_url.startswith("http"):
                    continue
                metas.append(
                    CapturedRequestMeta(
                        url=abs_url,
                        method="GET",
                        resource_type=resource,
                        source="html_script",
                    )
                )

        for match in _WS_RE.finditer(script_text):
            signals["websocket"].append(match.group(1))

        if "EventSource" in script_text or "text/event-stream" in script_text:
            signals["sse"].append("EventSource")

        for match in _NEXT_BUILD_RE.finditer(script_text):
            signals["nextjs"].append(f"buildId:{match.group(1)}")

        # Deduplicate by URL
        seen: set[str] = set()
        unique: list[CapturedRequestMeta] = []
        for m in metas:
            key = m.url.split("#")[0]
            if key in seen:
                continue
            seen.add(key)
            unique.append(m)

        return unique[:80], signals
