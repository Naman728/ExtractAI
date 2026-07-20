"""Normalization Engine — strict schemas from raw plugin output."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import phonenumbers

from app.core.logging import get_logger

logger = get_logger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_CURRENCY_MAP = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₹": "INR",
    "usd": "USD",
    "eur": "EUR",
    "gbp": "GBP",
    "inr": "INR",
}


class NormalizationEngine:
    """Normalize plugin payload into stable schema_version sections."""

    def normalize(self, payload: dict[str, Any], *, base_url: str) -> dict[str, Any]:
        return {
            "title": self._str(payload.get("title")),
            "meta": payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
            "headings": payload.get("headings") if isinstance(payload.get("headings"), list) else [],
            "paragraphs": [
                self._ws(p) for p in (payload.get("paragraphs") or []) if isinstance(p, str) and self._ws(p)
            ],
            "images": self._images(payload.get("images") or [], base_url),
            "links": self._links(payload.get("links") or [], base_url),
            "tables": payload.get("tables") if isinstance(payload.get("tables"), list) else [],
            "emails": self._emails(payload.get("emails") or []),
            "phones": self._phones(payload.get("phones") or []),
            "json_ld": payload.get("json_ld") if isinstance(payload.get("json_ld"), list) else [],
            "open_graph": payload.get("open_graph") if isinstance(payload.get("open_graph"), dict) else {},
            "twitter": payload.get("twitter") if isinstance(payload.get("twitter"), dict) else {},
            "canonical_url": self._url(payload.get("canonical_url"), base_url),
            "language": self._lang(payload.get("language")),
            "forms": payload.get("forms") if isinstance(payload.get("forms"), list) else [],
            "buttons": payload.get("buttons") if isinstance(payload.get("buttons"), list) else [],
            "downloads": self._links(payload.get("downloads") or [], base_url),
            "lists": payload.get("lists") if isinstance(payload.get("lists"), list) else [],
            "products": self._products(payload.get("products") or [], base_url),
            "prices": self._prices(payload.get("prices") or []),
            "favicon": self._url(payload.get("favicon"), base_url),
            "social_links": payload.get("social_links")
            if isinstance(payload.get("social_links"), list)
            else [],
            "officials": self._officials(payload.get("officials")),
            "agent": payload.get("agent") if isinstance(payload.get("agent"), dict) else {},
            "pagination": payload.get("pagination")
            if isinstance(payload.get("pagination"), dict)
            else {},
        }

    def _officials(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {
                "federal": [],
                "state": [],
                "local": [],
                "unknown": [],
                "all": [],
                "counts": {},
                "total": 0,
            }
        out: dict[str, Any] = {}
        for key in ("federal", "state", "local", "unknown", "all"):
            items = value.get(key) if isinstance(value.get(key), list) else []
            cleaned = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = self._str(item.get("name"))
                office = self._str(item.get("office"))
                if not name and not office:
                    continue
                rec: dict[str, Any] = {
                    "name": name,
                    "office": office,
                    "level": self._str(item.get("level"))
                    or (key if key != "all" else "unknown"),
                }
                for extra in ("party", "district"):
                    val = self._str(item.get(extra))
                    if val:
                        rec[extra] = val
                for extra in ("url", "image"):
                    raw = item.get(extra)
                    if isinstance(raw, str) and raw.startswith(("http://", "https://")):
                        rec[extra] = raw.split("#", 1)[0]
                cleaned.append(rec)
            out[key] = cleaned
        out["counts"] = value.get("counts") if isinstance(value.get("counts"), dict) else {
            k: len(out.get(k) or []) for k in ("federal", "state", "local", "unknown")
        }
        out["total"] = int(value.get("total") or len(out.get("all") or []))
        return out

    def _ws(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = self._ws(str(value))
        return text or None

    def _url(self, value: Any, base: str) -> str | None:
        if not value or not isinstance(value, str):
            return None
        try:
            absolute = urljoin(base, value.strip())
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                return None
            return urlunparse(parsed._replace(fragment=""))
        except Exception:
            return None

    def _emails(self, values: list[Any]) -> list[str]:
        out = []
        for v in values:
            email = self._ws(str(v)).lower()
            if _EMAIL_RE.match(email):
                out.append(email)
        return list(dict.fromkeys(out))

    def _phones(self, values: list[Any]) -> list[dict[str, str]]:
        out = []
        seen = set()
        for v in values:
            raw = self._ws(str(v))
            if not raw:
                continue
            try:
                parsed = phonenumbers.parse(raw, None)
                if not phonenumbers.is_possible_number(parsed):
                    # try US default for bare numbers
                    parsed = phonenumbers.parse(raw, "US")
                if phonenumbers.is_possible_number(parsed):
                    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    if e164 not in seen:
                        seen.add(e164)
                        out.append({"raw": raw, "e164": e164})
                    continue
            except Exception:
                pass
            digits = re.sub(r"\D", "", raw)
            if 7 <= len(digits) <= 15 and raw not in seen:
                seen.add(raw)
                out.append({"raw": raw, "e164": raw})
        return out

    def _images(self, values: list[Any], base: str) -> list[dict[str, Any]]:
        out = []
        seen = set()
        for item in values:
            if not isinstance(item, dict):
                continue
            url = self._url(item.get("url"), base)
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(
                {
                    "url": url,
                    "alt": self._str(item.get("alt")),
                    "width": item.get("width"),
                    "height": item.get("height"),
                }
            )
        return out

    def _links(self, values: list[Any], base: str) -> list[dict[str, Any]]:
        out = []
        seen = set()
        for item in values:
            if isinstance(item, str):
                url = self._url(item, base)
                text = None
            elif isinstance(item, dict):
                url = self._url(item.get("url"), base)
                text = self._str(item.get("text"))
            else:
                continue
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({"url": url, "text": text})
        return out

    def _lang(self, value: Any) -> str | None:
        if not value:
            return None
        lang = self._ws(str(value)).replace("_", "-")
        return lang[:16] if lang else None

    def _product_image(self, value: Any, base: str) -> str | None:
        if isinstance(value, str):
            return self._url(value, base)
        if isinstance(value, list) and value:
            return self._product_image(value[0], base)
        if isinstance(value, dict):
            for k in ("url", "contentUrl", "@id", "src"):
                if isinstance(value.get(k), str):
                    return self._url(value.get(k), base)
        return None

    def _products(self, values: list[Any], base: str) -> list[dict[str, Any]]:
        out = []
        seen = set()
        for item in values:
            if not isinstance(item, dict):
                continue
            name = self._str(item.get("name"))
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            image = self._product_image(item.get("image"), base)
            price = item.get("price")
            if price is not None and not isinstance(price, str):
                price = str(price)
            out.append(
                {
                    "name": name,
                    "sku": self._str(item.get("sku")),
                    "description": self._str(item.get("description")),
                    "url": self._url(item.get("url"), base),
                    "image": image,
                    "price": self._str(price),
                    "currency": self._str(item.get("currency")),
                    "type": self._str(item.get("type")) or "product",
                    "source": item.get("source"),
                }
            )
        return out

    def _prices(self, values: list[Any]) -> list[dict[str, Any]]:
        out = []
        for item in values:
            if not isinstance(item, dict):
                continue
            raw = self._str(item.get("raw"))
            if not raw:
                continue
            currency = item.get("currency")
            amount = None
            # detect currency symbol
            for sym, code in _CURRENCY_MAP.items():
                if sym in raw.lower() or sym in raw:
                    currency = currency or code
            num = re.sub(r"[^\d.]", "", raw.replace(",", ""))
            try:
                amount = str(Decimal(num)) if num else None
            except InvalidOperation:
                amount = None
            out.append(
                {
                    "raw": raw,
                    "amount": amount,
                    "currency": (str(currency).upper() if currency else None),
                    "source": item.get("source"),
                }
            )
        return out
