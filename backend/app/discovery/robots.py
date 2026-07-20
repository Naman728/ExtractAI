"""robots.txt parser (compliant — no bypass)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def parse_robots(text: str, user_agent: str = "*") -> dict[str, Any]:
    """Parse robots.txt into a structured summary for the requested UA group."""
    if not text:
        return {"available": False, "sitemaps": [], "allows": [], "disallows": []}

    sitemaps: list[str] = []
    groups: list[dict[str, Any]] = []
    current_agents: list[str] = []
    current_rules: list[tuple[str, str]] = []

    def flush() -> None:
        nonlocal current_agents, current_rules
        if current_agents:
            groups.append({"user_agents": current_agents, "rules": current_rules})
        current_agents, current_rules = [], []

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if current_rules and current_agents:
                flush()
            elif current_agents and not current_rules:
                current_agents.append(value.lower())
                continue
            current_agents = [value.lower()]
            current_rules = []
        elif key in {"allow", "disallow"}:
            if not current_agents:
                current_agents = ["*"]
            current_rules.append((key, value))
        elif key == "sitemap":
            sitemaps.append(value)
        elif key == "crawl-delay":
            current_rules.append(("crawl-delay", value))

    flush()

    # Select matching group
    matched = None
    for group in groups:
        agents = group["user_agents"]
        if any(a == "*" or a in user_agent.lower() for a in agents):
            matched = group
            if any(a != "*" for a in agents):
                break

    allows = [v for k, v in (matched["rules"] if matched else []) if k == "allow"]
    disallows = [v for k, v in (matched["rules"] if matched else []) if k == "disallow"]
    crawl_delay = next((v for k, v in (matched["rules"] if matched else []) if k == "crawl-delay"), None)

    return {
        "available": True,
        "sitemaps": sitemaps,
        "allows": allows,
        "disallows": disallows,
        "crawl_delay": crawl_delay,
        "groups_count": len(groups),
    }


def path_allowed(robots: dict[str, Any], path: str) -> bool | None:
    """Best-effort allow check. None if robots unavailable."""
    if not robots.get("available"):
        return None
    disallows: list[str] = robots.get("disallows") or []
    allows: list[str] = robots.get("allows") or []
    # Longest match wins (simplified)
    best_allow = max((a for a in allows if path.startswith(a)), key=len, default="")
    best_disallow = max((d for d in disallows if d and path.startswith(d)), key=len, default="")
    if not best_allow and not best_disallow:
        return True
    if len(best_allow) >= len(best_disallow):
        return True
    return False


def origin_of(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
