"""Abstract extraction strategy — Strategy Pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.website_intelligence.profile import WebsiteProfile
from app.strategy.types import ExecutionPlan, StrategyScore


class ExtractionStrategy(ABC):
    """
    Pluggable strategy that scores a WebsiteProfile and builds an ExecutionPlan.

    Implementations must be independently unit-testable with no registry coupling.
    """

    @abstractmethod
    def id(self) -> str:
        """Stable machine id, e.g. static_html."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""

    @abstractmethod
    def priority(self) -> int:
        """
        Tie-break priority (higher wins when suitability scores are equal).
        Does not replace scoring — only breaks ties.
        """

    @abstractmethod
    def version(self) -> str:
        """Strategy implementation version."""

    @abstractmethod
    def can_handle(self, profile: WebsiteProfile) -> bool:
        """Fast gate — False means strategy is skipped (not scored as viable)."""

    @abstractmethod
    def score(self, profile: WebsiteProfile) -> StrategyScore:
        """Return suitability score and rationale. Call only when can_handle is True."""

    @abstractmethod
    def build_execution_plan(self, profile: WebsiteProfile) -> ExecutionPlan:
        """Build the declarative plan this strategy would execute."""

    def is_enabled(self) -> bool:
        """Future/reserved strategies return False until implemented."""
        return True
