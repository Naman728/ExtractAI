"""Observability facades — structured logs, tracing, metrics (OTel/Prometheus later)."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_job_id: ContextVar[str | None] = ContextVar("job_id", default=None)


def set_trace_id(trace_id: str | None) -> None:
    _trace_id.set(trace_id)


def get_trace_id() -> str | None:
    return _trace_id.get()


def set_job_id(job_id: str | None) -> None:
    _job_id.set(job_id)


def get_job_id() -> str | None:
    return _job_id.get()


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    kind: str = "counter"


class MetricsRegistry:
    """In-process metrics buffer; swap for Prometheus client later."""

    def __init__(self) -> None:
        self._points: list[MetricPoint] = []

    def incr(self, name: str, value: float = 1.0, **labels: str) -> None:
        self._points.append(MetricPoint(name=name, value=value, labels=labels, kind="counter"))
        logger.debug("metric.incr", name=name, value=value, **labels)

    def observe(self, name: str, value: float, **labels: str) -> None:
        self._points.append(MetricPoint(name=name, value=value, labels=labels, kind="histogram"))
        logger.debug("metric.observe", name=name, value=value, **labels)

    def snapshot(self) -> list[MetricPoint]:
        return list(self._points)


metrics = MetricsRegistry()


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[None]:
    """Lightweight tracing span facade (OpenTelemetry-compatible later)."""
    start = time.perf_counter()
    logger.info(
        "span.start",
        span=name,
        trace_id=get_trace_id(),
        job_id=get_job_id(),
        **attributes,
    )
    try:
        yield
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "span.error",
            span=name,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
            trace_id=get_trace_id(),
            job_id=get_job_id(),
        )
        metrics.incr("span.errors", span=name)
        raise
    else:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "span.end",
            span=name,
            duration_ms=round(duration_ms, 2),
            trace_id=get_trace_id(),
            job_id=get_job_id(),
        )
        metrics.observe("span.duration_ms", duration_ms, span=name)
