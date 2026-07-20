"""Rendering mode and JS-required heuristics."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.website_intelligence.profile import RenderingMode
from app.website_intelligence.types import ConfidentValue


def detect_rendering(html: str, framework: str | None) -> tuple[
    ConfidentValue[RenderingMode],
    ConfidentValue[bool],
]:
    """Estimate static vs CSR/SSR/hybrid and whether JS is required for content."""
    soup = BeautifulSoup(html or "", "lxml")
    body = soup.body
    text_len = len(body.get_text(" ", strip=True)) if body else 0
    script_tags = soup.find_all("script")
    script_count = len(script_tags)
    external_scripts = sum(1 for s in script_tags if s.get("src"))

    root_empty = False
    for sel in ("#__next", "#root", "#app", "#__nuxt", "[data-reactroot]"):
        node = soup.select_one(sel)
        if node is not None and len(node.get_text(strip=True)) < 40:
            root_empty = True
            break

    evidence: list[str] = [
        f"text_len={text_len}",
        f"scripts={script_count}",
        f"external_scripts={external_scripts}",
    ]

    js_required = False
    mode: RenderingMode = "unknown"
    confidence = 0.5

    if framework in {"nextjs", "nuxt", "astro"}:
        # SSR frameworks often ship HTML; CSR still possible
        if root_empty and text_len < 200:
            mode, js_required, confidence = "csr_heavy", True, 0.85
            evidence.append("empty_app_root")
        elif text_len > 500:
            mode, js_required, confidence = "ssr", False, 0.8
            evidence.append("substantial_ssr_html")
        else:
            mode, js_required, confidence = "hybrid", text_len < 300, 0.65
    elif framework in {"react", "vue", "angular", "svelte"}:
        if root_empty or text_len < 150:
            mode, js_required, confidence = "csr_heavy", True, 0.88
            evidence.append("spa_empty_shell")
        else:
            mode, js_required, confidence = "hybrid", True, 0.7
    else:
        if script_count <= 2 and text_len > 400:
            mode, js_required, confidence = "static", False, 0.82
            evidence.append("mostly_static_html")
        elif root_empty or (text_len < 120 and external_scripts >= 3):
            mode, js_required, confidence = "csr_heavy", True, 0.75
            evidence.append("thin_dom_many_scripts")
        elif text_len > 300:
            mode, js_required, confidence = "static", False, 0.7
        else:
            mode, js_required, confidence = "unknown", script_count > 5, 0.45

    # noscript / "enable javascript" banners
    if re.search(r"enable javascript|turn on javascript|requires? javascript", html or "", re.I):
        js_required = True
        confidence = max(confidence, 0.8)
        evidence.append("js_required_banner")

    return (
        ConfidentValue(value=mode, confidence=confidence, evidence=evidence),
        ConfidentValue(
            value=js_required,
            confidence=confidence,
            evidence=evidence,
        ),
    )
