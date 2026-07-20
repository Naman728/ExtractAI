"""HTML cleaning stage."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Comment

_TRACKING_HINTS = (
    "google-analytics",
    "googletagmanager",
    "doubleclick",
    "facebook.net",
    "hotjar",
    "segment.com",
    "mixpanel",
    "adservice",
    "adsystem",
    "scorecardresearch",
)


class HtmlCleaner:
    """Remove non-semantic noise while preserving content structure."""

    def clean(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript", "svg", "iframe", "canvas"]):
            tag.decompose()

        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        for tag in soup.find_all(True):
            # Some parsers leave attrs as None on certain nodes (e.g. after agent HTML).
            attrs = tag.attrs
            if attrs is None:
                tag.attrs = {}
                attrs = tag.attrs
            # Strip event handlers and tracking-ish attributes
            for attr in list(attrs):
                if attr.startswith("on") or attr in {"data-analytics", "data-track"}:
                    del attrs[attr]
            # Remove obvious ad/tracking nodes
            classes = " ".join(tag.get("class") or []).lower()
            tid = (tag.get("id") or "").lower()
            blob = f"{classes} {tid}"
            if any(h in blob for h in ("ad-container", "adsbox", "advert", "cookie-banner")):
                tag.decompose()
                continue
            src = (tag.get("src") or tag.get("href") or "").lower()
            if any(h in src for h in _TRACKING_HINTS):
                tag.decompose()

        # Preserve full document structure (head meta/title needed by plugins)
        text = str(soup)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()