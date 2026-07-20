"""Universal scrape helper — site presets + multi-engine cascade."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logging import get_logger
from app.engines.pipeline import ExtractionPipeline, PipelineResult
from app.scrapers.site_profiles import (
    build_search_url,
    list_profiles,
    profile_to_crawl,
    resolve_site_profile,
)

logger = get_logger(__name__)

_BLOCK_TITLES = {
    "access denied",
    "bot or not?",
    "robot or human?",
    "just a moment...",
    "attention required!",
    "error: the request could not be satisfied",
}


@dataclass
class UniversalScrapeResult:
    success: bool
    url: str
    final_url: str | None
    site_profile: str
    engine_used: str | None
    engines_tried: list[str] = field(default_factory=list)
    title: str | None = None
    products: list[dict[str, Any]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    pagination: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    blocked: bool = False
    grade: str = "fail"
    normalized: dict[str, Any] = field(default_factory=dict)
    raw_payload: dict[str, Any] = field(default_factory=dict)
    timings_ms: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _counts(payload: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for k, v in (payload or {}).items():
        if isinstance(v, list):
            out[k] = len(v)
        elif isinstance(v, dict) and isinstance(v.get("total"), int):
            out[k] = int(v["total"])
        elif isinstance(v, dict):
            out[k] = len(v)
        elif v:
            out[k] = 1
    return out


def _is_blocked(result: PipelineResult) -> bool:
    if result.error_code in {"CAPTCHA", "CLOUDFLARE", "HTTP_403"}:
        return True
    title = str((result.normalized_payload or {}).get("title") or "").strip().lower()
    if title in _BLOCK_TITLES or "access denied" in title:
        return True
    html = (result.raw_html or "").lower()
    if "cf-browser-verification" in html or "challenge-platform" in html:
        return True
    if "robot or human" in html or "bot or not" in html:
        return True
    return False


def _usefulness(result: PipelineResult) -> tuple[str, int]:
    """Return (grade, score). Higher score = better."""
    if not result.success and not (result.normalized_payload or {}):
        return "fail", 0
    if _is_blocked(result):
        return "blocked", 0
    c = _counts(result.normalized_payload or {})
    score = (
        c.get("products", 0) * 5
        + min(c.get("prices", 0), 40)
        + min(c.get("links", 0), 200) // 10
        + min(c.get("images", 0), 80) // 4
        + min(c.get("paragraphs", 0), 40) // 2
        + (8 if c.get("title") else 0)
        + c.get("json_ld", 0) * 3
    )
    pages = int((result.pagination or {}).get("pages_crawled") or 1)
    if pages > 1:
        score += 10
    if score >= 40:
        return "strong", score
    if score >= 18:
        return "partial", score
    if score >= 8:
        return "thin", score
    return "empty", score


class UniversalScraper:
    """
    Easy entrypoint for scripts & jobs.

    - Picks a site profile from the URL host
    - Optionally rewrites to a search URL when ``query`` is set
    - Cascades fetch engines until content is useful (or options exhausted)
    """

    def __init__(self, pipeline: ExtractionPipeline | None = None) -> None:
        self._pipeline = pipeline or ExtractionPipeline()

    def scrape(
        self,
        url: str,
        *,
        query: str | None = None,
        max_pages: int | None = None,
        engine: str | None = None,
        follow_pagination: bool | None = None,
        scroll_rounds: int | None = None,
        inputs: dict[str, str] | None = None,
        cascade: bool = True,
    ) -> UniversalScrapeResult:
        profile = resolve_site_profile(url)
        target = url
        job_inputs = dict(inputs or {})

        if query and query.strip():
            job_inputs.setdefault("query", query.strip())
            search = build_search_url(profile, query)
            if search:
                target = search

        overrides: dict[str, Any] = {}
        if max_pages is not None:
            overrides["max_pages"] = max_pages
        if follow_pagination is not None:
            overrides["follow_pagination"] = follow_pagination
        if scroll_rounds is not None:
            overrides["scroll_rounds"] = scroll_rounds
        if engine:
            overrides["force_engine"] = engine

        crawl_base = profile_to_crawl(profile, overrides=overrides)

        if engine:
            engines: list[str] = [engine]
        elif cascade:
            engines = list(profile.engines)
            # Prefer forced engine first if set
            forced = crawl_base.get("force_engine")
            if forced and forced in engines:
                engines = [forced] + [e for e in engines if e != forced]
            elif forced:
                engines = [forced] + engines
        else:
            forced = crawl_base.get("force_engine") or "playwright"
            engines = [str(forced)]

        # browser_agent only when we have interactive inputs
        if "browser_agent" in engines and not job_inputs:
            engines = [e for e in engines if e != "browser_agent"]
        if not engines:
            engines = ["playwright", "requests_http"]

        tried: list[str] = []
        best: tuple[int, PipelineResult, str] | None = None

        for eng in engines:
            crawl = {**crawl_base, "force_engine": eng}
            # Agent path: start from original host URL, not SERP rewrite
            run_url = url if eng == "browser_agent" else target
            logger.info(
                "universal.scrape_attempt",
                url=run_url,
                engine=eng,
                site_profile=profile.id,
            )
            tried.append(eng)
            result = self._pipeline.run(
                run_url,
                inputs=job_inputs or None,
                crawl=crawl,
            )
            grade, score = _usefulness(result)
            if best is None or score > best[0]:
                best = (score, result, eng)
            if grade in {"strong", "partial"} and not _is_blocked(result):
                break
            # Keep going if blocked/empty
            if grade == "blocked":
                logger.info("universal.blocked", engine=eng, error=result.error_code)
                continue

        assert best is not None
        score, result, used = best
        grade, _ = _usefulness(result)
        payload = result.normalized_payload or {}
        blocked = _is_blocked(result)

        return UniversalScrapeResult(
            success=bool(result.success) and not blocked and grade not in {"fail", "empty", "blocked"},
            url=target,
            final_url=(result.profile.final_url if result.profile else None),
            site_profile=profile.id,
            engine_used=used,
            engines_tried=tried,
            title=payload.get("title"),
            products=[p for p in (payload.get("products") or []) if isinstance(p, dict)][:100],
            counts=_counts(payload),
            pagination=result.pagination or payload.get("pagination") or {},
            error_code=result.error_code,
            error_message=result.error_message,
            blocked=blocked,
            grade=grade if not blocked else "blocked",
            normalized=payload,
            raw_payload=result.raw_payload or {},
            timings_ms={
                "total_ms": result.timings.total_ms,
                "fetch_ms": result.timings.fetch_ms,
                "plugins_ms": result.timings.plugins_ms,
            },
            notes=profile.notes,
        )


def preset_targets() -> list[dict[str, str]]:
    """Handy list for scrape_all.py."""
    out: list[dict[str, str]] = []
    for p in list_profiles():
        if not p.hosts:
            continue
        host = p.hosts[0]
        if not host.startswith("www.") and "." in host:
            # prefer www when available
            www = next((h for h in p.hosts if h.startswith("www.")), host)
            host = www
        url = f"https://{host}/"
        sample_q = {
            "amazon": "wireless headphones",
            "walmart": "laptop",
            "nike": "running shoes",
            "zara": "jacket",
            "booking": "Paris",
            "airbnb": "Paris",
            "expedia": "New York",
            "tripadvisor": "Paris",
            "imdb": "Inception",
            "figma": "dashboard",
            "books_toscrape": "",
        }.get(p.id, "test")
        out.append({"id": p.id, "url": url, "query": sample_q, "notes": p.notes})
    return out
