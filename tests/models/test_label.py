from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models import deserialize_default
from rossum_api.models.label import Label

if TYPE_CHECKING:
    from typing import Any


@pytest.fixture(params=["#FF5733", None], ids=["with_color", "null_color"])
def dummy_label(request: pytest.FixtureRequest) -> dict[str, Any]:
    return {
        "id": 1,
        "url": "https://elis.rossum.ai/api/v1/labels/1",
        "name": "expedite",
        "organization": "https://elis.rossum.ai/api/v1/organizations/1",
        "color": request.param,
    }


class TestLabelModel:
    def test_deserialize_label(self, dummy_label: dict[str, Any]) -> None:
        label = deserialize_default(Resource.Label, dummy_label)

        assert label == Label(**dummy_label)

    def test_serialization_roundtrip(self, dummy_label: dict[str, Any]) -> None:
        """Test that label can be deserialized from a payload and serialized back to it."""
        label = deserialize_default(Resource.Label, dummy_label)

        label_dict = asdict(label)

        assert label_dict == dummy_label
        assert deserialize_default(Resource.Label, label_dict) == label
