# ExtractAI — Level 5–7 Hard Sites Benchmark

**Report date:** 2026-07-20  
**Suite:** Booking, Airbnb, Amazon, Expedia, Nike, Tripadvisor, IMDb, Zara, Figma Community, Walmart  
**Method:** Live `ExtractionPipeline` runs (static HTTP, Playwright, browser-agent search, pagination where enabled)  
**Raw data:** [`docs/level5-7-benchmark-raw.json`](./level5-7-benchmark-raw.json)  
**Harness:** `backend/scripts/benchmark_level57.py`

---

## Bottom line

**No — ExtractAI cannot reliably scrape all of these websites today.**

| Outcome | Count | Sites |
|---------|-------|--------|
| **Usable shell / partial** | 5 (+2 agent variants) | Booking, Airbnb, Amazon, Nike, IMDb |
| **Hard fail (bot wall)** | 5 | Expedia, Tripadvisor, Zara, Figma, Walmart |
| **Full catalog / booking / filter automation** | **0** | — |

Against this Level 5–7 set, ExtractAI is a **marketing-page and shallow HTML extractor**, not a production travel/e‑commerce scraper. Bot walls (CAPTCHA / WAF / 403) block half the suite. On sites that load, plugins rarely emit structured **products/listings**; you mostly get title, links, prices-as-text, images, and nav chrome.

Estimated coverage of *this* suite’s intended capabilities (forms, filters, infinite scroll, deep structured SKUs): **~15–25%**.

---

## Scoreboard (easiest → hardest)

| Rank | Website | Verdict | Strategy used | Time | What we got | What failed |
|------|---------|---------|---------------|------|-------------|-------------|
| 1 | **Amazon.com** (search URL) | **Easiest (partial)** | `static_html` + pagination (2 pages) | ~26 s | Correct SERP title; **803 links**, **62 prices**; pagination followed | **0 products** structured; no filters/sort automation |
| 2 | **IMDb** (agent search) | **Partial + workflow win** | `browser_agent` | ~25 s | Navigated home → **Inception (2010)** page; 298 links | No rich cast/ratings schema; “blocked” string noise in HTML |
| 3 | **Booking.com** | **Partial** | `dynamic_browser` (Playwright) | ~8 s | Homepage shell: 270 links, 83 images, 50 prices, forms/buttons | No hotel search/calendar/filter workflow; no listing cards as products |
| 4 | **Nike** | **Partial** | `metadata` / static | ~7 s | Category title + 380 links + 39 prices | No product grid as `products[]`; filters not driven |
| 5 | **Airbnb** | **Partial / fragile** | `json_ld` / static | ~7 s | Homepage title + links/prices | No listing cards; captcha signals in profile; infinite scroll unused |
| 6 | **IMDb** (find URL) | **Thin–partial** | `dynamic_browser` | ~6 s | Find page title + ~107 links | Thin result rows; no structured titles/years |
| 7 | **Amazon** (agent search) | **Partial / noisy** | `browser_agent` | ~62 s | Landed on a PDP (headphones) | Did not return a clean SERP; access-denied wording in page; 0 products |
| 8 | **Expedia** | **Hard fail** | Playwright | ~7 s | Title: *Bot or Not?* | **CAPTCHA** |
| 9 | **Walmart** | **Hard fail** | Playwright | ~4 s | Title: *Robot or human?* | **CAPTCHA** |
| 10 | **Tripadvisor** | **Hard fail** | static/metadata | ~1.5 s | Empty | **HTTP 403** + captcha profile |
| 11 | **Zara** | **Hard fail** | static | ~0.4 s | *Access Denied* | **WAF 403** |
| 12 | **Figma Community** | **Hard fail** | static | ~1 s | CloudFront error | **WAF 403** |

---

## Capability coverage (this suite)

