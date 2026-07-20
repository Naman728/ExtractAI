"""Validation Engine — reject malformed data and dedupe."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class ValidationEngine:
    def validate(self, normalized: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        report: dict[str, Any] = {"accepted": {}, "rejected": {}, "duplicates_removed": {}}
        result = dict(normalized)

        emails, dup_e, rej_e = self._dedupe_list(
            [e for e in (normalized.get("emails") or []) if isinstance(e, str) and _EMAIL_RE.match(e)],
            reject=lambda e: not _EMAIL_RE.match(e),
        )
        result["emails"] = emails
        report["duplicates_removed"]["emails"] = dup_e
        report["rejected"]["emails"] = rej_e
        report["accepted"]["emails"] = len(emails)

        phones = []
        seen_p = set()
        rejected_p = 0
        for p in normalized.get("phones") or []:
            if not isinstance(p, dict) or not p.get("raw"):
                rejected_p += 1
                continue
            key = p.get("e164") or p["raw"]
            if key in seen_p:
                continue
            seen_p.add(key)
            phones.append(p)
        result["phones"] = phones
        report["accepted"]["phones"] = len(phones)
        report["rejected"]["phones"] = rejected_p

        images, dup_i, rej_i = self._dedupe_url_items(normalized.get("images") or [])
        result["images"] = images
        report["duplicates_removed"]["images"] = dup_i
        report["rejected"]["images"] = rej_i
        report["accepted"]["images"] = len(images)

        links, dup_l, rej_l = self._dedupe_url_items(normalized.get("links") or [])
        result["links"] = links
        report["duplicates_removed"]["links"] = dup_l
        report["rejected"]["links"] = rej_l

        products = []
        seen_prod = set()
        rej_prod = 0
        for p in normalized.get("products") or []:
            if not isinstance(p, dict) or not p.get("name"):
                rej_prod += 1
                continue
            key = p["name"].lower()
            if key in seen_prod:
                continue
            seen_prod.add(key)
            products.append(p)
        result["products"] = products
        report["accepted"]["products"] = len(products)
        report["rejected"]["products"] = rej_prod

        tables = []
        for t in normalized.get("tables") or []:
            if isinstance(t, dict) and t.get("rows"):
                tables.append(t)
        result["tables"] = tables
        report["accepted"]["tables"] = len(tables)

        # overall confidence proxy
        sections_with_data = sum(
            1
            for k, v in result.items()
            if v not in (None, [], {}, "")
        )
        report["overall_confidence"] = round(min(1.0, sections_with_data / 12), 3)
        return result, report

    def _dedupe_list(self, values: list[Any], reject) -> tuple[list[Any], int, int]:
        out = []
        seen = set()
        dups = 0
        rejected = 0
        for v in values:
            if reject(v):
                rejected += 1
                continue
            if v in seen:
                dups += 1
                continue
            seen.add(v)
            out.append(v)
        return out, dups, rejected

    def _dedupe_url_items(self, values: list[Any]) -> tuple[list[Any], int, int]:
        out = []
        seen = set()
        dups = 0
        rejected = 0
        for item in values:
            if not isinstance(item, dict) or not item.get("url"):
                rejected += 1
                continue
            url = item["url"]
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                rejected += 1
                continue
            if url in seen:
                dups += 1
                continue
            seen.add(url)
            out.append(item)
        return out, dups, rejected
