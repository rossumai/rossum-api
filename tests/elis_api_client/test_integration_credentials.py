from __future__ import annotations

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.integration_credential import (
    IntegrationCredential,
    IntegrationCredentialKind,
    IntegrationCredentialTestResult,
)


@pytest.fixture
def dummy_integration_credential():
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
def expected_integration_credential(dummy_integration_credential):
    return IntegrationCredential.from_dict(dummy_integration_credential)


@pytest.fixture
def credential_data():
    return {
        "name": "Acme Corp — Coupa prod",
        "type": "coupa_sand_oauth2",
        "secret": {
            "client_id": "a1b2c3d4",
            "client_secret": "s3cr3t",
            "base_api_url": "https://example.coupahost.com",
            "scope": "core.invoice.create core.common.read",
        },
    }


@pytest.fixture
def dummy_test_result():
    return {
        "status": "ok",
        "error": None,
        "granted_scopes": ["core.common.read", "core.invoice.create"],
        "missing_scopes": [],
    }


@pytest.fixture
def expected_test_result(dummy_test_result):
    return IntegrationCredentialTestResult(**dummy_test_result)


@pytest.mark.asyncio
class TestIntegrationCredentials:
    async def test_list_integration_credentials(
        self,
        elis_client,
        dummy_integration_credential,
        expected_integration_credential,
        mock_generator,
    ):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_integration_credential)

        credentials = client.list_integration_credentials()

        async for c in credentials:
            assert c == expected_integration_credential

        http_client.fetch_all.assert_called_with(Resource.IntegrationCredential, ())

    async def test_list_integration_credentials_with_filters(
        self,
        elis_client,
        dummy_integration_credential,
        expected_integration_credential,
        mock_generator,
    ):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_integration_credential)

        credentials = client.list_integration_credentials(
            ordering=["-name"], type="coupa_sand_oauth2"
        )

        async for c in credentials:
            assert c == expected_integration_credential

        http_client.fetch_all.assert_called_with(
            Resource.IntegrationCredential, ["-name"], type="coupa_sand_oauth2"
        )

    async def test_retrieve_integration_credential(
        self, elis_client, dummy_integration_credential, expected_integration_credential
    ):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        credential = await client.retrieve_integration_credential(cid)

        assert credential == expected_integration_credential

        http_client.fetch_one.assert_called_with(Resource.IntegrationCredential, cid)

    async def test_create_new_integration_credential(
        self,
        elis_client,
        dummy_integration_credential,
        expected_integration_credential,
        credential_data,
    ):
        client, http_client = elis_client
        http_client.create.return_value = dummy_integration_credential

        credential = await client.create_new_integration_credential(credential_data)

        assert credential == expected_integration_credential

        http_client.create.assert_called_with(Resource.IntegrationCredential, credential_data)

    async def test_update_integration_credential(
        self,
        elis_client,
        dummy_integration_credential,
        expected_integration_credential,
        credential_data,
    ):
        client, http_client = elis_client
        http_client.replace.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        credential = await client.update_integration_credential(cid, credential_data)

        assert credential == expected_integration_credential

        http_client.replace.assert_called_with(
            Resource.IntegrationCredential, cid, credential_data
        )

    async def test_update_part_integration_credential(
        self, elis_client, dummy_integration_credential, expected_integration_credential
    ):
        client, http_client = elis_client
        http_client.update.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        data = {"name": "Acme Corp — Coupa prod"}
        credential = await client.update_part_integration_credential(cid, data)

        assert credential == expected_integration_credential

        http_client.update.assert_called_with(Resource.IntegrationCredential, cid, data)

    async def test_delete_integration_credential(self, elis_client, dummy_integration_credential):
        client, http_client = elis_client
        http_client.delete.return_value = None

        cid = dummy_integration_credential["id"]
        await client.delete_integration_credential(cid)

        http_client.delete.assert_called_with(Resource.IntegrationCredential, cid)

    async def test_test_integration_credential(
        self, elis_client, dummy_test_result, expected_test_result
    ):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_test_result

        result = await client.test_integration_credential(42)

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST", "integration_credentials/42/test", json={}
        )

    async def test_test_integration_credential_with_partial_secret(
        self, elis_client, dummy_test_result, expected_test_result
    ):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_test_result

        # Only the changed key is sent, the rest of the stored secret is merged in by the API
        secret = {"client_secret": "n3w-s3cr3t"}
        result = await client.test_integration_credential(42, secret=secret)

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST",
            "integration_credentials/42/test",
            json={"secret": {"client_secret": "n3w-s3cr3t"}},
        )

    async def test_test_unsaved_integration_credential(
        self, elis_client, dummy_test_result, expected_test_result, credential_data
    ):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_test_result

        secret = credential_data["secret"]
        result = await client.test_unsaved_integration_credential(
            IntegrationCredentialKind.COUPA_SAND_OAUTH2, secret
        )

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST",
            "integration_credentials/test",
            json={"type": "coupa_sand_oauth2", "secret": secret},
        )


