#!/usr/bin/env python3
"""
Scrape the Level 5–7 preset suite (or any listed site profiles) in one go.

Examples:
  PYTHONPATH=. python scripts/scrape_all.py --out-dir /tmp/extract-runs
  PYTHONPATH=. python scripts/scrape_all.py --only amazon,imdb,books_toscrape
  PYTHONPATH=. python scripts/scrape_all.py --list
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch-scrape preset hard/easy sites.")
    parser.add_argument("--out-dir", default="docs/scrape-runs", help="Directory for JSON outputs")
    parser.add_argument("--only", help="Comma-separated profile ids (e.g. amazon,imdb,nike)")
    parser.add_argument("--pages", type=int, default=2, help="Max pages per site")
    parser.add_argument("--list", action="store_true", help="List presets and exit")
    parser.add_argument("--no-cascade", action="store_true")
    args = parser.parse_args(argv)

    from app.scrapers.universal import UniversalScraper, preset_targets

    targets = preset_targets()
    if args.list:
        for t in targets:
            print(f"{t['id']:16} {t['url']}  q={t.get('query')!r}")
            if t.get("notes"):
                print(f"  {t['notes']}")
        return 0

    only = {x.strip() for x in (args.only or "").split(",") if x.strip()}
    if only:
        targets = [t for t in targets if t["id"] in only]

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        # Resolve relative to repo root (parent of backend/)
        out_dir = Path(__file__).resolve().parents[2] / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    scraper = UniversalScraper()
    rows = []
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    for i, t in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {t['id']} …", flush=True)
        started = time.perf_counter()
        result = scraper.scrape(
            t["url"],
            query=t.get("query") or None,
            max_pages=args.pages,
            cascade=not args.no_cascade,
        )
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        row = {
            "id": t["id"],
            "requested_url": t["url"],
            "query": t.get("query"),
            "success": result.success,
            "grade": result.grade,
            "blocked": result.blocked,
            "engine_used": result.engine_used,
            "engines_tried": result.engines_tried,
            "title": result.title,
            "product_count": len(result.products),
            "counts": result.counts,
            "error_code": result.error_code,
            "elapsed_ms": elapsed,
            "notes": result.notes,
        }
        rows.append(row)
        site_path = out_dir / f"{stamp}_{t['id']}.json"
        site_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(
            f"  → {result.grade} products={len(result.products)} "
            f"engine={result.engine_used} err={result.error_code} → {site_path.name}",
            flush=True,
        )

    summary_path = out_dir / f"{stamp}_summary.json"
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "out_dir": str(out_dir),
        "results": rows,
        "totals": {
            "sites": len(rows),
            "success": sum(1 for r in rows if r["success"]),
            "blocked": sum(1 for r in rows if r["blocked"]),
            "with_products": sum(1 for r in rows if r["product_count"] > 0),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary["totals"], indent=2))
    print(f"Summary → {summary_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
