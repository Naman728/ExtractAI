"""Shared scoring helpers for strategies (no decision trees for selection)."""

from __future__ import annotations

from app.website_intelligence.profile import WebsiteProfile


def complexity(profile: WebsiteProfile) -> float:
    return float(profile.estimated_complexity.value or 0.0)


def js_required(profile: WebsiteProfile) -> bool:
    return bool(profile.javascript_required.value)


def has_json_ld(profile: WebsiteProfile) -> bool:
    return bool(profile.has_json_ld.value)


def has_rich_metadata(profile: WebsiteProfile) -> bool:
    return bool(profile.open_graph.value) or bool(profile.twitter_cards.value)


def cloudflare_blocked(profile: WebsiteProfile) -> bool:
    return bool(profile.cloudflare.value) and profile.bot_protection.value == "cloudflare"


def captcha_present(profile: WebsiteProfile) -> bool:
    return bool(profile.captcha.value)


def rendering_mode(profile: WebsiteProfile) -> str:
    return str(profile.rendering_mode.value or "unknown")


def clamp(score: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, score))
