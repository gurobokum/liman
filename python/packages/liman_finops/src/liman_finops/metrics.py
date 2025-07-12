from opentelemetry.metrics import Meter


class Metrics:
    def __init__(self, meter: Meter) -> None:
        self.meter = meter

        self.node_calls = self.meter.create_counter(
            name="liman.finops.node.calls",
            description="Count of calls of Liman nodes",
        )
