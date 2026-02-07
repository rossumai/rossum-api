from __future__ import annotations

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.organization_group import OrganizationGroup


@pytest.fixture
def dummy_organization_group():
    return {
        "id": 42,
        "name": "Rossum group",
        "is_trial": False,
        "is_production": True,
        "deployment_location": "prod-eu",
        "features": None,
        "usage": {},
        "modified_by": "https://elis.rossum.ai/api/v1/users/10775",
        "modified_at": "2021-04-26T10:08:03.856648Z",
    }


@pytest.mark.asyncio
class TestOrganizationGroups:
    async def test_list_organization_groups(
        self, elis_client, dummy_organization_group, mock_generator
    ):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_organization_group)

        organization_groups = client.list_organization_groups()

        async for og in organization_groups:
            assert og == OrganizationGroup(**dummy_organization_group)

        http_client.fetch_all.assert_called_with(Resource.OrganizationGroup, ())

    async def test_retrieve_organization_group(self, elis_client, dummy_organization_group):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_organization_group

        og_id = dummy_organization_group["id"]
        organization_group = await client.retrieve_organization_group(og_id)

        assert organization_group == OrganizationGroup(**dummy_organization_group)

        http_client.fetch_one.assert_called_with(Resource.OrganizationGroup, og_id)


class TestOrganizationGroupsSync:
    def test_list_organization_groups(self, elis_client_sync, dummy_organization_group):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_organization_group,))

        organization_groups = client.list_organization_groups()

        for og in organization_groups:
            assert og == OrganizationGroup(**dummy_organization_group)

        http_client.fetch_resources.assert_called_with(Resource.OrganizationGroup, ())

    def test_retrieve_organization_group(self, elis_client_sync, dummy_organization_group):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_organization_group

        og_id = dummy_organization_group["id"]
        organization_group = client.retrieve_organization_group(og_id)

        assert organization_group == OrganizationGroup(**dummy_organization_group)

        http_client.fetch_resource.assert_called_with(Resource.OrganizationGroup, og_id)
