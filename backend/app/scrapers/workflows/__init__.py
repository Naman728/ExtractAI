"""Interactive browser workflows — selected by name or auto-detected from URL + inputs."""

from app.scrapers.workflows.registry import resolve_workflow, run_workflow

__all__ = ["resolve_workflow", "run_workflow"]
