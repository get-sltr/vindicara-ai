# The five-minute loop: sign in, get keys, paste the snippet, see the first run (plan, 2026-09-07)

## Context

Langfuse and LangSmith are the competitors. The user's own words for the gap: "when I
install Langfuse I get secret keys, all the API keys I need to set it up, the screen shows
it. And I don't have that." Project AIR must own this loop on its own product.

Verified state of the tree (three read-only explorations, spot-checked):
- **No end user can get a workspace or a key.** `POST /v1/workspaces` is operator-only
  (`src/vindicara/cloud/routes/workspaces.py:54-93`, `admin.py:30-52`). `/v1/sso/login` needs
  a pre-provisioned workspace with an SSO config. `air login` (`cli.py:1165-1218`) never
  calls AIR Cloud. Today every Auth0 user lands as `admin` in the one shared `ws_vindicara`
  workspace via env-seeded SSO (`factory.py:53-70`, `air_cloud_stack.py:112-115`).
- **The console never talks to AIR Cloud.** It stores the raw Auth0 token and calls
  endpoints that do not exist (`vindicara-site/src/lib/console/api/live.ts`). No workspace
  store, no keys screen, no snippet. Dead demo sign-in surfaces are mounted in the live
  layout (`components/LockScreen.svelte`, `components/forensics/SignIn.svelte`).
- **The SDK cannot reach the cloud with defaults.** `HTTPTransport` defaults to header
  `X-Vindicara-Key` (`airsdk/transport.py:148`) but the server reads only `X-API-Key`
  (`middleware.py:103`). No env-driven cloud transport exists. `AIRCallbackHandler` builds a
  disk-only recorder (`callback.py:38-47`). Nothing prints a run link.
- **No run concept server-side.** `StoredCapsule(workspace_id, record, api_key_id)`; capsules
  are a flat list; `analytics.py:120` hardcodes chain health.
- **Deployed-stack defects:** `factory.py:201` never calls the existing
  `_resolve_admin_token` (Secrets Manager path dead, `POST /v1/workspaces` is 503);
  `VINDICARA_SESSION_SECRET`, `VINDICARA_API_KEY_HMAC_SECRET`, and
  `VINDICARA_LICENSE_SIGNING_KEY_PEM` are not in the Lambda env; `DDBWorkspaceStore` never
  writes or reads `tier`; CORS lacks PATCH; site `PUBLIC_AUTH0_AUDIENCE` is
  `cabinet-coach.v2` (another project). `cloud.vindicara.io` already resolves to an API
  Gateway custom domain created outside CDK (leave it).

Decisions taken with the user (2026-09-07): Auth0 audience `https://api.vindicara.io` for
console and CLI; no free-tier expiry in this build; resetting existing keys when the real
HMAC secret lands is acceptable; the first trace lands in a Runs list + run detail.

**Customer value:** sign in to Flightdeck, copy one snippet, and the first run your agent
makes is on screen, signed, with its own link, while the local chain stays on your disk.
**Readiness:** `beta` on Keys, Runs, `air login`, `air push`, and the CHANGELOG entry.
**Do not touch:** `packages/projectair/src/airsdk/integrations/langfuse.py` and its test
(owned by another session).

## Phase 0: infra and secrets (unblocks every deployed step)

Files: `src/vindicara/infra/stacks/air_cloud_stack.py`, `site_server_stack.py:47,124`,
new `src/vindicara/cloud/secrets.py`, `cloud/lambda_handler.py`, `cloud/factory.py`.

- `secrets.py`: `hydrate_env_from_secrets(mapping)`: for each `NAME -> NAME_ARN`, if `NAME`
  unset and the ARN env set, read Secrets Manager and set `os.environ[NAME]`; log and skip on
  failure (existing fail-closed paths then apply). Called from `lambda_handler.py` before
  `create_air_cloud_app()`. Names: `VINDICARA_SESSION_SECRET`, `VINDICARA_API_KEY_HMAC_SECRET`,
  `VINDICARA_LICENSE_SIGNING_KEY_PEM`, `AIR_CLOUD_ADMIN_TOKEN`.
- `factory.py:201`: `app.state.cloud_admin_token = _resolve_admin_token(admin_token)`; add
  `PATCH` to CORS `allow_methods`.
