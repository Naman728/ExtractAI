#!/usr/bin/env python3
"""
Easy one-URL scrape CLI with site presets + engine cascade.

Examples:
  PYTHONPATH=. python scripts/scrape.py https://books.toscrape.com/ --pages 3
  PYTHONPATH=. python scripts/scrape.py https://www.amazon.com/ --query "wireless headphones"
  PYTHONPATH=. python scripts/scrape.py https://www.imdb.com/ --query Inception -o /tmp/imdb.json
  PYTHONPATH=. python scripts/scrape.py https://www.nike.com/w/mens-shoes-nik1zy7ok --engine playwright
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured data from any public URL (site presets + cascade)."
    )
    parser.add_argument("url", help="Page URL to scrape")
    parser.add_argument("--query", "-q", help="Search query (uses site search URL when known)")
    parser.add_argument("--pages", type=int, default=None, help="Max pagination pages (default: profile)")
    parser.add_argument(
        "--engine",
        choices=["auto", "requests_http", "playwright", "browser_agent"],
        default="auto",
        help="Force fetch engine (default: auto cascade)",
    )
    parser.add_argument("--no-cascade", action="store_true", help="Only try one engine")
    parser.add_argument("--no-pagination", action="store_true", help="Disable pagination follow")
    parser.add_argument("--scroll", type=int, default=None, help="Playwright scroll rounds")
    parser.add_argument("--out", "-o", help="Write full JSON result to this path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON to stdout")
    args = parser.parse_args(argv)

    from app.scrapers.universal import UniversalScraper

    scraper = UniversalScraper()
    result = scraper.scrape(
        args.url,
        query=args.query,
        max_pages=args.pages,
        engine=None if args.engine == "auto" else args.engine,
        follow_pagination=False if args.no_pagination else None,
        scroll_rounds=args.scroll,
        cascade=not args.no_cascade,
    )

    summary = {
        "success": result.success,
        "grade": result.grade,
        "blocked": result.blocked,
        "site_profile": result.site_profile,
        "engine_used": result.engine_used,
        "engines_tried": result.engines_tried,
        "url": result.url,
        "title": result.title,
        "counts": result.counts,
        "products": result.products[:25],
        "pagination": result.pagination,
        "error_code": result.error_code,
        "error_message": result.error_message,
        "timings_ms": result.timings_ms,
        "notes": result.notes,
    }

    text = json.dumps(summary, indent=2 if args.pretty else None, ensure_ascii=False)
    print(text)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Wrote full payload → {path}", file=sys.stderr)

    return 0 if result.success or result.grade in {"partial", "thin"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
