"""Level 5–7 live scrape benchmark — hard modern public sites."""

from __future__ import annotations

import json
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.engines.pipeline import ExtractionPipeline

TARGETS: list[dict[str, Any]] = [
    {
        "id": "booking",
        "name": "Booking.com",
        "url": "https://www.booking.com/",
        "capabilities": ["multi_step_forms", "filters", "pagination", "navigation"],
        "inputs": None,
        "crawl": {"follow_pagination": True, "max_pages": 2},
    },
    {
        "id": "airbnb",
        "name": "Airbnb",
        "url": "https://www.airbnb.com/",
        "capabilities": ["js_rendering", "filters", "lazy_load", "infinite_scroll"],
        "inputs": None,
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "amazon",
        "name": "Amazon.com",
        "url": "https://www.amazon.com/s?k=wireless+headphones",
        "capabilities": ["search", "filters", "pagination", "structured_data"],
        "inputs": None,
        "crawl": {"follow_pagination": True, "max_pages": 2},
    },
    {
        "id": "amazon_search",
        "name": "Amazon.com (agent search)",
        "url": "https://www.amazon.com/",
        "capabilities": ["search_automation"],
        "inputs": {"query": "wireless headphones"},
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "expedia",
        "name": "Expedia",
        "url": "https://www.expedia.com/",
        "capabilities": ["multi_step_forms", "navigation"],
        "inputs": None,
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "nike",
        "name": "Nike",
        "url": "https://www.nike.com/w/mens-shoes-nik1zy7ok",
        "capabilities": ["js_rendering", "filters", "dynamic_ui"],
        "inputs": None,
        "crawl": {"follow_pagination": True, "max_pages": 2},
    },
    {
        "id": "tripadvisor",
        "name": "Tripadvisor",
        "url": "https://www.tripadvisor.com/Search?q=Paris",
        "capabilities": ["search", "reviews", "nested_content", "structured_data"],
        "inputs": None,
        "crawl": {"follow_pagination": True, "max_pages": 2},
    },
    {
        "id": "imdb",
        "name": "IMDb",
        "url": "https://www.imdb.com/find/?q=Inception",
        "capabilities": ["search", "metadata", "structured_data"],
        "inputs": None,
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "imdb_search",
        "name": "IMDb (agent search)",
        "url": "https://www.imdb.com/",
        "capabilities": ["search_automation"],
        "inputs": {"query": "Inception"},
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "zara",
        "name": "Zara",
        "url": "https://www.zara.com/us/en/",
        "capabilities": ["js_rendering", "dynamic_loading", "product_variations"],
        "inputs": None,
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "figma",
        "name": "Figma Community",
        "url": "https://www.figma.com/community",
        "capabilities": ["infinite_scroll", "js_rendering", "cards", "filters"],
        "inputs": None,
        "crawl": {"follow_pagination": False},
    },
    {
        "id": "walmart",
        "name": "Walmart",
        "url": "https://www.walmart.com/search?q=laptop",
        "capabilities": ["ecommerce", "filters", "pagination", "structured_data"],
        "inputs": None,
        "crawl": {"follow_pagination": True, "max_pages": 2},
    },
]