- CDK: two generated secrets (session, HMAC), one imported by name
  (`air-cloud-license-signing-key`, created by hand from the PEM whose public half is in
  `airsdk_pro`), grants + `*_ARN` env vars; new table `air-cloud-identities` (pk
  `identity_id`); capsules GSIs `by_content_hash` (ws + content_hash) and `by_run`
  (ws + run_id), one GSI per deploy (CloudFormation limit); env
  `AIR_CLOUD_OIDC_ISSUER`, `AIR_CLOUD_OIDC_AUDIENCE=https://api.vindicara.io`,
  `AIR_CLOUD_PUBLIC_URL`, `AIR_CLOUD_CONSOLE_URL`; delete the `AIR_CLOUD_SSO_*` seeds
  (closes the shared-admin hole; `_seed_sso_from_env` stays for self-hosters); CORS
  preflight adds PATCH.
- `site_server_stack.py`: `PUBLIC_AUTH0_AUDIENCE=https://api.vindicara.io`.
- Tests: `tests/unit/cloud/test_secrets_hydrate.py` (fake boto3 client). `cdk synth`.

## Phase 1: server: identity link and `POST /v1/auth/exchange`

Files: new `cloud/identity_store.py`, `cloud/ddb_identity_store.py`, `cloud/signup.py`,
`cloud/routes/auth.py`; modify `cloud/middleware.py`, `cloud/factory.py`,
`cloud/ddb_workspace_store.py`.

- `IdentityLink(identity_id, issuer, sub, workspace_id, email, created_at)`,
  `identity_id_for(issuer, sub) = "idn_" + sha256(f"{issuer}|{sub}")[:32]`. Store protocol
  `get`, `link` (put-if-absent, returns the winner). DDB uses
  `attribute_not_exists(identity_id)`; link-first ordering means a lost race reads the
  winner's workspace and never orphans one.
- `signup.py`: `ServiceOidc(issuer, audience, jwks_uri)` from env; `as_sso_config()` so the
  existing `verify_oidc_token` (`sso.py:97-154`) is reused unchanged; `resolve_email` (claims
  `email`, then `https://vindicara.io/email`, then `{issuer}userinfo` with the bearer token,
  best effort, 3 s); `provision_identity(...) -> Provisioned(workspace, key_id, role,
  api_key | None, created)`: link first with `ws_<12 hex>`, create workspace
  (`name = "<local-part>'s workspace"`, tier `free`, owner_email), owner key
  `key_{ws}_owner` created only if absent and its secret returned only when minted now.
- Route `POST /v1/auth/exchange` `{token}` -> `{session_token, workspace, role, key_id,
  api_key | None, created, email, sub, cloud_url, console_url}`; 201 on create, 200 after;
  503 without service OIDC; 401 on verification failure. Session TTL 3600 s. Add the path to
  `UNAUTHED_PATHS`; middleware also accepts `X-Vindicara-Key` as a legacy alias.
- `factory.py`: kwargs `identity_store`, `service_oidc`; DDB wiring requires
  `AIR_CLOUD_IDENTITIES_TABLE`; `app.state.cloud_url` / `console_url`; include `auth.router`.
- `ddb_workspace_store.py`: write `tier` on create, read `tier` (default `free`).
- Tests (pattern: `tests/unit/cloud/test_sso_session.py`, `test_middleware.py`):
  `test_identity_store.py`, `test_auth_exchange.py` (first 201 with key, second 200 without,
  different sub gets a different workspace, 503/401 paths, session token works on
  `GET /v1/keys` as owner), legacy header alias, workspace tier round-trip.

## Phase 2: SDK: correct header, zero-config mirror, callback passthrough, run URL

Files (`packages/projectair/src/airsdk/`): new `cloud_config.py`, new `_http_transport.py`
(HTTPTransport moved, `transport.py` re-exports to stay under 300 lines), modify
`recorder.py` (~12 lines, uses existing `add_transport` at :227), `live.py`, `callback.py`.

- `cloud_config.py`: `DEFAULT_CLOUD_URL`, `DEFAULT_CONSOLE_URL`,
  `CloudConfig(api_key, url, console_url)`, `cloud_config_from_env()`
  (`AIRSDK_CLOUD_API_KEY` required; `AIRSDK_CLOUD_URL`, `AIRSDK_CONSOLE_URL` optional),
  `genesis_step_id(records)`, `run_url(console_url, run_id) = f"{console}/runs/{run_id}"`.
- `HTTPTransport`: header default `X-API-Key`; `from_config(cfg)`; worker batches up to 100
  queued records to `/v1/capsules/bulk` as NDJSON (one record still goes to `/v1/capsules`).
- `AIRRecorder`: when `transports is None` and the env config exists, append
  `HTTPTransport.from_config(cfg)` to the default `[FileTransport]` (local chain kept);
  property `run_url`; first emit calls `live.announce_cloud(url)`.
