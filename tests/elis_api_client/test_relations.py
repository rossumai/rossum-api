from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.relation import Relation, RelationType

if TYPE_CHECKING:
    from typing import Any
    from unittest.mock import MagicMock

    from rossum_api.clients.external_async_client import (
        AsyncRossumAPIClientWithDefaultDeserializer,
    )
    from rossum_api.clients.external_sync_client import SyncRossumAPIClientWithDefaultDeserializer


@pytest.fixture
def dummy_relation() -> dict[str, Any]:
    return {
        "id": 1500,
        "type": RelationType.EDIT.value,
        "key": None,
        "parent": "https://elis.rossum.ai/api/v1/annotations/123",
        "annotations": [
            "https://elis.rossum.ai/api/v1/annotations/456",
            "https://elis.rossum.ai/api/v1/annotations/457",
        ],
        "url": "https://elis.rossum.ai/api/v1/relations/1500",
    }


@pytest.mark.asyncio
class TestRelations:
    async def test_list_relations(
        self,
        elis_client: tuple[AsyncRossumAPIClientWithDefaultDeserializer, MagicMock],
        dummy_relation: dict[str, Any],
        mock_generator,
    ) -> None:
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_relation)

        relations = client.list_relations()

        async for r in relations:
            assert r == Relation(**dummy_relation)

        http_client.fetch_all.assert_called_with(Resource.Relation, ())

    async def test_list_relations_with_filters(
        self,
        elis_client: tuple[AsyncRossumAPIClientWithDefaultDeserializer, MagicMock],
        dummy_relation: dict[str, Any],
        mock_generator,
    ) -> None:
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_relation)

        relations = client.list_relations(
            type=RelationType.EDIT.value,
            parent=123,
            key=None,
            annotation=456,
        )

        async for r in relations:
            assert r == Relation(**dummy_relation)

        http_client.fetch_all.assert_called_with(
            Resource.Relation,
            (),
            type=RelationType.EDIT.value,
            parent=123,
            key=None,
            annotation=456,
        )


class TestRelationsSync:
    def test_list_relations(
        self,
        elis_client_sync: tuple[SyncRossumAPIClientWithDefaultDeserializer, MagicMock],
        dummy_relation: dict[str, Any],
    ) -> None:
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_relation,))

        relations = client.list_relations()

        for r in relations:
            assert r == Relation(**dummy_relation)

        http_client.fetch_resources.assert_called_with(Resource.Relation, ())

    def test_list_relations_with_filters(
        self,
        elis_client_sync: tuple[SyncRossumAPIClientWithDefaultDeserializer, MagicMock],
        dummy_relation: dict[str, Any],
    ) -> None:
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_relation,))

        relations = client.list_relations(
            type=RelationType.EDIT.value,
            parent=123,
            key=None,
            annotation=456,
        )

        for r in relations:
            assert r == Relation(**dummy_relation)

        http_client.fetch_resources.assert_called_with(
            Resource.Relation,
            (),
            type=RelationType.EDIT.value,
            parent=123,
            key=None,
            annotation=456,
        )
