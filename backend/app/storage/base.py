"""Storage backend abstraction (local now, S3 later)."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StoredObject:
    path: str
    size_bytes: int
    checksum: str
    content_type: str | None = None


class StorageBackend(ABC):
    """Abstract object storage interface."""

    @abstractmethod
    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Filesystem-backed storage under a configurable root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        safe = key.lstrip("/").replace("..", "")
        path = (self.root / safe).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> StoredObject:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        logger.debug("storage.put", key=key, size=len(data))
        return StoredObject(
            path=key,
            size_bytes=len(data),
            checksum=checksum,
            content_type=content_type,
        )

    def get_bytes(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()


def create_storage_backend(settings: Settings | None = None) -> StorageBackend:
    """Factory for storage backends."""
    cfg = settings or get_settings()
    if cfg.storage_backend == "local":
        return LocalStorageBackend(cfg.storage_local_path)
    raise ValueError(f"Unsupported storage backend: {cfg.storage_backend}")
