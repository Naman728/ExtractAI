"""Classify discovered URLs into endpoint types with confidence."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.network.types import CapturedRequestMeta, EndpointClassification, EndpointType

_GRAPHQL_RE = re.compile(r"graphql|gql", re.I)
_JSON_EXT_RE = re.compile(r"\.json(\?|$)", re.I)
_XML_EXT_RE = re.compile(r"\.(xml|rss|atom)(\?|$)", re.I)
_WP_RE = re.compile(r"/wp-json(/|$)", re.I)
_NEXT_DATA_RE = re.compile(r"/_next/data/|__NEXT_DATA__|_next/static", re.I)
_SHOPIFY_RE = re.compile(
    r"(?:cdn\.shopify\.com|/products\.json|/collections\.json|/cart\.js)",
    re.I,
)
_MEDIA_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg|mp4|webm|mp3|woff2?)(\?|$)", re.I)
_ASSET_RE = re.compile(r"\.(js|css|map)(\?|$)", re.I)
_API_PATH_RE = re.compile(r"/api(/|$)|/v\d+(/|$)|/rest(/|$)", re.I)


class ApiClassifier:
    """Deterministic classifier — no fuzzing, public signals only."""

    def classify(self, meta: CapturedRequestMeta) -> EndpointClassification:
        url = meta.url
        ct = (meta.content_type or "").lower()
        evidence: list[str] = []
        endpoint_type: EndpointType = "unknown"
        confidence = 0.4

        if _GRAPHQL_RE.search(url) or "graphql" in ct:
            endpoint_type, confidence = "graphql", 0.92
            evidence.append("graphql_marker")
        elif _WP_RE.search(url):
            endpoint_type, confidence = "rest", 0.95
            evidence.append("wordpress_rest")
        elif _NEXT_DATA_RE.search(url):
            endpoint_type, confidence = "next_data", 0.93
            evidence.append("nextjs_data")
        elif _SHOPIFY_RE.search(url):
            endpoint_type, confidence = "json_feed", 0.94
            evidence.append("shopify_json")
        elif _JSON_EXT_RE.search(url) or "application/json" in ct:
            endpoint_type, confidence = "json_feed", 0.88
            evidence.append("json_content")
            if _API_PATH_RE.search(url):
                endpoint_type, confidence = "rest", 0.9
                evidence.append("api_path")
        elif _XML_EXT_RE.search(url) or "xml" in ct or "rss" in ct or "atom" in ct:
            endpoint_type, confidence = "xml_feed", 0.9
            evidence.append("xml_feed")
        elif _MEDIA_RE.search(url) or ct.startswith("image/") or ct.startswith("video/"):
            endpoint_type, confidence = "media", 0.95
            evidence.append("media")
        elif _ASSET_RE.search(url) or "javascript" in ct or ct == "text/css":
            endpoint_type, confidence = "static_asset", 0.95
            evidence.append("static_asset")
        elif _API_PATH_RE.search(url):
            endpoint_type, confidence = "rest", 0.7
            evidence.append("api_path_heuristic")
        elif meta.resource_type in {"xhr", "fetch"}:
            endpoint_type, confidence = "rest", 0.55
            evidence.append(f"resource_type:{meta.resource_type}")

        path = urlparse(url).path.lower()
        if path.endswith((".html", ".htm")) and endpoint_type == "unknown":
            endpoint_type, confidence = "unknown", 0.3
            evidence.append("html_like_path")

        return EndpointClassification(
            endpoint_type=endpoint_type,
            confidence=confidence,
            evidence=evidence,
        )