def _section_counts(payload: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for k, v in (payload or {}).items():
        if isinstance(v, list):
            out[k] = len(v)
        elif isinstance(v, dict):
            if "total" in v and isinstance(v.get("total"), int):
                out[k] = int(v["total"])
            else:
                out[k] = len(v)
        elif v:
            out[k] = 1
    return out


def _bot_signals(html: str, profile: Any) -> dict[str, Any]:
    lower = (html or "").lower()
    signals = {
        "cloudflare_challenge": "cf-browser-verification" in lower or "challenge-platform" in lower,
        "captcha_hint": any(x in lower for x in ("recaptcha", "hcaptcha", "captcha")),
        "access_denied": any(
            x in lower for x in ("access denied", "robot check", "are you a human", "blocked")
        ),
    }
    if profile is not None:
        try:
            signals["profile_bot"] = getattr(profile.bot_protection, "value", None) or str(
                getattr(profile, "bot_protection", None)
            )
            signals["profile_cloudflare"] = bool(getattr(profile.cloudflare, "value", False))
        except Exception:
            pass
    return signals


def _usefulness(counts: dict[str, int], bot: dict[str, Any], success: bool) -> str:
    if not success:
        return "fail"
    if bot.get("cloudflare_challenge") or bot.get("access_denied"):
        return "blocked"
    useful = (
        counts.get("products", 0)
        + counts.get("json_ld", 0)
        + counts.get("tables", 0)
        + min(counts.get("links", 0), 20) // 5
        + min(counts.get("images", 0), 20) // 5
        + counts.get("paragraphs", 0) // 3
    )
    title_ok = counts.get("title", 0) > 0
    if useful >= 12 and title_ok:
        return "strong"
    if useful >= 5 and title_ok:
        return "partial"
    if title_ok or useful >= 2:
        return "thin"
    return "empty"


def run_one(pipe: ExtractionPipeline, target: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    row: dict[str, Any] = {
        "id": target["id"],
        "name": target["name"],
        "url": target["url"],
        "capabilities": target["capabilities"],
        "inputs": target.get("inputs"),
        "crawl": target.get("crawl"),
        "started_at": datetime.now(UTC).isoformat(),
    }
    try:
        result = pipe.run(
            target["url"],
            inputs=target.get("inputs"),
            crawl=target.get("crawl") or {},
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        payload = result.normalized_payload or {}
        counts = _section_counts(payload)
        bot = _bot_signals(result.raw_html or "", result.profile)
        grade = _usefulness(counts, bot, result.success)
        pag = result.pagination or payload.get("pagination") or {}
        row.update(
            {
                "ok": True,
                "pipeline_success": result.success,
                "error_code": result.error_code,
                "error_message": (result.error_message or "")[:500] or None,
                "elapsed_ms": round(elapsed_ms, 1),
                "strategy": result.plan.strategy_id if result.plan else None,
                "fetch_engine": result.plan.fetch_engine if result.plan else None,
                "title": payload.get("title"),
                "counts": counts,
                "products_sample": [
                    {
                        "name": (p.get("name") or "")[:80],
                        "price": p.get("price"),
                        "url": (p.get("url") or "")[:120],
                    }
                    for p in (payload.get("products") or [])[:5]
                    if isinstance(p, dict)
                ],
                "pagination": {
                    "pages_crawled": pag.get("pages_crawled"),
                    "page_urls": (pag.get("page_urls") or [])[:5],
                    "stopped_reason": pag.get("stopped_reason"),
                },
                "bot": bot,
                "grade": grade,
                "html_bytes": len((result.raw_html or "").encode("utf-8", errors="replace")),
            }
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        row.update(
            {
                "ok": False,
                "pipeline_success": False,
                "error_code": "EXCEPTION",
                "error_message": f"{type(exc).__name__}: {exc}"[:800],
                "elapsed_ms": round(elapsed_ms, 1),
                "traceback": traceback.format_exc()[-1500:],
                "grade": "fail",
            }
        )
    return row


def main() -> None:
    pipe = ExtractionPipeline()
    rows: list[dict[str, Any]] = []
    for i, target in enumerate(TARGETS, 1):
        print(f"[{i}/{len(TARGETS)}] {target['name']} …", flush=True)
        row = run_one(pipe, target)
        print(
            f"  → grade={row.get('grade')} success={row.get('pipeline_success')} "
            f"strategy={row.get('strategy')} ms={row.get('elapsed_ms')} "
            f"err={row.get('error_code')}",
            flush=True,
        )
        rows.append(row)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "suite": "level_5_7_hard_sites",
        "targets": rows,
    }
    root = Path(__file__).resolve().parents[2]
    raw_path = root / "docs" / "level5-7-benchmark-raw.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {raw_path}", flush=True)


if __name__ == "__main__":
    main()
