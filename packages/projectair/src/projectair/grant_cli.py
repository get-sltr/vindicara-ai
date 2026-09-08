"""``air grant``: pull this workspace's entitlements from the console.

The workspace's tier in AIR Cloud is the authority for what is gated, on
every tier including free. ``air grant`` asks the console for the signed
grant that tier earns and installs it where ``airsdk_pro`` already looks
(``~/.airsdk/license.json``). Nothing local is gated: the whole package
runs free and open source without a grant. The grant only unlocks the paid tier's
features in ``projectair-pro``.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import TypedDict

import typer

_DEFAULT_CLOUD_URL = "https://cloud.vindicara.io"
_TIMEOUT_SECONDS = 10


class GrantPayload(TypedDict):
    workspace_id: str
    tier: str
    email: str
    expires_at: int
    features: list[str]
    token: dict[str, object]


class GrantError(Exception):
    """The console did not hand back a grant."""


def register(app: typer.Typer) -> None:
    """Attach the grant command to ``app``."""
    app.command(name="grant")(grant_cmd)


def grant_cmd(
    api_key: str | None = typer.Option(
        None, "--api-key", envvar="AIRSDK_CLOUD_API_KEY",
        help="Workspace API key (air_...). Issued in the Flightdeck console under Keys.",
    ),
    url: str | None = typer.Option(
        None, "--url", envvar="AIRSDK_CLOUD_URL", help=f"AIR Cloud endpoint (default: {_DEFAULT_CLOUD_URL}).",
    ),
) -> None:
    """Pull this workspace's entitlement grant from the console and install it.

    Every tier gets a grant, free included; a free grant unlocks nothing and
    only records which workspace you are on. Paid grants unlock the tier's
    features in projectair-pro. Grants last 30 days; run again to renew.
    """
    if not api_key:
        typer.secho(
            "A workspace API key is required. Pass --api-key or set AIRSDK_CLOUD_API_KEY.\n"
            "Issue one in the console: https://vindicara.io/dashboard (Keys).",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=2)
    base = (url or _DEFAULT_CLOUD_URL).rstrip("/")
    try:
        grant = fetch_grant(base, api_key)
    except GrantError as exc:
        typer.secho(f"Grant failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    _report(grant)
    _install(grant)


def fetch_grant(base_url: str, api_key: str) -> GrantPayload:
    """GET the grant for the workspace ``api_key`` belongs to."""
    if not base_url.startswith(("https://", "http://")):
        raise GrantError(f"console URL must be http(s): {base_url!r}")
    request = urllib.request.Request(  # noqa: S310 (scheme checked above)
        f"{base_url}/v1/entitlements/grant",
        headers={"X-API-Key": api_key, "Accept": "application/json", "User-Agent": "air-cli"},
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310 (scheme checked above)
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        raise GrantError(f"console answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GrantError(f"could not reach {base_url}: {exc}") from exc
    if not isinstance(body, dict) or not isinstance(body.get("token"), dict):
        raise GrantError("console response carried no token")
    return GrantPayload(
        workspace_id=str(body.get("workspace_id", "")),
        tier=str(body.get("tier", "")),
        email=str(body.get("email", "")),
        expires_at=int(body.get("expires_at", 0)),
        features=[str(f) for f in body.get("features", [])],
        token=dict(body["token"]),
    )


def _report(grant: GrantPayload) -> None:
    typer.secho(f"Grant for workspace {grant['workspace_id']}: {grant['tier']} tier", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  email:     {grant['email']}")
    typer.echo(f"  features:  {', '.join(grant['features']) if grant['features'] else '(none: free tier)'}")


def _install(grant: GrantPayload) -> None:
    try:
        from airsdk_pro.license import LicenseError, install_license
    except ImportError:
        if grant["tier"] == "free":
            typer.echo("  Nothing to install: everything local is free. Upgrade at https://vindicara.io/pricing")
            return
        typer.secho(
            "  This grant unlocks projectair-pro features. Install it, then run `air grant` again:\n"
            "    pip install projectair-pro",
            fg=typer.colors.YELLOW,
        )
        return
    try:
        installed = install_license(json.dumps(grant["token"]))
    except LicenseError as exc:
        typer.secho(f"  Grant refused by the local verifier: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"  installed: {installed.days_remaining} day(s) remaining; run `air grant` again to renew")
    typer.echo("  check:     air status")
