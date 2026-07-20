"""Entity extraction service."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from app.ai.models.entities import (
    ContactEntity,
    EntityBundle,
    LocationEntity,
    OrganizationEntity,
    PersonEntity,
    ProductEntity,
    ServiceEntity,
    TechnologyEntity,
)
from app.ai.prompts import load_prompt
from app.ai.providers.base import LLMMessage, LLMProvider
from app.ai.providers.heuristic import HeuristicProvider
from app.ai.services.classification_service import _safe_json


class EntityService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(self, content: dict[str, Any], *, url: str = "") -> tuple[EntityBundle, dict[str, Any]]:
        if isinstance(self._provider, HeuristicProvider):
            return self._heuristic(content, url=url), {
                "latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "estimated_cost_usd": 0.0,
                "model": "heuristic-v1",
            }

        system = load_prompt("entity_extraction")
        user = json.dumps({"url": url, "extraction": content}, ensure_ascii=False, default=str)
        resp = self._provider.complete(
            [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
            response_format_json=True,
        )
        data = _safe_json(resp.text)
        bundle = self._from_dict(data)
        meta = {
            "latency_ms": resp.latency_ms,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "estimated_cost_usd": resp.estimated_cost_usd,
            "model": resp.model,
        }
        return bundle, meta

    def _from_dict(self, data: dict[str, Any]) -> EntityBundle:
        return EntityBundle(
            people=[PersonEntity(**p) for p in (data.get("people") or []) if isinstance(p, dict) and p.get("name")],
            organizations=[
                OrganizationEntity(**o)
                for o in (data.get("organizations") or [])
                if isinstance(o, dict) and o.get("name")
            ],
            products=[ProductEntity(**p) for p in (data.get("products") or []) if isinstance(p, dict) and p.get("name")],
            services=[ServiceEntity(**s) for s in (data.get("services") or []) if isinstance(s, dict) and s.get("name")],
            departments=[str(d) for d in (data.get("departments") or []) if d],
            locations=[
                LocationEntity(**loc) for loc in (data.get("locations") or []) if isinstance(loc, dict) and loc.get("name")
            ],
            contacts=[
                ContactEntity(**c) for c in (data.get("contacts") or []) if isinstance(c, dict) and c.get("value")
            ],
            technologies=[
                TechnologyEntity(**t) for t in (data.get("technologies") or []) if isinstance(t, dict) and t.get("name")
            ],
            tags=[str(t) for t in (data.get("tags") or []) if t],
        )

    def _heuristic(self, content: dict[str, Any], *, url: str) -> EntityBundle:
        people: list[PersonEntity] = []
        orgs: list[OrganizationEntity] = []
        products: list[ProductEntity] = []
        services: list[ServiceEntity] = []
        departments: list[str] = []
        locations: list[LocationEntity] = []
        contacts: list[ContactEntity] = []
        technologies: list[TechnologyEntity] = []
        tags: list[str] = []

        title = str(content.get("title") or "").strip()
        host = urlparse(url).netloc.replace("www.", "") if url else ""
        org_name = title.split("|")[0].split("-")[0].strip() if title else host
        if org_name:
            orgs.append(
                OrganizationEntity(name=org_name, org_type="website", confidence=0.55, evidence=["title"])
            )

        # Officials from browser agent
        officials = content.get("officials") or {}
        if isinstance(officials, dict):
            for level in ("federal", "state", "local"):
                for item in officials.get(level) or []:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name") or item.get("official_name")
                    if not name:
                        continue
                    people.append(
                        PersonEntity(
                            name=str(name),
                            role=str(item.get("office") or item.get("title") or level),
                            organization=org_name or None,
                            confidence=0.8,
                            evidence=[f"officials.{level}"],
                        )
                    )

        for p in content.get("products") or []:
            if isinstance(p, dict) and p.get("name"):
                products.append(
                    ProductEntity(
                        name=str(p["name"]),
                        description=str(p.get("description") or "") or None,
                        price=str(p.get("price") or "") or None,
                        confidence=0.7,
                    )
                )
            elif isinstance(p, str) and p.strip():
                products.append(ProductEntity(name=p.strip(), confidence=0.55))

        for email in content.get("emails") or []:
            val = email if isinstance(email, str) else (email.get("value") if isinstance(email, dict) else None)
            if val:
                contacts.append(ContactEntity(kind="email", value=str(val), confidence=0.9))

        for phone in content.get("phones") or []:
            val = phone if isinstance(phone, str) else (phone.get("value") if isinstance(phone, dict) else None)
            if val:
                contacts.append(ContactEntity(kind="phone", value=str(val), confidence=0.85))

        for link in content.get("social_links") or []:
            if isinstance(link, dict) and link.get("url"):
                contacts.append(
                    ContactEntity(
                        kind="social",
                        value=str(link["url"]),
                        label=str(link.get("platform") or link.get("network") or "social"),
                        confidence=0.75,
                    )
                )
            elif isinstance(link, str):
                contacts.append(ContactEntity(kind="social", value=link, confidence=0.7))

        # Technologies from common signals
        blob = json.dumps(content, ensure_ascii=False, default=str).lower()
        tech_signals = [
            ("Next.js", "framework"),
            ("React", "framework"),
            ("WordPress", "cms"),
            ("Shopify", "cms"),
            ("Vercel", "hosting"),
            ("Cloudflare", "hosting"),
            ("Google Analytics", "analytics"),
            ("Stripe", "other"),
            ("Payload", "cms"),
        ]
        for name, cat in tech_signals:
            if name.lower() in blob:
                technologies.append(TechnologyEntity(name=name, category=cat, confidence=0.65))

        # Departments from headings
        for h in content.get("headings") or []:
            text = h if isinstance(h, str) else (h.get("text") if isinstance(h, dict) else None)
            if not text:
                continue
            if re.search(r"\b(department|ministry|office of|division|team)\b", str(text), re.I):
                departments.append(str(text).strip()[:120])

        agent = content.get("agent") or {}
        if isinstance(agent, dict) and agent.get("address_normalized"):
            locations.append(
                LocationEntity(
                    name="Queried address",
                    address=str(agent["address_normalized"]),
                    confidence=0.7,
                )
            )

        meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
        desc = str((meta or {}).get("description") or "")
        if desc:
            tags.extend(re.findall(r"[A-Za-z][A-Za-z0-9+\-]{3,}", desc)[:10])

        # Infer services from headings
        for h in (content.get("headings") or [])[:20]:
            text = h if isinstance(h, str) else (h.get("text") if isinstance(h, dict) else None)
            if text and re.search(r"\b(service|services|solutions|offerings)\b", str(text), re.I):
                services.append(ServiceEntity(name=str(text).strip()[:120], confidence=0.5))

        return EntityBundle(
            people=people[:50],
            organizations=orgs[:20],
            products=products[:40],
            services=services[:30],
            departments=list(dict.fromkeys(departments))[:20],
            locations=locations[:20],
            contacts=contacts[:40],
            technologies=technologies[:20],
            tags=list(dict.fromkeys(tags))[:15],
        )