- `live.py`: banner line `[air] mirroring to AIR Cloud: <run url>`; summary ends with
  `[air] Flightdeck: <run url>`.
- `AIRCallbackHandler(..., recorder=None, transports=None)`: `recorder=` wins.
- Tests: `test_transport.py` (header, bulk NDJSON, `from_config`), new `test_cloud_config.py`,
  `test_recorder.py` (env adds the second transport, file still written), new
  `test_callback.py`, `test_live.py` (URL in banner and summary).

## Phase 3: server: runs

Files: modify `cloud/capsule_store.py` (`StoredCapsule.run_id: str = ""`; protocol adds
`find_by_content_hash(ws, content_hash)` and `for_run(ws, run_id)`; InMemory + JSONL impls),
`cloud/ddb_capsule_store.py` (persist `content_hash`, `run_id`; query the two GSIs), new
`cloud/runs.py` (pure functions), new `cloud/routes/runs.py`, modify `routes/capsules.py`.

- `resolve_run_id`: genesis record (prev_hash all zeros) -> its own step_id; else the run of
  the record whose content_hash equals prev_hash; parent not yet ingested -> own step_id
  (documented limitation). Ingest and bulk persist it and return it.
- `order_chain`, `group_runs` (legacy rows with empty run_id walked in memory),
  `summarize_run`, `build_run_detail` = `verify_chain` + `run_detectors` +
  `airsdk.incident.assemble_incident` + `airsdk.health.assess_health`.
- Models: `RunSummary {run_id, started_at, last_at, records, kinds, user_intent, signer_key,
  verification, findings, max_severity, console_url}`, `RunsPage`, `RunDetail {run_id,
  workspace_id, records, verification, findings, timeline, health, console_url}`.
  `GET /v1/runs?limit&offset` (READ_CAPSULES, member/viewer scoped like
  `routes/capsules.py:118`), `GET /v1/runs/{run_id}` (404 outside scope).
- SSE stays for self-hosted; the console polls (Lambda cannot hold SSE).
- Tests: `test_runs.py` (grouping, ordering, orphan fallback, legacy rows),
  `test_runs_route.py` (bulk ingest 4 records -> one run, ordered detail with 4 timeline
  entries, member scoping), `test_capsule_store.py` additions.

## Phase 4: console: cloud session, Keys screen, Runs screens, cleanup

Files (`vindicara-site/src/`): new `lib/console/api/cloud.ts` (`CloudClient`: `exchange`,
`me`, `listKeys`, `issueKey`, `revokeKey`, `listRuns`, `getRun`; Bearer = AIR session token;
one re-exchange on 401), `api/cloud-types.ts`, `stores/cloud.ts` (`cloudSession` in
sessionStorage, `freshApiKey` memory only, `establishCloudSession`, `refreshCloudSession`,
`clearCloudSession` hooked into `logout()`/`lockSession()`).

- `routes/flightdeck/auth/callback/+page.svelte`: after `unlock(token)`, exchange; go to
  `/flightdeck/keys?welcome=1` when a key was minted, else `/flightdeck/runs`.
- New screens (split to respect 300 lines): `screens/Keys.svelte` + `keys/KeyReveal.svelte`,
  `keys/KeyTable.svelte`, `keys/SetupSnippets.svelte`, `keys/snippets.ts` (workspace, tier,
  cloud URL, shown-once reveal with copy, create/revoke, framework tabs with the real key
  substituted while `freshApiKey` exists); `screens/Runs.svelte` (table, 3 s polling while
  visible, empty state "Waiting for your first run" with the plain-recorder snippet);
  `screens/RunDetail.svelte` + `runs/RunTable.svelte` (ordinal, time, kind, what executed,
  authority, evidence, findings from `timeline.entries`) + `runs/RecordPanel.svelte`
  (prompt/response/tool args/output/metadata/hashes); reuse
  `components/forensics/IntegrityPanel.svelte` for the verification block. Routes
  `flightdeck/keys`, `flightdeck/runs`, `flightdeck/runs/[run_id]`. Drawer gets Runs and Keys
  at the top.
- Remove `LockScreen.svelte` and `forensics/SignIn.svelte` and their mounts in
  `routes/flightdeck/+layout.svelte`; `Overview.svelte:134` goes to `/flightdeck/sign-in/`.
- `/get-started`: fix the LangChain snippet, add a "Send to Flightdeck" step; move snippet
  arrays to a shared `snippets.ts` so the page and the Keys screen cannot drift.
