from datetime import datetime

from opentelemetry.metrics import Meter


class NodeActorMetrics:
    """
    Metrics and performance data for NodeActor
    """

    def __init__(self) -> None:
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time: datetime | None = None
        self.error_count = 0
        self.created_at = datetime.now()


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
        self.actor_executions = self.meter.create_counter(
            name="liman.finops.actor.executions",
            description="Count of NodeActor executions",
            unit="{execution}",
        )
        self.actor_execution_time = self.meter.create_histogram(
            name="liman.finops.actor.execution_time",
            description="Execution time of NodeActor operations",
            unit="s",
        )
        self.actor_errors = self.meter.create_counter(
            name="liman.finops.actor.errors",
            description="Count of NodeActor execution errors",
            unit="{error}",
        )
