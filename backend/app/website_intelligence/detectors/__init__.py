"""Detectors package."""

from app.website_intelligence.detectors.bot_protection import detect_bot_protection
from app.website_intelligence.detectors.document import (
    detect_auth_signals,
    detect_cookies,
    detect_document_meta,
    detect_downloads,
    detect_forms,
    detect_security_headers,
    detect_social_links,
)
from app.website_intelligence.detectors.rendering import detect_rendering
from app.website_intelligence.detectors.technology import detect_technologies

__all__ = [
    "detect_auth_signals",
    "detect_bot_protection",
    "detect_cookies",
    "detect_document_meta",
    "detect_downloads",
    "detect_forms",
    "detect_rendering",
    "detect_security_headers",
    "detect_social_links",
    "detect_technologies",
]
