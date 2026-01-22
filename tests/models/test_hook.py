from __future__ import annotations

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models import deserialize_default
from rossum_api.models.hook import Hook


@pytest.fixture
def minimal_hook_payload():
    """Minimal valid hook payload from API."""
    return {
        "id": 1500,
        "name": "Test Hook",
        "url": "https://elis.rossum.ai/api/v1/hooks/1500",
        "active": True,
        "config": {"url": "https://example.com/webhook"},
        "test": {},
        "guide": None,
        "read_more_url": None,
        "extension_image_url": None,
    }


class TestHookDeserialization:
    def test_deserialize_hook_with_settings_none(self, minimal_hook_payload):
        """Test that Hook can be deserialized when settings is None."""
        minimal_hook_payload["settings"] = None

        hook = deserialize_default(Resource.Hook, minimal_hook_payload)

        assert isinstance(hook, Hook)
        assert hook.settings is None

    def test_deserialize_hook_with_settings_empty_dict(self, minimal_hook_payload):
        """Test that Hook can be deserialized when settings is an empty dict."""
        minimal_hook_payload["settings"] = {}

        hook = deserialize_default(Resource.Hook, minimal_hook_payload)

        assert isinstance(hook, Hook)
        assert hook.settings == {}

    def test_deserialize_hook_with_settings_populated(self, minimal_hook_payload):
        """Test that Hook can be deserialized when settings has values."""
        minimal_hook_payload["settings"] = {"key": "value", "nested": {"a": 1}}

        hook = deserialize_default(Resource.Hook, minimal_hook_payload)

        assert isinstance(hook, Hook)
        assert hook.settings == {"key": "value", "nested": {"a": 1}}

    def test_deserialize_hook_without_settings_field(self, minimal_hook_payload):
        """Test that Hook uses default when settings field is missing."""
        hook = deserialize_default(Resource.Hook, minimal_hook_payload)

        assert isinstance(hook, Hook)
        assert hook.settings == {}
