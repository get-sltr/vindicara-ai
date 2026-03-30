"""EventBridge event bus for Vindicara."""

from aws_cdk import Stack
from aws_cdk import aws_events as events
from constructs import Construct


class EventsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.event_bus = events.EventBus(
            self, "VindicaraEventBus",
            event_bus_name="vindicara-events",
        )

        events.Rule(
            self, "LogAllEvaluations",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(source=["vindicara.engine"]),
            rule_name="vindicara-log-evaluations",
        )
