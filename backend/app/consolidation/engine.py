"""
Build a project-ready payload where each entity is ONE dictionary.

Flat plugin sections (products, prices, images, links, officials, json_ld, …)
are joined into self-contained records that can be copied straight into an app.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_IMAGE_KEY = re.compile(r"(image|img|thumbnail|thumb|photo|picture|cover|logo|avatar)", re.I)
_BOOK_TYPES = {"book", "ebook", "publication"}
_PRODUCT_TYPES = {"product", "individualproduct", "productmodel", "productgroup"}
_PERSON_TYPES = {"person"}
_ORG_TYPES = {"organization", "corporation", "localbusiness", "store"}


def consolidate(
    normalized: dict[str, Any] | None,
    *,
    url: str | None = None,
    ai: dict[str, Any] | None = None,
) -> dict[str, Any]:
    n = normalized if isinstance(normalized, dict) else {}
    ai = ai if isinstance(ai, dict) else {}

    images = _as_images(n.get("images"))
    links = _as_links(n.get("links"))
    prices = n.get("prices") if isinstance(n.get("prices"), list) else []

    products_all = _build_products(n.get("products") or [], prices, images, links, n.get("json_ld") or [])
    books_from_ld = _build_books_from_json_ld(n.get("json_ld") or [], images, links)
    # Split product records tagged as books into the books group
    products: list[dict[str, Any]] = []
    books: list[dict[str, Any]] = list(books_from_ld)
    seen_books = {str(b.get("name") or "").lower() for b in books}
    for p in products_all:
        if str(p.get("type") or "").lower() == "book":
            key = str(p.get("name") or "").lower()
            if key and key not in seen_books:
                seen_books.add(key)
                books.append({**p, "title": p.get("name"), "type": "book"})
            continue
        products.append(p)
    officials = _build_officials(n.get("officials"), images, links)
    people = _merge_people(officials, ai)
    organizations = _from_ai_list((ai.get("entities") or {}).get("organizations"), "organizations")
    locations = _from_ai_list((ai.get("entities") or {}).get("locations"), "locations")
    downloads = _clean_list(n.get("downloads") or [])
    tables = _clean_list(n.get("tables") or [])
    forms = _clean_list(n.get("forms") or [])

    # Lists that look like entity catalogs (name-like items)
    catalog_items = _lists_as_items(n.get("lists") or [])

    entities: dict[str, list[dict[str, Any]]] = {}
    for key, records in (
        ("officials", officials),
        ("products", products),
        ("books", books),
        ("people", people),
        ("organizations", organizations),
        ("locations", locations),
        ("downloads", downloads),
        ("tables", tables),
        ("forms", forms),
        ("catalog_items", catalog_items),
    ):
        cleaned = [_clean(r) for r in records if isinstance(r, dict) and _clean(r)]
        if cleaned:
            entities[key] = cleaned

    source = _clean(
        {
            "url": url or n.get("canonical_url"),
            "title": n.get("title"),
            "language": n.get("language"),
            "canonical_url": n.get("canonical_url"),
            "favicon": n.get("favicon"),
            "description": (n.get("meta") or {}).get("description")
            if isinstance(n.get("meta"), dict)
            else None,
            "keywords": (n.get("meta") or {}).get("keywords")
            if isinstance(n.get("meta"), dict)
            else None,
            "open_graph": n.get("open_graph") if isinstance(n.get("open_graph"), dict) else None,
        }
    )

    contacts = _clean(
        {
            "emails": n.get("emails") or [],
            "phones": n.get("phones") or [],
            "social_links": n.get("social_links") or [],
        }
    )

    bp = ai.get("business_profile") if isinstance(ai.get("business_profile"), dict) else None

    ready = _clean(
        {
            "source": source,
            "summary": ai.get("summary"),
            "category": ai.get("category"),
            "business_profile": _clean(bp) if bp else None,
            "entities": entities,
            "media": _clean({"images": images[:80]}),
            "links": links[:80],
            "contacts": contacts if any(contacts.values()) else None,
            "agent": n.get("agent") if isinstance(n.get("agent"), dict) and n.get("agent") else None,
            "counts": {k: len(v) for k, v in entities.items()},
        }
    )
    return ready


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if v is None:
                continue
            if isinstance(v, str) and not v.strip():
                continue
            if isinstance(v, (list, dict)) and not v:
                continue
            cleaned = _clean(v)
            if cleaned is None or cleaned == {} or cleaned == []:
                continue
            out[k] = cleaned
        return out
    if isinstance(obj, list):
        return [c for c in (_clean(x) for x in obj) if c not in (None, {}, [])]
    return obj


def _as_images(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("src")
        if not isinstance(url, str) or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        out.append(
            {
                "url": url,
                "alt": item.get("alt") if isinstance(item.get("alt"), str) else None,
            }
        )
    return out


def _as_links(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            url, text = item, None
        elif isinstance(item, dict):
            url, text = item.get("url"), item.get("text")
        else:
            continue
        if not isinstance(url, str) or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "text": text if isinstance(text, str) else None})
    return out


def _clean_price(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    m = re.search(r"(?:USD|EUR|GBP|INR|\$|€|£|₹)\s*[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s*(?:USD|EUR|GBP|INR)", text, re.I)
    if m:
        return m.group(0).strip()
    m2 = re.search(r"[\$€£₹]\s*[\d,]+(?:\.\d+)?", text)
    return m2.group(0).strip() if m2 else text[:40]


def _image_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("http"):
        return value
    if isinstance(value, list) and value:
        return _image_url(value[0])
    if isinstance(value, dict):
        for k in ("url", "contentUrl", "@id", "src"):
            if isinstance(value.get(k), str) and value[k].startswith("http"):
                return value[k]
    return None


def _offer_price(offers: Any) -> tuple[str | None, str | None]:
    offer_list = offers if isinstance(offers, list) else [offers] if offers else []
    for offer in offer_list:
        if not isinstance(offer, dict):
            continue
        price = offer.get("price")
        currency = offer.get("priceCurrency") or offer.get("currency")
        if price is not None:
            return str(price), str(currency).upper() if currency else None
    return None, None


def _types(item: dict[str, Any]) -> set[str]:
    raw = item.get("@type")
    vals = raw if isinstance(raw, list) else [raw]
    return {str(t).lower() for t in vals if t}


def _walk_json_ld(blocks: list[Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for x in node:
                walk(x)
            return
        if not isinstance(node, dict):
            return
        if node.get("@type"):
            found.append(node)
        if isinstance(node.get("@graph"), list):
            walk(node["@graph"])
        for v in node.values():
            if isinstance(v, (dict, list)) and v is not node.get("@graph"):
                # shallow — avoid deep recursion on huge trees via @graph only + top
                pass

    for block in blocks:
        walk(block)
        if isinstance(block, dict) and isinstance(block.get("@graph"), list):
            for g in block["@graph"]:
                if isinstance(g, dict):
                    found.append(g)
    # dedupe by id/name
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in found:
        key = str(item.get("@id") or item.get("name") or id(item))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _match_media(name: str, images: list[dict[str, Any]], links: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    if not name:
        return [], []
    lname = name.lower()
    tokens = [t for t in re.split(r"\W+", lname) if len(t) >= 4][:4]
    rel_imgs: list[str] = []
    for im in images:
        alt = (im.get("alt") or "").lower()
        path = urlparse(im.get("url") or "").path.lower()
        blob = f"{alt} {path}"
        if lname in blob or any(t in blob for t in tokens):
            rel_imgs.append(im["url"])
    rel_links: list[dict[str, Any]] = []
    for link in links:
        text = (link.get("text") or "").lower()
        path = urlparse(link.get("url") or "").path.lower()
        blob = f"{text} {path}"
        if lname in blob or any(t in blob for t in tokens):
            rel_links.append(link)
    return rel_imgs[:5], rel_links[:5]


def _build_products(
    products: list[Any],
    prices: list[Any],
    images: list[dict[str, Any]],
    links: list[dict[str, Any]],
    json_ld: list[Any],
) -> list[dict[str, Any]]:
    # Seed from JSON-LD Product nodes (includes offers)
    by_name: dict[str, dict[str, Any]] = {}

    def upsert(rec: dict[str, Any]) -> None:
        name = str(rec.get("name") or "").strip()
        if not name:
            return
        key = name.lower()
        if key not in by_name:
            by_name[key] = rec
            return
        existing = by_name[key]
        for k, v in rec.items():
            if v is None or v == "" or v == []:
                continue
            if existing.get(k) in (None, "", []):
                existing[k] = v

    for node in _walk_json_ld(json_ld):
        types = _types(node)
        if not (types & _PRODUCT_TYPES):
            continue
        price, currency = _offer_price(node.get("offers"))
        img = _image_url(node.get("image"))
        upsert(
            {
                "name": node.get("name"),
                "description": node.get("description"),
                "sku": node.get("sku"),
                "brand": (node.get("brand") or {}).get("name")
                if isinstance(node.get("brand"), dict)
                else node.get("brand"),
                "url": node.get("url"),
                "image": img,
                "images": [img] if img else [],
                "price": price,
                "currency": currency,
                "type": "product",
                "source": "json_ld",
            }
        )

    for item in products:
        if not isinstance(item, dict):
            continue
        img = _image_url(item.get("image"))
        upsert(
            {
                "name": item.get("name"),
                "description": item.get("description"),
                "sku": item.get("sku"),
                "url": item.get("url"),
                "image": img,
                "images": [img] if img else [],
                "price": item.get("price"),
                "currency": item.get("currency"),
                "type": item.get("type") or "product",
                "source": item.get("source") or "plugins",
            }
        )

    # Attach orphan prices by order when products lack price
    price_pool = [p for p in prices if isinstance(p, dict)]
    pi = 0
    for rec in by_name.values():
        if rec.get("price") is None and pi < len(price_pool):
            p = price_pool[pi]
            rec["price"] = p.get("amount") or p.get("raw")
            rec["currency"] = rec.get("currency") or p.get("currency")
            pi += 1
        if rec.get("price"):
            rec["price"] = _clean_price(rec.get("price"))
        name = str(rec.get("name") or "")
        rel_imgs, rel_links = _match_media(name, images, links)
        if rel_imgs:
            existing = list(rec.get("images") or [])
            for u in rel_imgs:
                if u not in existing:
                    existing.append(u)
            rec["images"] = existing
            if not rec.get("image") and existing:
                rec["image"] = existing[0]
        if rel_links and not rec.get("links"):
            rec["links"] = rel_links
        if not rec.get("url") and rel_links:
            rec["url"] = rel_links[0].get("url")

    return list(by_name.values())


def _build_books_from_json_ld(
    json_ld: list[Any],
    images: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    books: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in _walk_json_ld(json_ld):
        if not (_types(node) & _BOOK_TYPES):
            continue
        name = str(node.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        img = _image_url(node.get("image"))
        author = node.get("author")
        if isinstance(author, list) and author:
            author = author[0]
        if isinstance(author, dict):
            author = author.get("name")
        rel_imgs, rel_links = _match_media(name, images, links)
        images_out = ([img] if img else []) + [u for u in rel_imgs if u != img]
        books.append(
            {
                "name": name,
                "title": name,
                "author": author,
                "isbn": node.get("isbn"),
                "description": node.get("description"),
                "url": node.get("url"),
                "image": img or (images_out[0] if images_out else None),
                "images": images_out[:5],
                "links": rel_links,
                "price": _offer_price(node.get("offers"))[0],
                "currency": _offer_price(node.get("offers"))[1],
                "type": "book",
                "source": "json_ld",
            }
        )
    return books


def _build_officials(
    officials: Any,
    images: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(officials, dict):
        return []
    items = officials.get("all") if isinstance(officials.get("all"), list) else []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        rel_imgs, rel_links = _match_media(name, images, links)
        out.append(
            {
                "name": name,
                "office": item.get("office"),
                "level": item.get("level"),
                "image": rel_imgs[0] if rel_imgs else None,
                "images": rel_imgs,
                "links": rel_links,
                "type": "official",
                "source": "workflow",
            }
        )
    return out


def _merge_people(officials: list[dict[str, Any]], ai: dict[str, Any]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for o in officials:
        key = str(o.get("name") or "").lower()
        if key:
            by_name[key] = {
                "name": o.get("name"),
                "role": o.get("office"),
                "level": o.get("level"),
                "image": o.get("image"),
                "images": o.get("images"),
                "links": o.get("links"),
                "type": "person",
                "source": "officials",
            }
    for p in (ai.get("entities") or {}).get("people") or []:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in by_name:
            if p.get("role") and not by_name[key].get("role"):
                by_name[key]["role"] = p.get("role")
            continue
        by_name[key] = {
            "name": name,
            "role": p.get("role"),
            "type": "person",
            "source": "ai",
        }
    return list(by_name.values())


def _from_ai_list(items: Any, kind: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rec = dict(item)
        rec.setdefault("type", kind.rstrip("s"))
        rec.setdefault("source", "ai")
        out.append(rec)
    return out


def _clean_list(items: list[Any]) -> list[dict[str, Any]]:
    return [x for x in items if isinstance(x, dict)]


def _lists_as_items(lists: list[Any]) -> list[dict[str, Any]]:
    """Turn meaningful list blocks into copyable item dicts when no products exist."""
    out: list[dict[str, Any]] = []
    for block in lists[:20]:
        if not isinstance(block, dict):
            continue
        items = block.get("items") if isinstance(block.get("items"), list) else []
        # Prefer short catalog-like lists
        if not (2 <= len(items) <= 40):
            continue
        for text in items:
            if not isinstance(text, str):
                continue
            t = text.strip()
            if 2 < len(t) < 180:
                out.append({"name": t, "type": "list_item", "source": "lists"})
        if len(out) >= 80:
            break
    return out[:80]
