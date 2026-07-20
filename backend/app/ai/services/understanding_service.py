"""Orchestrates AI Understanding after extraction."""

from __future__ import annotations

import time
from typing import Any

from app.ai.chunking import hash_normalized, select_relevant_content
from app.ai.models.website_profile import AIObservability, WebsiteUnderstanding
from app.ai.prompts import PROMPT_VERSION
from app.ai.providers.base import LLMProvider
from app.ai.providers.factory import create_llm_provider
from app.ai.providers.heuristic import HeuristicProvider
from app.ai.services.classification_service import ClassificationService
from app.ai.services.entity_service import EntityService
from app.ai.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.ai.services.schema_service import SchemaService
from app.ai.services.summary_service import SummaryService
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnderstandingService:
    """AI Understanding Engine — consumes normalized extraction only."""

    def __init__(
        self,
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
        cache: Any | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or create_llm_provider(self._settings)
        self._cache = cache
        self._classification = ClassificationService(self._provider)
        self._entities = EntityService(self._provider)
        self._summary = SummaryService(self._provider)
        self._graph = KnowledgeGraphBuilder()
        self._schema = SchemaService()

    @property
    def enabled(self) -> bool:
        return bool(self._settings.ai_understanding_enabled)

    def understand(
        self,
        normalized: dict[str, Any],
        *,
        url: str = "",
        force: bool = False,
    ) -> WebsiteUnderstanding:
        """Run full understanding pipeline on normalized extraction data."""
        if not self.enabled and not force:
            return self._schema.empty(status="skipped", reason="AI_UNDERSTANDING_ENABLED=false")

        if not normalized:
            return self._schema.empty(status="failed", reason="empty_normalized_payload")

        model_name = getattr(self._provider, "_model", None) or self._provider.name
        content_hash = hash_normalized(
            normalized,
            prompt_version=PROMPT_VERSION,
            model=str(model_name),
        )

        # Cache lookup
        if self._cache is not None and not force:
            cached = self._cache.get(content_hash)
            if cached:
                understanding = self._schema.parse(cached)
                understanding.content_hash = content_hash
                understanding.observability.cache_hit = True
                understanding.status = "completed"
                logger.info(
                    "ai.understanding.cache_hit",
                    content_hash=content_hash[:12],
                    provider=self._provider.name,
                )
                return understanding

        started = time.perf_counter()
        max_chars = int(self._settings.ai_max_input_chars)
        content = select_relevant_content(normalized, max_chars=max_chars)
        chunked = content != normalized

        try:
            # 1) Classification
            cls = self._classification.classify(content, url=url)
            category = cls["category"]

            # 2) Summary + business profile
            summary_result = self._summary.summarize(content, url=url, category=category)
            # Prefer summary category if LLM returned one with higher confidence
            if summary_result.get("category") and float(summary_result.get("category_confidence") or 0) > float(
                cls.get("category_confidence") or 0
            ):
                category = summary_result["category"]
                cat_conf = float(summary_result.get("category_confidence") or cls["category_confidence"])
            else:
                cat_conf = float(cls.get("category_confidence") or 0.5)

            # 3) Entities
            entities, entity_meta = self._entities.extract(content, url=url)

            # Merge tags
            tags = list(
                dict.fromkeys(
                    list(summary_result.get("semantic_tags") or [])
                    + list(cls.get("semantic_tags") or [])
                    + list(entities.tags or [])
                )
            )

            profile = summary_result["business_profile"]
            graph = self._graph.build(
                url=url,
                entities=entities,
                profile=profile,
                category=category.value if hasattr(category, "value") else str(category),
            )

            # Aggregate observability
            metas = [cls.get("_llm") or {}, summary_result.get("_llm") or {}, entity_meta or {}]
            latency_ms = int((time.perf_counter() - started) * 1000)
            prompt_tokens = sum(int(m.get("prompt_tokens") or 0) for m in metas)
            completion_tokens = sum(int(m.get("completion_tokens") or 0) for m in metas)
            cost = sum(float(m.get("estimated_cost_usd") or 0) for m in metas)
            model = next((m.get("model") for m in metas if m.get("model")), model_name)

            overall = (
                float(summary_result.get("overall_confidence") or 0.5) * 0.4
                + float(cat_conf) * 0.3
                + min(0.9, 0.3 + 0.02 * (len(entities.people) + len(entities.organizations) + len(entities.products)))
            )
            overall = max(0.0, min(1.0, overall))

            understanding = WebsiteUnderstanding(
                summary=str(summary_result.get("summary") or ""),
                category=category,
                category_confidence=cat_conf,
                business_profile=profile,
                entities=entities,
                knowledge_graph=graph,
                semantic_tags=tags[:24],
                overall_confidence=round(overall, 3),
                observability=AIObservability(
                    provider=self._provider.name,
                    model=str(model),
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    estimated_cost_usd=round(cost, 6),
                    prompt_version=PROMPT_VERSION,
                    cache_hit=False,
                    chunked=chunked,
                ),
                content_hash=content_hash,
                understanding_version=self._settings.understanding_version,
                status="completed",
            )

            if self._cache is not None:
                self._cache.put(content_hash, self._schema.to_storage(understanding))

            logger.info(
                "ai.understanding.completed",
                provider=self._provider.name,
                latency_ms=latency_ms,
                tokens=prompt_tokens + completion_tokens,
                cache_hit=False,
                category=category.value if hasattr(category, "value") else category,
            )
            return understanding

        except Exception as exc:
            logger.exception("ai.understanding.failed", error=str(exc))
            # Offline fallback so results still get something useful
            if not isinstance(self._provider, HeuristicProvider):
                try:
                    fallback = UnderstandingService(
                        settings=self._settings,
                        provider=HeuristicProvider(),
                        cache=None,
                    )
                    result = fallback.understand(normalized, url=url, force=True)
                    result.observability.error = str(exc)[:500]
                    result.extras["fallback"] = "heuristic"
                    result.content_hash = content_hash
                    return result
                except Exception:
                    pass
            failed = self._schema.empty(status="failed", reason=str(exc)[:500])
            failed.content_hash = content_hash
            failed.observability.provider = self._provider.name
            failed.observability.latency_ms = int((time.perf_counter() - started) * 1000)
            return failed
