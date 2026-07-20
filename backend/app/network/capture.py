"""Well-known public endpoint probes — fixed allowlist, never fuzzed."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import Settings, get_settings
from app.discovery.robots import origin_of, path_allowed
from app.network.headers import redact_headers
from app.network.types import CapturedRequestMeta
from app.utils.url import assert_public_url

# Fixed convention paths only — no dictionary attacks / brute force.
_CONVENTION_PATHS: list[tuple[str, str, list[str]]] = [
    # path, expected content hint, cms/framework tags
    ("/wp-json/", "json", ["wordpress"]),
    ("/wp-json/wp/v2/posts", "json", ["wordpress"]),
    ("/wp-json/wp/v2/pages", "json", ["wordpress"]),
    ("/wp-json/wp/v2/categories", "json", ["wordpress"]),
    ("/wp-json/wp/v2/media", "json", ["wordpress"]),
    ("/products.json", "json", ["shopify"]),
    ("/collections.json", "json", ["shopify"]),
    ("/cart.js", "json", ["shopify"]),
    # removed /search/suggest.json — too ambiguous across CMS platforms
    ("/graphql", "graphql", ["graphql"]),
    ("/api/graphql", "graphql", ["graphql"]),
    ("/index.json", "json", ["json_feed"]),
    ("/feed.json", "json", ["json_feed"]),
    ("/api/v1/", "json", ["rest"]),
    ("/api/", "json", ["rest"]),
]


class ConventionProbe:
    """
    Probe a small allowlist of well-known public endpoints.

    Respects robots.txt when available. Never fuzzes or enumerates.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def probe(
        self,
        base_url: str,
        *,
        robots: dict | None = None,
        framework_hints: list[str] | None = None,
        cms_hints: list[str] | None = None,
    ) -> list[CapturedRequestMeta]:
        origin = origin_of(base_url)
        hints = {*(framework_hints or []), *(cms_hints or [])}
        hints_l = {h.lower() for h in hints}

        # Prioritize relevant conventions; still probe a minimal common set
        paths = list(_CONVENTION_PATHS)
        if "wordpress" in hints_l or "wp" in hints_l:
            paths = [p for p in paths if "wordpress" in p[2]] + [
                p for p in paths if "wordpress" not in p[2]
            ][:4]
        elif "shopify" in hints_l:
            paths = [p for p in paths if "shopify" in p[2]] + [
                p for p in paths if "shopify" not in p[2]
            ][:4]
        else:
            # Cap probes for unknown stacks to reduce load
            paths = paths[:10]

        results: list[CapturedRequestMeta] = []
        timeout = min(10, self._settings.http_timeout_seconds)

        with httpx.Client(
            headers={
                "User-Agent": (
                    "ExtractAI-Network/1.0 (+https://extractai.local; "
                    "public endpoint discovery; respectful)"
                ),
                "Accept": "application/json, application/xml, text/html;q=0.5, */*;q=0.1",
            },
            follow_redirects=True,
            timeout=timeout,
            verify=True,
        ) as client:
            for path, _hint, tags in paths:
                if robots and path_allowed(robots, path) is False:
                    continue
                url = urljoin(origin + "/", path.lstrip("/"))
                # Keep same-origin only for convention probes
                if urlparse(url).netloc != urlparse(origin).netloc:
                    continue
                try:
                    assert_public_url(url)
                except Exception:
                    continue
                try:
                    # Prefer HEAD then light GET — no body persistence
                    head = client.head(url)
                    status = head.status_code
                    ct = head.headers.get("content-type")
                    # Some servers reject HEAD — fall back to GET with small read
                    if status in {405, 501} or (status == 200 and not ct):
                        get = client.get(url)
                        status = get.status_code
                        ct = get.headers.get("content-type")
                        resp_headers = redact_headers({k.lower(): v for k, v in get.headers.items()})
                        size = len(get.content) if get.content else None
                    else:
                        resp_headers = redact_headers({k.lower(): v for k, v in head.headers.items()})
                        size = None

                    # Only record if looks like a real endpoint (not soft 404 HTML)
                    if status == 404:
                        continue
                    if status >= 500:
                        continue
                    results.append(
                        CapturedRequestMeta(
                            url=str(url),
                            method="GET",
                            status_code=status,
                            content_type=ct,
                            resource_type="convention",
                            transfer_size=size,
                            source="convention",
                            response_headers_redacted=resp_headers,
                        )
                    )
                except Exception:
                    continue

        return results
