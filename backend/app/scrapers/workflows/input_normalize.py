"""Normalize arbitrary user inputs into a stable agent payload."""

from __future__ import annotations

import json
import re
from typing import Any


SEARCH_KEYS = ("query", "q", "search", "keyword", "keywords", "topic", "topics", "term")
ADDRESS_KEYS = ("address", "addr", "location", "zip", "postal", "postcode")


def normalize_agent_inputs(raw: dict[str, Any] | None) -> dict[str, str]:
    """
    Accept flexible input shapes and produce string-valued inputs for the agent.

    Supports:
      - {"query": "FastAPI"}
      - {"search": "...", "address": "..."}
      - {"topics": '["AI","ML"]'} or topics as JSON array string
      - {"topics": "AI\\nML"} newline list
    """
    if not raw:
        return {}

    out: dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        k = str(key).strip().lower()
        if isinstance(value, (list, dict)):
            out[k] = json.dumps(value, ensure_ascii=False)
        else:
            s = str(value).strip()
            if s:
                out[k] = s

    # Promote first search-like value to canonical "query" if missing
    if "query" not in out:
        for key in SEARCH_KEYS:
            if key in out and key != "topics":
                out["query"] = out[key]
                break

    # Expand topics JSON / lines into query if still missing
    if "query" not in out and "topics" in out:
        topics = parse_list_value(out["topics"])
        if topics:
            out["query"] = topics[0]
            out["topics"] = json.dumps(topics, ensure_ascii=False)

    return out


def parse_list_value(raw: str) -> list[str]:
    """Parse JSON array, newline list, or semicolon list into strings."""
    text = (raw or "").strip()
    if not text:
        return []

    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return _clean_list([str(x) for x in parsed])
        except json.JSONDecodeError:
            pass

    if "\n" in text:
        parts = text.splitlines()
    elif ";" in text:
        parts = re.split(r"\s*;\s*", text)
    else:
        # Single value — also allow comma-separated ONLY when no street-like digits
        # (avoid splitting addresses). For topics like "AI, ML" allow commas.
        if re.search(r"\d", text) and "," in text:
            parts = [text]
        else:
            parts = re.split(r"\s*,\s*", text) if "," in text else [text]

    return _clean_list(parts)


def _clean_list(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        item = part.strip().strip('"').strip("'")
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def primary_search_value(inputs: dict[str, str]) -> str | None:
    if inputs.get("query"):
        return inputs["query"]
    for key in SEARCH_KEYS:
        if inputs.get(key) and key != "topics":
            return inputs[key]
    topics = parse_list_value(inputs.get("topics") or "")
    return topics[0] if topics else None


def all_search_targets(inputs: dict[str, str], *, max_items: int = 25) -> list[str]:
    """Topics list if present, else single query/address search targets."""
    topics = parse_list_value(inputs.get("topics") or "")
    if topics:
        return topics[:max_items]
    q = primary_search_value(inputs)
    if q:
        return [q]
    if inputs.get("address"):
        return [inputs["address"]]
    # Any remaining free-form values
    for key, val in inputs.items():
        if key in {"topics"}:
            continue
        if val:
            return [val]
    return []
