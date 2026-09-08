"""ECS Fargate + ALB for the server-rendered vindicara.io (adapter-node).

Replaces the static S3/CloudFront export with a live Node server so the
Flightdeck console runs dynamic + real-time in the same app. Lives in the
workload region (us-west-2) because the ALB and its ACM certificate are
regional (unlike the CloudFront cert in :mod:`site_stack`, which must be
us-east-1).

The same container image is the self-hostable Flightdeck artifact: a customer
runs it in their own VPC / air-gapped network, so security headers live in the
app (vindicara-site/src/hooks.server.js), not at a CloudFront edge that a
self-hosted deployment would not have.

Deploy: VINDICARA_AWS_ACCOUNT_ID=... cdk deploy VindicaraSiteServer
(requires Docker running locally; CDK builds + pushes the image as an asset).
"""

import os

from aws_cdk import CfnOutput, Duration, Environment, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_logs as logs
from aws_cdk import aws_route53 as route53
from constructs import Construct

DOMAIN = "vindicara.io"

# vindicara-site/ relative to this file: stacks -> infra -> vindicara -> src -> repo root.
_SITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "vindicara-site")
)


class SiteServerStack(Stack):
    """Server-rendered vindicara.io on Fargate behind an ALB (us-west-2)."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        # AIR Cloud, not the engine API. The console's only backend is AIR Cloud
        # (POST /v1/auth/exchange, /v1/runs, /v1/keys). Pointing this at the
        # engine (qk0ymrk5be / vindicara-api) makes every console call hit the
        # engine's APIKeyAuth middleware, which answers "Invalid API key.
        # Provide a valid key via X-Vindicara-Key header." and sign-in dies
        # right after Auth0 succeeds. This value is also the CSP connect-src
        # allowance in hooks.server.js, so it must be the origin the browser
        # actually calls.
        api_origin: str = "https://cloud.vindicara.io",
        env: Environment | None = None,
    ) -> None:
        super().__init__(scope, construct_id, env=env)

        # Default VPC + public subnets: Fargate tasks get a public IP to pull the
        # image and reach the API, so there is no NAT gateway to pay for.
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)
        zone = route53.HostedZone.from_lookup(self, "Zone", domain_name=DOMAIN)

        # Regional ACM cert for the ALB (DNS-validated against the hosted zone).
        certificate = acm.Certificate(
            self,
            "AlbCertificate",
            domain_name=DOMAIN,
            subject_alternative_names=[f"www.{DOMAIN}"],
            validation=acm.CertificateValidation.from_dns(zone),
        )

        # CDK builds vindicara-site/Dockerfile and pushes it as an asset image.
        # Pin LINUX_AMD64: the build host may be arm64 (Apple Silicon) but the
        # Fargate service runs the default X86_64 runtime platform. An arm64
        # image on x86 Fargate fails to start ("exec format error"), so the
        # asset arch must match the task arch. CDK cross-builds via buildx.
        image = ecr_assets.DockerImageAsset(
            self,
            "SiteImage",
            directory=_SITE_DIR,
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        cluster = ecs.Cluster(self, "SiteCluster", vpc=vpc, container_insights=True)

        log_group = logs.LogGroup(
            self,
            "SiteLogs",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "SiteService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            assign_public_ip=True,
            public_load_balancer=True,
            # Do NOT let the ALB do the http->https redirect: its redirect action
            # templates the port into the Location (https://vindicara.io:443/),
            # which strict domain verifiers reject as a different host. Instead we
            # forward :80 to the app (below) and redirect to clean https in
            # hooks.server.js, where the Location has no port.
            redirect_http=False,
            certificate=certificate,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            # No domain_name/domain_zone on purpose: do NOT auto-create the
            # vindicara.io A-record. The live record still points at CloudFront,
            # so the static site stays up. Verify this ALB at its own DNS first,
            # then cut vindicara.io -> ALB as a deliberate, reversible step.
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(image),
                container_port=3000,
                environment={
                    "NODE_ENV": "production",
                    "PORT": "3000",
                    # This app reads Auth0 + API config via $env/dynamic/public,
                    # i.e. from the Node server's process.env at RUNTIME (not
                    # inlined at build time). These are public client-side values
                    # (they mirror the GitHub repo Variables the old static
                    # workflow injected) and are not secrets. Without them the
                    # Flightdeck console boots with "Auth0 is not configured" and
                    # login breaks. This stack is now the source of truth for them.
                    "PUBLIC_AIR_API_MODE": "live",
                    "PUBLIC_AIR_API_BASE": api_origin,
                    "PUBLIC_AUTH0_DOMAIN": "dev-kilt2vkudvbu75ny.us.auth0.com",
                    "PUBLIC_AUTH0_CLIENT_ID": "GszbWqSkD65eUjv7FrRWYO4IkmGWdd4y",
                    "PUBLIC_AUTH0_AUDIENCE": "https://api.vindicara.io",
                    # Also passed for the security-header hook's CSP (hooks.server.js).
                    "AIR_API_ORIGIN": api_origin,
                },
                log_driver=ecs.LogDrivers.aws_logs(stream_prefix="site", log_group=log_group),
            ),
            health_check_grace_period=Duration.seconds(30),
        )

        # Forward plain HTTP (:80) to the app so it issues a clean http->https
        # redirect (redirect_http=False above). hooks.server.js returns
        # 301 -> https://vindicara.io/... with no ":443" port artifact.
        #
        # NOTE: this listener is added in a SECOND deploy. CloudFormation creates
        # a new listener before deleting the old redirect one, which conflicts on
        # port 80; so the first deploy runs with redirect_http=False and no :80
        # listener (removes the old redirect), then this is added on the next.
        service.load_balancer.add_listener(
            "HttpForward",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.forward([service.target_group]),
        )

        # SvelteKit's node server returns 200 on /; 200-399 covers any redirect.
        service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200-399",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Connection draining so in-flight requests finish on deploy/scale-in.
        service.target_group.set_attribute("deregistration_delay.timeout_seconds", "20")

        scaling = service.service.auto_scale_task_count(min_capacity=2, max_capacity=6)
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=60,
            scale_in_cooldown=Duration.seconds(120),
            scale_out_cooldown=Duration.seconds(60),
        )

        CfnOutput(self, "AlbDnsName", value=service.load_balancer.load_balancer_dns_name)
        CfnOutput(self, "ServiceUrl", value=f"https://{DOMAIN}")
        CfnOutput(self, "EcrImageUri", value=image.image_uri)

        self.service = service
        self.certificate = certificate
