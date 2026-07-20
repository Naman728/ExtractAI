"""Pipeline / strategy / schema version pins for job reproducibility."""

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class VersionPins:
    """Immutable version set recorded on every job."""

    pipeline_version: str
    strategy_version: str
    schema_version: int
    profile_version: str
    discovery_version: str
    plugin_set_version: str


BUILTIN_PLUGIN_SET_VERSION = "1.0.0-foundation"


def current_version_pins() -> VersionPins:
    """Resolve version pins from settings + builtin plugin pack."""
    settings = get_settings()
    return VersionPins(
        pipeline_version=settings.pipeline_version,
        strategy_version=settings.strategy_version,
        schema_version=settings.schema_version,
        profile_version=settings.profile_version,
        discovery_version=settings.discovery_version,
        plugin_set_version=BUILTIN_PLUGIN_SET_VERSION,
    )