- Brand rules: "AIR" in `--air` red everywhere, no dim text, no SF Mono.
- Tests (vitest): `api/cloud.test.ts` (exchange body, 401 re-exchange once), `keys/snippets.test.ts`
  (every snippet has `AIRRecorder(`, LangChain uses `recorder=recorder`), `stores/cloud.test.ts`
  (`freshApiKey` never persisted), layout source test (no LockScreen / SignIn).

## Phase 5: CLI: `air login` exchange, `air push` bulk + link, shared cloud config

Files (`packages/projectair/src/projectair/`): new `cloud_login.py`
(`exchange_device_token`, `store_cloud_login` -> `cloud.workspace_id|url|console_url|api_key`
in config.toml), new `cloud_target.py` (`resolve_cloud_target(flag, flag)`: flag, env,
config; used by `push_cli.py` and `grant_cli.py`), `config.py` (`_write_toml` mode 0600),
`cli.py` `login` (exchange after `save_session`, print workspace, key shown once, console URL;
failure is a warning, local login still succeeds) and `whoami`, `push_cli.py` (NDJSON chunks
of 200 to `/v1/capsules/bulk`, per-record fallback on 404, print `Run: <console>/runs/<id>`).
Tests: `test_cloud_login.py`, `test_cloud_target.py`, `test_push_cli.py`, `test_config.py` mode.

## Phase 6: proof, docs

- `scripts/e2e_first_five_minutes.py` (under 60 s, offline): local JWKS server + RS256 token
  (iss local, aud `https://api.vindicara.io`), uvicorn with `create_air_cloud_app(service_oidc=...)`
  and in-memory stores, exchange -> 201 with key, fresh venv `pip install -e packages/projectair`,
  six-line recorder script under `AIRSDK_CLOUD_API_KEY` / `AIRSDK_CLOUD_URL`, assert stderr has
  `mirroring to AIR Cloud:` and a `/runs/` URL, `GET /v1/runs` shows one run of 4 verified
  records with a 4-entry timeline and a health level, second exchange is 200 without a key.
- CHANGELOG `[Unreleased]` entries (beta), `docs/air-cloud-deploy.md` notes (two GSI deploys,
  key reset on HMAC rotation, hand-created license secret, Auth0 API check),
  `docs/superpowers/plans/2026-09-07-five-minute-loop.md`, README CLI table (`air login`
  now yields a workspace and key).

## Setup snippets the Keys screen renders

