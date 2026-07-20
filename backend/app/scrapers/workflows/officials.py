"""Parse office-holder page text into federal / state / local officials."""

from __future__ import annotations

import re
from typing import Any


_CHROME = {
    "Your civic center",
    "Your preferences",
    "Your ballot",
    "English",
    "All",
    "Federal",
    "State",
    "Local",
    "BallotReady",
}

_STOP = re.compile(
    r"Need help|Privacy|Terms|Powered by|Copyright|Subscribe|Please select",
    re.I,
)


def classify_level(office: str) -> str:
    o = office.lower()
    if any(
        x in o
        for x in (
            "president of the united states",
            "vice president of the united states",
            "u.s. senate",
            "u.s. house",
            "united states senate",
            "united states house",
            "us senate",
            "us house",
        )
    ):
        return "federal"
    if any(
        x in o
        for x in (
            "governor",
            "lieutenant governor",
            "attorney general",
            "secretary of state",
            "agriculture",
            "insurance",
            "labor commission",
            "school superintendent",
            "public service commission",
            "state senate",
            "house of representatives",
            "public defender",
            "state attorney",
            "district attorney",
            "chief financial officer",
        )
    ):
        return "state"
    if any(
        x in o
        for x in (
            "county",
            "city",
            "school board",
            "mayor",
            "municipal",
            "soil and water",
            "sheriff",
            "coroner",
            "tax collector",
            "property appraiser",
            "supervisor of elections",
            "court clerk",
            "commission",
        )
    ):
        return "local"
    if "circuit" in o or "judicial" in o:
        return "state"
    return "unknown"


def parse_officials_from_text(body: str) -> dict[str, Any]:
    """Split visible office-holders text into leveled official records."""
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    start = 0
    for i, ln in enumerate(lines):
        if ln == "Local" and i + 1 < len(lines) and lines[i + 1] not in _CHROME:
            start = i + 1
            break

    flat: list[dict[str, str]] = []
    i = start
    while i < len(lines) - 1:
        name, office = lines[i], lines[i + 1]
        if name in _CHROME:
            i += 1
            continue
        if _STOP.search(name) or _STOP.search(office):
            break
        level = classify_level(office)
        flat.append({"name": name, "office": office, "level": level})
        i += 2

    grouped: dict[str, list[dict[str, str]]] = {
        "federal": [],
        "state": [],
        "local": [],
        "unknown": [],
    }
    for item in flat:
        grouped[item["level"]].append(item)

    return {
        "federal": grouped["federal"],
        "state": grouped["state"],
        "local": grouped["local"],
        "unknown": grouped["unknown"],
        "all": flat,
        "counts": {k: len(v) for k, v in grouped.items()},
        "total": len(flat),
    }
