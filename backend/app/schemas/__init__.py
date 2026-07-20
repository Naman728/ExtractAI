"""Shared Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageResponse(BaseModel):
    message: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)


class UserResponse(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime


class JobCreateRequest(BaseModel):
    url: HttpUrl
    inputs: dict[str, str] = Field(default_factory=dict)
    workflow: str | None = None
    # Convenience: multiple addresses → creates a batch (preferred for 2+)
    addresses: list[str] = Field(default_factory=list)
    # Pagination crawl (None = use server defaults)
    follow_pagination: bool | None = None
    max_pages: int | None = Field(default=None, ge=1, le=50)


class JobResponse(ORMModel):
    id: UUID
    url: str
    normalized_url: str
    status: str
    progress_pct: int
    current_stage: str | None
    strategy_used: str | None
    selected_strategy: str | None
    extractor_type: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    error_code: str | None
    error_message: str | None
    retry_count: int
    output_size_bytes: int | None
    pipeline_version: str
    strategy_version: str
    plugin_set_version: str
    schema_version: int
    overall_confidence: float | None
    partial: bool
    created_at: datetime
    updated_at: datetime
    inputs: dict[str, str] = Field(default_factory=dict)
    workflow: str | None = None
    batch_id: UUID | None = None


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int


class JobEventResponse(ORMModel):
    stage: str
    level: str
    message: str
    details: dict = Field(default_factory=dict)
    created_at: datetime


class JobEventsResponse(BaseModel):
    job_id: UUID
    status: str
    progress_pct: int
    current_stage: str | None
    events: list[JobEventResponse] = Field(default_factory=list)


class BatchCreateRequest(BaseModel):
    url: HttpUrl
    addresses: list[str] = Field(min_length=1)
    workflow: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)


class BatchItemResponse(BaseModel):
    id: UUID
    position: int
    address: str
    job_id: UUID | None
    status: str
    error_message: str | None = None
    officials_total: int = 0
    officials_counts: dict[str, int] = Field(default_factory=dict)
    result_summary: dict = Field(default_factory=dict)


class BatchResponse(BaseModel):
    id: UUID
    url: str
    workflow: str | None
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    progress_pct: int
    created_at: datetime
    updated_at: datetime
    items: list[BatchItemResponse] = Field(default_factory=list)


class BatchResultsResponse(BaseModel):
    batch_id: UUID
    url: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    results: list[dict] = Field(default_factory=list)


class GuestSessionResponse(BaseModel):
    guest_key: str
    jobs_used: int
    jobs_limit: int
    remaining: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str
