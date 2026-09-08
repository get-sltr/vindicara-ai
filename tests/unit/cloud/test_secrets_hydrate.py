"""Secret hydration: exports configured secrets, keeps explicit values, fails closed."""

from __future__ import annotations

from typing import Any

import pytest

from vindicara.cloud import secrets as secrets_mod
from vindicara.cloud.secrets import SecretHydrationError, hydrate_env_from_secrets


def _fake_reader(values: dict[str, str]) -> Any:
    def read(arn: str) -> str:
        if arn not in values:
            raise RuntimeError(f"AccessDenied for {arn}")
        return values[arn]

    return read


def test_hydrates_only_configured_and_unset_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secrets_mod, "_read_secret", _fake_reader({"arn:a": "value-a", "arn:b": "value-b"}))
    env = {"A_ARN": "arn:a", "B": "explicit", "B_ARN": "arn:b"}
    hydrated = hydrate_env_from_secrets({"A": "A_ARN", "B": "B_ARN", "C": "C_ARN"}, environ=env)
    assert hydrated == ["A"]
    assert env["A"] == "value-a"
    assert env["B"] == "explicit"
    assert "C" not in env


def test_unreadable_secret_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secrets_mod, "_read_secret", _fake_reader({}))
    env = {"VINDICARA_SESSION_SECRET_ARN": "arn:missing"}
    with pytest.raises(SecretHydrationError, match="VINDICARA_SESSION_SECRET"):
        hydrate_env_from_secrets(environ=env)
    assert "VINDICARA_SESSION_SECRET" not in env


def test_default_mapping_covers_every_secret_the_lambda_needs() -> None:
    assert set(secrets_mod.SECRET_ENV_TO_ARN_ENV) == {
        "VINDICARA_SESSION_SECRET",
        "VINDICARA_API_KEY_HMAC_SECRET",
        "VINDICARA_LICENSE_SIGNING_KEY_PEM",
        "AIR_CLOUD_ADMIN_TOKEN",
    }
