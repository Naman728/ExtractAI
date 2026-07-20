"""Enrich ExecutionPlan with HTML / REST / JSON / GraphQL source considerations."""

from __future__ import annotations

from app.strategy.types import DataSourceKind, ExecutionPlan
from app.website_intelligence.profile import WebsiteProfile


def enrich_data_sources(plan: ExecutionPlan, profile: WebsiteProfile) -> ExecutionPlan:
    """
    Mark possible execution sources from Website Intelligence hints.

    Does not switch the pipeline to API extraction — HTML remains the active path
    until Network Intelligence updates the plan after discovery.
    """
    preferred: DataSourceKind = "html"
    fallbacks: list[DataSourceKind] = ["html"]
    reasoning = [
        "Default execution source is HTML (active extraction pipeline)",
    ]

    apis = profile.discovered_apis.value or []
    graphql = profile.discovered_graphql.value or []
    feeds = profile.rss_urls.value or []

    if apis:
        fallbacks.append("rest_api")
        reasoning.append(f"Website Intelligence found {len(apis)} public API hint(s)")
        if "rest_api" not in (plan.future_alternatives or []):
            plan.future_alternatives = [*(plan.future_alternatives or []), "rest_api"]
    if any(".json" in (a.url or "").lower() for a in apis):
        if "json_feed" not in fallbacks:
            fallbacks.append("json_feed")
        reasoning.append("JSON-looking endpoints present among API hints")
    if graphql:
        fallbacks.append("graphql")
        reasoning.append(f"GraphQL hint(s) present ({len(graphql)}) — ranking only")
        if "graphql" not in (plan.future_alternatives or []):
            plan.future_alternatives = [*(plan.future_alternatives or []), "graphql"]
    if feeds:
        if "xml_feed" not in fallbacks:
            fallbacks.append("xml_feed")
        reasoning.append(f"{len(feeds)} RSS/Atom feed(s) discovered")

    # De-dupe preserve order
    fallbacks = list(dict.fromkeys(fallbacks))

    plan.preferred_data_source = preferred
    plan.fallback_sources = fallbacks
    plan.estimated_speed = "medium" if plan.fetch_engine != "playwright" else "slow"
    plan.estimated_reliability = round(min(0.95, max(0.4, plan.confidence)), 3)
    plan.data_source_reasoning = reasoning
    plan.options = dict(plan.options or {})
    plan.options["possible_data_sources"] = fallbacks
    return plan
