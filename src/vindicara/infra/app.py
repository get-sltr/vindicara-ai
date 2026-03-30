"""CDK application entry point."""

import aws_cdk as cdk

from vindicara.infra.stacks.api_stack import APIStack
from vindicara.infra.stacks.data_stack import DataStack
from vindicara.infra.stacks.events_stack import EventsStack

app = cdk.App()

env = cdk.Environment(
    account="335741630084",
    region="us-east-1",
)

data = DataStack(app, "VindicaraData", env=env)
events_stack = EventsStack(app, "VindicaraEvents", env=env)

APIStack(
    app,
    "VindicaraAPI",
    policies_table=data.policies_table,
    evaluations_table=data.evaluations_table,
    api_keys_table=data.api_keys_table,
    audit_bucket=data.audit_bucket,
    event_bus=events_stack.event_bus,
    env=env,
)

app.synth()
