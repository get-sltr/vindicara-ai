"""Project AIR Layer 3: containment.

Layer 1 lets you prove what happened. Layer 2 lets you explain why.
Layer 3 lets you stop the bad thing from happening in the first place.

The package ships:

- :class:`ContainmentPolicy` and :class:`PolicyVerdict` for declaring
  what the agent is and is not allowed to do, plus what requires
  authenticated human approval.
- :class:`Auth0Verifier` for validating step-up approvals against an
  Auth0 (or any OIDC + JWKS) tenant. ``HUMAN_APPROVAL`` records on the
  chain bind the verified human identity to the action they
  authorized.
- :class:`BlockedActionError` and :class:`StepUpRequiredError` raised
  by ``AIRRecorder.tool_start`` when a rule trips, plus
  :class:`ApprovalInvalidError` and :class:`ChallengeNotFoundError`
  raised by ``AIRRecorder.approve`` when a token is rejected.

The hosted approval router (challenge dispatch, tenant management,
audit reports) lives in the commercial ``projectair-pro`` tier. The
Apache-2.0 package is the primitive every tier builds on; an OSS user with
their own Auth0 tenant can wire all of this up directly.
"""
from __future__ import annotations

from airsdk.containment.auth0 import Auth0Claims, Auth0Verifier
from airsdk.containment.auth0_flows import (
    Auth0DeviceFlowError,
    Auth0Tenant,
    DeviceAuthorization,
    build_authorize_url,
    make_pkce_pair,
    poll_device_token,
    start_device_flow,
)
from airsdk.containment.exceptions import (
    ApprovalInvalidError,
    BlockedActionError,
    ChallengeNotFoundError,
    ContainmentError,
    StepUpRequiredError,
)
from airsdk.containment.policy import (
    ContainmentPolicy,
    Decision,
    PolicyVerdict,
)
from airsdk.containment.require_delegation import (
    DelegationPolicy,
    EnforcementMode,
    declares_delegation,
    evaluate_require_delegation,
    should_require_delegation,
)

__all__ = [
    "ApprovalInvalidError",
    "Auth0Claims",
    "Auth0DeviceFlowError",
    "Auth0Tenant",
    "Auth0Verifier",
    "BlockedActionError",
    "ChallengeNotFoundError",
    "ContainmentError",
    "ContainmentPolicy",
    "Decision",
    "DelegationPolicy",
    "DeviceAuthorization",
    "EnforcementMode",
    "PolicyVerdict",
    "StepUpRequiredError",
    "build_authorize_url",
    "declares_delegation",
    "evaluate_require_delegation",
    "make_pkce_pair",
    "poll_device_token",
    "should_require_delegation",
    "start_device_flow",
]
