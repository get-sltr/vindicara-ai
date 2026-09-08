"""AWS Lambda entry point for AIR Cloud using Mangum.

DynamoDB table names are read from environment variables set by the
AirCloudStack CDK construct. The factory auto-wires DDB stores when
those env vars are present.
"""

from mangum import Mangum

from vindicara.cloud.secrets import hydrate_env_from_secrets

# Secrets are handed to the function as ARNs; export their values before any
# module that reads os.environ at import time is loaded. A configured secret
# that cannot be read raises here, so the function never serves on a default.
hydrate_env_from_secrets()

from vindicara.cloud.factory import create_air_cloud_app  # noqa: E402

app = create_air_cloud_app()
handler = Mangum(app, lifespan="off")
