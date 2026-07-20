"""Unit tests for AI Understanding Engine."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.ai.chunking import hash_normalized, select_relevant_content
from app.ai.models.entities import EntityBundle, PersonEntity, ProductEntity
from app.ai.models.website_profile import BusinessProfile, WebsiteCategory
from app.ai.providers.base import LLMMessage, LLMResponse
from app.ai.providers.factory import create_llm_provider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.heuristic import HeuristicProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.services.classification_service import ClassificationService, parse_category
from app.ai.services.entity_service import EntityService
from app.ai.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.ai.services.understanding_service import UnderstandingService
from app.core.config import Settings


def _settings(**kwargs: Any) -> Settings:
    base = dict(
        jwt_secret_key="x" * 32,
        ai_understanding_enabled=True,
        llm_provider="none",
    )
    base.update(kwargs)
    return Settings(**base)


SAMPLE_NORMALIZED = {
    "title": "Acme Analytics — Modern SaaS for Data Teams",
    "meta": {"description": "Acme helps companies extract insights with AI dashboards and APIs."},
    "headings": ["Product", "Pricing", "Documentation", "About Us"],
    "paragraphs": ["Start a free trial of our SaaS platform today."],
    "emails": ["hello@acme.example"],
    "phones": ["+1-555-0100"],
    "products": [{"name": "Acme Insights", "price": "$49/mo"}],
    "social_links": [{"url": "https://twitter.com/acme", "platform": "twitter"}],
}


class FakeLLM:
    name = "fake"
    _model = "fake-1"

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.calls = 0

    def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            text=json.dumps(self._payload),
            model=self._model,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            latency_ms=5,
            estimated_cost_usd=0.0001,
        )


def test_parse_category_aliases() -> None:
    assert parse_category("SaaS") == WebsiteCategory.SAAS
    assert parse_category("e-commerce") == WebsiteCategory.ECOMMERCE
    assert parse_category("gov") == WebsiteCategory.GOVERNMENT
    assert parse_category("unknown-xyz") == WebsiteCategory.OTHER


def test_factory_none_returns_heuristic() -> None:
    provider = create_llm_provider(_settings(llm_provider="none"))
    assert isinstance(provider, HeuristicProvider)


def test_factory_openai_without_key_falls_back() -> None:
    provider = create_llm_provider(_settings(llm_provider="openai", openai_api_key=None, llm_api_key=None))
    assert isinstance(provider, HeuristicProvider)


def test_factory_openai_with_key() -> None:
    provider = create_llm_provider(
        _settings(llm_provider="openai", openai_api_key="sk-test", llm_model="gpt-4o-mini")
    )
    assert isinstance(provider, OpenAIProvider)


def test_factory_gemini_with_key() -> None:
    provider = create_llm_provider(
        _settings(llm_provider="gemini", gemini_api_key="gem-test", llm_model="gemini-2.0-flash")
    )
    assert isinstance(provider, GeminiProvider)


def test_openai_provider_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "model": "gpt-4o-mini",
                "choices": [{"message": {"content": '{"ok": true}'}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            }

    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def post(self, *args: Any, **kwargs: Any) -> FakeResp:
            return FakeResp()

    monkeypatch.setattr("app.ai.providers.openai.httpx.Client", FakeClient)
    resp = provider.complete([LLMMessage(role="user", content="hi")])
    assert '{"ok": true}' in resp.text
    assert resp.total_tokens == 8


def test_gemini_provider_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GeminiProvider(api_key="gem-test", model="gemini-2.0-flash")

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "candidates": [{"content": {"parts": [{"text": '{"category": "SaaS"}'}]}}],
                "usageMetadata": {
                    "promptTokenCount": 4,
                    "candidatesTokenCount": 2,
                    "totalTokenCount": 6,
                },
            }

    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def post(self, *args: Any, **kwargs: Any) -> FakeResp:
            return FakeResp()

    monkeypatch.setattr("app.ai.providers.gemini.httpx.Client", FakeClient)
    resp = provider.complete([LLMMessage(role="user", content="classify")])
    assert "SaaS" in resp.text
    assert resp.prompt_tokens == 4


def test_classification_heuristic_saas() -> None:
    svc = ClassificationService(HeuristicProvider())
    result = svc.classify(SAMPLE_NORMALIZED, url="https://acme.example")
    assert result["category"] == WebsiteCategory.SAAS
    assert result["category_confidence"] > 0.4


def test_classification_heuristic_government() -> None:
    svc = ClassificationService(HeuristicProvider())
    result = svc.classify(
        {"title": "BallotReady", "officials": {"local": [{"name": "Mayor"}]}},
        url="https://www.ballotready.org/",
    )
    assert result["category"] == WebsiteCategory.GOVERNMENT


def test_entity_extraction_heuristic() -> None:
    svc = EntityService(HeuristicProvider())
    bundle, meta = svc.extract(SAMPLE_NORMALIZED, url="https://acme.example")
    assert any(c.kind == "email" for c in bundle.contacts)
    assert any(p.name == "Acme Insights" for p in bundle.products)
    assert bundle.organizations
    assert meta["model"] == "heuristic-v1"


def test_knowledge_graph_relationships() -> None:
    entities = EntityBundle(
        people=[PersonEntity(name="Ada Lovelace", role="Engineer", confidence=0.9)],
        products=[ProductEntity(name="Widget", confidence=0.8)],
        departments=["Engineering"],
        technologies=[],
    )
    profile = BusinessProfile(organization_name="Acme", main_services=["Analytics"])
    graph = KnowledgeGraphBuilder().build(
        url="https://acme.example",
        entities=entities,
        profile=profile,
        category="SaaS",
    )
    assert graph.node_count() >= 4
    assert graph.edge_count() >= 3
    types = {n.type for n in graph.nodes}
    assert "organization" in types
    assert "person" in types
    assert "product" in types


def test_hash_stable() -> None:
    a = hash_normalized(SAMPLE_NORMALIZED, prompt_version="1.0.0", model="m")
    b = hash_normalized(SAMPLE_NORMALIZED, prompt_version="1.0.0", model="m")
    c = hash_normalized(SAMPLE_NORMALIZED, prompt_version="1.0.1", model="m")
    assert a == b
    assert a != c


def test_select_relevant_truncates() -> None:
    huge = {
        **SAMPLE_NORMALIZED,
        "paragraphs": ["x" * 5000 for _ in range(40)],
        "links": [{"url": f"https://x/{i}"} for i in range(200)],
    }
    selected = select_relevant_content(huge, max_chars=3000)
    serialized = json.dumps(selected)
    assert len(serialized) <= 8000  # soft bound after truncation logic
    assert "title" in selected


def test_understanding_service_heuristic() -> None:
    svc = UnderstandingService(settings=_settings(), provider=HeuristicProvider(), cache=None)
    result = svc.understand(SAMPLE_NORMALIZED, url="https://acme.example", force=True)
    assert result.status == "completed"
    assert result.summary
    assert result.category == WebsiteCategory.SAAS
    assert result.knowledge_graph.node_count() > 0
    assert result.observability.provider == "heuristic"
    assert result.observability.cache_hit is False


def test_understanding_respects_disabled() -> None:
    svc = UnderstandingService(
        settings=_settings(ai_understanding_enabled=False),
        provider=HeuristicProvider(),
    )
    result = svc.understand(SAMPLE_NORMALIZED, url="https://acme.example")
    assert result.status == "skipped"


def test_understanding_cache_hit() -> None:
    cache = MagicMock()
    cached_payload = {
        "summary": "Cached summary",
        "category": "SaaS",
        "category_confidence": 0.9,
        "business_profile": {},
        "entities": {},
        "knowledge_graph": {"nodes": [], "edges": []},
        "semantic_tags": [],
        "overall_confidence": 0.9,
        "observability": {"provider": "heuristic", "cache_hit": False},
        "status": "completed",
        "understanding_version": "1.0.0",
    }
    cache.get.return_value = cached_payload
    svc = UnderstandingService(settings=_settings(), provider=HeuristicProvider(), cache=cache)
    result = svc.understand(SAMPLE_NORMALIZED, url="https://acme.example", force=False)
    assert result.observability.cache_hit is True
    assert result.summary == "Cached summary"
    cache.put.assert_not_called()


def test_understanding_with_fake_llm() -> None:
    payload = {
        "summary": "Acme is a SaaS analytics company.",
        "category": "SaaS",
        "category_confidence": 0.92,
        "business_description": "Analytics SaaS",
        "organization_name": "Acme",
        "industry": "Software",
        "main_products": ["Acme Insights"],
        "main_services": ["Dashboards"],
        "semantic_tags": ["saas", "analytics"],
        "overall_confidence": 0.9,
        "people": [],
        "organizations": [{"name": "Acme", "confidence": 0.9}],
        "products": [{"name": "Acme Insights", "confidence": 0.9}],
        "services": [{"name": "Dashboards", "confidence": 0.8}],
        "departments": [],
        "locations": [],
        "contacts": [{"kind": "email", "value": "hello@acme.example", "confidence": 0.9}],
        "technologies": [{"name": "React", "category": "framework", "confidence": 0.6}],
        "tags": ["saas"],
        "rationale": "SaaS signals",
        "secondary_categories": [],
    }
    fake = FakeLLM(payload)
    svc = UnderstandingService(settings=_settings(), provider=fake, cache=None)  # type: ignore[arg-type]
    result = svc.understand(SAMPLE_NORMALIZED, url="https://acme.example", force=True)
    assert result.status == "completed"
    assert "Acme" in result.summary
    assert result.category == WebsiteCategory.SAAS
    assert fake.calls >= 1
