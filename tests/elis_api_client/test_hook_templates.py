from __future__ import annotations

import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.hook_template import HookTemplate


@pytest.fixture
def dummy_hook_template():
    return {
        "type": "function",
        "url": "https://elis.rossum.ai/api/v1/hook_templates/100",
        "name": "Vendor Matching",
        "metadata": {},
        "events": ["annotation_content.initialize"],
        "sideload": [],
        "config": {},
        "test": {},
        "description": "Matches vendors automatically.",
        "extension_source": "rossum_store",
        "settings": {"threshold": 0.9},
        "settings_schema": {"type": "object"},
        "secrets_schema": None,
        "guide": "Install and configure vendor matching.",
        "read_more_url": "https://rossum.ai/extensions/vendor-matching",
        "extension_image_url": "https://rossum.ai/img/vendor-matching.png",
        "settings_description": [],
        "store_description": "Matches vendors automatically.",
        "external_url": "",
        "use_token_owner": True,
        "install_action": "copy",
        "token_lifetime_s": None,
        "order": 0,
    }


@pytest.mark.asyncio
class TestHookTemplates:
    async def test_list_hook_templates(self, elis_client, dummy_hook_template, mock_generator):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_hook_template)

        hook_templates = client.list_hook_templates()

        async for ht in hook_templates:
            assert ht == HookTemplate(**dummy_hook_template)

        http_client.fetch_all.assert_called_with(Resource.HookTemplate)

    async def test_retrieve_hook_template(self, elis_client, dummy_hook_template):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_hook_template

        uid = 100
        hook_template = await client.retrieve_hook_template(uid)

        assert hook_template == HookTemplate(**dummy_hook_template)
        assert hook_template.id == 100

        http_client.fetch_one.assert_called_with(Resource.HookTemplate, uid)


class TestHookTemplatesSync:
    def test_list_hook_templates(self, elis_client_sync, dummy_hook_template):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_hook_template,))

        hook_templates = client.list_hook_templates()

        for ht in hook_templates:
            assert ht == HookTemplate(**dummy_hook_template)

        http_client.fetch_resources.assert_called_with(Resource.HookTemplate)

    def test_retrieve_hook_template(self, elis_client_sync, dummy_hook_template):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_hook_template

        uid = 100
        hook_template = client.retrieve_hook_template(uid)

        assert hook_template == HookTemplate(**dummy_hook_template)

        http_client.fetch_resource.assert_called_with(Resource.HookTemplate, uid)
