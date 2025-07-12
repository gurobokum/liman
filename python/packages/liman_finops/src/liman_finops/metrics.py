from opentelemetry.metrics import Meter


class Metrics:
    def __init__(self, meter: Meter) -> None:
        self.meter = meter

        self.node_calls = self.meter.create_counter(
            name="liman.finops.node.calls",
            description="Count of calls of Liman nodes",
            unit="{call}",
        )
        self.input_llm_tokens = self.meter.create_counter(
            name="liman.finops.input_llm_tokens",
            description="Count of tokens used in Liman nodes",
            unit="{token}",
        )
        self.output_llm_tokens = self.meter.create_counter(
            name="liman.finops.output_llm_tokens",
            description="Count of tokens produced by Liman nodes",
            unit="{token}",
        )
        self.llm_tokens_cost = self.meter.create_counter(
            name="liman.finops.llm_tokens_cost",
            description="Cost of LLM tokens used in Liman nodes",
            unit="{currency}",
        )
