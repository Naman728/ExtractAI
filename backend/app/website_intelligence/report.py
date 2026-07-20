"""Build IntelligenceReport + strategy suggestions from a WebsiteProfile."""

from __future__ import annotations

from app.website_intelligence.profile import IntelligenceReport, WebsiteProfile


def build_intelligence_report(profile: WebsiteProfile) -> IntelligenceReport:
    """Derive actionable recommendations for the future Strategy Engine."""
    warnings: list[str] = []
    issues: list[str] = []
    rationale: list[str] = []

    framework = profile.framework.value
    cms = profile.cms.value
    js_required = profile.javascript_required.value
    cloudflare = profile.cloudflare.value
    captcha = profile.captcha.value
    complexity = profile.estimated_complexity.value

    # Website type
    if cms == "shopify":
        website_type = "ecommerce"
    elif cms in {"wordpress", "drupal"}:
        website_type = "cms_content"
    elif framework in {"nextjs", "nuxt", "react", "vue", "angular"}:
        website_type = "spa_or_ssr_app"
    elif profile.has_json_ld.value and any(
        t.lower() in {"article", "newsarticle", "blogposting"} for t in profile.schema_org_types.value
    ):
        website_type = "article"
    elif profile.rendering_mode.value == "static":
        website_type = "static_site"
    else:
        website_type = "general_web"

    # Suggested fetch strategy
    if captcha:
        suggested_fetch = "playwright_rendering"
        strategy_recommendation = (
            "CAPTCHA detected — browser rendering may be required; expect lower success without human/solver."
        )
        warnings.append("CAPTCHA present; automated extraction may fail.")
        issues.append("captcha")
        rationale.append("captcha_forces_browser")
    elif cloudflare and profile.bot_protection.value == "cloudflare":
        suggested_fetch = "playwright_rendering"
        strategy_recommendation = (
            "Cloudflare challenge signals present — prefer Playwright with careful pacing."
        )
        warnings.append("Cloudflare protection detected.")
        issues.append("cloudflare")
        rationale.append("cloudflare_challenge")
    elif profile.discovered_apis.value and not js_required:
        suggested_fetch = "public_rest_api"
        strategy_recommendation = (
            "Public API hints discovered — prefer REST/JSON strategy before HTML parsing."
        )
        rationale.append("api_hints_available")
    elif profile.has_json_ld.value and profile.schema_org_types.value:
        suggested_fetch = "json_ld"
        strategy_recommendation = (
            "Rich JSON-LD/Schema.org present — structured metadata strategy is preferred."
        )
        rationale.append("json_ld_rich")
    elif js_required or profile.rendering_mode.value == "csr_heavy":
        suggested_fetch = "playwright_rendering"
        strategy_recommendation = (
            "JavaScript-heavy / CSR page — Playwright rendering recommended."
        )
        rationale.append("js_required")
    else:
        suggested_fetch = "static_html"
        strategy_recommendation = (
            "Static or SSR HTML appears sufficient — use static HTML fetch strategy."
        )
        rationale.append("static_html_ok")

    if profile.auth_required.value:
        warnings.append("Authentication signals detected; public extraction may be incomplete.")
        issues.append("auth_required")
    if profile.status_code.value >= 400:
        warnings.append(f"HTTP status {profile.status_code.value} on probe.")
        issues.append(f"http_{profile.status_code.value}")
    if not profile.robots.value.get("available"):
        warnings.append("robots.txt not found or unavailable.")

    suggested_extractor = "basic"
    if complexity >= 70 or js_required:
        # Future: llm may help — recommend basic until LLM wired
        suggested_extractor = "basic"
        rationale.append("high_complexity_still_basic_until_llm")

    return IntelligenceReport(
        website_type=website_type,
        framework=framework,
        cms=cms,
        strategy_recommendation=strategy_recommendation,
        javascript_required=js_required,
        cloudflare=cloudflare,
        captcha=captcha,
        complexity_score=round(complexity, 1),
        suggested_fetch_strategy=suggested_fetch,
        suggested_extractor=suggested_extractor,
        warnings=warnings,
        potential_issues=issues,
        confidence=round(profile.overall_confidence, 3),
        rationale=rationale,
    )


def estimate_complexity(profile_bits: dict) -> tuple[float, list[str]]:
    """0–100 complexity score from intermediate signals."""
    score = 20.0
    evidence: list[str] = []
    if profile_bits.get("js_required"):
        score += 25
        evidence.append("js_required+25")
    if profile_bits.get("cloudflare"):
        score += 15
        evidence.append("cloudflare+15")
    if profile_bits.get("captcha"):
        score += 20
        evidence.append("captcha+20")
    if profile_bits.get("auth"):
        score += 15
        evidence.append("auth+15")
    mode = profile_bits.get("rendering_mode")
    if mode == "csr_heavy":
        score += 15
        evidence.append("csr+15")
    elif mode == "hybrid":
        score += 8
        evidence.append("hybrid+8")
    scripts_proxy = profile_bits.get("tech_count", 0)
    score += min(15, scripts_proxy * 2)
    return min(100.0, score), evidence
