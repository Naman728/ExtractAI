"""Centralized application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prefer repo-root .env, then backend/.env
_ROOT = Path(__file__).resolve().parents[3]
_BACKEND = Path(__file__).resolve().parents[2]
_ENV_FILES = (
    str(_ROOT / ".env"),
    str(_BACKEND / ".env"),
)


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ExtractAI"
    app_env: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3100"

    database_url: str = "postgresql+asyncpg://extractai:extractai@localhost:5432/extractai"
    database_url_sync: str = "postgresql+psycopg://extractai:extractai@localhost:5432/extractai"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    guest_job_limit: int = 100
    guest_session_expire_days: int = 7
    batch_max_addresses: int = 500
    batch_guest_max_addresses: int = 25

    extractor_type: str = "basic"
    storage_backend: str = "local"
    storage_local_path: str = "/data/storage"

    pipeline_version: str = "1.0.0"
    strategy_version: str = "1.0.0"
    schema_version: int = 1
    profile_version: str = "1.0.0"
    discovery_version: str = "1.0.0"
    network_version: str = "1.0.0"
    network_playwright_capture: bool = True

    # AI Understanding Engine (post-extraction)
    ai_understanding_enabled: bool = True
    llm_provider: str = "none"  # openai | gemini | anthropic | ollama | none
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 60
    llm_max_tokens: int = 4096
    ai_max_input_chars: int = 24_000
    understanding_version: str = "1.0.0"
    # When true, extraction completes first; AI runs in a background thread.
    ai_understanding_async: bool = True
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"

    http_timeout_seconds: int = 30
    playwright_timeout_ms: int = 30_000
    max_html_bytes: int = 5_242_880
    max_redirects: int = 5

    # Follow rel=next / Next links within a single job (in-pipeline crawl).
    pagination_enabled: bool = True
    pagination_max_pages: int = 5

    rate_limit_guest_per_minute: int = 10
    rate_limit_auth_per_minute: int = 60

    # Soft-production defaults
    use_celery: bool = True
    fetch_cascade_retry: bool = True

    # Transactional email (verification)
    # Prefer SMTP_* (Brevo relay) — Render cannot reach smtp.gmail.com (errno 101).
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str | None = None  # Brevo SMTP login (account email)
    smtp_password: str | None = None  # Brevo SMTP key (xsmtpsib-…)
    mail_from_email: str | None = None  # defaults to smtp_user / brevo_sender_email
    mail_from_name: str = "ExtractAI"

    # Brevo REST fallback (used when SMTP_PASSWORD is empty)
    brevo_api_key: str | None = None
    brevo_sender_email: str | None = None
    brevo_sender_name: str = "ExtractAI"
    brevo_smtp_login: str | None = None  # Brevo account email (SMTP login)
    brevo_smtp_host: str = "smtp-relay.brevo.com"
    brevo_smtp_port: int = 587
    brevo_use_smtp: bool = False  # auto-enabled for xsmtpsib- keys
    frontend_public_url: str = "http://localhost:3100"
    email_verification_expire_hours: int = 24
    email_verification_required: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _strip_origins(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local"}


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
