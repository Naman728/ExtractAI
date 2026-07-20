"""Bot protection, Cloudflare, CAPTCHA detection."""

from __future__ import annotations

import re

from app.website_intelligence.profile import BotProtection
from app.website_intelligence.types import ConfidentValue


def detect_bot_protection(
    html: str,
    headers: dict[str, str],
    status_code: int,
) -> tuple[ConfidentValue[BotProtection], ConfidentValue[bool], ConfidentValue[bool]]:
    """Detect Cloudflare / CAPTCHA / generic WAF challenges."""
    evidence: list[str] = []
    cloudflare = False
    captcha = False
    protection: BotProtection = "none"
    confidence = 0.6

    server = (headers.get("server") or "").lower()
    if "cloudflare" in server or "cf-ray" in headers or "cf-cache-status" in headers:
        cloudflare = True
        evidence.append("cloudflare_headers")
        confidence = 0.95

    body = html or ""
    cf_challenge = bool(
        re.search(
            r"cf-browser-verification|challenge-platform|cdn-cgi/challenge|Attention Required! \| Cloudflare",
            body,
            re.I,
        )
    )
    if cf_challenge or (status_code in {403, 503} and cloudflare):
        protection = "cloudflare"
        cloudflare = True
        confidence = 0.92
        evidence.append("cloudflare_challenge")

    captcha_patterns = (
        r"hcaptcha",
        r"recaptcha",
        r"g-recaptcha",
        r"cf-turnstile",
        r"captcha",
        r"challenges\.cloudflare\.com",
    )
    for rx in captcha_patterns:
        if re.search(rx, body, re.I) or any(re.search(rx, f"{k}{v}", re.I) for k, v in headers.items()):
            captcha = True
            evidence.append(rx)
            protection = "captcha" if protection == "none" else protection
            confidence = max(confidence, 0.9)
            break

    if protection == "none" and status_code == 403 and not cloudflare:
        protection = "waf_unknown"
        confidence = 0.55
        evidence.append("http_403")

    return (
        ConfidentValue(value=protection, confidence=confidence, evidence=evidence),
        ConfidentValue(value=cloudflare, confidence=0.95 if cloudflare else 0.7, evidence=evidence),
        ConfidentValue(value=captcha, confidence=0.9 if captcha else 0.7, evidence=evidence),
    )
