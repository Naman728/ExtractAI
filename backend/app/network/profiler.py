"""Build ApiEndpointProfile from classification + metadata."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.network.types import ApiEndpointProfile, CapturedRequestMeta, EndpointClassification


class ApiProfiler:
    def profile(
        self,
        meta: CapturedRequestMeta,
        classification: EndpointClassification,
        *,
        framework_hint: str | None = None,
    ) -> ApiEndpointProfile:
        parsed = urlparse(meta.url)
        params = sorted(parse_qs(parsed.query).keys())
        ct = (meta.content_type or "").lower()
        auth_required = self._auth_required(meta)
        returns_json = "json" in ct or classification.endpoint_type in {
            "rest",
            "graphql",
            "json_feed",
            "next_data",
        }
        returns_html = "html" in ct
        returns_xml = "xml" in ct or "rss" in ct or "atom" in ct or classification.endpoint_type == "xml_feed"

        value = self._estimated_value(classification, returns_json, auth_required, meta)
        pagination = any(p.lower() in {"page", "cursor", "offset", "limit", "after", "before"} for p in params)
        rate_hints = []
        for h, v in (meta.response_headers_redacted or {}).items():
            if "rate" in h.lower() or h.lower() in {"retry-after", "x-ratelimit-remaining"}:
                rate_hints.append(f"{h}:{v[:40]}")

        return ApiEndpointProfile(
            url=meta.url,
            method=meta.method.upper(),
            endpoint_type=classification.endpoint_type,
            parameters=params,
            content_type=meta.content_type,
            authentication_required=auth_required,
            returns_json=returns_json,
            returns_html=returns_html,
            returns_xml=returns_xml,
            rate_limit_indicators=rate_hints,
            pagination_support=pagination,
            estimated_value=value,
            confidence=classification.confidence,
            framework_hint=framework_hint,
            classification_evidence=classification.evidence,
            status_code=meta.status_code,
            source=meta.source,
        )

    def _auth_required(self, meta: CapturedRequestMeta) -> bool:
        if meta.status_code in {401, 403}:
            return True
        headers = {k.lower(): v for k, v in (meta.request_headers_redacted or {}).items()}
        if "authorization" in headers or "cookie" in headers:
            # Cookie alone is weak; only flag if also 401/403 or auth header present
            if "authorization" in headers:
                return True
        www = (meta.response_headers_redacted or {}).get("www-authenticate")
        return bool(www)

    def _estimated_value(
        self,
        classification: EndpointClassification,
        returns_json: bool,
        auth_required: bool,
        meta: CapturedRequestMeta,
    ) -> float:
        base = {
            "rest": 80.0,
            "graphql": 75.0,
            "json_feed": 85.0,
            "xml_feed": 70.0,
            "next_data": 88.0,
            "websocket": 40.0,
            "sse": 45.0,
            "media": 15.0,
            "static_asset": 5.0,
            "unknown": 25.0,
        }.get(classification.endpoint_type, 25.0)
        if returns_json:
            base += 5
        if auth_required:
            base -= 35
        if meta.status_code and meta.status_code >= 400:
            base -= 25
        if meta.status_code == 200:
            base += 5
        return max(0.0, min(100.0, base))
