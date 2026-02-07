from __future__ import annotations

from unittest.mock import call

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.organization import Organization
from rossum_api.models.organization_limit import EmailLimits, OrganizationLimit


@pytest.fixture
def dummy_organization_limit():
    return {
        "email_limits": {
            "count_today": 7,
            "count_today_notification": 4,
            "count_total": 9,
            "email_per_day_limit": 10,
            "email_per_day_limit_notification": 10,
            "email_total_limit": 20,
            "last_sent_at": "2022-01-13",
            "last_sent_at_notification": "2022-01-13",
        }
    }


@pytest.fixture
def dummy_organization():
    return {
        "id": 406,
        "url": "https://elis.rossum.ai/api/v1/organizations/406",
        "name": "East West Trading Co",
        "workspaces": ["https://elis.rossum.ai/api/v1/workspaces/7540"],
        "users": ["https://elis.rossum.ai/api/v1/users/10775"],
        "organization_group": "https://elis.rossum.ai/api/v1/organization_groups/17",
        "ui_settings": {},
        "metadata": {},
        "created_at": "2019-09-02T14:28:11.000000Z",
        "trial_expires_at": "2020-09-02T14:28:11.000000Z",
        "is_trial": True,
        "oidc_provider": "some_oidc_provider",
    }


@pytest.mark.asyncio
class TestOrganizations:
    async def test_list_organizations(self, elis_client, dummy_organization, mock_generator):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_organization)

        organizations = client.list_organizations()

        async for o in organizations:
            assert o == Organization(**dummy_organization)

        http_client.fetch_all.assert_called_with(Resource.Organization, ())

    async def test_retrieve_organization(self, elis_client, dummy_organization):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_organization

        oid = dummy_organization["id"]
        organization = await client.retrieve_organization(oid)

        assert organization == Organization(**dummy_organization)

        http_client.fetch_one.assert_called_with(Resource.Organization, oid)

    async def test_retrieve_own_organization(self, elis_client, dummy_user, dummy_organization):
        client, http_client = elis_client
        http_client.fetch_one.side_effect = [dummy_user, dummy_organization]

        organization = await client.retrieve_own_organization()

        assert organization == Organization(**dummy_organization)

        http_client.fetch_one.assert_has_calls(
            [call(Resource.Auth, "user"), call(Resource.Organization, 406)]
        )

    async def test_retrieve_organization_limit(self, elis_client, dummy_organization_limit):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_organization_limit

        result = await client.retrieve_organization_limit(406)

        assert result == OrganizationLimit(
            email_limits=EmailLimits(**dummy_organization_limit["email_limits"])
        )

        http_client.request_json.assert_called_with("GET", "organizations/406/limits")


class TestOrganizationsSync:
    def test_list_organizations(self, elis_client_sync, dummy_organization):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_organization,))

        organizations = client.list_organizations()

        for o in organizations:
            assert o == Organization(**dummy_organization)

        http_client.fetch_resources.assert_called_with(Resource.Organization, ())

    def test_retrieve_organization(self, elis_client_sync, dummy_organization):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_organization

        oid = dummy_organization["id"]
        organization = client.retrieve_organization(oid)

        assert organization == Organization(**dummy_organization)

        http_client.fetch_resource.assert_called_with(Resource.Organization, oid)

    def test_retrieve_my_organization(self, elis_client_sync, dummy_user, dummy_organization):
        client, http_client = elis_client_sync
        http_client.fetch_resource.side_effect = [dummy_user, dummy_organization]

        organization = client.retrieve_my_organization()

        assert organization == Organization(**dummy_organization)

        http_client.fetch_resource.assert_has_calls(
            [call(Resource.Auth, "user"), call(Resource.Organization, 406)]
        )

    def test_retrieve_organization_limit(self, elis_client_sync, dummy_organization_limit):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_organization_limit

        result = client.retrieve_organization_limit(406)

        assert result == OrganizationLimit(
            email_limits=EmailLimits(**dummy_organization_limit["email_limits"])
        )

        http_client.request_json.assert_called_with("GET", "organizations/406/limits")
