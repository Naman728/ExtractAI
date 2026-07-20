"""Website summary + business profile service."""

from __future__ import annotations

import json
from typing import Any

from app.ai.models.website_profile import BusinessProfile, WebsiteCategory
from app.ai.prompts import load_prompt
from app.ai.providers.base import LLMMessage, LLMProvider
from app.ai.providers.heuristic import HeuristicProvider
from app.ai.services.classification_service import _safe_json, parse_category


class SummaryService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def summarize(
        self,
        content: dict[str, Any],
        *,
        url: str = "",
        category: WebsiteCategory | None = None,
    ) -> dict[str, Any]:
        if isinstance(self._provider, HeuristicProvider):
            return self._heuristic(content, url=url, category=category)

        system = load_prompt("website_summary")
        user = json.dumps(
            {"url": url, "extraction": content, "hint_category": category.value if category else None},
            ensure_ascii=False,
            default=str,
        )
        resp = self._provider.complete(
            [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
            response_format_json=True,
        )
        data = _safe_json(resp.text)
        return {
            "summary": str(data.get("summary") or "").strip(),
            "category": parse_category(str(data.get("category") or "")) if data.get("category") else category,
            "category_confidence": float(data.get("category_confidence") or 0.5),
            "business_profile": BusinessProfile(
                organization_name=data.get("organization_name"),
                description=data.get("business_description"),
                industry=data.get("industry"),
                main_products=[str(x) for x in (data.get("main_products") or []) if x],
                main_services=[str(x) for x in (data.get("main_services") or []) if x],
            ),
            "semantic_tags": [str(t) for t in (data.get("semantic_tags") or []) if t],
            "overall_confidence": float(data.get("overall_confidence") or 0.5),
            "_llm": {
                "latency_ms": resp.latency_ms,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "estimated_cost_usd": resp.estimated_cost_usd,
                "model": resp.model,
            },
        }

    def _heuristic(
        self,
        content: dict[str, Any],
        *,
        url: str,
        category: WebsiteCategory | None,
    ) -> dict[str, Any]:
        title = str(content.get("title") or "Untitled site").strip()
        meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
        desc = str((meta or {}).get("description") or (meta or {}).get("og:description") or "").strip()
        headings = content.get("headings") or []
        heading_texts = []
        for h in headings[:6]:
            if isinstance(h, str):
                heading_texts.append(h)
            elif isinstance(h, dict) and h.get("text"):
                heading_texts.append(str(h["text"]))

        org = title.split("|")[0].split("-")[0].strip()
        cat = category or WebsiteCategory.OTHER
        parts = [
            f"{title} appears to be a {cat.value.lower()} website",
            f"at {url}." if url else ".",
        ]
        if desc:
            parts.append(desc[:280])
        elif heading_texts:
            parts.append("Key topics include: " + "; ".join(heading_texts[:4]) + ".")

        products = []
        for p in content.get("products") or []:
            if isinstance(p, dict) and p.get("name"):
                products.append(str(p["name"]))
            elif isinstance(p, str):
                products.append(p)

        officials = content.get("officials") or {}
        services: list[str] = []
        if isinstance(officials, dict) and any(officials.get(k) for k in ("federal", "state", "local")):
            services.append("Elected officials lookup")
            services.append("Civic information")

        summary = " ".join(p.strip() for p in parts if p).strip()
        if not summary.endswith("."):
            summary += "."

        return {
            "summary": summary,
            "category": cat,
            "category_confidence": 0.55,
            "business_profile": BusinessProfile(
                organization_name=org or None,
                description=desc or summary,
                industry=cat.value,
                main_products=products[:15],
                main_services=services[:15],
            ),
            "semantic_tags": heading_texts[:8],
            "overall_confidence": 0.55,
            "_llm": {
                "latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "estimated_cost_usd": 0.0,
                "model": "heuristic-v1",
            },
        }
