# Vindicara Auth System Design Spec

## Purpose

Self-managed authentication for the Vindicara dashboard. No third-party auth providers. Vindicara is a security company; we own our auth end to end.

## Scope

- Signup (email + password)
- Login with bcrypt verification
- JWT sessions (HttpOnly cookies)
- CSRF protection on all POST
- Login rate limiting (5 failed = 15 min lockout)
- Email verification via SES
- TOTP MFA (authenticator app)
- API key management (create, revoke, rotate, scope)
- Session revocation
- DynamoDB storage (single-table design)

## Architecture

### File Structure

```
src/vindicara/dashboard/
  auth/
    __init__.py
    models.py         # Pydantic models: SignupRequest, LoginRequest, User, Session, APIKey
    passwords.py      # bcrypt hashing and verification
    tokens.py         # JWT creation, validation, refresh, CSRF
    mfa.py            # TOTP setup, verification (pyotp)
    store.py          # DynamoDB user/session/key storage
    middleware.py      # Auth middleware for dashboard routes
    routes.py         # Auth page routes (signup, login pages)
    api.py            # Auth API endpoints (POST signup, login, logout, etc.)
  keys/
    __init__.py
    models.py         # API key models
    manager.py        # Key generation, hashing, rotation, scoping
    routes.py         # Key management page
    api.py            # Key CRUD API endpoints
  templates/
    pages/
      login.html      # Login page
      signup.html      # Signup page
      mfa_setup.html   # MFA setup page
      api_keys.html    # API key management page
```

### DynamoDB Single-Table Design

Uses the existing `vindicara-policies` table (or a new `vindicara-users` table).

```
PK: USER#<user_id>          SK: PROFILE              # email, password_hash, created_at, verified, mfa_enabled
PK: USER#<user_id>          SK: KEY#<key_id>         # key_hash, scopes, created_at, rotated_from
PK: USER#<user_id>          SK: SESSION#<session_id> # jwt_id, created_at, expires_at, revoked (TTL)
PK: USER#<user_id>          SK: MFA#totp             # encrypted_secret, backup_codes

GSI1 (email lookup):
GSI1PK: EMAIL#<email>       GSI1SK: USER#<user_id>

GSI2 (API key lookup):
GSI2PK: APIKEY#<key_hash>   GSI2SK: USER#<user_id>
```

### Security Requirements

- bcrypt cost factor 12
- JWT: 15 min access token, 7 day refresh token
- Cookies: HttpOnly, Secure, SameSite=Strict
- CSRF token on all state-changing requests
- 5 failed login attempts = 15 min lockout (stored in DynamoDB with TTL)
- API keys: SHA-256 hashed before storage, shown once at creation
- Key format: `vnd_live_` + 32 random bytes (hex)
- Key scoping: guard, mcp, agents, monitor, compliance
- Key rotation: 24hr grace period on old key
- TOTP via pyotp (RFC 6238)
- Email verification tokens: 24hr expiry, single use

### Dependencies to Add

- `bcrypt` - password hashing
- `PyJWT` - JWT tokens
- `pyotp` - TOTP MFA
- `qrcode` - QR code generation for MFA setup

### Auth Flow

**Signup:**
1. POST /dashboard/api/auth/signup with email + password
2. Validate password complexity (min 12 chars, upper, lower, digit)
3. Hash password with bcrypt (cost 12)
4. Create user in DynamoDB
5. Send verification email via SES
6. Return success (user must verify email before login)

**Login:**
1. POST /dashboard/api/auth/login with email + password
2. Check lockout status
3. Look up user by email (GSI1)
4. Verify bcrypt hash
5. If MFA enabled, return mfa_required flag
6. If MFA not enabled (or after MFA verify), issue JWT pair
7. Set access token in HttpOnly cookie
8. Set refresh token in separate HttpOnly cookie
9. Set CSRF token in non-HttpOnly cookie (JS readable)

**Protected Routes:**
1. Dashboard auth middleware checks access token cookie
2. If expired, try refresh via refresh token cookie
3. If refresh valid, issue new access token
4. If refresh expired, redirect to login
5. All POST requests must include CSRF token header matching cookie

**API Key Usage:**
1. SDK users authenticate via X-Vindicara-Key header
2. Key hash looked up in DynamoDB (GSI2)
3. Scopes checked against requested operation
4. Rate limiting per key

