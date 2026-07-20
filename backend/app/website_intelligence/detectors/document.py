"""Document-level detectors: auth, cookies, forms, metadata, social, downloads."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.website_intelligence.types import (
    ConfidentValue,
    DiscoveredAsset,
    SocialLink,
)

_SOCIAL_HOSTS = {
    "twitter.com": "twitter",
    "x.com": "twitter",
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "github.com": "github",
    "tiktok.com": "tiktok",
}

_DOWNLOAD_EXT = (".pdf", ".csv", ".xlsx", ".xls", ".zip", ".doc", ".docx", ".ppt", ".pptx")


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def detect_auth_signals(html: str, status_code: int, headers: dict[str, str]) -> ConfidentValue[list[str]]:
    signals: list[str] = []
    if status_code == 401:
        signals.append("http_401")
    if status_code == 403 and "www-authenticate" in headers:
        signals.append("www_authenticate")
    if headers.get("www-authenticate"):
        signals.append("www_authenticate_header")

    soup = _soup(html)
    password_inputs = soup.select('input[type="password"]')
    if password_inputs:
        signals.append("password_form")
    text = (html or "").lower()
    for needle in ("sign in", "log in", "login", "oauth", "sso"):
        if needle in text and ("password" in text or "auth" in text):
            signals.append(f"copy:{needle.replace(' ', '_')}")
            break

    return ConfidentValue(
        value=list(dict.fromkeys(signals)),
        confidence=0.9 if signals else 0.6,
        evidence=signals,
    )


def detect_cookies(cookies: dict[str, str]) -> tuple[ConfidentValue[bool], ConfidentValue[list[str]]]:
    names = list(cookies.keys())
    return (
        ConfidentValue(value=bool(names), confidence=1.0 if names else 0.8, evidence=names[:10]),
        ConfidentValue(value=names, confidence=1.0 if names else 0.8, evidence=names[:10]),
    )


def detect_forms(html: str) -> ConfidentValue[int]:
    soup = _soup(html)
    forms = soup.find_all("form")
    return ConfidentValue(value=len(forms), confidence=0.95, evidence=[f"forms={len(forms)}"])


def detect_document_meta(html: str, base_url: str) -> dict[str, ConfidentValue]:
    """Title, canonical, favicon, language, charset, OG, Twitter, JSON-LD."""
    soup = _soup(html)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    canonical = None
    link_canon = soup.find("link", rel=lambda v: v and "canonical" in v)
    if link_canon and link_canon.get("href"):
        canonical = urljoin(base_url, link_canon["href"])

    favicon = None
    for rel in ("icon", "shortcut icon", "apple-touch-icon"):
        link = soup.find("link", rel=lambda v, r=rel: v and r in " ".join(v).lower() if isinstance(v, list) else r in str(v).lower())
        if link and link.get("href"):
            favicon = urljoin(base_url, link["href"])
            break

    html_tag = soup.find("html")
    language = html_tag.get("lang") if html_tag and html_tag.get("lang") else None

    charset = None
    meta_charset = soup.find("meta", charset=True)
    if meta_charset:
        charset = meta_charset.get("charset")
    else:
        meta_ct = soup.find("meta", attrs={"http-equiv": re.compile("content-type", re.I)})
        if meta_ct and meta_ct.get("content"):
            m = re.search(r"charset=([\w-]+)", meta_ct["content"], re.I)
            if m:
                charset = m.group(1)

    og: dict[str, str] = {}
    for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
        prop = tag.get("property")
        content = tag.get("content")
        if prop and content:
            og[prop] = content

    twitter: dict[str, str] = {}
    for tag in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:", re.I)}):
        name = tag.get("name")
        content = tag.get("content")
        if name and content:
            twitter[name] = content

    schema_types: list[str] = []
    has_json_ld = False
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        has_json_ld = True
        raw = script.string or script.get_text() or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                t = item.get("@type")
                if isinstance(t, list):
                    schema_types.extend(str(x) for x in t)
                elif t:
                    schema_types.append(str(t))

    return {
        "title": ConfidentValue(value=title, confidence=0.95 if title else 0.0, evidence=["title"] if title else []),
        "canonical_url": ConfidentValue(
            value=canonical, confidence=0.95 if canonical else 0.0, evidence=["link[rel=canonical]"] if canonical else []
        ),
        "favicon": ConfidentValue(value=favicon, confidence=0.9 if favicon else 0.4, evidence=["link[rel=icon]"] if favicon else []),
        "language": ConfidentValue(value=language, confidence=0.9 if language else 0.3, evidence=["html[lang]"] if language else []),
        "charset": ConfidentValue(value=charset, confidence=0.9 if charset else 0.4, evidence=["meta charset"] if charset else []),
        "open_graph": ConfidentValue(value=og, confidence=0.95 if og else 0.5, evidence=list(og.keys())[:8]),
        "twitter_cards": ConfidentValue(value=twitter, confidence=0.95 if twitter else 0.5, evidence=list(twitter.keys())[:8]),
        "has_json_ld": ConfidentValue(value=has_json_ld, confidence=0.98 if has_json_ld else 0.8, evidence=["ld+json"] if has_json_ld else []),
        "schema_org_types": ConfidentValue(
            value=list(dict.fromkeys(schema_types)),
            confidence=0.95 if schema_types else 0.5,
            evidence=schema_types[:10],
        ),
    }


def detect_social_links(html: str, base_url: str) -> ConfidentValue[list[SocialLink]]:
    soup = _soup(html)
    found: list[SocialLink] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        host = (urlparse(href).hostname or "").lower().removeprefix("www.")
        for domain, platform in _SOCIAL_HOSTS.items():
            if host == domain or host.endswith("." + domain):
                if href in seen:
                    continue
                seen.add(href)
                found.append(SocialLink(platform=platform, url=href, confidence=0.9))
                break
    return ConfidentValue(
        value=found,
        confidence=0.85 if found else 0.6,
        evidence=[f.platform for f in found[:10]],
    )


def detect_downloads(html: str, base_url: str) -> ConfidentValue[list[DiscoveredAsset]]:
    soup = _soup(html)
    assets: list[DiscoveredAsset] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        path = urlparse(href).path.lower()
        if any(path.endswith(ext) for ext in _DOWNLOAD_EXT):
            if href in seen:
                continue
            seen.add(href)
            assets.append(DiscoveredAsset(url=href, kind="download", confidence=0.9))
    return ConfidentValue(
        value=assets,
        confidence=0.9 if assets else 0.7,
        evidence=[a.url for a in assets[:5]],
    )


def detect_security_headers(headers: dict[str, str]) -> ConfidentValue[dict[str, str]]:
    keys = (
        "content-security-policy",
        "strict-transport-security",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
    )
    found = {k: headers[k] for k in keys if k in headers}
    return ConfidentValue(
        value=found,
        confidence=0.95 if found else 0.7,
        evidence=list(found.keys()),
    )
