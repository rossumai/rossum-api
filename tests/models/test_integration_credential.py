from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models import deserialize_default
from rossum_api.models.integration_credential import (
    CoupaSandOAuth2Secret,
    IntegrationCredential,
    IntegrationCredentialKind,
    IntegrationCredentialTestResult,
)

if TYPE_CHECKING:
    from typing import Any


@pytest.fixture
def dummy_integration_credential() -> dict[str, Any]:
    return {
        "id": 42,
        "url": "https://elis.rossum.ai/api/v1/integration_credentials/42",
        "name": "Acme Corp — Coupa prod",
        "type": "coupa_sand_oauth2",
        "secret": {
            "client_id": "a1b2c3d4",
            "client_secret": "[redacted...]",
            "base_api_url": "https://example.coupahost.com",
            "scope": "core.invoice.create core.common.read",
        },
        "hooks": ["https://elis.rossum.ai/api/v1/hooks/1500"],
        "organization": "https://elis.rossum.ai/api/v1/organizations/1",
        "created_by": "https://elis.rossum.ai/api/v1/users/9524",
        "created_at": "2026-01-01T15:02:25.653324Z",
        "modified_by": "https://elis.rossum.ai/api/v1/users/10775",
        "modified_at": "2026-04-26T10:08:03.856648Z",
    }


@pytest.fixture
def dummy_unknown_type_credential(dummy_integration_credential: dict[str, Any]) -> dict[str, Any]:
    return {
        **dummy_integration_credential,
        "type": "some_future_type",
        "secret": {"api_key": "[redacted...]"},
    }


class TestIntegrationCredentialModel:
    def test_deserialize_coupa_sand_oauth2(
        self, dummy_integration_credential: dict[str, Any]
    ) -> None:
        credential = deserialize_default(
            Resource.IntegrationCredential, dummy_integration_credential
        )

        assert isinstance(credential, IntegrationCredential)
        assert credential.type == IntegrationCredentialKind.COUPA_SAND_OAUTH2
        assert credential.secret == CoupaSandOAuth2Secret(**dummy_integration_credential["secret"])

    def test_deserialize_unknown_type_is_rejected(
        self, dummy_unknown_type_credential: dict[str, Any]
    ) -> None:
        with pytest.raises(ValueError, match="some_future_type"):
            deserialize_default(Resource.IntegrationCredential, dummy_unknown_type_credential)

    def test_serialization_roundtrip(self, dummy_integration_credential: dict[str, Any]) -> None:
        """Test that credential can be deserialized from a payload and serialized back to it."""
        credential = deserialize_default(
            Resource.IntegrationCredential, dummy_integration_credential
        )

        credential_dict = asdict(credential)

        assert credential_dict == dummy_integration_credential
        assert deserialize_default(Resource.IntegrationCredential, credential_dict) == credential


class TestIntegrationCredentialTestResultModel:
    @pytest.mark.parametrize(
        "payload",
        [
            {
                "status": "ok",
                "error": None,
                "granted_scopes": ["core.common.read", "core.invoice.create"],
                "missing_scopes": [],
            },
            {
                "status": "failed",
                "error": "Invalid client credentials.",
                "granted_scopes": None,
                "missing_scopes": None,
            },
        ],
        ids=["ok", "failed"],
    )
    def test_serialization_roundtrip(self, payload: dict[str, Any]) -> None:
        result = deserialize_default(Resource.IntegrationCredentialTestResult, payload)

        assert result == IntegrationCredentialTestResult(**payload)
        assert asdict(result) == payload
