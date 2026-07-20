"""Knowledge graph models for AI understanding."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

NodeType = Literal[
    "organization",
    "person",
    "product",
    "service",
    "department",
    "location",
    "contact",
    "technology",
    "website",
    "other",
]

EdgeType = Literal[
    "owns",
    "offers",
    "employs",
    "belongs_to",
    "located_at",
    "contactable_via",
    "uses",
    "related_to",
    "part_of",
]


class KnowledgeNode(BaseModel):
    id: str
    label: str
    type: NodeType = "other"
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class KnowledgeEdge(BaseModel):
    id: str
    source: str
    target: str
    type: EdgeType = "related_to"
    label: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraph(BaseModel):
    nodes: list[KnowledgeNode] = Field(default_factory=list)
    edges: list[KnowledgeEdge] = Field(default_factory=list)
    root_id: str | None = None

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)
