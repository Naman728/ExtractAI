"""In-DB cache for AI understanding outputs.

Uses its own short-lived sessions so cache races never poison the job session.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.models.ai_understanding_cache import AIUnderstandingCache

logger = get_logger(__name__)


class UnderstandingCache:
    """Hash-keyed cache over the ai_understanding_cache table."""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        session: Session | None = None,
    ) -> None:
        # Prefer a dedicated session factory so conflicts stay isolated.
        self._session_factory = session_factory
        self._session = session

    def _open(self) -> Session:
        if self._session_factory is not None:
            return self._session_factory()
        if self._session is not None:
            return self._session
        raise RuntimeError("UnderstandingCache requires session_factory or session")

    def get(self, content_hash: str) -> dict[str, Any] | None:
        owns = self._session_factory is not None
        session = self._open()
        try:
            row = (
                session.query(AIUnderstandingCache)
                .filter_by(content_hash=content_hash)
                .one_or_none()
            )
            if row is None:
                return None
            row.hit_count = int(row.hit_count or 0) + 1
            row.last_hit_at = datetime.now(UTC)
            if owns:
                session.commit()
            else:
                session.flush()
            return dict(row.payload or {})
        except SQLAlchemyError as exc:
            logger.warning("ai.cache.get_failed", error=str(exc)[:200])
            try:
                session.rollback()
            except Exception:
                pass
            return None
        finally:
            if owns:
                session.close()

    def put(self, content_hash: str, payload: dict[str, Any]) -> None:
        """Upsert by content_hash — safe under concurrent jobs."""
        owns = self._session_factory is not None
        session = self._open()
        now = datetime.now(UTC)
        try:
            stmt = (
                insert(AIUnderstandingCache)
                .values(
                    content_hash=content_hash,
                    payload=payload,
                    hit_count=0,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=["content_hash"],
                    set_={
                        "payload": payload,
                        "updated_at": now,
                    },
                )
            )
            session.execute(stmt)
            if owns:
                session.commit()
            else:
                session.flush()
        except SQLAlchemyError as exc:
            # Never let cache failures break extraction / understanding.
            logger.warning("ai.cache.put_failed", error=str(exc)[:200])
            try:
                session.rollback()
            except Exception:
                pass
            # Fallback: update existing row if present
            try:
                row = (
                    session.query(AIUnderstandingCache)
                    .filter_by(content_hash=content_hash)
                    .one_or_none()
                )
                if row is not None:
                    row.payload = payload
                    row.updated_at = datetime.now(UTC)
                    if owns:
                        session.commit()
                    else:
                        session.flush()
            except SQLAlchemyError as inner:
                logger.warning("ai.cache.put_fallback_failed", error=str(inner)[:200])
                try:
                    session.rollback()
                except Exception:
                    pass
        finally:
            if owns:
                session.close()
