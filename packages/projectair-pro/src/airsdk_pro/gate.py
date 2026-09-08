"""``@requires_pro`` decorator for gating Pro features at call time."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from airsdk_pro.license import (
    LicenseError,
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseMissingError,
    has_feature,
    load_license,
)

_F = TypeVar("_F", bound=Callable[..., Any])


def requires_pro(*, feature: str | None = None) -> Callable[[_F], _F]:
    """Decorate a function so it refuses to run without a valid Pro license.

    Parameters
    ----------
    feature:
        Optional feature flag the license must include in its ``features``
        list. ``None`` means any valid Pro license unlocks this function.

    Raises ``LicenseMissingError`` / ``LicenseInvalidError`` /
    ``LicenseExpiredError`` (subclasses of :class:`LicenseError`) at call time
    so callers can present a clear remediation message to the user.
    """
    def _wrap(fn: _F) -> _F:
        @wraps(fn)
        def _gated(*args: Any, **kwargs: Any) -> Any:
            license_obj = load_license()
            if not license_obj.is_paid:
                raise LicenseInvalidError(
                    "this feature requires a paid tier; the installed grant is for the free tier. "
                    "See https://vindicara.io/pricing"
                )
            if feature is not None and not license_obj.has_feature(feature):
                raise LicenseInvalidError(
                    f"this feature requires the {feature!r} entitlement; your current "
                    f"{license_obj.tier} license does not include it. See "
                    "https://vindicara.io/pricing"
                )
            return fn(*args, **kwargs)

        return _gated  # type: ignore[return-value]

    return _wrap


__all__ = [
    "LicenseError",
    "LicenseExpiredError",
    "LicenseInvalidError",
    "LicenseMissingError",
    "has_feature",
    "requires_pro",
]
