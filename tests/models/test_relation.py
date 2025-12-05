from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rossum_api.models.relation import Relation, RelationType

if TYPE_CHECKING:
    from typing import Any


@pytest.fixture
def dummy_relation_without_parent() -> dict[str, Any]:
    return {
        "id": 1501,
        "type": RelationType.DUPLICATE.value,
        "key": "d41d8cd98f00b204e9800998ecf8427e",
        "parent": None,
        "annotations": [
            "https://elis.rossum.ai/api/v1/annotations/456",
            "https://elis.rossum.ai/api/v1/annotations/457",
        ],
        "url": "https://elis.rossum.ai/api/v1/relations/1501",
    }


class TestRelationModel:
    def test_relation_without_parent(self, dummy_relation_without_parent: dict[str, Any]) -> None:
        relation = Relation(**dummy_relation_without_parent)

        assert relation.id == 1501
        assert relation.type == RelationType.DUPLICATE
        assert relation.key == "d41d8cd98f00b204e9800998ecf8427e"
        assert relation.parent is None
        assert len(relation.annotations) == 2
        assert relation.url == "https://elis.rossum.ai/api/v1/relations/1501"
