from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from opentelemetry.trace import Tracer

from liman_finops.metrics import Metrics

R = TypeVar("R")


class TraceableObject(Protocol):
    id: str | None
    name: str | None
    kind: str | None


def node_invoke(
    tracer: Tracer, metrics: Metrics
) -> Callable[[Callable[..., R], TraceableObject, Any, Any], R]:
    """
    Wrapper for the node invoke method to trace and log events.
    """

    def traced_method(
        wrapped: Callable[..., R],
        instance: TraceableObject,
        args: Any,
        kwargs: Any,
    ) -> R:
        attrs = extract_attrs(instance)
        with tracer.start_as_current_span(
            f"{instance.__class__.__name__}.{wrapped.__name__}",
            attributes=attrs,
            end_on_exit=True,
        ):
            try:
                result = wrapped(*args, **kwargs)
                return result
            except Exception:
                raise
            finally:
                metrics.node_calls.add(1, attributes=attrs)

    return traced_method


def node_ainvoke(
    tracer: Tracer, metrics: Metrics
) -> Callable[[Callable[..., Awaitable[R]], TraceableObject, Any, Any], Awaitable[R]]:
    """
    Wrapper for the node invoke method to trace and log events.
    """

    async def traced_method(
        wrapped: Callable[..., Awaitable[R]],
        instance: TraceableObject,
        args: Any,
        kwargs: Any,
    ) -> R:
        attrs = extract_attrs(instance)
        with tracer.start_as_current_span(
            f"{instance.__class__.__name__}.{wrapped.__name__}",
            attributes=attrs,
            end_on_exit=True,
        ):
            try:
                result = await wrapped(*args, **kwargs)
                return result
            except Exception:
                raise
            finally:
                metrics.node_calls.add(1, attributes=attrs)

    return traced_method


def extract_attrs(instance: TraceableObject) -> dict[str, str]:
    """
    Extract attributes from the instance for tracing.
    """
    return {
        k: str(v)
        for k in TraceableObject.__annotations__
        if (v := getattr(instance, k, None)) is not None
    }
