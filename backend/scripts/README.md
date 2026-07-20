# Easy scrape scripts

From `backend/`:

```bash
source .venv/bin/activate
export PYTHONPATH=.

# One URL (auto site profile + engine cascade)
python scripts/scrape.py https://books.toscrape.com/ --pages 3 --pretty

# Search-aware (Amazon / IMDb / Nike / …)
python scripts/scrape.py https://www.amazon.com/ -q "wireless headphones" -o /tmp/amazon.json --pretty

# Batch the hard-site presets
python scripts/scrape_all.py --list
python scripts/scrape_all.py --only amazon,imdb,books_toscrape --pages 2
python scripts/scrape_all.py --out-dir docs/scrape-runs
```

What you get:

- Per-host **presets** (engine, scroll, pagination, search URL)
- **Cascade** (`playwright` ↔ `requests_http` ↔ `browser_agent` when query set)
- Browser-like headers + scroll for SPAs
- Stronger product extraction (Amazon ASINs, hydration JSON, IMDb rows)

Bot walls (CAPTCHA / WAF) still cannot be bypassed without proxies/solvers — the scripts report `blocked` clearly instead of silent empty pages.
