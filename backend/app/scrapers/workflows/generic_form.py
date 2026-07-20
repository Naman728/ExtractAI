"""Legacy alias — delegates to GeneralBrowserWorkflow."""

from __future__ import annotations

from app.scrapers.workflows.base import BrowserWorkflow, WorkflowResult
from app.scrapers.workflows.general_browser import GeneralBrowserWorkflow


class GenericFormWorkflow(BrowserWorkflow):
    """Kept for backward compatibility with older workflow ids / tests."""

    def __init__(self) -> None:
        self._impl = GeneralBrowserWorkflow()

    def id(self) -> str:
        return "generic_form"

    def can_handle(self, url: str, inputs: dict[str, str]) -> bool:
        # Prefer general_browser in the registry; this only matches if general did not.
        return False

    def run(
        self,
        url: str,
        inputs: dict[str, str],
        *,
        timeout_ms: int = 60_000,
    ) -> WorkflowResult:
        return self._impl.run(url, inputs, timeout_ms=timeout_ms)
