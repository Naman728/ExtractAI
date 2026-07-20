"""Website Intelligence package."""

from app.website_intelligence.profile import (
    AnalyzeRequest,
    AnalyzeResponse,
    IntelligenceReport,
    WebsiteProfile,
)

__all__ = [
    "AnalyzeRequest",
    "AnalyzeResponse",
    "IntelligenceReport",
    "WebsiteProfile",
]


def get_intelligence_engine():
    """Lazy factory to avoid circular imports at package import time."""
    from app.website_intelligence.engine import WebsiteIntelligenceEngine

    return WebsiteIntelligenceEngine()
