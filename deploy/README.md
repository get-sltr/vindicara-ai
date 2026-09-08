# AIR Enterprise, self-hosted / air-gapped unit (beta)

**Run Project AIR entirely inside your own network. It verifies its license
offline and refuses to start without one, and it persists every forensic chain,
tenant, and API key to a volume you control, so your regulated data never leaves
your walls and nothing is lost on restart.**

This is the deployable artifact for regulated buyers (healthcare, finance,
public sector) who cannot send data to a hosted service. It is a single
container: the AIR Cloud ingest API, gated at startup by an offline Ed25519
license check and backed by durable filesystem storage. No AWS, no outbound
network, no phone-home.

## What the container does, in order

1. **Gate.** `air-server` runs the offline license preflight. If the license is
   missing, invalid, tampered, expired, or not an Enterprise tier, it prints the
   reason and **exits non-zero**. The API never starts. This is the entire
   security contract of the tier: no valid Enterprise license, no server.
2. **Serve.** Only on a clean gate, it serves the ingest API (`/v1/capsules`,
   `/v1/workspaces`, ...) behind uvicorn, backed by durable stores under
   `AIRSDK_DATA_DIR`. Capsules append to a per-workspace JSONL log; workspaces
   and API keys persist to JSON files. A restart recovers the full history.

## Build

Build from the repo root (the image needs all three packages: the Apache-2.0 SDK, the
engine, and the commercial gate):

```bash
docker build -f deploy/Dockerfile -t air-enterprise:local .
```

## Run

Mount a signed license read-only and a data volume for durability:

```bash
docker run --rm -p 8080:8080 \
  -v "$PWD/license.json:/etc/airsdk/license.json:ro" \
  -v air-data:/var/lib/airsdk \
  -e AIR_CLOUD_ADMIN_TOKEN=<operator-token> \
  air-enterprise:local
```

With no valid license mounted, the container prints the reason and exits 1.

## Configuration (environment only)

| Variable | Default | Meaning |
| --- | --- | --- |
| `AIRSDK_LICENSE_PATH` | `/etc/airsdk/license.json` | Signed license to verify at startup |
| `AIRSDK_DATA_DIR` | `/var/lib/airsdk` | Durable data directory (mount a volume) |
| `AIRSDK_HOST` / `AIRSDK_PORT` | `0.0.0.0` / `8080` | Bind address |
| `AIRSDK_AIR_GAPPED` | `1` | Surfaces the air-gapped anchoring advisory |
| `AIR_CLOUD_ADMIN_TOKEN` | (unset) | Operator token gating `POST /v1/workspaces`; unset disables workspace creation (fail-closed) |

## 60-second proof

`deploy/demo_selfhosted.sh` builds the image and proves all three properties end
to end: it refuses to start without a license, boots with a valid Enterprise
license, then POSTs a signed capsule, restarts the container, and shows the
capsule (and its workspace and key) survived the restart. Requires Docker and,
to mint the demo license, the operator vendor signing key.

```bash
bash deploy/demo_selfhosted.sh
```

## Air-gapped anchoring

Layer 1 external anchoring (Sigstore Rekor, FreeTSA) reaches public endpoints
that are unreachable air-gapped. Air-gapped deployments must either disable
anchoring or point it at a private RFC 3161 TSA (`tsa_url=`) or an HSM checkpoint
key. The startup report prints this advisory when `AIRSDK_AIR_GAPPED=1` and the
`[anchoring]` extra is installed, so chains are never left silently unanchored.

## Readiness boundary (honest)

This unit is **beta**. What that means, precisely:

- **Proven:** the license gate (full reject matrix, fail-closed on any error),
  boot, and durable persistence across restart are covered by tests and the
  runnable demo above.
- **Single-node only.** The filesystem stores are a single-container design.
  There is no HA, no multi-node coordination, and no automatic backup of the
  data volume yet. Back up `AIRSDK_DATA_DIR` with your own volume snapshots.
- **Not yet production-labeled.** Production requires an SLO, monitoring, a
  restore runbook, and a load-tested storage tier (Postgres) for high volume.
  Those are the gaps between beta and production; do not represent them as done.
- **License lifecycle is manual air-gapped.** Renewals must be installed by hand
  before expiry (`air install-license`); the startup report warns at <= 30 days.
