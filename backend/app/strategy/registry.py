"""Auto-discovery Strategy Registry — add a module, zero engine changes."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Iterable

from app.core.logging import get_logger
from app.strategy.base import ExtractionStrategy

logger = get_logger(__name__)


class StrategyRegistry:
    """
    Discovers ExtractionStrategy subclasses under app.strategy.strategies.

    New strategies appear automatically when their module is importable —
    no modifications to the Strategy Engine required.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, ExtractionStrategy] = {}

    def register(self, strategy: ExtractionStrategy) -> None:
        sid = strategy.id()
        if sid in self._strategies:
            logger.warning("strategy.registry_overwrite", strategy_id=sid)
        self._strategies[sid] = strategy
        logger.info(
            "strategy.registered",
            strategy_id=sid,
            name=strategy.name(),
            enabled=strategy.is_enabled(),
        )

    def get(self, strategy_id: str) -> ExtractionStrategy | None:
        return self._strategies.get(strategy_id)

    def all(self) -> list[ExtractionStrategy]:
        return list(self._strategies.values())

    def enabled(self) -> list[ExtractionStrategy]:
        return [s for s in self._strategies.values() if s.is_enabled()]

    def discover(self, package_name: str = "app.strategy.strategies") -> None:
        """Import all modules in the strategies package and register concrete classes."""
        package = importlib.import_module(package_name)
        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            module = importlib.import_module(module_info.name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, ExtractionStrategy):
                    continue
                if obj is ExtractionStrategy:
                    continue
                if inspect.isabstract(obj):
                    continue
                # Skip private base helpers
                if obj.__name__.startswith("_"):
                    continue
                self.register(obj())

    def ids(self) -> Iterable[str]:
        return self._strategies.keys()


_registry: StrategyRegistry | None = None


def get_strategy_registry() -> StrategyRegistry:
    """Singleton registry with auto-discovery on first use."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
        _registry.discover()
    return _registry