Header on every tab: `pip install projectair` and `export AIRSDK_CLOUD_API_KEY=air_<key>`
(plus `export AIRSDK_CLOUD_URL=<url>` only when the console's base differs from the default).

```python
# OpenAI (and any OpenAI-compatible endpoint)
from openai import OpenAI
from airsdk import AIRRecorder
from airsdk.integrations.openai import instrument_openai
recorder = AIRRecorder("agent.jsonl", user_intent="Summarize the quarterly report")
client = instrument_openai(OpenAI(), recorder)

# Anthropic
from airsdk.integrations.anthropic import instrument_anthropic
client = instrument_anthropic(Anthropic(), recorder)

# LangChain
from airsdk import AIRCallbackHandler
handler = AIRCallbackHandler(recorder=recorder)
agent.invoke({"input": "..."}, config={"callbacks": [handler]})

# Gemini / LlamaIndex: instrument_gemini(genai.Client(), recorder) / instrument_llamaindex(llm, recorder)

# Plain recorder (any framework)
recorder.llm_start(prompt="..."); recorder.tool_start(tool_name="search", tool_args={"q": "..."})
recorder.tool_end(tool_output="..."); recorder.agent_finish(final_output="...")
```
Every tab ends: "Run it. The terminal prints your run link: https://vindicara.io/flightdeck/runs/<run_id>".

## Verification

1. Unit: `pytest tests/unit/cloud` (engine, 80% floor via `./scripts/test.sh`),
   `cd packages/projectair && pytest tests && ruff check . && mypy src`,
   `cd vindicara-site && npm run check && npm run test`.
2. End to end: `python scripts/e2e_first_five_minutes.py` passes in under 60 s.
3. Manual after deploy: sign in at `/flightdeck`, land on Keys with a shown-once key, paste
   the OpenAI snippet, run, see the run in Runs within 3 s, open detail, revoke the key and
   confirm the next run 401s locally (warning only) and stops appearing.

## Effort

About 6.5 engineering days: Phase 0 half a day (plus two sequential `AirCloud` deploys and one
site deploy), Phase 1 one day, Phase 2 one day, Phase 3 one day, Phase 4 two days, Phase 5
half a day, Phase 6 half a day.

## Amendments after external review (2026-09-07, verified against the tree)

Confirmed facts that change the design:
- `AIRRecorder` never resumes a chain: `Signer` starts at genesis (`agdr.py:144`) and
  `FileTransport` appends (`transport.py:98`). Each process is its own run (good), but the
  fixed `agent.jsonl` filename in the snippets makes `air trace` report `broken_chain` on the
  second run. Fix: `log_path` becomes optional and defaults to `.air/air-trace-<unix>.log`
  (same as the callback), and every snippet uses `AIRRecorder(user_intent=...)`.
- The device flow already sends `audience` (`auth0_flows.py:100`); the tenant-side API and
  client authorizations are external tasks, and the CLI must fail loud when exchange fails.
- `verify_oidc_token` builds a new `PyJWKClient` per call: no JWKS caching. Add a
  per-jwks-uri cached client.
- `HTTPTransport` already drains at exit (`transport.py:162,195`); the live summary hook is
  registered later (`recorder.py:195`) so it runs first. The summary must drain transports
  before printing the run link.
- Chains are always signed by the agent's own Ed25519 key; verification never depends on
  `airsdk_pro`. Review item 14 does not apply.
- `airsdk` is unregistered on PyPI (404). Squat risk for the import name people will type.

Adopted changes:
1. **Release gate.** Publish `projectair` 1.4.0 before the site deploy that exposes Keys;
   snippet header is `pip install "projectair>=1.4"`; register an `airsdk` stub on PyPI that
   depends on `projectair` (packaging task, needs PyPI credentials).
2. **Client sends the run id.** `X-AIR-Run-Id` header (genesis step_id, computed by the SDK
   and `air push`), outside the signed record. Server trusts it for new clients; bulk
   ingest without the header resolves lineage in memory across the batch (the DAG pass)
   with one store lookup per batch root; legacy single records fall back to their own
   step_id and are regrouped at read time. Drops the `by_content_hash` GSI and one deploy.
3. **Precomputed runs.** New `air-cloud-runs` table (pk workspace_id, sk run_id, GSI
   `by_last_at` pk workspace_id sk last_at) upserted at ingest with count, kinds, first/last
   timestamps, user_intent, signer_key, findings count, max_severity. `GET /v1/runs` is one
   Query. Verification and detectors run on detail, not on list.
4. **Bounded detail.** `GET /v1/runs/{id}` returns summary, verification, health, findings,
   and timeline entries without payload bodies; `GET /v1/runs/{id}/records?offset&limit`
   pages the records; `GET /v1/capsules/{step_id}` serves one body. Ingest rejects records
   over 350 KB with 413 and a clear message (DynamoDB item limit); documented limitation.
5. **Hydration fails closed.** When any `*_ARN` is set and the value is still missing after
   hydration, the Lambda refuses to build the app. Generated secrets get `RETAIN`; the HMAC
   secret is documented as non-rotatable without invalidating every key.
6. **Exchange lock-down.** `azp` must be in `AIR_CLOUD_OIDC_CLIENT_IDS`; cached JWKS;
   email fallback name `workspace <sub[:8]>`; identity lookup by `(iss, sub)` first, then by
   verified email for the same issuer so Google and password logins share one workspace;
   exchange creates a missing linked workspace or owner key idempotently.
7. **SDK safety.** `AIRSDK_CLOUD=off` kill switch; banner says payloads are mirrored;
   retry with backoff on 429/5xx, warn once and stop on 401/403, never block the agent;
   summary drains before printing the link.
8. **Ops.** CloudWatch alarms on exchange 5xx and ingest 5xx, a log line per exchange
   outcome, and a hydration-failure metric. Delete the `AIR_CLOUD_SSO_*` seeds in the Phase 1
   deploy, not Phase 0, so an auth path always exists.
9. **Tests.** DDB stores run once against moto if it is available, otherwise fakes; the e2e
   uses `uv` and a local wheel, budget 90 s.
10. **Effort.** 10 to 12 days. Blocking for beta: items 1, 2, 3, 4, 5, 7 above plus the
    Auth0 tenant tasks (API `https://api.vindicara.io`, both clients authorized, an Action
    adding a verified-email claim, account linking on).

## Out of scope (next)

Free-tier 7-day TTL; the Langfuse-class runs table (filters, search, columns, sessions,
users, scores, alerts, datasets); Flightdeck grant button; custom-domain CDK ownership.
