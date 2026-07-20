"""Rank endpoints and recommend preferred data sources (discovery only)."""

from __future__ import annotations

from app.network.types import (
    ApiEndpointProfile,
    DataSourceKind,
    DataSourceRecommendation,
)


class DataSourceRanker:
    """Convert profiled endpoints into an execution-source recommendation."""

    _USEFUL_TYPES = {"rest", "graphql", "json_feed", "xml_feed", "next_data"}

    def recommend(
        self,
        endpoints: list[ApiEndpointProfile],
        *,
        html_baseline_reliability: float = 0.75,
    ) -> DataSourceRecommendation:
        useful = [
            e
            for e in endpoints
            if e.endpoint_type in self._USEFUL_TYPES
            and not e.authentication_required
            and (e.status_code is None or e.status_code < 400)
            and e.estimated_value >= 50
        ]
        useful.sort(key=lambda e: (e.estimated_value * e.confidence), reverse=True)

        has_rest = any(e.endpoint_type in {"rest", "next_data"} for e in useful)
        has_json = any(e.endpoint_type in {"json_feed", "next_data"} for e in useful)
        has_gql = any(e.endpoint_type == "graphql" for e in useful)
        has_xml = any(e.endpoint_type == "xml_feed" for e in useful)

        reasoning: list[str] = []
        preferred: DataSourceKind = "html"
        fallbacks: list[DataSourceKind] = ["html"]
        speed = "medium"
        reliability = html_baseline_reliability

        if useful:
            top = useful[0]
            if top.endpoint_type in {"json_feed", "next_data"} and top.estimated_value >= 70:
                preferred = "json_feed"
                speed = "fast"
                reliability = min(0.95, 0.55 + top.confidence * 0.4)
                reasoning.append(
                    f"High-value JSON feed/data endpoint ranked first: {top.url}"
                )
            elif top.endpoint_type == "rest" and top.estimated_value >= 70:
                preferred = "rest_api"
                speed = "fast"
                reliability = min(0.92, 0.5 + top.confidence * 0.4)
                reasoning.append(f"Public REST endpoint preferred for speed: {top.url}")
            elif top.endpoint_type == "graphql" and top.estimated_value >= 70:
                # Prefer GraphQL as source recommendation only — extraction not implemented
                preferred = "graphql"
                speed = "fast"
                reliability = min(0.85, 0.45 + top.confidence * 0.35)
                reasoning.append(
                    f"GraphQL endpoint discovered (ranking only, no extraction): {top.url}"
                )
            else:
                reasoning.append("Useful API candidates found but HTML remains safer default")

            for kind, flag in (
                ("json_feed", has_json),
                ("rest_api", has_rest),
                ("graphql", has_gql),
                ("xml_feed", has_xml),
            ):
                if flag and kind != preferred and kind not in fallbacks:
                    fallbacks.append(kind)  # type: ignore[arg-type]
            if "html" not in fallbacks:
                fallbacks.append("html")
        else:
            reasoning.append("No high-value public APIs found — prefer HTML extraction")

        reasoning.append(
            "API/GraphQL extraction is not enabled; recommendation prepares future pipelines"
        )

        return DataSourceRecommendation(
            preferred_data_source=preferred,
            fallback_sources=fallbacks,
            estimated_speed=speed,
            estimated_reliability=round(reliability, 3),
            reasoning=reasoning,
            top_endpoints=[e.url for e in useful[:5]],
        )

    def partition(
        self, endpoints: list[ApiEndpointProfile]
    ) -> dict[str, list[ApiEndpointProfile]]:
        buckets: dict[str, list[ApiEndpointProfile]] = {
            "rest": [],
            "graphql": [],
            "json_feed": [],
            "xml_feed": [],
            "xhr": [],
            "all": endpoints,
        }
        for e in endpoints:
            if e.endpoint_type == "rest" or e.endpoint_type == "next_data":
                buckets["rest"].append(e)
            if e.endpoint_type == "graphql":
                buckets["graphql"].append(e)
            if e.endpoint_type in {"json_feed", "next_data"}:
                buckets["json_feed"].append(e)
            if e.endpoint_type == "xml_feed":
                buckets["xml_feed"].append(e)
            if e.source == "playwright" and e.endpoint_type not in {
                "media",
                "static_asset",
            }:
                buckets["xhr"].append(e)
        return buckets