### In-Memory Fallback

For local development and demo mode, the store uses in-memory dicts instead of DynamoDB. The store interface is the same; the implementation switches based on `VINDICARA_STAGE`.

### Pages

**Login (/dashboard/login):**
- Email + password form
- "Sign up" link
- Error messages for invalid credentials, locked out, unverified email

**Signup (/dashboard/signup):**
- Email + password + confirm password
- Password strength indicator
- "Already have an account?" link

**MFA Setup (/dashboard/settings/mfa):**
- QR code for authenticator app
- Manual entry key
- Verification code input to confirm setup

**API Keys (/dashboard/api-keys):**
- List of active keys (masked, last 4 chars visible)
- Create new key (name, scopes selection)
- Revoke button per key
- Rotate button (creates new, 24hr grace on old)
- Key shown once at creation in a copy-able box

---

## Production Readiness (Addendum, 2026-04-15)

This section captures operational decisions made after the initial implementation but before the production plan. It resolves ambiguities in the original spec so the implementation plan can be pure execution.

### JWT Secret Management

- Secret source: `VINDICARA_JWT_SECRET` environment variable, read once at app startup via `VindicaraSettings`, not at module import time. This fixes the cold-start bug where every Lambda invocation was regenerating the signing key and invalidating all existing JWTs.
- Dev/test fallback: if `VINDICARA_JWT_SECRET` is empty, generate a random secret once per process (stable within a process, different across processes). This preserves local dev ergonomics without the prod footgun.
- Production injection: CDK wires the Lambda environment variable from AWS Secrets Manager. The secret is created out-of-band (one-time) and referenced in `api_stack.py` via `secrets_manager.Secret.from_secret_name_v2`. Secret rotation is not automated in this plan; document the rotation procedure instead.
- Tests use a fixed hardcoded secret via settings override.

### DynamoDB Storage

- New table: `vindicara-users`. Not folded into `vindicara-policies`. Rationale: different access patterns, different GSI layout, different TTL needs, cleaner IAM scoping.
- Schema follows the single-table design from the main spec:
  - `PK=USER#<user_id>, SK=PROFILE` — user record
  - `PK=USER#<user_id>, SK=SESSION#<session_id>` — active sessions, TTL on `expires_at`
  - `PK=USER#<user_id>, SK=KEY#<key_id>` — API key records (including revoked + rotated ones, kept for audit)
  - `PK=USER#<user_id>, SK=VERIFY#<token>` — email verification tokens, TTL 24h
  - `PK=USER#<user_id>, SK=MFA#totp` — encrypted TOTP secret, backup codes
  - `GSI1PK=EMAIL#<email>, GSI1SK=USER#<user_id>` — email lookup for login
  - `GSI2PK=APIKEY#<key_hash>, GSI2SK=USER#<user_id>` — key hash lookup for SDK auth
- CDK: add the table in `DataStack`, grant `APIStack` Lambda read/write on it, pass table name via env `VINDICARA_USERS_TABLE`.
- Store implementation: introduce a `UserStoreBackend` protocol with `InMemoryBackend` (current behavior) and `DynamoBackend`. `get_user_store()` selects based on `VINDICARA_STAGE` and whether `VINDICARA_USERS_TABLE` is set. Tests continue to use in-memory.

### API Key Store Unification

- Delete the duplicate in-memory `APIKeyStore` in `api/middleware/auth.py`. The public API middleware must consult `dashboard/keys/manager.py::APIKeyManager.validate_key` so keys created in the dashboard actually authenticate real SDK calls.
- Scope enforcement: `APIKeyAuthMiddleware` maps request path to required scope (e.g. `/v1/guard/*` → `guard`, `/v1/scans/*` → `mcp`, `/v1/agents/*` → `agents`, `/v1/monitor/*` → `monitor`, `/v1/reports/*` → `compliance`). Missing scope returns 403.
- Dev keys (like `vnd_test` used in tests) are still supported by pre-seeding the `APIKeyManager` via `create_app(dev_api_keys=[...])`. The seeded keys get all scopes.

### Email Verification with SES (with Dev Fallback)