class TestIntegrationCredentialsSync:
    def test_list_integration_credentials(
        self, elis_client_sync, dummy_integration_credential, expected_integration_credential
    ):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_integration_credential,))

        credentials = client.list_integration_credentials()

        for c in credentials:
            assert c == expected_integration_credential

        http_client.fetch_resources.assert_called_with(Resource.IntegrationCredential, ())

    def test_retrieve_integration_credential(
        self, elis_client_sync, dummy_integration_credential, expected_integration_credential
    ):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        credential = client.retrieve_integration_credential(cid)

        assert credential == expected_integration_credential

        http_client.fetch_resource.assert_called_with(Resource.IntegrationCredential, cid)

    def test_create_new_integration_credential(
        self,
        elis_client_sync,
        dummy_integration_credential,
        expected_integration_credential,
        credential_data,
    ):
        client, http_client = elis_client_sync
        http_client.create.return_value = dummy_integration_credential

        credential = client.create_new_integration_credential(credential_data)

        assert credential == expected_integration_credential

        http_client.create.assert_called_with(Resource.IntegrationCredential, credential_data)

    def test_update_integration_credential(
        self,
        elis_client_sync,
        dummy_integration_credential,
        expected_integration_credential,
        credential_data,
    ):
        client, http_client = elis_client_sync
        http_client.replace.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        credential = client.update_integration_credential(cid, credential_data)

        assert credential == expected_integration_credential

        http_client.replace.assert_called_with(
            Resource.IntegrationCredential, cid, credential_data
        )

    def test_update_part_integration_credential(
        self, elis_client_sync, dummy_integration_credential, expected_integration_credential
    ):
        client, http_client = elis_client_sync
        http_client.update.return_value = dummy_integration_credential

        cid = dummy_integration_credential["id"]
        data = {"name": "Acme Corp — Coupa prod"}
        credential = client.update_part_integration_credential(cid, data)

        assert credential == expected_integration_credential

        http_client.update.assert_called_with(Resource.IntegrationCredential, cid, data)

    def test_delete_integration_credential(self, elis_client_sync, dummy_integration_credential):
        client, http_client = elis_client_sync
        http_client.delete.return_value = None

        cid = dummy_integration_credential["id"]
        client.delete_integration_credential(cid)

        http_client.delete.assert_called_with(Resource.IntegrationCredential, cid)

    def test_test_integration_credential(
        self, elis_client_sync, dummy_test_result, expected_test_result
    ):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_test_result

        result = client.test_integration_credential(42)

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST", "integration_credentials/42/test", json={}
        )

    def test_test_integration_credential_with_partial_secret(
        self, elis_client_sync, dummy_test_result, expected_test_result
    ):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_test_result

        # Only the changed key is sent, the rest of the stored secret is merged in by the API
        secret = {"client_secret": "n3w-s3cr3t"}
        result = client.test_integration_credential(42, secret=secret)

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST",
            "integration_credentials/42/test",
            json={"secret": {"client_secret": "n3w-s3cr3t"}},
        )

    def test_test_unsaved_integration_credential(
        self, elis_client_sync, dummy_test_result, expected_test_result, credential_data
    ):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_test_result

        secret = credential_data["secret"]
        result = client.test_unsaved_integration_credential(
            IntegrationCredentialKind.COUPA_SAND_OAUTH2, secret
        )

        assert result == expected_test_result

        http_client.request_json.assert_called_with(
            "POST",
            "integration_credentials/test",
            json={"type": "coupa_sand_oauth2", "secret": secret},
        )
