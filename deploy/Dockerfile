# Self-hosted / air-gapped AIR Enterprise unit.
#
# A regulated buyer runs this image entirely inside their own network. It boots
# only after the offline license gate passes (airsdk_pro.serve:main), and it
# persists every forensic chain, tenant, and API key to a mounted volume, so no
# data ever leaves their walls and nothing is lost on restart.
#
# Build (context = repo root):
#   docker build -f deploy/Dockerfile -t air-enterprise:local .
#
# Run (license + data volume mounted; no network required):
#   docker run --rm -p 8080:8080 \
#     -v "$PWD/license.json:/etc/airsdk/license.json:ro" \
#     -v air-data:/var/lib/airsdk \
#     air-enterprise:local
#
# With no valid license mounted, the container prints the reason and exits 1.
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Source for all three packages: the Apache-2.0 SDK (projectair), the Apache engine
# that owns vindicara.cloud (vindicara), and the commercial gate (projectair-pro).
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY packages/projectair/ ./packages/projectair/
COPY packages/projectair-pro/ ./packages/projectair-pro/

# Install in dependency order. projectair first so the pinned SDK is already
# present; then the engine with its API extra (fastapi/uvicorn/etc.); then the
# commercial gate with its deploy extra. cryptography floors are aligned across
# all three, so this resolves without a pre-release.
RUN pip install ./packages/projectair \
    && pip install ".[api]" \
    && pip install "./packages/projectair-pro[deploy]"

# Run as an unprivileged user. The license mounts read-only at
# /etc/airsdk/license.json; durable data lives on the /var/lib/airsdk volume.
RUN useradd --create-home --uid 10001 air \
    && mkdir -p /var/lib/airsdk /etc/airsdk \
    && chown -R air:air /var/lib/airsdk /etc/airsdk

USER air

ENV AIRSDK_DATA_DIR=/var/lib/airsdk \
    AIRSDK_LICENSE_PATH=/etc/airsdk/license.json \
    AIRSDK_HOST=0.0.0.0 \
    AIRSDK_PORT=8080 \
    AIRSDK_AIR_GAPPED=1

EXPOSE 8080

# air-server gates on the license, then serves. Exits non-zero if the gate fails.
ENTRYPOINT ["air-server"]
