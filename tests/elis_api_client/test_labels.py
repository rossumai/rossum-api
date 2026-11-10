from __future__ import annotations

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.label import Label


@pytest.fixture
def dummy_label():
    return {
        "id": 1,
        "url": "https://elis.rossum.ai/api/v1/labels/1",
        "name": "expedite",
        "organization": "https://elis.rossum.ai/api/v1/organizations/1",
        "color": "#FF5733",
    }


@pytest.fixture
def expected_label(dummy_label):
    return Label(**dummy_label)


@pytest.fixture
def apply_labels_args():
    annotations = [
        "https://elis.rossum.ai/api/v1/annotations/101",
        "https://elis.rossum.ai/api/v1/annotations/102",
    ]
    add = ["https://elis.rossum.ai/api/v1/labels/1"]
    remove = ["https://elis.rossum.ai/api/v1/labels/2"]
    return annotations, add, remove


@pytest.mark.asyncio
class TestLabels:
    async def test_list_labels(self, elis_client, dummy_label, expected_label, mock_generator):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_label)

        labels = client.list_labels()

        async for label in labels:
            assert label == expected_label

        http_client.fetch_all.assert_called_with(Resource.Label, ())

    async def test_list_labels_with_filters(
        self, elis_client, dummy_label, expected_label, mock_generator
    ):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_label)

        labels = client.list_labels(ordering=["name"], name="expedite")

        async for label in labels:
            assert label == expected_label

        http_client.fetch_all.assert_called_with(Resource.Label, ["name"], name="expedite")

    async def test_retrieve_label(self, elis_client, dummy_label, expected_label):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_label

        lid = dummy_label["id"]
        label = await client.retrieve_label(lid)

        assert label == expected_label

        http_client.fetch_one.assert_called_with(Resource.Label, lid)

    async def test_create_new_label(self, elis_client, dummy_label, expected_label):
        client, http_client = elis_client
        http_client.create.return_value = dummy_label

        data = {"name": "expedite", "color": "#FF5733"}
        label = await client.create_new_label(data)

        assert label == expected_label

        http_client.create.assert_called_with(Resource.Label, data)

    async def test_update_label(self, elis_client, dummy_label, expected_label):
        client, http_client = elis_client
        http_client.replace.return_value = dummy_label

        lid = dummy_label["id"]
        data = {"name": "expedite", "color": "#FF5733"}
        label = await client.update_label(lid, data)

        assert label == expected_label

        http_client.replace.assert_called_with(Resource.Label, lid, data)

    async def test_update_part_label(self, elis_client, dummy_label, expected_label):
        client, http_client = elis_client
        http_client.update.return_value = dummy_label

        lid = dummy_label["id"]
        data = {"color": "#FF5733"}
        label = await client.update_part_label(lid, data)

        assert label == expected_label

        http_client.update.assert_called_with(Resource.Label, lid, data)

    async def test_delete_label(self, elis_client, dummy_label):
        client, http_client = elis_client
        http_client.delete.return_value = None

        lid = dummy_label["id"]
        await client.delete_label(lid)

        http_client.delete.assert_called_with(Resource.Label, lid)

    async def test_apply_labels(self, elis_client, apply_labels_args):
        client, http_client = elis_client
        annotations, add, remove = apply_labels_args

        await client.apply_labels(annotations, add=add, remove=remove)

        http_client.request_json.assert_called_with(
            "POST",
            "labels/apply",
            json={
                "operations": {"add": add, "remove": remove},
                "objects": {"annotations": annotations},
            },
        )

    async def test_apply_labels_defaults(self, elis_client, apply_labels_args):
        client, http_client = elis_client
        annotations, add, _ = apply_labels_args

        await client.apply_labels(annotations, add=add)

        http_client.request_json.assert_called_with(
            "POST",
            "labels/apply",
            json={
                "operations": {"add": add, "remove": []},
                "objects": {"annotations": annotations},
            },
        )


class TestLabelsSync:
    def test_list_labels(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_label,))

        labels = client.list_labels()

        for label in labels:
            assert label == expected_label

        http_client.fetch_resources.assert_called_with(Resource.Label, ())

    def test_list_labels_with_filters(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_label,))

        labels = client.list_labels(ordering=["name"], name="expedite")

        for label in labels:
            assert label == expected_label

        http_client.fetch_resources.assert_called_with(Resource.Label, ["name"], name="expedite")

    def test_retrieve_label(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_label

        lid = dummy_label["id"]
        label = client.retrieve_label(lid)

        assert label == expected_label

        http_client.fetch_resource.assert_called_with(Resource.Label, lid)

    def test_create_new_label(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.create.return_value = dummy_label

        data = {"name": "expedite", "color": "#FF5733"}
        label = client.create_new_label(data)

        assert label == expected_label

        http_client.create.assert_called_with(Resource.Label, data)

    def test_update_label(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.replace.return_value = dummy_label

        lid = dummy_label["id"]
        data = {"name": "expedite", "color": "#FF5733"}
        label = client.update_label(lid, data)

        assert label == expected_label

        http_client.replace.assert_called_with(Resource.Label, lid, data)

    def test_update_part_label(self, elis_client_sync, dummy_label, expected_label):
        client, http_client = elis_client_sync
        http_client.update.return_value = dummy_label

        lid = dummy_label["id"]
        data = {"color": "#FF5733"}
        label = client.update_part_label(lid, data)

        assert label == expected_label

        http_client.update.assert_called_with(Resource.Label, lid, data)

    def test_delete_label(self, elis_client_sync, dummy_label):
        client, http_client = elis_client_sync
        http_client.delete.return_value = None

        lid = dummy_label["id"]
        client.delete_label(lid)

        http_client.delete.assert_called_with(Resource.Label, lid)

    def test_apply_labels(self, elis_client_sync, apply_labels_args):
        client, http_client = elis_client_sync
        annotations, add, remove = apply_labels_args

        client.apply_labels(annotations, add=add, remove=remove)

        http_client.request_json.assert_called_with(
            "POST",
            "labels/apply",
            json={
                "operations": {"add": add, "remove": remove},
                "objects": {"annotations": annotations},
            },
        )
