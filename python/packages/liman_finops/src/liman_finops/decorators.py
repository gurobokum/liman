from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from opentelemetry.trace import Tracer

from liman_finops.metrics import Metrics
from liman_finops.token_pricing import get_token_price

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
            "model_name": getattr(instance, "model_name", "unknown"),
        }
        result = None
        with tracer.start_as_current_span(
            f"{instance.__class__.__name__}.{wrapped.__name__}",
            attributes=attrs,
            end_on_exit=True,
        ) as span:
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
                    prompt_tokens = usage["prompt_tokens"]
                    completion_tokens = usage["completion_tokens"]
                    total_tokens = prompt_tokens + completion_tokens

                    # Add token usage to span attributes
                    attrs.update(
                        {
                            "llm.usage.prompt_tokens": str(prompt_tokens),
                            "llm.usage.completion_tokens": str(completion_tokens),
                            "llm.usage.total_tokens": str(total_tokens),
                        }
                    )

                    # Calculate and add cost to span attributes
                    if llm_tokens_cost := get_llm_cost(usage, attrs["model_name"]):
                        attrs["llm.usage.cost_usd"] = f"{llm_tokens_cost:.6f}"
                        metrics.llm_tokens_cost.add(llm_tokens_cost, attributes=attrs)

                    metrics.input_llm_tokens.add(prompt_tokens, attributes=attrs)
                    metrics.output_llm_tokens.add(completion_tokens, attributes=attrs)

                span.set_attributes(attrs)

    return traced_method


def extend_langchain_attrs(_attrs: dict[str, str], result: Any) -> dict[str, str]:
    attrs = {**_attrs}
    if not result:
        return attrs

    if response_metadata := getattr(result, "response_metadata", None):
        if model_name := response_metadata.get("model_name"):
            attrs["model_version"] = model_name

        if system_fingerprint := response_metadata.get("system_fingerprint"):
            attrs["system_fingerprint"] = system_fingerprint

    if id_ := getattr(result, "id", None):
        attrs["id"] = id_

    return attrs


def actor_execute(
    tracer: Tracer, metrics: Metrics
) -> Callable[[Callable[..., Awaitable[R]], TraceableObject, Any, Any], Awaitable[R]]:
    """
    Wrapper for NodeActor execute method to trace and log events.
    """

    async def traced_method(
        wrapped: Callable[..., Awaitable[R]],
        instance: TraceableObject,
        args: Any,
        kwargs: Any,
    ) -> R:
        node = getattr(instance, "node", None)
        node_name = node.name if node and hasattr(node, "name") else "unknown"
        node_type = node.spec.kind if node and hasattr(node, "spec") else "unknown"

        attrs = {
            "actor_id": str(getattr(instance, "id", "unknown")),
            "node_name": node_name,
            "node_type": node_type,
        }

        import time

        start_time = time.time()

        with tracer.start_as_current_span(
            f"{instance.__class__.__name__}.{wrapped.__name__}",
            attributes=attrs,
            end_on_exit=True,
        ):
            try:
                result = await wrapped(*args, **kwargs)
                execution_time = time.time() - start_time
                metrics.actor_executions.add(1, attributes=attrs)
                metrics.actor_execution_time.record(execution_time, attributes=attrs)
                return result
            except Exception:
                execution_time = time.time() - start_time
                metrics.actor_errors.add(1, attributes=attrs)
                metrics.actor_execution_time.record(execution_time, attributes=attrs)
                raise

    return traced_method


def get_llm_cost(usage: Any, model_name: str) -> float | None:
    """
    Calculate the cost of LLM usage based on the model and token counts.
    """
    input_tokens = float(usage.get("prompt_tokens", 0))
    output_tokens = float(usage.get("completion_tokens", 0))

    input_price, _, output_price = get_token_price(model_name)
    return input_tokens * input_price + output_tokens * output_price
