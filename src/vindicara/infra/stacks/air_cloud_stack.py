"""AIR Cloud stack: DynamoDB tables + Lambda + API Gateway.

Deployed independently from the Vindicara engine API. Serves the
hosted capsule ingest surface that the AIR dashboard connects to.
"""

from aws_cdk import Duration, Environment, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

from vindicara.infra.stacks.air_cloud_alarms import add_air_cloud_alarms


class AirCloudStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env: Environment | None = None,
    ) -> None:
        super().__init__(scope, construct_id, env=env)

        self.capsules_table = dynamodb.Table(
            self,
            "CapsulesTable",
            table_name="air-cloud-capsules",
            partition_key=dynamodb.Attribute(
                name="workspace_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="step_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        # A run's records in one query (the run page). One GSI per deploy is
        # the CloudFormation limit; this is the only one the capsules table needs.
        self.capsules_table.add_global_secondary_index(
            index_name="by_run",
            partition_key=dynamodb.Attribute(name="workspace_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="run_id", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.workspaces_table = dynamodb.Table(
            self,
            "WorkspacesTable",
            table_name="air-cloud-workspaces",
            partition_key=dynamodb.Attribute(
                name="workspace_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.api_keys_table = dynamodb.Table(
            self,
            "ApiKeysTable",
            table_name="air-cloud-api-keys",
            partition_key=dynamodb.Attribute(
                name="key_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.api_keys_table.add_global_secondary_index(
            index_name="by_key_hash",
            partition_key=dynamodb.Attribute(
                name="key_hash",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Self-serve sign-in: one row per (issuer, sub), pointing at the
        # workspace that identity owns. by_email joins a second connection
        # (Google today, password tomorrow) to the same workspace when the
        # provider vouches for the email.
        self.identities_table = dynamodb.Table(
            self,
            "IdentitiesTable",
            table_name="air-cloud-identities",
            partition_key=dynamodb.Attribute(name="identity_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.identities_table.add_global_secondary_index(
            index_name="by_email",
            partition_key=dynamodb.Attribute(name="email_key", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Runs: one precomputed summary per (workspace, run) so the console's
        # list is a single Query instead of a scan over every capsule.
        self.runs_table = dynamodb.Table(
            self,
            "RunsTable",
            table_name="air-cloud-runs",
            partition_key=dynamodb.Attribute(name="workspace_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="run_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.runs_table.add_global_secondary_index(
            index_name="by_last_at",
            partition_key=dynamodb.Attribute(name="workspace_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="last_at", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Secrets the Lambda hydrates at cold start (vindicara.cloud.secrets).
        # Generated here so no value ever appears in source or the template;
        # RETAIN because the HMAC secret is a lookup index for every API key:
        # rotating or losing it invalidates every key ever issued.
        self.session_secret = secretsmanager.Secret(
            self,
            "SessionSecret",
            secret_name="air-cloud-session-secret",  # noqa: S106 - resource name
            description="HS256 secret for AIR Cloud dashboard session tokens.",
            generate_secret_string=secretsmanager.SecretStringGenerator(password_length=64, exclude_punctuation=True),
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.api_key_hmac_secret = secretsmanager.Secret(
            self,
            "ApiKeyHmacSecret",
            secret_name="air-cloud-api-key-hmac-secret",  # noqa: S106 - resource name
            description="HMAC key for stored API-key hashes. Never rotate: it is the lookup index.",
            generate_secret_string=secretsmanager.SecretStringGenerator(password_length=64, exclude_punctuation=True),
            removal_policy=RemovalPolicy.RETAIN,
        )
        # Created by hand from the Ed25519 PEM whose public half is embedded in
        # airsdk_pro; CDK only references it, it must never generate it.
        self.license_signing_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "LicenseSigningKey", "air-cloud-license-signing-key"
        )

        # Operator admin token gating POST /v1/workspaces (W3.10). Auto-generated
        # so the secret never lives in source or the CloudFormation template;
        # the Lambda reads it at cold start via the secret ARN below.
        self.admin_token_secret = secretsmanager.Secret(
            self,
            "AdminTokenSecret",
            secret_name="air-cloud-admin-token",  # noqa: S106 - resource name, not a secret value
            description="Operator admin token gating POST /v1/workspaces (W3.10).",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=48,
                exclude_punctuation=True,
            ),
        )

        self.api_function = lambda_.Function(
            self,
            "CloudFunction",
            function_name="air-cloud-api",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="vindicara.cloud.lambda_handler.handler",
            code=lambda_.Code.from_asset("lambda_package"),
            memory_size=256,
            timeout=Duration.seconds(30),
            environment={
                "AIR_CLOUD_CAPSULES_TABLE": self.capsules_table.table_name,
                "AIR_CLOUD_WORKSPACES_TABLE": self.workspaces_table.table_name,
                "AIR_CLOUD_API_KEYS_TABLE": self.api_keys_table.table_name,
                "AIR_CLOUD_IDENTITIES_TABLE": self.identities_table.table_name,
                "AIR_CLOUD_RUNS_TABLE": self.runs_table.table_name,
                "AIR_CLOUD_ADMIN_TOKEN_SECRET_ARN": self.admin_token_secret.secret_arn,
                "VINDICARA_SESSION_SECRET_ARN": self.session_secret.secret_arn,
                "VINDICARA_API_KEY_HMAC_SECRET_ARN": self.api_key_hmac_secret.secret_arn,
                "VINDICARA_LICENSE_SIGNING_KEY_PEM_ARN": self.license_signing_secret.secret_arn,
                # Self-serve sign-in trust (POST /v1/auth/exchange). One API
                # identifier shared by the console and the CLI; both Auth0
                # clients must be authorized for it in the tenant.
                "AIR_CLOUD_OIDC_ISSUER": "https://dev-kilt2vkudvbu75ny.us.auth0.com/",
                "AIR_CLOUD_OIDC_AUDIENCE": "https://api.vindicara.io",
                "AIR_CLOUD_OIDC_CLIENT_IDS": "GszbWqSkD65eUjv7FrRWYO4IkmGWdd4y",
                "AIR_CLOUD_PUBLIC_URL": "https://cloud.vindicara.io",
                "AIR_CLOUD_CONSOLE_URL": "https://vindicara.io/flightdeck",
                # First-run lead capture: the public /v1/identity/register route
                # writes install emails here (table owned by the data stack).
                "VINDICARA_IDENTITY_TABLE": "vindicara-identity-registrations",
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE,
        )

        # Existing identity-registrations table (defined in the data stack). Import
        # by name and grant write so the register route can persist install emails.
        identity_registrations_table = dynamodb.Table.from_table_name(
            self,
            "IdentityRegistrationsImport",
            "vindicara-identity-registrations",
        )

        self.capsules_table.grant_read_write_data(self.api_function)
        self.workspaces_table.grant_read_write_data(self.api_function)
        self.api_keys_table.grant_read_write_data(self.api_function)
        self.identities_table.grant_read_write_data(self.api_function)
        self.runs_table.grant_read_write_data(self.api_function)
        identity_registrations_table.grant_write_data(self.api_function)
        self.admin_token_secret.grant_read(self.api_function)
        self.session_secret.grant_read(self.api_function)
        self.api_key_hmac_secret.grant_read(self.api_function)
        self.license_signing_secret.grant_read(self.api_function)

        self.http_api = apigw.HttpApi(
            self,
            "AirCloudAPI",
            api_name="air-cloud-api",
            default_integration=integrations.HttpLambdaIntegration(
                "CloudLambdaIntegration",
                handler=self.api_function,
            ),
            cors_preflight=apigw.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[
                    apigw.CorsHttpMethod.GET,
                    apigw.CorsHttpMethod.POST,
                    apigw.CorsHttpMethod.PATCH,
                    apigw.CorsHttpMethod.DELETE,
                    apigw.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=["*"],
            ),
        )

        add_air_cloud_alarms(self, function=self.api_function, http_api=self.http_api)
