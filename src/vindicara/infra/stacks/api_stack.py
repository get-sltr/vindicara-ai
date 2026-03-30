"""Lambda function and API Gateway for Vindicara API."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct


class APIStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        policies_table: dynamodb.Table,
        evaluations_table: dynamodb.Table,
        api_keys_table: dynamodb.Table,
        audit_bucket: s3.Bucket,
        event_bus: events.EventBus,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api_function = lambda_.Function(
            self, "APIFunction",
            function_name="vindicara-api",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="vindicara.lambda_handler.handler",
            code=lambda_.Code.from_asset(
                ".",
                exclude=["tests", "scripts", "site", "docs", "*.md", ".venv", ".git", "node_modules", "cdk.out"],
            ),
            memory_size=256,
            timeout=Duration.seconds(30),
            environment={
                "VINDICARA_STAGE": "prod",
                "VINDICARA_LOG_LEVEL": "INFO",
                "POLICIES_TABLE": policies_table.table_name,
                "EVALUATIONS_TABLE": evaluations_table.table_name,
                "API_KEYS_TABLE": api_keys_table.table_name,
                "AUDIT_BUCKET": audit_bucket.bucket_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE,
        )

        policies_table.grant_read_write_data(self.api_function)
        evaluations_table.grant_read_write_data(self.api_function)
        api_keys_table.grant_read_data(self.api_function)
        audit_bucket.grant_write(self.api_function)
        event_bus.grant_put_events_to(self.api_function)

        self.http_api = apigw.HttpApi(
            self, "VindicaraAPI",
            api_name="vindicara-api",
            default_integration=integrations.HttpLambdaIntegration(
                "LambdaIntegration",
                handler=self.api_function,
            ),
            cors_preflight=apigw.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[
                    apigw.CorsHttpMethod.GET,
                    apigw.CorsHttpMethod.POST,
                    apigw.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=["*"],
            ),
        )
