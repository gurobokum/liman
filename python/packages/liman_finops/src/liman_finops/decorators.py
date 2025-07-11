from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from opentelemetry.trace import Tracer

R = TypeVar("R")


class TraceableObject:
    id: str | None
    name: str | None
    kind: str | None


def node_invoke(
    tracer: Tracer,
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
                ...

    return traced_method


def node_ainvoke(
    tracer: Tracer,
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
                ...

    return traced_method


def extract_attrs(instance: TraceableObject) -> dict[str, str]:
    """
    Extract attributes from the instance for tracing.
    """
    return {
        k: v
        for k in TraceableObject.__annotations__
        if (v := getattr(instance, k, None)) is not None
    }
