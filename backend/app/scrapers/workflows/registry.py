"""Resolve and run browser workflows."""

from __future__ import annotations

from app.scrapers.workflows.ballotready import BallotReadyOfficialsWorkflow
from app.scrapers.workflows.base import BrowserWorkflow, WorkflowResult
from app.scrapers.workflows.general_browser import GeneralBrowserWorkflow
from app.scrapers.workflows.generic_form import GenericFormWorkflow

# Specialized fast-paths first; general agent is the universal default.
_WORKFLOWS: list[BrowserWorkflow] = [
    BallotReadyOfficialsWorkflow(),
    GeneralBrowserWorkflow(),
    GenericFormWorkflow(),  # legacy alias — can_handle only if general somehow skipped
]


def get_workflow(workflow_id: str | None) -> BrowserWorkflow | None:
    if not workflow_id:
        return None
    # Aliases
    if workflow_id in {"generic_form", "general", "browserbase", "agent"}:
        workflow_id = "general_browser"
    for wf in _WORKFLOWS:
        if wf.id() == workflow_id:
            return wf
    return None


def resolve_workflow(url: str, inputs: dict[str, str], workflow_id: str | None = None) -> BrowserWorkflow:
    """Pick explicit workflow, else first can_handle match (specialized before general)."""
    if workflow_id:
        wf = get_workflow(workflow_id)
        if wf is not None:
            return wf
    for wf in _WORKFLOWS:
        if wf.can_handle(url, inputs):
            return wf
    return GeneralBrowserWorkflow()


def run_workflow(
    url: str,
    inputs: dict[str, str],
    *,
    workflow_id: str | None = None,
    timeout_ms: int = 60_000,
) -> WorkflowResult:
    wf = resolve_workflow(url, inputs, workflow_id)
    return wf.run(url, inputs, timeout_ms=timeout_ms)
