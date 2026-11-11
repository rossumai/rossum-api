from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import dacite


class IntegrationCredentialKind(str, Enum):
    """Type of an integration credential; determines the shape of its ``secret``.

    Each member maps to a dataclass describing the shape of its secret.

    Attributes
    ----------
    COUPA_SAND_OAUTH2
        OAuth2 client credentials for the Coupa API,
        see :class:`~rossum_api.models.integration_credential.CoupaSandOAuth2Secret`.
    """

    COUPA_SAND_OAUTH2 = "coupa_sand_oauth2"


@dataclass
class CoupaSandOAuth2Secret:
    """Secret of a ``coupa_sand_oauth2`` integration credential.

    Attributes
    ----------
    client_id
        OAuth2 client ID issued by Coupa.
    client_secret
        OAuth2 client secret issued by Coupa. Masked as ``[redacted...]`` in responses.
    base_api_url
        Base URL of the Coupa instance API.
    scope
        OAuth2 scopes requested for the token, separated by commas or spaces.

    References
    ----------
    https://rossum.app/api/docs/openapi/api/integration-credential/
    """

    client_id: str
    client_secret: str
    base_api_url: str
    scope: str


# To support a new credential type:
#   1. add a member to IntegrationCredentialKind,
#   2. add a dataclass describing its secret (see CoupaSandOAuth2Secret),
#   3. add that dataclass to the IntegrationCredentialSecret and _SecretClass unions,
#   4. map the new member to the dataclass in _TYPE_TO_SECRET,
#   5. document the dataclass in docs/models.rst.
IntegrationCredentialSecret = CoupaSandOAuth2Secret

_SecretClass = type[CoupaSandOAuth2Secret]

_TYPE_TO_SECRET: dict[IntegrationCredentialKind, _SecretClass] = {
    IntegrationCredentialKind.COUPA_SAND_OAUTH2: CoupaSandOAuth2Secret,
}


@dataclass
class IntegrationCredential:
    """Integration credential stores secrets used by hooks to authenticate to external systems.

    Attributes
    ----------
    id
        ID of the integration credential.
    url
        URL of the integration credential.
    name
        Name of the integration credential shown in the UI.
    type
        Type of the credential, see
        :class:`~rossum_api.models.integration_credential.IntegrationCredentialKind`;
        determines the shape of ``secret``. Cannot be changed after creation.
    secret
        Credential content. Structure depends on ``type``, e.g.
        :class:`~rossum_api.models.integration_credential.CoupaSandOAuth2Secret` for
        ``coupa_sand_oauth2``.
    organization
        URL of the :class:`~rossum_api.models.organization.Organization` the credential
        belongs to.
    hooks
        List of URLs of :class:`~rossum_api.models.hook.Hook` objects that use this credential.
    created_by
        URL of the :class:`~rossum_api.models.user.User` who created the credential.
    created_at
        Timestamp of the credential creation.
    modified_by
        URL of the :class:`~rossum_api.models.user.User` who last modified the credential.
    modified_at
        Timestamp of last modification.

    References
    ----------
    https://rossum.app/api/docs/openapi/api/integration-credential/
    """

    id: int
    url: str
    name: str
    type: IntegrationCredentialKind
    secret: IntegrationCredentialSecret
    organization: str
    hooks: list[str]
    created_by: str
    created_at: str
    modified_by: str
    modified_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IntegrationCredential:
        """Create IntegrationCredential from dictionary, resolving the correct secret type."""
        data = data.copy()
        data["type"] = IntegrationCredentialKind(data["type"])
        data["secret"] = dacite.from_dict(_TYPE_TO_SECRET[data["type"]], data["secret"])
        credential: IntegrationCredential = dacite.from_dict(cls, data)
        return credential


IntegrationCredentialTestStatus = Literal["ok", "failed"]


@dataclass
class IntegrationCredentialTestResult:
    """Result of testing an integration credential against the external system.

    Attributes
    ----------
    status
        ``ok`` when a token was obtained and no requested scope is missing, ``failed`` otherwise.
    error
        Human-readable description of the failure. ``None`` when the test passed.
    granted_scopes
        Scopes granted in the issued token. ``None`` when the token could not be obtained or
        the granted scopes could not be determined.
    missing_scopes
        Requested scopes that are not granted in the issued token. ``None`` when the granted
        scopes could not be determined.

    References
    ----------
    https://rossum.app/api/docs/openapi/api/integration-credential/#test-integration-credential
    """

    status: IntegrationCredentialTestStatus
    error: str | None
    granted_scopes: list[str] | None
    missing_scopes: list[str] | None
