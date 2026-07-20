"""Entity models extracted by the AI Understanding Engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PersonEntity(BaseModel):
    name: str
    role: str | None = None
    organization: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class OrganizationEntity(BaseModel):
    name: str
    org_type: str | None = None
    description: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class ProductEntity(BaseModel):
    name: str
    description: str | None = None
    price: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ServiceEntity(BaseModel):
    name: str
    description: str | None = None
    department: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class LocationEntity(BaseModel):
    name: str
    address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ContactEntity(BaseModel):
    kind: str  # email | phone | social | form | other
    value: str
    label: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class TechnologyEntity(BaseModel):
    name: str
    category: str | None = None  # cms | framework | analytics | hosting | other
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EntityBundle(BaseModel):
    people: list[PersonEntity] = Field(default_factory=list)
    organizations: list[OrganizationEntity] = Field(default_factory=list)
    products: list[ProductEntity] = Field(default_factory=list)
    services: list[ServiceEntity] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    locations: list[LocationEntity] = Field(default_factory=list)
    contacts: list[ContactEntity] = Field(default_factory=list)
    technologies: list[TechnologyEntity] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    extras: dict[str, Any] = Field(default_factory=dict)
