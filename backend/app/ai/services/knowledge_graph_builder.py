"""Build a knowledge graph from entities + business profile."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.ai.models.entities import EntityBundle
from app.ai.models.knowledge_graph import KnowledgeEdge, KnowledgeGraph, KnowledgeNode
from app.ai.models.website_profile import BusinessProfile


def _slug(text: str, prefix: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return f"{prefix}:{cleaned[:64] or 'unknown'}"


class KnowledgeGraphBuilder:
    """Company → Products → Services → Departments → People → Contacts."""

    def build(
        self,
        *,
        url: str,
        entities: EntityBundle,
        profile: BusinessProfile,
        category: str | None = None,
    ) -> KnowledgeGraph:
        nodes: list[KnowledgeNode] = []
        edges: list[KnowledgeEdge] = []
        seen_nodes: set[str] = set()
        edge_i = 0

        def add_node(node: KnowledgeNode) -> str:
            if node.id in seen_nodes:
                return node.id
            seen_nodes.add(node.id)
            nodes.append(node)
            return node.id

        def add_edge(source: str, target: str, etype: str, label: str | None = None, conf: float = 0.6) -> None:
            nonlocal edge_i
            edge_i += 1
            edges.append(
                KnowledgeEdge(
                    id=f"e{edge_i}",
                    source=source,
                    target=target,
                    type=etype,  # type: ignore[arg-type]
                    label=label or etype,
                    confidence=conf,
                )
            )

        host = urlparse(url).netloc.replace("www.", "") if url else "website"
        website_id = add_node(
            KnowledgeNode(
                id=_slug(host or "site", "website"),
                label=host or url or "Website",
                type="website",
                properties={"url": url, "category": category},
                confidence=0.9,
            )
        )

        org_name = profile.organization_name
        if not org_name and entities.organizations:
            org_name = entities.organizations[0].name
        org_id = None
        if org_name:
            org_id = add_node(
                KnowledgeNode(
                    id=_slug(org_name, "org"),
                    label=org_name,
                    type="organization",
                    properties={"description": profile.description, "industry": profile.industry},
                    confidence=0.75,
                )
            )
            add_edge(website_id, org_id, "related_to", "represents", 0.8)

        root = org_id or website_id

        for product in entities.products:
            pid = add_node(
                KnowledgeNode(
                    id=_slug(product.name, "product"),
                    label=product.name,
                    type="product",
                    properties={"description": product.description, "price": product.price},
                    confidence=product.confidence,
                )
            )
            add_edge(root, pid, "offers", "offers product", product.confidence)

        for name in profile.main_products:
            if any(p.name.lower() == name.lower() for p in entities.products):
                continue
            pid = add_node(
                KnowledgeNode(id=_slug(name, "product"), label=name, type="product", confidence=0.55)
            )
            add_edge(root, pid, "offers", "offers product", 0.55)

        for service in entities.services:
            sid = add_node(
                KnowledgeNode(
                    id=_slug(service.name, "service"),
                    label=service.name,
                    type="service",
                    properties={"description": service.description, "department": service.department},
                    confidence=service.confidence,
                )
            )
            add_edge(root, sid, "offers", "offers service", service.confidence)

        for name in profile.main_services:
            if any(s.name.lower() == name.lower() for s in entities.services):
                continue
            sid = add_node(
                KnowledgeNode(id=_slug(name, "service"), label=name, type="service", confidence=0.55)
            )
            add_edge(root, sid, "offers", "offers service", 0.55)

        dept_ids: dict[str, str] = {}
        for dept in entities.departments:
            did = add_node(
                KnowledgeNode(id=_slug(dept, "dept"), label=dept, type="department", confidence=0.6)
            )
            dept_ids[dept.lower()] = did
            add_edge(root, did, "part_of", "has department", 0.6)

        for person in entities.people:
            pid = add_node(
                KnowledgeNode(
                    id=_slug(person.name, "person"),
                    label=person.name,
                    type="person",
                    properties={"role": person.role, "organization": person.organization},
                    confidence=person.confidence,
                )
            )
            add_edge(root, pid, "employs", person.role or "associated with", person.confidence)
            if person.role:
                for dept, did in dept_ids.items():
                    if dept in person.role.lower():
                        add_edge(did, pid, "belongs_to", "member of", 0.5)

        for loc in entities.locations:
            lid = add_node(
                KnowledgeNode(
                    id=_slug(loc.name, "loc"),
                    label=loc.name,
                    type="location",
                    properties={
                        "address": loc.address,
                        "city": loc.city,
                        "region": loc.region,
                        "country": loc.country,
                    },
                    confidence=loc.confidence,
                )
            )
            add_edge(root, lid, "located_at", "located at", loc.confidence)

        for contact in entities.contacts:
            cid = add_node(
                KnowledgeNode(
                    id=_slug(f"{contact.kind}-{contact.value}", "contact"),
                    label=contact.label or contact.value,
                    type="contact",
                    properties={"kind": contact.kind, "value": contact.value},
                    confidence=contact.confidence,
                )
            )
            add_edge(root, cid, "contactable_via", contact.kind, contact.confidence)

        for tech in entities.technologies:
            tid = add_node(
                KnowledgeNode(
                    id=_slug(tech.name, "tech"),
                    label=tech.name,
                    type="technology",
                    properties={"category": tech.category},
                    confidence=tech.confidence,
                )
            )
            add_edge(website_id, tid, "uses", "uses technology", tech.confidence)

        return KnowledgeGraph(nodes=nodes, edges=edges, root_id=root)
