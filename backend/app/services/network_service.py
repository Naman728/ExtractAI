"""Network Intelligence application service."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.models.api_endpoint import ApiEndpoint
from app.models.execution_source import ExecutionSource
from app.models.network_profile import NetworkProfileRecord
from app.models.network_request import NetworkRequest
from app.network.engine import NetworkDiscoveryEngine
from app.network.types import NetworkAnalyzeResponse, NetworkProfile
from app.observability import metrics
from app.repositories.network_repository import NetworkProfileRepository
from app.repositories.strategy_repository import StrategyAnalysisRepository
from app.repositories.website_profile_repository import WebsiteProfileRepository
from app.strategy.types import ExecutionPlan
from app.website_intelligence.profile import WebsiteProfile

logger = get_logger(__name__)


class NetworkService:
    """Runs Network Discovery Engine and persists profiles / recommendations."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._profiles = WebsiteProfileRepository(session)
        self._strategies = StrategyAnalysisRepository(session)
        self._networks = NetworkProfileRepository(session)
        self._engine = NetworkDiscoveryEngine(self._settings)

    async def analyze(
        self,
        website_profile_id: str,
        strategy_analysis_id: str | None = None,
    ) -> NetworkAnalyzeResponse:
        try:
            profile_uuid = uuid.UUID(website_profile_id)
        except ValueError as exc:
            raise ValidationAppError("Invalid website_profile_id") from exc

        strategy_uuid: uuid.UUID | None = None
        if strategy_analysis_id:
            try:
                strategy_uuid = uuid.UUID(strategy_analysis_id)
            except ValueError as exc:
                raise ValidationAppError("Invalid strategy_analysis_id") from exc

        record = await self._profiles.get_by_id(profile_uuid)
        if not record:
            raise NotFoundError("Website profile not found")

        strategy_row = None
        use_playwright: bool | None = None
        if strategy_uuid:
            strategy_row = await self._strategies.get_by_id(strategy_uuid)
            if not strategy_row:
                raise NotFoundError("Strategy analysis not found")
            if strategy_row.website_profile_id != record.id:
                raise ValidationAppError("strategy_analysis_id does not match website_profile_id")
            plan = strategy_row.execution_plan or {}
            use_playwright = plan.get("fetch_engine") == "playwright"

        profile = WebsiteProfile.model_validate(record.profile)

        network_profile = await asyncio.to_thread(
            self._engine.discover,
            profile,
            website_profile_id=str(record.id),
            strategy_analysis_id=str(strategy_uuid) if strategy_uuid else None,
            use_playwright=use_playwright,
        )

        diag = network_profile.diagnostics or {}
        timings = network_profile.timings or {}

        np_row = NetworkProfileRecord(
            website_profile_id=record.id,
            strategy_analysis_id=strategy_uuid,
            final_url=network_profile.final_url,
            discovery_version=network_profile.discovery_version,
            profile=network_profile.model_dump(mode="json"),
            recommendation=network_profile.recommendation.model_dump(mode="json"),
            timings=timings,
            diagnostics=diag,
            endpoints_found=int(diag.get("endpoints_found") or len(network_profile.endpoints)),
            useful_endpoints=int(diag.get("useful_endpoints") or 0),
            rejected_endpoints=int(diag.get("rejected_endpoints") or 0),
            websocket_detected=network_profile.websocket_detected,
            sse_detected=network_profile.sse_detected,
            discovery_time_ms=float(timings.get("discovery_total_ms") or 0),
            classification_time_ms=float(timings.get("classification_ms") or 0),
        )
        np_row = await self._networks.create(np_row)

        endpoint_rows = [
            ApiEndpoint(
                network_profile_id=np_row.id,
                url=ep.url,
                method=ep.method,
                endpoint_type=ep.endpoint_type,
                content_type=ep.content_type,
                status_code=ep.status_code,
                authentication_required=ep.authentication_required,
                returns_json=ep.returns_json,
                returns_html=ep.returns_html,
                returns_xml=ep.returns_xml,
                pagination_support=ep.pagination_support,
                estimated_value=ep.estimated_value,
                confidence=ep.confidence,
                framework_hint=ep.framework_hint,
                source=ep.source,
                parameters=ep.parameters,
                rate_limit_indicators=ep.rate_limit_indicators,
                classification_evidence=ep.classification_evidence,
                profile_json=ep.model_dump(mode="json"),
            )
            for ep in network_profile.endpoints
        ]
        await self._networks.add_endpoints(endpoint_rows)

        # Persist metadata-only request stubs for playwright/convention sources
        request_rows = [
            NetworkRequest(
                job_id=None,
                network_profile_id=np_row.id,
                method=ep.method,
                url=ep.url,
                resource_type=ep.endpoint_type,
                status_code=ep.status_code,
                request_headers={},
                response_headers={},
                content_type=ep.content_type,
                is_graphql=ep.endpoint_type == "graphql",
                is_json=ep.returns_json,
                is_public_candidate=not ep.authentication_required and ep.estimated_value >= 50,
                transfer_size=None,
            )
            for ep in network_profile.endpoints
            if ep.source in {"playwright", "convention"}
        ][:100]
        if request_rows:
            await self._networks.add_requests(request_rows)

        applied = False
        if strategy_row is not None:
            applied = self._apply_to_execution_plan(strategy_row, network_profile)

        source_row = ExecutionSource(
            network_profile_id=np_row.id,
            strategy_analysis_id=strategy_uuid,
            preferred_data_source=network_profile.recommendation.preferred_data_source,
            fallback_sources=list(network_profile.recommendation.fallback_sources),
            estimated_speed=network_profile.recommendation.estimated_speed,
            estimated_reliability=network_profile.recommendation.estimated_reliability,
            reasoning=list(network_profile.recommendation.reasoning),
            top_endpoints=list(network_profile.recommendation.top_endpoints),
            is_applied_to_plan=applied,
            rank=0,
            notes="Discovery only — API/GraphQL extraction not implemented",
        )
        await self._networks.add_execution_source(source_row)

        await self._session.commit()
        await self._session.refresh(np_row)

        metrics.incr("network.analyzed")
        metrics.observe("network.endpoints_found", float(np_row.endpoints_found))
        metrics.observe("network.useful_endpoints", float(np_row.useful_endpoints))
        metrics.observe("network.discovery_time_ms", np_row.discovery_time_ms)
        metrics.observe("network.classification_time_ms", np_row.classification_time_ms)

        logger.info(
            "network.persisted",
            network_profile_id=str(np_row.id),
            website_profile_id=str(record.id),
            endpoints=np_row.endpoints_found,
            preferred=network_profile.recommendation.preferred_data_source,
        )

        return NetworkAnalyzeResponse(
            id=str(np_row.id),
            network_profile=network_profile,
            execution_recommendation=network_profile.recommendation,
            metrics={
                "discovery_time_ms": np_row.discovery_time_ms,
                "classification_time_ms": np_row.classification_time_ms,
                "endpoints_found": np_row.endpoints_found,
                "useful_endpoints": np_row.useful_endpoints,
                "rejected_endpoints": np_row.rejected_endpoints,
                "plan_updated": applied,
            },
        )

    def _apply_to_execution_plan(self, strategy_row: Any, network_profile: NetworkProfile) -> bool:
        """Merge network recommendation into stored ExecutionPlan (HTML pipeline unchanged)."""
        try:
            plan = ExecutionPlan.model_validate(strategy_row.execution_plan)
        except Exception:
            return False

        rec = network_profile.recommendation
        plan.preferred_data_source = rec.preferred_data_source
        plan.fallback_sources = list(rec.fallback_sources)
        plan.estimated_speed = rec.estimated_speed
        plan.estimated_reliability = rec.estimated_reliability
        plan.data_source_reasoning = list(rec.reasoning)

        # Surface API strategies as future alternatives without enabling extraction
        alts = list(plan.future_alternatives or [])
        for candidate in ("rest_api", "graphql", "json_feed"):
            kind_map = {"rest_api": "rest_api", "graphql": "graphql", "json_feed": "json_feed"}
            if rec.preferred_data_source == kind_map.get(candidate) or candidate.replace(
                "_api", ""
            ) in (rec.preferred_data_source,):
                if candidate not in alts:
                    alts.insert(0, candidate)
            elif any(
                s == rec.preferred_data_source or s in rec.fallback_sources
                for s in (candidate, candidate.replace("_api", ""))
            ):
                if candidate not in alts:
                    alts.append(candidate)
        # Ensure rest_api / graphql appear when those endpoints exist
        if network_profile.rest_endpoints and "rest_api" not in alts:
            alts.append("rest_api")
        if network_profile.graphql_endpoints and "graphql" not in alts:
            alts.append("graphql")
        if network_profile.json_feeds and "json_feed" not in alts:
            alts.append("json_feed")
        plan.future_alternatives = alts

        plan.options = dict(plan.options or {})
        plan.options["network_profile_considered"] = True
        plan.options["preferred_data_source"] = rec.preferred_data_source
        plan.options["top_network_endpoints"] = rec.top_endpoints[:5]

        strategy_row.execution_plan = plan.model_dump(mode="json")
        return True

    async def get_analysis(self, network_profile_id: uuid.UUID) -> NetworkAnalyzeResponse:
        row = await self._networks.get_by_id(network_profile_id)
        if not row:
            raise NotFoundError("Network profile not found")
        profile = NetworkProfile.model_validate(row.profile)
        return NetworkAnalyzeResponse(
            id=str(row.id),
            network_profile=profile,
            execution_recommendation=profile.recommendation,
            metrics={
                "discovery_time_ms": row.discovery_time_ms,
                "classification_time_ms": row.classification_time_ms,
                "endpoints_found": row.endpoints_found,
                "useful_endpoints": row.useful_endpoints,
                "rejected_endpoints": row.rejected_endpoints,
            },
        )
