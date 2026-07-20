"""Discovery package."""

from app.discovery.bundle import DiscoveryBundle

__all__ = ["DiscoveryBundle", "DiscoveryEngine"]


def __getattr__(name: str):
    if name == "DiscoveryEngine":
        from app.discovery.engine import DiscoveryEngine

        return DiscoveryEngine
    raise AttributeError(name)
