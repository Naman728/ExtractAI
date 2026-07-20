"""Hash + chunk helpers for AI cost optimization and caching."""

from __future__ import annotations

import hashlib
import json
from typing import Any


# Sections that matter most for understanding (ordered by priority).
RELEVANT_SECTIONS = (
    "title",
    "meta",
    "open_graph",
    "twitter",
    "headings",
    "paragraphs",
    "products",
    "prices",
    "emails",
    "phones",
    "social_links",
    "forms",
    "json_ld",
    "officials",
    "agent",
    "links",
    "canonical_url",
    "language",
)


def hash_normalized(normalized: dict[str, Any], *, prompt_version: str, model: str) -> str:
    """Stable SHA-256 of normalized extraction + prompt/model pins."""
    payload = {
        "normalized": _canonicalize(normalized),
        "prompt_version": prompt_version,
        "model": model,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]
    return obj


def select_relevant_content(
    normalized: dict[str, Any],
    *,
    max_chars: int = 24_000,
) -> dict[str, Any]:
    """Pick high-signal sections and truncate to stay under token budgets."""
    selected: dict[str, Any] = {}
    for key in RELEVANT_SECTIONS:
        if key in normalized and normalized[key] not in (None, "", [], {}):
            selected[key] = normalized[key]

    # Include any leftover small scalars (favicon, language already covered)
    for key, value in normalized.items():
        if key in selected:
            continue
        if isinstance(value, (str, int, float, bool)) and value not in ("", None):
            selected[key] = value

    serialized = json.dumps(selected, ensure_ascii=False, default=str)
    if len(serialized) <= max_chars:
        return selected

    # Truncate large list sections progressively
    trimmed = dict(selected)
    for key in ("paragraphs", "links", "headings", "images", "tables", "lists"):
        if key not in trimmed:
            continue
        val = trimmed[key]
        if isinstance(val, list) and len(val) > 8:
            trimmed[key] = val[:8]
        serialized = json.dumps(trimmed, ensure_ascii=False, default=str)
        if len(serialized) <= max_chars:
            return trimmed

    # Hard truncate paragraphs/text
    if isinstance(trimmed.get("paragraphs"), list):
        paras = []
        budget = max_chars // 2
        used = 0
        for p in trimmed["paragraphs"]:
            s = str(p) if not isinstance(p, dict) else json.dumps(p, ensure_ascii=False)
            if used + len(s) > budget:
                break
            paras.append(p)
            used += len(s)
        trimmed["paragraphs"] = paras

    return trimmed


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token)."""
    return max(1, len(text) // 4)
