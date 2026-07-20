"""Prompt loader utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt file by name (with or without .txt)."""
    filename = name if name.endswith(".txt") else f"{name}.txt"
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


PROMPT_VERSION = "1.0.0"
