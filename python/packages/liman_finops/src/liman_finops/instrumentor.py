from collections.abc import Collection
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor  # type: ignore
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from liman_finops.decorators import node_ainvoke, node_invoke
from liman_finops.version import version


def configure_instrumentor(console: bool = False) -> "LimanInstrumentor":
    """
    Configure the Liman instrumentor.
    This function is used to set up the Liman instrumentor with the necessary configurations.
    """

    tracer_provider = TracerProvider()
    if console:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        tracer_provider.add_span_processor(processor)

    instrumentor = LimanInstrumentor()
    instrumentor.instrument(tracer_provider=tracer_provider)

    return instrumentor


class LimanInstrumentor(BaseInstrumentor):  # type: ignore
    """
    OpenTelemetry instrumentor for the Liman library.
    """

    methods = {
        "LLMNode.invoke": "liman_core.llm_node.node",
        "ToolNode.invoke": "liman_core.tool_node.node",
    }

    amethods = {
        "LLMNode.ainvoke": "liman_core.llm_node.node",
        "ToolNode.ainvoke": "liman_core.tool_node.node",
    }

    def _instrument(self, **kwargs: Any) -> None:
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            version,
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )

        for method, module in self.methods.items():
            wrap_function_wrapper(
                module=module,
                name=method,
                wrapper=node_invoke(tracer),
            )

        for method, module in self.amethods.items():
            wrap_function_wrapper(
                module=module,
                name=method,
                wrapper=node_ainvoke(tracer),
            )

    def _uninstrument(self, **kwargs: Any) -> None: ...

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("liman-core ~= 0.1.0rc0",)