- Mailer interface: `dashboard/auth/mailer.py` exposes `Mailer.send_verification_email(to: str, token: str)`.
- Implementations: `SESMailer` (uses `boto3` SES) and `LoggingMailer` (structlog at info level, no network call). Factory picks based on `VINDICARA_STAGE`.
- Signup flow change: `store.create_user` now sets `verified=False`. The signup endpoint generates a verification token, stores it in DynamoDB with 24h TTL, and calls `mailer.send_verification_email`. Response redirects to `/dashboard/verify-pending` instead of straight into the dashboard.
- Verify endpoint: `GET /dashboard/verify?token=<token>` — looks up token, marks user verified, consumes token, redirects to login with a success flash.
- Login change: if user is not verified, return an error with a "resend verification" link instead of issuing tokens.
- Resend endpoint: `POST /dashboard/api/auth/resend-verification` — rate-limited (1 per minute per email) to prevent abuse.
- SES requirements: verified sender identity (e.g. `noreply@vindicara.io`). Not automated in CDK for this plan; document the one-time setup. Sandbox-to-production move is also documented, not automated.

### Refresh Token Flow

- Middleware behavior: when `decode_token(access)` returns empty and the path is not public, the middleware attempts refresh:
  1. Decode `vnd_refresh` cookie. If invalid or expired, fall through to the existing redirect/401 path.
  2. Look up the session by `sid` in the store. If revoked, treat as expired.
  3. Mint a new access token, attach it to the response as a `Set-Cookie` header via a wrapper, and continue the request.
- Implementation note: Starlette `BaseHTTPMiddleware` makes response mutation awkward; use a simple wrapper that calls `call_next`, then sets the cookie on the returned response. This works because we only mutate headers, not body.
- Logout still revokes the session via `store.revoke_session(sid)`; the refresh flow honors this.

### Key Rotation Grace Enforcement

- `APIKeyManager.validate_key` treats a key with `grace_expires` past `now` as revoked, returning `None`.
- `rotate_key` sets `grace_expires` on the old record and the old record's hash remains in `GSI2` during grace. After grace expires, the next `validate_key` call returns `None` (the hash can also be lazily removed from the index).
- The rotation response continues to show the new raw key once.

### MFA Setup Page

- New page: `/dashboard/settings/mfa` with template `pages/mfa_setup.html`.
- Flow: GET renders current MFA status. If disabled, "Enable MFA" button posts to `/dashboard/api/auth/mfa/setup` (existing endpoint), which returns the QR + secret + verify form inline (existing behavior). Verify form posts to `/dashboard/api/auth/mfa/verify` (existing endpoint).
- Disable MFA: new endpoint `POST /dashboard/api/auth/mfa/disable`, requires current TOTP code to disarm.

### Test Matrix

Tests are written TDD-style for all new code and retroactively for existing code. Minimum coverage:

- `tests/unit/dashboard/auth/test_passwords.py` — hash round-trip, complexity validation (all error branches), wrong-password rejection.
- `tests/unit/dashboard/auth/test_tokens.py` — encode/decode round-trip, expired-token rejection, invalid-signature rejection, CSRF constant-time compare.
- `tests/unit/dashboard/auth/test_mfa.py` — TOTP round-trip with pinned time, drift window behavior, QR generation smoke test.
- `tests/unit/dashboard/keys/test_manager.py` — create/revoke/rotate, grace expiration, scope filtering, key hash lookup.
- `tests/unit/dashboard/auth/test_store.py` — user create/lookup/update, lockout threshold, session revoke, verification token consume.
- `tests/integration/dashboard/test_auth_flow.py` — full signup → verify → login → protected route → logout happy path plus unverified login rejection, wrong password lockout after 5 tries, CSRF bypass rejection on state-changing routes.
- `tests/integration/dashboard/test_refresh.py` — expired access token with valid refresh gets a new access cookie and the request succeeds; revoked session refuses refresh.
- `tests/integration/dashboard/test_keys_api.py` — create/list/revoke/rotate via the form endpoints, verifies the one-time raw-key exposure.
- `tests/integration/api/test_public_api_scope.py` — X-Vindicara-Key with insufficient scope returns 403; with correct scope returns 200.
- `tests/integration/dashboard/test_mfa_setup_page.py` — page renders, enable/disable flow works end to end.

### Out of Scope (for this plan)

- Password reset via email link. Documented as a follow-up.
- SOC 2 audit trail beyond structlog events.
- Hardware key (WebAuthn) MFA. TOTP only.
- SAML / SSO. Follow-up when an enterprise customer asks.
- Automated JWT secret rotation.
- SES sender reputation warm-up.
