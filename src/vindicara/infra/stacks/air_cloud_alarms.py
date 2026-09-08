"""CloudWatch alarms for the AIR Cloud stack.

Kept apart from the stack so each file stays readable. The generic Lambda and
API Gateway 5xx alarms cover crashes; the two log-based alarms cover the
product's actual promise: a sign-in that fails for a real person and a cold
start that could not read its secrets.
"""

from aws_cdk import Duration
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from constructs import Construct

ALARM_EMAIL = "kev.minn9@gmail.com"


def add_air_cloud_alarms(scope: Construct, *, function: lambda_.Function, http_api: apigw.HttpApi) -> None:
    """Attach the AIR Cloud alarm set to ``scope``."""
    self = scope
    alarm_topic = sns.Topic(
        self,
        "CloudAlarmTopic",
        topic_name="air-cloud-alarms",
        display_name="AIR Cloud workload alarms",
    )
    alarm_topic.add_subscription(
        sns_subscriptions.EmailSubscription(ALARM_EMAIL),
    )

    lambda_errors = cloudwatch.Alarm(
        self,
        "CloudLambdaErrors",
        alarm_name="air-cloud-lambda-errors",
        alarm_description="AIR Cloud Lambda errors >= 5 in 5 min.",
        metric=function.metric_errors(
            period=Duration.minutes(5),
        ),
        threshold=5,
        evaluation_periods=1,
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
    )
    lambda_errors.add_alarm_action(
        cloudwatch_actions.SnsAction(alarm_topic),
    )

    apigw_5xx = cloudwatch.Alarm(
        self,
        "CloudApiGateway5xx",
        alarm_name="air-cloud-api-5xx",
        alarm_description="AIR Cloud API 5XX >= 5 in 5 min.",
        metric=cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="5XXError",
            dimensions_map={
                "ApiId": http_api.http_api_id,
            },
            statistic="Sum",
            period=Duration.minutes(5),
        ),
        threshold=5,
        evaluation_periods=1,
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
    )
    apigw_5xx.add_alarm_action(
        cloudwatch_actions.SnsAction(alarm_topic),
    )

    # The first five minutes are the product: alarm the moment sign-in
    # or secret hydration fails for anyone, not only on generic 5xx.
    for name, pattern, description in (
        ("ExchangeFailures", '"air_cloud.auth.exchange" "rejected"', "AIR Cloud sign-in exchanges rejected >= 5 in 5 min."),
        ("HydrationFailures", "SecretHydrationError", "AIR Cloud secret hydration failed at cold start."),
    ):
        metric_filter = logs.MetricFilter(
            self,
            f"{name}Filter",
            log_group=function.log_group,
            metric_namespace="AirCloud",
            metric_name=name,
            filter_pattern=logs.FilterPattern.literal(pattern),
            metric_value="1",
        )
        alarm = cloudwatch.Alarm(
            self,
            f"{name}Alarm",
            alarm_name=f"air-cloud-{name.lower()}",
            alarm_description=description,
            metric=metric_filter.metric(period=Duration.minutes(5), statistic="Sum"),
            threshold=5 if name == "ExchangeFailures" else 1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
