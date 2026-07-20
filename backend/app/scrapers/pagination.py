"""Pagination discovery and multi-page payload merge."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from app.core.exceptions import InvalidUrlError, SsrfBlockedError
from app.utils.url import assert_public_url, normalize_url

_NEXT_TEXT = re.compile(r"^\s*(next|older|›|»|→|>|more)\s*$", re.I)
_NEXT_CONTAINS = re.compile(r"\b(next\s*page|older\s*posts|load\s*more)\b", re.I)
_PAGE_PATH = re.compile(r"(?P<prefix>/page[-_/]?)(?P<num>\d+)(?P<suffix>(?:\.html?/?)?(?:/|$))", re.I)


def _same_site(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.hostname or "").lower() == (pb.hostname or "").lower()


def _canonical_key(url: str) -> str:
    try:
        return normalize_url(url)
    except Exception:
        return url.rstrip("/")


def _safe_public(url: str) -> str | None:
    try:
        return assert_public_url(url)
    except (InvalidUrlError, SsrfBlockedError, ValueError):
        return None


def _rel_has_next(rel: Any) -> bool:
    if rel is None:
        return False
    if isinstance(rel, (list, tuple)):
        tokens = [str(x).lower() for x in rel]
    else:
        tokens = str(rel).lower().replace(",", " ").split()
    return "next" in tokens


def discover_next_url(html: str, base_url: str, *, seen: set[str]) -> str | None:
    """
    Find the best next-page URL from HTML.

    Priority: link[rel=next] → a[rel=next] → labeled Next controls → page-N heuristic.
    Only same-site public URLs not already in ``seen`` are returned.
    """
    if not html or not base_url:
        return None

    soup = BeautifulSoup(html, "lxml")
    candidates: list[tuple[int, str]] = []

    def consider(href: str | None, score: int) -> None:
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return
        absolute = urljoin(base_url, href.strip())
        safe = _safe_public(absolute)
        if not safe or not _same_site(base_url, safe):
            return
        key = _canonical_key(safe)
        if key in seen or key == _canonical_key(base_url):
            return
        candidates.append((score, safe))

    for link in soup.find_all("link", href=True):
        if _rel_has_next(link.get("rel")):
            consider(link.get("href"), 100)

    for a in soup.find_all("a", href=True):
        if _rel_has_next(a.get("rel")):
            consider(a.get("href"), 95)
            continue
        text = a.get_text(" ", strip=True)
        aria = " ".join(
            filter(
                None,
                [
                    str(a.get("aria-label") or ""),
                    str(a.get("title") or ""),
                ],
            )
        )
        classes = " ".join(a.get("class") or []).lower()
        parent_classes = " ".join((a.parent.get("class") if a.parent else None) or []).lower()
        blob = f"{classes} {parent_classes}"

        if _NEXT_TEXT.match(text) or _NEXT_TEXT.match(aria.strip()):
            consider(a.get("href"), 90)
        elif _NEXT_CONTAINS.search(text) or _NEXT_CONTAINS.search(aria):
            consider(a.get("href"), 85)
        elif "next" in blob and "prev" not in blob:
            consider(a.get("href"), 70)

    # Path / query page increment when explicit next was missing
    if not candidates:
        bumped = _bump_page_url(base_url)
        if bumped:
            consider(bumped, 40)

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def _bump_page_url(url: str) -> str | None:
    """Increment ?page=N / ?p=N / /page/N/ when present; otherwise None."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("page", "p", "pg", "paged"):
        if key in qs and qs[key]:
            try:
                current = int(qs[key][0])
            except (TypeError, ValueError):
                continue
            qs[key] = [str(current + 1)]
            query = urlencode(qs, doseq=True)
            return urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, "")
            )

    match = _PAGE_PATH.search(parsed.path or "")
    if match:
        num = int(match.group("num"))
        new_path = (
            (parsed.path or "")[: match.start("num")]
            + str(num + 1)
            + (parsed.path or "")[match.end("num") :]
        )
        return urlunparse(
            (parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, "")
        )
    return None


_LIST_SECTIONS = frozenset(
    {
        "links",
        "images",
        "paragraphs",
        "headings",
        "lists",
        "tables",
        "emails",
        "phones",
        "prices",
        "products",
        "downloads",
        "buttons",
        "forms",
        "social_links",
        "json_ld",
    }
)


def merge_plugin_payloads(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """Merge page payloads: concatenate list sections, keep first-page scalars."""
    out = dict(base or {})
    for key, value in (extra or {}).items():
        if key == "pagination":
            continue
        if key in _LIST_SECTIONS and isinstance(value, list):
            existing = out.get(key)
            if isinstance(existing, list):
                out[key] = existing + value
            elif existing is None:
                out[key] = list(value)
            else:
                out[key] = value
        elif key not in out or out[key] in (None, "", [], {}):
            out[key] = value
    return out


def merge_section_confidence(
    base: dict[str, float], extra: dict[str, float]
) -> dict[str, float]:
    out = dict(base or {})
    for key, value in (extra or {}).items():
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        prev = out.get(key)
        out[key] = max(float(prev), score) if prev is not None else score
    return out
