"""Website category classification service."""

from __future__ import annotations

import json
import re
from typing import Any

from app.ai.models.website_profile import WebsiteCategory
from app.ai.prompts import load_prompt
from app.ai.providers.base import LLMMessage, LLMProvider
from app.ai.providers.heuristic import HeuristicProvider


_CATEGORY_ALIASES: dict[str, WebsiteCategory] = {
    c.value.lower(): c for c in WebsiteCategory
}
_CATEGORY_ALIASES.update(
    {
        "ecommerce": WebsiteCategory.ECOMMERCE,
        "e-commerce": WebsiteCategory.ECOMMERCE,
        "e commerce": WebsiteCategory.ECOMMERCE,
        "gov": WebsiteCategory.GOVERNMENT,
        "government": WebsiteCategory.GOVERNMENT,
        "uni": WebsiteCategory.UNIVERSITY,
        "college": WebsiteCategory.UNIVERSITY,
        "docs": WebsiteCategory.DOCUMENTATION,
        "documentation": WebsiteCategory.DOCUMENTATION,
        "dev": WebsiteCategory.DEVELOPER,
        "developer": WebsiteCategory.DEVELOPER,
        "saas": WebsiteCategory.SAAS,
        "software": WebsiteCategory.SAAS,
        "news": WebsiteCategory.NEWS,
        "blog": WebsiteCategory.BLOG,
        "nonprofit": WebsiteCategory.NONPROFIT,
        "non-profit": WebsiteCategory.NONPROFIT,
        "finance": WebsiteCategory.FINANCIAL,
        "financial": WebsiteCategory.FINANCIAL,
        "health": WebsiteCategory.HEALTHCARE,
        "healthcare": WebsiteCategory.HEALTHCARE,
        "travel": WebsiteCategory.TRAVEL,
        "education": WebsiteCategory.EDUCATION,
        "marketplace": WebsiteCategory.MARKETPLACE,
        "portfolio": WebsiteCategory.PORTFOLIO,
        "corporate": WebsiteCategory.CORPORATE,
        "company": WebsiteCategory.CORPORATE,
    }
)


def parse_category(raw: str | None) -> WebsiteCategory:
    if not raw:
        return WebsiteCategory.OTHER
    key = raw.strip().lower()
    return _CATEGORY_ALIASES.get(key, WebsiteCategory.OTHER)


class ClassificationService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def classify(self, content: dict[str, Any], *, url: str = "") -> dict[str, Any]:
        if isinstance(self._provider, HeuristicProvider):
            return self._heuristic(content, url=url)

        system = load_prompt("classification")
        user = json.dumps({"url": url, "extraction": content}, ensure_ascii=False, default=str)
        resp = self._provider.complete(
            [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
            response_format_json=True,
        )
        data = _safe_json(resp.text)
        category = parse_category(str(data.get("category") or ""))
        return {
            "category": category,
            "category_confidence": float(data.get("category_confidence") or 0.5),
            "rationale": data.get("rationale"),
            "secondary_categories": data.get("secondary_categories") or [],
            "semantic_tags": data.get("semantic_tags") or [],
            "_llm": {
                "latency_ms": resp.latency_ms,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "estimated_cost_usd": resp.estimated_cost_usd,
                "model": resp.model,
            },
        }

    def _heuristic(self, content: dict[str, Any], *, url: str) -> dict[str, Any]:
        blob = json.dumps(content, ensure_ascii=False, default=str).lower()
        host = url.lower()
        scores: dict[WebsiteCategory, float] = {c: 0.0 for c in WebsiteCategory}

        def bump(cat: WebsiteCategory, amount: float) -> None:
            scores[cat] += amount

        if any(x in host for x in (".gov", "ballotready", "civic", "city.", "county.")):
            bump(WebsiteCategory.GOVERNMENT, 3.0)
        if "officials" in content or "civic" in blob:
            bump(WebsiteCategory.GOVERNMENT, 2.0)
        if any(k in blob for k in ("add to cart", "sku", "checkout", "product price", "buy now")):
            bump(WebsiteCategory.ECOMMERCE, 2.5)
        if content.get("products") or content.get("prices"):
            # Products appear on SaaS pricing pages too — lighter bump
            bump(WebsiteCategory.ECOMMERCE, 1.0)
        if any(x in host for x in (".edu", "university", "college")):
            bump(WebsiteCategory.UNIVERSITY, 3.0)
        if any(k in blob for k in ("patient", "clinic", "hospital", "healthcare")):
            bump(WebsiteCategory.HEALTHCARE, 2.0)
        if any(k in blob for k in ("breaking news", "article", "journalist")):
            bump(WebsiteCategory.NEWS, 1.8)
        if any(k in blob for k in ("api docs", "documentation", "getting started", "reference")):
            bump(WebsiteCategory.DOCUMENTATION, 2.0)
        if any(k in blob for k in ("saas", "pricing plans", "free trial", "dashboard", "analytics")):
            bump(WebsiteCategory.SAAS, 2.8)
        if any(k in blob for k in ("marketplace", "sellers", "buyers")):
            bump(WebsiteCategory.MARKETPLACE, 1.8)
        if any(k in blob for k in ("nonprofit", "donate", "charity")):
            bump(WebsiteCategory.NONPROFIT, 2.0)
        if any(k in blob for k in ("bank", "invest", "fintech", "insurance")):
            bump(WebsiteCategory.FINANCIAL, 1.8)
        if any(k in blob for k in ("flight", "hotel", "booking", "travel")):
            bump(WebsiteCategory.TRAVEL, 1.8)
        if any(k in blob for k in ("github", "developer", "sdk", "openapi")):
            bump(WebsiteCategory.DEVELOPER, 1.5)
        if any(k in blob for k in ("portfolio", "my work", "case studies")):
            bump(WebsiteCategory.PORTFOLIO, 1.5)
        if any(k in blob for k in ("blog", "posted on", "comments")):
            bump(WebsiteCategory.BLOG, 1.2)
        if any(k in blob for k in ("about us", "our company", "careers", "investors")):
            bump(WebsiteCategory.CORPORATE, 1.0)

        best = max(scores.items(), key=lambda kv: kv[1])
        if best[1] < 0.8:
            category = WebsiteCategory.OTHER
            conf = 0.35
        else:
            category = best[0]
            conf = min(0.95, 0.45 + best[1] / 6.0)

        tags = _extract_tags(content)
        return {
            "category": category,
            "category_confidence": round(conf, 3),
            "rationale": "Heuristic classification from extraction signals",
            "secondary_categories": [],
            "semantic_tags": tags,
            "_llm": {"latency_ms": 0, "prompt_tokens": 0, "completion_tokens": 0, "estimated_cost_usd": 0.0, "model": "heuristic-v1"},
        }


def _extract_tags(content: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    title = str(content.get("title") or "")
    if title:
        tags.extend(re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}", title)[:6])
    meta = content.get("meta") or {}
    if isinstance(meta, dict):
        desc = str(meta.get("description") or meta.get("og:description") or "")
        tags.extend(re.findall(r"[A-Za-z][A-Za-z0-9+\-]{3,}", desc)[:8])
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out[:12]


def _safe_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}
