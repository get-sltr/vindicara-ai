"""Cold-start secret hydration for the AIR Cloud Lambda.

The CDK stack hands the Lambda secret *ARNs*, never secret values, so nothing
sensitive lands in the CloudFormation template or the function configuration.
At cold start this module reads each secret once and exports it under the
environment name the rest of the code already expects, so modules that read
``os.environ`` at import time (the API-key HMAC, the session secret) see the
real value.

Fail closed: when an ARN is configured and the value cannot be read, the
function must not start. Starting anyway would mean minting keys and session
tokens under a development default, which is exactly the outcome the secrets
exist to prevent.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping

_log = logging.getLogger(__name__)

#: Environment name -> environment name holding its Secrets Manager ARN.
SECRET_ENV_TO_ARN_ENV: dict[str, str] = {
    "VINDICARA_SESSION_SECRET": "VINDICARA_SESSION_SECRET_ARN",
    "VINDICARA_API_KEY_HMAC_SECRET": "VINDICARA_API_KEY_HMAC_SECRET_ARN",
    "VINDICARA_LICENSE_SIGNING_KEY_PEM": "VINDICARA_LICENSE_SIGNING_KEY_PEM_ARN",
    "AIR_CLOUD_ADMIN_TOKEN": "AIR_CLOUD_ADMIN_TOKEN_SECRET_ARN",
}


class SecretHydrationError(RuntimeError):
    """A configured secret could not be read; the service must not start."""


def _read_secret(arn: str) -> str:
    import boto3

    response = boto3.client("secretsmanager").get_secret_value(SecretId=arn)
    value = response.get("SecretString")
    if not value:
        raise SecretHydrationError(f"secret {arn} has no SecretString")
    return str(value)


def hydrate_env_from_secrets(
    mapping: dict[str, str] | None = None,
    *,
    environ: MutableMapping[str, str] | None = None,
) -> list[str]:
    """Export every configured secret into the environment. Returns the names hydrated.

    For each ``NAME -> NAME_ARN`` pair: an already-set ``NAME`` wins (local runs and
    tests set values directly); otherwise, when ``NAME_ARN`` is set, the secret is
    read and exported. A configured ARN whose value cannot be read raises
    :class:`SecretHydrationError`. Pairs with neither set are skipped.
    """
    env: MutableMapping[str, str] = environ if environ is not None else os.environ
    pairs = mapping if mapping is not None else SECRET_ENV_TO_ARN_ENV
    hydrated: list[str] = []
    for name, arn_name in pairs.items():
        if env.get(name):
            continue
        arn = env.get(arn_name)
        if not arn:
            continue
        try:
            env[name] = _read_secret(arn)
        except SecretHydrationError:
            raise
        except Exception as exc:
            raise SecretHydrationError(f"could not read {name} from {arn}: {exc}") from exc
        hydrated.append(name)
        _log.info("air_cloud.secrets.hydrated", extra={"name": name})
    return hydrated


__all__ = ["SECRET_ENV_TO_ARN_ENV", "SecretHydrationError", "hydrate_env_from_secrets"]
