"""Auto-discovery plugin registry."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import time
from typing import Any

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.plugins.base import ExtractionPlugin, PluginContext, PluginResult

logger = get_logger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, ExtractionPlugin] = {}

    def register(self, plugin: ExtractionPlugin) -> None:
        self._plugins[plugin.name()] = plugin
        logger.info("plugin.registered", name=plugin.name(), section=plugin.section())

    def enabled(self) -> list[ExtractionPlugin]:
        return sorted(
            [p for p in self._plugins.values() if p.is_enabled()],
            key=lambda p: (-p.priority(), p.name()),
        )

    def discover(self, package_name: str = "app.plugins.builtin") -> None:
        package = importlib.import_module(package_name)
        modules = [package]
        for info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            modules.append(importlib.import_module(info.name))
        for module in modules:
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, ExtractionPlugin)
                    and obj is not ExtractionPlugin
                    and not inspect.isabstract(obj)
                    and not obj.__name__.startswith("_")
                    and obj.__module__.startswith(package_name)
                ):
                    self.register(obj())

    def run_all(self, *, url: str, final_url: str, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html or "", "lxml")
        ctx = PluginContext(url=url, final_url=final_url, html=html, soup=soup)
        payload: dict[str, Any] = {}
        timings: dict[str, float] = {}
        confidence: dict[str, float] = {}

        for plugin in self.enabled():
            started = time.perf_counter()
            try:
                result: PluginResult = plugin.extract(ctx)
                payload[result.section] = result.data
                confidence[result.section] = result.confidence
            except Exception as exc:
                logger.warning("plugin.failed", plugin=plugin.name(), error=str(exc))
                payload[plugin.section()] = None
                confidence[plugin.section()] = 0.0
            timings[plugin.name()] = round((time.perf_counter() - started) * 1000, 2)

        return {"payload": payload, "section_confidence": confidence, "plugin_timings": timings}


_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.discover()
    return _registry
