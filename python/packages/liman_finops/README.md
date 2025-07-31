# liman-finops

OpenTelemetry instrumentation and cost tracking for Liman agent framework.

## Jaeger Integration Example

**Run Jaeger locally** using Docker:

```bash
docker run --rm --name jaeger \
-p 16686:16686 \
-p 4317:4317 \
-p 4318:4318 \
-p 5778:5778 \
-p 9411:9411 \
cr.jaegertracing.io/jaegertracing/jaeger:2.8.0
```

https://www.jaegertracing.io/docs/2.8/getting-started/

**Setup Liman FinOps with Jaeger**:

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from liman_finops import configure_instrumentor

# Configure Jaeger via OTLP
jaeger_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
instrumentor = configure_instrumentor(span_exporter=jaeger_exporter)
```

## Trace Attributes

Your traces will include cost information:

- `llm.usage.cost_usd`: Cost in USD (e.g., "0.000150")
- `llm.usage.prompt_tokens`: Input token count
- `llm.usage.completion_tokens`: Output token count
- `model_name`: LLM model used

