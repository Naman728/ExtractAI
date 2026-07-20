"""Discovery Engine — find public signals before strategy selection."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.discovery.bundle import DiscoveryBundle
from app.discovery.robots import origin_of, parse_robots
from app.website_intelligence.probe import ProbeClient, ProbeResult
from app.website_intelligence.types import ApiHint, DiscoveredAsset, GraphqlHint

logger = get_logger(__name__)

_JSON_URL_RE = re.compile(
    r"""["'](https?://[^"' ]+\.json(?:\?[^"' ]*)?|/[^"' ]+\.json(?:\?[^"' ]*)?)["']""",
    re.I,
)
_API_PATH_RE = re.compile(
    r"""["']((?:https?:)?//[^"' ]+/api/[^"' ]+|/api/v\d+/[^"' ]+|/wp-json/[^"' ]+)["']""",
    re.I,
)
_GRAPHQL_RE = re.compile(r"""["']([^"' ]*graphql[^"' ]*)["']""", re.I)


class DiscoveryEngine:
    """
    Discovers public metadata, feeds, and API hints.

    Never attempts to bypass auth, CAPTCHA, or robots restrictions.
    """

    def __init__(
        self,
        probe: ProbeClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._probe = probe or ProbeClient(self._settings)

    def discover(self, page: ProbeResult) -> DiscoveryBundle:
        base = page.final_url or page.requested_url
        origin = origin_of(base)
        soup = BeautifulSoup(page.text or "", "lxml")
        diagnostics: dict[str, Any] = {}

        robots_result = self._probe.fetch_text(origin, "/robots.txt")
        robots_raw = robots_result.text if robots_result.status_code == 200 else None
        robots = parse_robots(robots_raw or "")
        diagnostics["robots_status"] = robots_result.status_code

        sitemap_urls = list(robots.get("sitemaps") or [])
        # Common locations
        for candidate in ("/sitemap.xml", "/sitemap_index.xml"):
            absolute = f"{origin}{candidate}"
            if absolute not in sitemap_urls:
                probe = self._probe.fetch(absolute, max_bytes=500_000)
                if probe.status_code == 200 and (
                    "xml" in (probe.headers.get("content-type") or "")
                    or "<urlset" in probe.text
                    or "<sitemapindex" in probe.text
                ):
                    sitemap_urls.append(absolute)
                    sitemap_urls.extend(self._extract_sitemap_locs(probe.text)[:50])

        rss_urls = self._find_feeds(soup, base)
        manifest_url = self._find_manifest(soup, base)
        favicon_url = self._find_favicon(soup, base)

        og, twitter = self._meta_maps(soup)
        json_ld, schema_types = self._json_ld(soup)

        rest, graphql, json_eps = self._api_hints(page.text or "", base, origin)
        downloads, media = self._assets(soup, base)

        return DiscoveryBundle(
            discovery_version=self._settings.discovery_version,
            robots_raw=robots_raw[:50_000] if robots_raw else None,
            robots=robots,
            sitemap_urls=list(dict.fromkeys(sitemap_urls))[:100],
            rss_urls=rss_urls,
            json_ld_blocks=json_ld[:20],
            open_graph=og,
            twitter_cards=twitter,
            schema_org_types=schema_types,
            manifest_url=manifest_url,
            favicon_url=favicon_url,
            rest_candidates=rest[:30],
            graphql_candidates=graphql[:10],
            json_endpoints=json_eps[:30],
            downloads=downloads[:40],
            media=media[:40],
            diagnostics=diagnostics,
        )

    def _extract_sitemap_locs(self, xml_text: str) -> list[str]:
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return []
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text.strip() for el in root.findall(".//sm:loc", ns) if el.text]
        if not locs:
            locs = [el.text.strip() for el in root.findall(".//{*}loc") if el.text]
        return locs

    def _find_feeds(self, soup: BeautifulSoup, base: str) -> list[str]:
        urls: list[str] = []
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel") or []).lower() if isinstance(link.get("rel"), list) else str(link.get("rel") or "").lower()
            typ = (link.get("type") or "").lower()
            if "alternate" in rel and ("rss" in typ or "atom" in typ or "xml" in typ):
                urls.append(urljoin(base, link["href"]))
        return list(dict.fromkeys(urls))[:20]

    def _find_manifest(self, soup: BeautifulSoup, base: str) -> str | None:
        link = soup.find("link", rel=lambda v: v and "manifest" in (v if isinstance(v, list) else [v]))
        if link and link.get("href"):
            return urljoin(base, link["href"])
        return None

    def _find_favicon(self, soup: BeautifulSoup, base: str) -> str | None:
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel") or []).lower() if isinstance(link.get("rel"), list) else str(link.get("rel") or "").lower()
            if "icon" in rel:
                return urljoin(base, link["href"])
        return urljoin(base, "/favicon.ico")

    def _meta_maps(self, soup: BeautifulSoup) -> tuple[dict[str, str], dict[str, str]]:
        og: dict[str, str] = {}
        tw: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            prop = tag.get("property") or ""
            name = tag.get("name") or ""
            content = tag.get("content")
            if not content:
                continue
            if prop.lower().startswith("og:"):
                og[prop] = content
            if name.lower().startswith("twitter:"):
                tw[name] = content
        return og, tw

    def _json_ld(self, soup: BeautifulSoup) -> tuple[list[Any], list[str]]:
        blocks: list[Any] = []
        types: list[str] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            blocks.append(data)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type"):
                    t = item["@type"]
                    if isinstance(t, list):
                        types.extend(str(x) for x in t)
                    else:
                        types.append(str(t))
        return blocks, list(dict.fromkeys(types))

    def _api_hints(
        self,
        html: str,
        base: str,
        origin: str,
    ) -> tuple[list[ApiHint], list[GraphqlHint], list[ApiHint]]:
        rest: list[ApiHint] = []
        graphql: list[GraphqlHint] = []
        json_eps: list[ApiHint] = []
        seen: set[str] = set()

        for match in _API_PATH_RE.finditer(html):
            raw = match.group(1)
            url = urljoin(base, raw)
            if url in seen:
                continue
            if urlparse(url).netloc and urlparse(url).netloc != urlparse(origin).netloc:
                # Only same-origin public hints by default
                continue
            seen.add(url)
            rest.append(ApiHint(url=url, source="html_script_string", confidence=0.55))

        for match in _GRAPHQL_RE.finditer(html):
            raw = match.group(1)
            if "graphql" not in raw.lower():
                continue
            url = urljoin(base, raw)
            if urlparse(url).netloc and urlparse(url).netloc != urlparse(origin).netloc:
                continue
            graphql.append(GraphqlHint(url=url, source="html_script_string", confidence=0.5))

        for match in _JSON_URL_RE.finditer(html):
            url = urljoin(base, match.group(1))
            if urlparse(url).netloc and urlparse(url).netloc != urlparse(origin).netloc:
                continue
            json_eps.append(
                ApiHint(url=url, source="html_json_url", confidence=0.5, content_type="application/json")
            )

        # WordPress REST well-known
        if "wp-content" in html or "wp-includes" in html:
            wp = f"{origin}/wp-json/"
            rest.append(ApiHint(url=wp, source="wordpress_convention", confidence=0.7))

        return rest, graphql, json_eps

    def _assets(
        self, soup: BeautifulSoup, base: str
    ) -> tuple[list[DiscoveredAsset], list[DiscoveredAsset]]:
        downloads: list[DiscoveredAsset] = []
        media: list[DiscoveredAsset] = []
        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            path = urlparse(href).path.lower()
            if any(path.endswith(ext) for ext in (".pdf", ".csv", ".xlsx", ".zip", ".doc", ".docx")):
                downloads.append(DiscoveredAsset(url=href, kind="download", confidence=0.9))
        for img in soup.find_all("img", src=True)[:30]:
            media.append(
                DiscoveredAsset(url=urljoin(base, img["src"]), kind="media", confidence=0.85)
            )
        for video in soup.find_all(["video", "source"], src=True)[:10]:
            media.append(
                DiscoveredAsset(url=urljoin(base, video["src"]), kind="media", confidence=0.85)
            )
        return downloads, media
