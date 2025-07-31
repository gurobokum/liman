import logging
from collections.abc import Collection
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor  # type: ignore
from opentelemetry.metrics import get_meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    MetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from liman_finops.decorators import (
    actor_execute,
    langchain_ainvoke,
    node_ainvoke,
    node_invoke,
)
from liman_finops.metrics import Metrics
from liman_finops.version import version

logger = logging.getLogger(__name__)


def configure_instrumentor(
    span_exporter: SpanExporter | None = None,
    metric_exporter: MetricExporter | None = None,
    *,
    console: bool = False,
    service_name: str = "liman",
) -> "LimanInstrumentor":
    """
    Configure the Liman instrumentor.

    Args:
        console: Enable console exporters for debugging
        span_exporter: Custom span exporter (e.g., Jaeger, OTLP, etc.)
        metric_exporter: Custom metric exporter
        service_name: Name of the service for telemetry data
    """

    resource = Resource.create({ResourceAttributes.SERVICE_NAME: service_name})
    tracer_provider = TracerProvider(resource=resource)
    meter_provider = None

    if console:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        tracer_provider.add_span_processor(processor)

        reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])

    if span_exporter:
        processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)

    if metric_exporter:
        reader = PeriodicExportingMetricReader(metric_exporter)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])

    instrumentor = LimanInstrumentor()
    instrumentor.instrument(
        tracer_provider=tracer_provider, meter_provider=meter_provider
    )

    return instrumentor


class LimanInstrumentor(BaseInstrumentor):  # type: ignore
    """
    OpenTelemetry instrumentor for the Liman library.
    """

    methods = {
        "LLMNode.invoke": ("liman_core.llm_node.node", node_invoke),
        "ToolNode.invoke": ("liman_core.tool_node.node", node_invoke),
        "LLMNode.ainvoke": ("liman_core.llm_node.node", node_ainvoke),
        "ToolNode.ainvoke": ("liman_core.tool_node.node", node_ainvoke),
        "AsyncNodeActor.execute": ("liman_core.node_actor.actor", actor_execute),
        "NodeActor.execute": ("liman_core.node_actor", actor_execute),
        "ChatOpenAI.ainvoke": ("langchain_openai", langchain_ainvoke),
    }

    def _instrument(self, **kwargs: Any) -> None:
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            version,
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )

        meter_provider = kwargs.get("meter_provider")
        meter = get_meter(
            __name__,
            version,
            meter_provider,
            schema_url=Schemas.V1_28_0.value,
        )
        metrics = Metrics(meter)

        for method, (module, fn) in self.methods.items():
            try:
                wrap_function_wrapper(
                    module=module,
                    name=method,
                    wrapper=fn(tracer, metrics),
                )
            except ImportError as e:
                logger.warning(f"Failed to instrument {method} in {module}: {e}. ")

    def _uninstrument(self, **kwargs: Any) -> None: ...

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("liman-core ~= 0.1.0rc0",)