| Capability | Target sites | Live result |
|------------|--------------|-------------|
| Multi-step forms | Booking, Expedia, Airbnb | **Not automated.** Booking returned a homepage form shell only; Expedia CAPTCHA’d. |
| Search automation | Amazon, IMDb, Tripadvisor | **Mixed.** IMDb agent reached the film page; Amazon agent reached a PDP; Tripadvisor blocked. |
| Filters & sorting | Nike, Walmart, Zara | **Not supported.** Nike gave category HTML only; Walmart/Zara blocked. |
| JavaScript rendering | Airbnb, Nike, Zara, Figma | Playwright used when strategy chose it (Booking, Expedia, IMDb, Walmart). Still fails on CAPTCHA/WAF; static often preferred incorrectly for SPA shells. |
| Infinite scroll | Airbnb, Figma | **Not implemented.** Figma blocked before scroll mattered. |
| Structured data (SKU/reviews) | Amazon, Walmart, IMDb, Tripadvisor | **Weak.** Price-like strings and links appear; `products[]` stayed **0** across all runs; reviews/ratings schema not extracted. |
| Pagination | Amazon, Booking, Walmart | **Amazon: yes (2 pages).** Booking: no `next` on homepage. Walmart: blocked before crawl. |
| Dynamic loading | Zara, Nike, Airbnb | Nike/Airbnb partial HTML only; Zara denied. |
| Navigation workflows | Expedia, Booking, Tripadvisor | Booking shell only; Expedia/Tripadvisor blocked. |
| Performance & resilience | All 10 | Fast on blocks (&lt;2 s); 4–62 s when browsers/agents run. Resilience = detect CAPTCHA/403, **not bypass**. |

---

## Per-site notes

### Easier (relative)

**Amazon (direct SERP URL)** — Best result in the suite. Server HTML is rich enough for links/prices and our new pagination followed page 2. Product plugin did not materialize ASIN cards into `products[]`.

**IMDb (agent)** — Strongest workflow signal: query `Inception` → correct title page. Still not a structured movie extractor.

**Booking / Nike / Airbnb** — Homepage or category chrome loads. Good for SEO/meta/nav dumps; not for inventory or booking flows.

### Hard / not scrapable with current stack

| Site | Blocker |
|------|---------|
| Expedia | CAPTCHA (“Bot or Not?”) even with Playwright |
| Walmart | CAPTCHA (“Robot or human?”) |
| Tripadvisor | HTTP 403 |
| Zara | WAF Access Denied |
| Figma Community | CloudFront / WAF deny |

These need residential proxies, solved CAPTCHAs, sticky sessions, or official APIs — none of which ExtractAI does today.

---

## Can it scrape “all websites”?

| Tier | Examples | Realistic expectation with ExtractAI today |
|------|----------|-----------------------------------------------|
| L1–3 static / light dynamic | example.com, books.toscrape, Wikipedia, HN | **Yes** — strong |
| L4 catalogs with clear DOM/JSON-LD | Many Shopify/blog sites | **Often yes** |
| **L5–7** (this suite) | Booking, Amazon, Nike, Airbnb… | **Shell only or blocked** |
| Bot-walled e-com / travel | Expedia, Walmart, Zara, Figma, Tripadvisor | **No** without anti-bot stack |

**Answer to “is it capable of scraping all these websites?”**  
**No.** About **half hard-fail**. Of the rest, **none** delivered full multi-step / filter / infinite-scroll / structured catalog extraction. Closest wins: Amazon SERP+pagination, IMDb search navigation.

---

## Gaps exposed (priority)

1. **Anti-bot** — CAPTCHA/WAF detection exists; bypass/proxy rotation does not.  
2. **Product/listing plugins** for Amazon/Nike-style cards (ASIN / data attributes / hydration JSON).  
3. **Force Playwright** when intelligence says SPA but static still “wins” on thin shells.  
4. **Infinite scroll** + wait-for-network for Airbnb/Figma-class UIs.  
5. **Form/filter drivers** beyond simple search `inputs.query`.  
6. **Official APIs / partner feeds** for travel and big-box retail when public HTML is hostile.

---

## Comparison vs earlier easy-suite benchmark

| Metric | Easy suite (example/books/wiki/HN) | This L5–7 suite |
|--------|--------------------------------------|-----------------|
| Pipeline completion with useful content | High | Low–medium |
| Structured products | books.toscrape: **20–60** | **0** on all 10 brands |
| Bot walls | Rare | **5/10 hard fails** |
| Pagination | books.toscrape works | Amazon works; others N/A or blocked |

---

## How to reproduce

```bash
cd backend && source .venv/bin/activate
PYTHONPATH=. python scripts/benchmark_level57.py
# → docs/level5-7-benchmark-raw.json
```

Optional API flags used in spirit of the suite: `follow_pagination`, `max_pages`, agent `inputs.query`.
