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


def langchain_ainvoke(
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
        attrs = {
            "name": instance.__class__.__name__,
        }
        result = None
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
                attrs = extend_langchain_attrs(attrs, result)
                if (
                    result
                    and (
                        response_metadata := getattr(result, "response_metadata", None)
                    )
                    and (usage := response_metadata.get("token_usage", None))
                ):
                    metrics.input_llm_tokens.add(
                        usage["prompt_tokens"], attributes=attrs
                    )
                    metrics.output_llm_tokens.add(
                        usage["completion_tokens"], attributes=attrs
                    )
                    if llm_tokens_cost := get_llm_cost(usage, attrs.get("model_name")):
                        metrics.llm_tokens_cost.add(llm_tokens_cost, attributes=attrs)

    return traced_method


def extend_langchain_attrs(_attrs: dict[str, str], result: Any) -> dict[str, str]:
    attrs = {**_attrs}
    if not result:
        return attrs

    if response_metadata := getattr(result, "response_metadata", None):
        if model_name := response_metadata.get("model_name"):
            attrs["model_name"] = model_name

        if system_fingerprint := response_metadata.get("system_fingerprint"):
            attrs["system_fingerprint"] = system_fingerprint

    if id_ := getattr(result, "id", None):
        attrs["id"] = id_

    return attrs


def get_llm_cost(usage: Any, model_name: str | None = None) -> float | None:
    """
    Calculate the cost of LLM usage based on the model and token counts.
    """
    input_tokens = float(usage.get("prompt_tokens", 0))
    output_tokens = float(usage.get("completion_tokens", 0))

    match model_name:
        case "gpt-3.5-turbo":
            return input_tokens * 0.0000015 + output_tokens * 0.000002
        case "gpt-4":
            return input_tokens * 0.00003 + output_tokens * 0.00006
        case "gpt-4o-2024-08-06":
            return input_tokens * 0.00003 + output_tokens * 0.00006
        case "gpt-4-1106-preview":
            return input_tokens * 0.00003 + output_tokens * 0.00006
        case _:
            return None
