"""Builtin extraction plugins — one module per concern where practical."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from app.plugins.base import ExtractionPlugin, PluginContext, PluginResult

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{3,4}"
)
_PRICE_RE = re.compile(
    r"(?:USD|EUR|GBP|INR|\$|€|£|₹)\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|INR)"
)


class TitlePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "title"

    def section(self) -> str:
        return "title"

    def priority(self) -> int:
        return 100

    def extract(self, ctx: PluginContext) -> PluginResult:
        tag = ctx.soup.find("title")
        value = tag.get_text(strip=True) if tag else None
        return PluginResult(self.name(), self.section(), value, 0.95 if value else 0.0, ["title"])


class MetaPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "meta"

    def section(self) -> str:
        return "meta"

    def priority(self) -> int:
        return 95

    def extract(self, ctx: PluginContext) -> PluginResult:
        desc = ctx.soup.find("meta", attrs={"name": re.compile("description", re.I)})
        keywords = ctx.soup.find("meta", attrs={"name": re.compile("keywords", re.I)})
        data = {
            "description": desc.get("content") if desc else None,
            "keywords": keywords.get("content") if keywords else None,
        }
        return PluginResult(self.name(), self.section(), data, 0.9 if desc else 0.5)


class HeadingPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "headings"

    def section(self) -> str:
        return "headings"

    def extract(self, ctx: PluginContext) -> PluginResult:
        items = []
        for level in range(1, 7):
            for tag in ctx.soup.find_all(f"h{level}"):
                text = tag.get_text(" ", strip=True)
                if text:
                    items.append({"level": level, "text": text})
        return PluginResult(self.name(), self.section(), items, 0.9 if items else 0.4)


class ParagraphPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "paragraphs"

    def section(self) -> str:
        return "paragraphs"

    def extract(self, ctx: PluginContext) -> PluginResult:
        paras = []
        for p in ctx.soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if len(text) >= 25:
                paras.append(text)
        return PluginResult(self.name(), self.section(), paras[:200], 0.85 if paras else 0.3)


class ImagePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "images"

    def section(self) -> str:
        return "images"

    def extract(self, ctx: PluginContext) -> PluginResult:
        images = []
        seen = set()
        for img in ctx.soup.find_all("img"):
            candidates = [
                img.get("src"),
                img.get("data-src"),
                img.get("data-lazy-src"),
                img.get("data-original"),
            ]
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                # take largest candidate from srcset
                parts = [p.strip().split(" ")[0] for p in srcset.split(",") if p.strip()]
                candidates.extend(parts)
            src = next((c for c in candidates if c), None)
            if not src:
                continue
            abs_url = urljoin(ctx.final_url, src)
            if abs_url in seen or abs_url.startswith("data:"):
                continue
            seen.add(abs_url)
            images.append(
                {
                    "url": abs_url,
                    "alt": img.get("alt"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                }
            )
        return PluginResult(self.name(), self.section(), images[:300], 0.9 if images else 0.4)


class LinkPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "links"

    def section(self) -> str:
        return "links"

    def extract(self, ctx: PluginContext) -> PluginResult:
        links = []
        seen = set()
        for a in ctx.soup.find_all("a", href=True):
            href = urljoin(ctx.final_url, a["href"])
            if href in seen or href.startswith(("javascript:", "mailto:", "tel:")):
                continue
            seen.add(href)
            links.append({"url": href, "text": a.get_text(" ", strip=True)[:200]})
        return PluginResult(self.name(), self.section(), links[:500], 0.9 if links else 0.4)


class TablePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "tables"

    def section(self) -> str:
        return "tables"

    def extract(self, ctx: PluginContext) -> PluginResult:
        tables = []
        for table in ctx.soup.find_all("table")[:30]:
            rows = []
            for tr in table.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({"rows": rows})
        return PluginResult(self.name(), self.section(), tables, 0.9 if tables else 0.5)


class EmailPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "emails"

    def section(self) -> str:
        return "emails"

    def extract(self, ctx: PluginContext) -> PluginResult:
        found = sorted(set(_EMAIL_RE.findall(ctx.html or "")))
        # also mailto
        for a in ctx.soup.find_all("a", href=True):
            if a["href"].lower().startswith("mailto:"):
                found.append(a["href"].split(":", 1)[1].split("?")[0])
        emails = sorted({e.strip() for e in found if e})
        return PluginResult(self.name(), self.section(), emails[:100], 0.85 if emails else 0.5)


class PhonePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "phones"

    def section(self) -> str:
        return "phones"

    def extract(self, ctx: PluginContext) -> PluginResult:
        phones = []
        for a in ctx.soup.find_all("a", href=True):
            if a["href"].lower().startswith("tel:"):
                phones.append(a["href"].split(":", 1)[1])
        text = ctx.soup.get_text(" ", strip=True)
        phones.extend(_PHONE_RE.findall(text))
        # crude filter
        cleaned = []
        for p in phones:
            digits = re.sub(r"\D", "", p)
            if 7 <= len(digits) <= 15:
                cleaned.append(p.strip())
        unique = list(dict.fromkeys(cleaned))[:100]
        return PluginResult(self.name(), self.section(), unique, 0.7 if unique else 0.4)


class JSONLDPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "json_ld"

    def section(self) -> str:
        return "json_ld"

    def priority(self) -> int:
        return 90

    def extract(self, ctx: PluginContext) -> PluginResult:
        blocks = []
        for script in ctx.soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            try:
                blocks.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        return PluginResult(self.name(), self.section(), blocks, 0.95 if blocks else 0.5)


class OpenGraphPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "open_graph"

    def section(self) -> str:
        return "open_graph"

    def extract(self, ctx: PluginContext) -> PluginResult:
        og = {}
        for tag in ctx.soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
            if tag.get("property") and tag.get("content"):
                og[tag["property"]] = tag["content"]
        return PluginResult(self.name(), self.section(), og, 0.95 if og else 0.5)


class TwitterCardPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "twitter"

    def section(self) -> str:
        return "twitter"

    def extract(self, ctx: PluginContext) -> PluginResult:
        tw = {}
        for tag in ctx.soup.find_all("meta", attrs={"name": re.compile(r"^twitter:", re.I)}):
            if tag.get("name") and tag.get("content"):
                tw[tag["name"]] = tag["content"]
        return PluginResult(self.name(), self.section(), tw, 0.95 if tw else 0.5)


class CanonicalPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "canonical_url"

    def section(self) -> str:
        return "canonical_url"

    def extract(self, ctx: PluginContext) -> PluginResult:
        link = ctx.soup.find("link", rel=lambda v: v and "canonical" in v)
        value = urljoin(ctx.final_url, link["href"]) if link and link.get("href") else None
        return PluginResult(self.name(), self.section(), value, 0.95 if value else 0.3)


class LanguagePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "language"

    def section(self) -> str:
        return "language"

    def extract(self, ctx: PluginContext) -> PluginResult:
        html = ctx.soup.find("html")
        lang = html.get("lang") if html else None
        return PluginResult(self.name(), self.section(), lang, 0.9 if lang else 0.3)


class FormPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "forms"

    def section(self) -> str:
        return "forms"

    def extract(self, ctx: PluginContext) -> PluginResult:
        forms = []
        for form in ctx.soup.find_all("form")[:50]:
            inputs = [
                {"name": i.get("name"), "type": i.get("type", "text")}
                for i in form.find_all(["input", "textarea", "select"])
            ]
            forms.append(
                {
                    "action": urljoin(ctx.final_url, form.get("action") or ""),
                    "method": (form.get("method") or "get").upper(),
                    "inputs": inputs[:40],
                }
            )
        return PluginResult(self.name(), self.section(), forms, 0.9 if forms else 0.5)


class ButtonPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "buttons"

    def section(self) -> str:
        return "buttons"

    def extract(self, ctx: PluginContext) -> PluginResult:
        buttons = []
        for el in ctx.soup.find_all(["button", "input"]):
            if el.name == "input" and (el.get("type") or "").lower() not in {
                "button",
                "submit",
                "reset",
            }:
                continue
            text = el.get_text(" ", strip=True) or el.get("value") or el.get("aria-label")
            if text:
                buttons.append({"text": text[:120], "type": el.get("type")})
        # dedupe
        unique = []
        seen = set()
        for b in buttons:
            key = (b["text"], b.get("type"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(b)
        return PluginResult(self.name(), self.section(), unique[:200], 0.8 if unique else 0.4)


class DownloadPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "downloads"

    def section(self) -> str:
        return "downloads"

    def extract(self, ctx: PluginContext) -> PluginResult:
        exts = (".pdf", ".csv", ".xlsx", ".xls", ".zip", ".doc", ".docx", ".ppt", ".pptx")
        files = []
        for a in ctx.soup.find_all("a", href=True):
            href = urljoin(ctx.final_url, a["href"])
            path = urlparse(href).path.lower()
            if any(path.endswith(ext) for ext in exts):
                files.append({"url": href, "text": a.get_text(" ", strip=True)[:120]})
        return PluginResult(self.name(), self.section(), files[:100], 0.9 if files else 0.5)


class ListPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "lists"

    def section(self) -> str:
        return "lists"

    def extract(self, ctx: PluginContext) -> PluginResult:
        lists = []
        for ul in ctx.soup.find_all(["ul", "ol"])[:40]:
            items = [li.get_text(" ", strip=True) for li in ul.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                lists.append({"ordered": ul.name == "ol", "items": items[:100]})
        return PluginResult(self.name(), self.section(), lists, 0.85 if lists else 0.4)


class ProductPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "products"

    def section(self) -> str:
        return "products"

    def priority(self) -> int:
        return 40

    def extract(self, ctx: PluginContext) -> PluginResult:
        products = []

        def _image_url(value):
            if isinstance(value, str) and value.startswith("http"):
                return value
            if isinstance(value, list) and value:
                return _image_url(value[0])
            if isinstance(value, dict):
                for k in ("url", "contentUrl", "@id", "src"):
                    if isinstance(value.get(k), str) and value[k].startswith("http"):
                        return value[k]
            return None

        def _offer(item):
            offers = item.get("offers")
            offer_list = offers if isinstance(offers, list) else [offers] if offers else []
            for offer in offer_list:
                if isinstance(offer, dict) and offer.get("price") is not None:
                    return str(offer.get("price")), offer.get("priceCurrency")
            return None, None

        def _walk(node, sink):
            if isinstance(node, list):
                for x in node:
                    _walk(x, sink)
                return
            if not isinstance(node, dict):
                return
            if node.get("@graph"):
                _walk(node["@graph"], sink)
            types = node.get("@type")
            type_list = types if isinstance(types, list) else [types]
            lowered = {str(t).lower() for t in type_list if t}
            if lowered & {"product", "individualproduct", "productmodel", "book", "ebook"}:
                price, currency = _offer(node)
                img = _image_url(node.get("image"))
                sink.append(
                    {
                        "name": node.get("name"),
                        "sku": node.get("sku"),
                        "description": node.get("description"),
                        "image": img,
                        "url": node.get("url"),
                        "price": price,
                        "currency": currency,
                        "type": "book" if lowered & {"book", "ebook"} else "product",
                        "source": "json_ld",
                    }
                )

        # From JSON-LD (products + books, with offers/price)
        for script in ctx.soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            _walk(data, products)

        # Embedded hydration / Next.js / JSON blobs
        for script in ctx.soup.find_all("script", id=True):
            sid = (script.get("id") or "").lower()
            if sid not in {"__next_data__", "__nuxt_data__", "__apollo_state__"}:
                continue
            raw = script.string or script.get_text() or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            _harvest_json_products(data, products, ctx.final_url)

        for script in ctx.soup.find_all("script", attrs={"type": "application/json"}):
            raw = (script.string or script.get_text() or "").strip()
            if not raw or len(raw) < 20 or len(raw) > 2_000_000:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            _harvest_json_products(data, products, ctx.final_url)

        # Amazon SERP cards
        for card in ctx.soup.select('div[data-asin]:not([data-asin=""])')[:60]:
            asin = (card.get("data-asin") or "").strip()
            if not asin or len(asin) < 8:
                continue
            title_el = card.select_one("h2 a span, h2 span, h2 a")
            name = title_el.get_text(" ", strip=True) if title_el else ""
            if len(name) < 3:
                continue
            link_el = card.select_one("h2 a[href], a.a-link-normal[href]")
            url = urljoin(ctx.final_url, link_el["href"]) if link_el and link_el.get("href") else None
            img_el = card.select_one("img.s-image, img[data-image-latency], img")
            img = None
            if img_el:
                src = img_el.get("src") or img_el.get("data-src")
                if src:
                    img = urljoin(ctx.final_url, src)
            price = None
            price_el = card.select_one(".a-price .a-offscreen, .a-price-whole")
            if price_el:
                price = price_el.get_text(" ", strip=True)
            products.append(
                {
                    "name": name[:200],
                    "sku": asin,
                    "image": img,
                    "url": url,
                    "price": price,
                    "type": "product",
                    "source": "amazon_dom",
                }
            )

        # IMDb find / title list rows
        for row in ctx.soup.select(
            ".ipc-metadata-list-summary-item, .find-title-result, .findResult, "
            "li.ipc-metadata-list-summary-item"
        )[:50]:
            a = row.select_one("a.ipc-metadata-list-summary-item__t, a.result_text, a[href*='/title/']")
            if not a:
                continue
            name = a.get_text(" ", strip=True)
            if len(name) < 2:
                continue
            href = a.get("href") or ""
            products.append(
                {
                    "name": name[:200],
                    "url": urljoin(ctx.final_url, href),
                    "type": "title",
                    "source": "imdb_dom",
                }
            )

        # DOM cards: name + image + link + nearby price
        for card in ctx.soup.select(
            "[class*='product'], [class*='Product'], [itemtype*='Product'], "
            "article.product_pod, [class*='book'], [data-product], "
            "[class*='product-card'], [class*='ProductCard'], [data-testid*='product'], "
            "[class*='listing'], [class*='ListingCard'], [class*='item-card']"
        )[:80]:
            name = None
            # Prefer explicit titles first (CSS multi-selector is document-order, not list-order)
            for el in card.select("a[title], [itemprop='name']"):
                name = (el.get("title") or el.get_text(" ", strip=True) or "").strip()
                if len(name) >= 3:
                    break
            if not name:
                for el in card.select("h1, h2, h3, h4"):
                    # Prefer nested titled link inside heading
                    titled = el.find("a", title=True)
                    if titled and titled.get("title"):
                        name = titled["title"].strip()
                    else:
                        name = el.get_text(" ", strip=True)
                    if name and len(name) >= 3:
                        break
            if not name or len(name) < 3:
                continue
            # img alt as last-resort full title
            if name.endswith("..."):
                img_alt = card.find("img")
                if img_alt and img_alt.get("alt") and len(img_alt["alt"]) > len(name):
                    name = img_alt["alt"].strip()
            # Skip price-only containers mistaken for cards
            classes = " ".join(card.get("class") or []).lower()
            if "price" in classes and "product" in classes and not card.find(["h1", "h2", "h3", "h4"]):
                continue
            img_el = card.find("img")
            img = None
            if img_el:
                src = (
                    img_el.get("src")
                    or img_el.get("data-src")
                    or img_el.get("data-lazy-src")
                    or img_el.get("data-original")
                )
                if src:
                    img = urljoin(ctx.final_url, src)
            link_el = None
            for a in card.find_all("a", href=True):
                # Prefer the title/name link over the image link
                if a.get("title") or (a.get_text(" ", strip=True) and len(a.get_text(" ", strip=True)) > 2):
                    link_el = a
                    break
            if link_el is None:
                link_el = card.find("a", href=True)
            url = urljoin(ctx.final_url, link_el["href"]) if link_el else None
            price = None
            price_el = card.select_one(".price_color, [itemprop='price']")
            if price_el:
                price = (price_el.get("content") or price_el.get_text(" ", strip=True) or "").strip()
            if not price:
                m = _PRICE_RE.search(card.get_text(" ", strip=True))
                if m:
                    price = m.group(0)
            products.append(
                {
                    "name": name[:200],
                    "image": img,
                    "url": url,
                    "price": price,
                    "type": "book" if "book" in classes or "product_pod" in classes else "product",
                    "source": "dom",
                }
            )

        # dedupe by name
        seen = set()
        unique = []
        for p in products:
            key = (p.get("name") or "").lower()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(p)
        return PluginResult(self.name(), self.section(), unique[:120], 0.8 if unique else 0.4)


def _harvest_json_products(node, sink: list, base_url: str, depth: int = 0) -> None:
    """Best-effort walk of hydration JSON for product-like dicts."""
    if depth > 8 or node is None:
        return
    if isinstance(node, list):
        for item in node[:200]:
            _harvest_json_products(item, sink, base_url, depth + 1)
        return
    if not isinstance(node, dict):
        return

    name = node.get("name") or node.get("title") or node.get("productName") or node.get("product_title")
    price = node.get("price") or node.get("priceAmount") or node.get("currentPrice")
    if isinstance(price, dict):
        price = price.get("value") or price.get("amount") or price.get("raw")
    url = node.get("url") or node.get("link") or node.get("pdpUrl") or node.get("productUrl")
    image = node.get("image") or node.get("imageUrl") or node.get("thumbnail")
    if isinstance(image, list) and image:
        image = image[0]
    if isinstance(image, dict):
        image = image.get("url") or image.get("src")

    name_s = str(name).strip() if name else ""
    if name_s and len(name_s) >= 3 and (
        price is not None
        or node.get("asin")
        or node.get("sku")
        or node.get("productId")
        or (isinstance(url, str) and ("/dp/" in url or "/product" in url or "/p/" in url))
    ):
        sink.append(
            {
                "name": name_s[:200],
                "sku": node.get("asin") or node.get("sku") or node.get("productId"),
                "price": str(price) if price is not None else None,
                "currency": node.get("currency") or node.get("priceCurrency"),
                "url": urljoin(base_url, url) if isinstance(url, str) else None,
                "image": urljoin(base_url, image) if isinstance(image, str) else None,
                "type": "product",
                "source": "hydration_json",
            }
        )

    # Prefer diving into common product containers first
    for key in ("products", "items", "results", "searchResults", "props", "pageProps", "data"):
        if key in node:
            _harvest_json_products(node[key], sink, base_url, depth + 1)
    if depth < 4:
        for key, val in list(node.items())[:40]:
            if key in {"products", "items", "results", "searchResults", "props", "pageProps", "data"}:
                continue
            if isinstance(val, (dict, list)):
                _harvest_json_products(val, sink, base_url, depth + 1)


class PricePlugin(ExtractionPlugin):
    def name(self) -> str:
        return "prices"

    def section(self) -> str:
        return "prices"

    def priority(self) -> int:
        return 35

    def extract(self, ctx: PluginContext) -> PluginResult:
        prices = []
        # JSON-LD offers
        for script in ctx.soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                offers = item.get("offers")
                offer_list = offers if isinstance(offers, list) else [offers] if offers else []
                for offer in offer_list:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        prices.append(
                            {
                                "raw": str(offer.get("price")),
                                "currency": offer.get("priceCurrency"),
                                "source": "json_ld",
                            }
                        )
        text = ctx.soup.get_text(" ", strip=True)
        for match in _PRICE_RE.findall(text)[:50]:
            prices.append({"raw": match, "currency": None, "source": "text"})
        return PluginResult(self.name(), self.section(), prices[:80], 0.75 if prices else 0.4)


class FaviconPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "favicon"

    def section(self) -> str:
        return "favicon"

    def extract(self, ctx: PluginContext) -> PluginResult:
        for link in ctx.soup.find_all("link", href=True):
            rel = " ".join(link.get("rel") or []).lower() if isinstance(link.get("rel"), list) else str(link.get("rel") or "").lower()
            if "icon" in rel:
                return PluginResult(
                    self.name(),
                    self.section(),
                    urljoin(ctx.final_url, link["href"]),
                    0.9,
                )
        return PluginResult(self.name(), self.section(), urljoin(ctx.final_url, "/favicon.ico"), 0.5)


class SocialLinksPlugin(ExtractionPlugin):
    def name(self) -> str:
        return "social_links"

    def section(self) -> str:
        return "social_links"

    def extract(self, ctx: PluginContext) -> PluginResult:
        hosts = {
            "twitter.com": "twitter",
            "x.com": "twitter",
            "facebook.com": "facebook",
            "instagram.com": "instagram",
            "linkedin.com": "linkedin",
            "youtube.com": "youtube",
            "github.com": "github",
        }
        found = []
        seen = set()
        for a in ctx.soup.find_all("a", href=True):
            href = urljoin(ctx.final_url, a["href"])
            host = (urlparse(href).hostname or "").lower().removeprefix("www.")
            for domain, platform in hosts.items():
                if host == domain or host.endswith("." + domain):
                    if href in seen:
                        break
                    seen.add(href)
                    found.append({"platform": platform, "url": href})
                    break
        return PluginResult(self.name(), self.section(), found, 0.85 if found else 0.5)
