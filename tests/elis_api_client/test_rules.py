from __future__ import annotations

import dacite
import pytest

from rossum_api.domain_logic.resources import Resource
from rossum_api.models.rule import (
    AddAutomationBlockerPayload,
    AddValidationSourcePayload,
    ChangeQueuePayload,
    ChangeStatusPayload,
    LabelsPayload,
    Rule,
    SchemaIdsPayload,
    SendEmailPayload,
    ShowMessagePayload,
)


@pytest.fixture
def dummy_rule():
    return {
        "id": 123,
        "url": "https://elis.rossum.ai/api/v1/rules/123",
        "name": "rule",
        "enabled": True,
        "organization": "https://elis.rossum.ai/api/v1/organizations/1001",
        "schema": "https://elis.rossum.ai/api/v1/schemas/1001",
        "trigger_condition": "True",
        "created_by": "https://elis.rossum.ai/api/v1/users/9524",
        "created_at": "2022-01-01T15:02:25.653324Z",
        "modified_by": "https://elis.rossum.ai/api/v1/users/2345",
        "modified_at": "2020-01-01T10:08:03.856648Z",
        "rule_template": None,
        "synchronized_from_template": False,
        "actions": [
            {
                "id": "f3c43f16-b5f1-4ac8-b789-17d4c26463d7",
                "enabled": True,
                "type": "show_message",
                "payload": {
                    "type": "error",
                    "content": "Error message!",
                    "schema_id": "invoice_id",
                },
                "event": "validation",
            }
        ],
    }


@pytest.fixture
def dummy_rule_without_schema(dummy_rule):
    """Creates a Rule dict without schema field (optional field)."""
    rule_data = dummy_rule.copy()
    rule_data["schema"] = None
    return rule_data


@pytest.fixture
def expected_rule(dummy_rule):
    """Creates a Rule object with properly constructed RuleAction objects."""
    return Rule.from_dict(dummy_rule)


@pytest.fixture
def expected_rule_without_schema(dummy_rule_without_schema):
    """Creates a Rule object without schema."""
    return Rule.from_dict(dummy_rule_without_schema)


@pytest.mark.asyncio
class TestRules:
    async def test_list_rules(self, elis_client, dummy_rule, expected_rule, mock_generator):
        client, http_client = elis_client
        http_client.fetch_all.return_value = mock_generator(dummy_rule)

        rules = client.list_rules()

        async for r in rules:
            assert r == expected_rule

        http_client.fetch_all.assert_called_with(Resource.Rule, ())

    async def test_retrieve_rule(self, elis_client, dummy_rule, expected_rule):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_rule

        uid = dummy_rule["id"]
        rule = await client.retrieve_rule(uid)

        assert rule == expected_rule

        http_client.fetch_one.assert_called_with(Resource.Rule, uid)

    async def test_create_new_rule(self, elis_client, dummy_rule, expected_rule):
        client, http_client = elis_client
        http_client.create.return_value = dummy_rule

        data = {
            "name": "Test Rule",
            "schema": "https://elis.rossum.ai/api/v1/schemas/1001",
            "trigger_condition": "True",
            "actions": [],
        }
        rule = await client.create_new_rule(data)

        assert rule == expected_rule

        http_client.create.assert_called_with(Resource.Rule, data)

    async def test_create_new_rule_with_formula_condition(self, elis_client, dummy_rule):
        client, http_client = elis_client
        formula_condition = "field.amount > 100"
        response_rule = {**dummy_rule, "trigger_condition": formula_condition}
        http_client.create.return_value = response_rule

        data = {
            "name": "Test Rule with Formula",
            "schema": "https://elis.rossum.ai/api/v1/schemas/1001",
            "trigger_condition": formula_condition,
            "actions": [],
        }
        rule = await client.create_new_rule(data)

        assert rule.trigger_condition == formula_condition
        http_client.create.assert_called_with(Resource.Rule, data)

    async def test_update_part_rule(self, elis_client, dummy_rule, expected_rule):
        client, http_client = elis_client
        http_client.update.return_value = dummy_rule

        rid = dummy_rule["id"]
        data = {
            "name": "New Rule Name",
        }
        rule = await client.update_part_rule(rid, data)

        assert rule == expected_rule

        http_client.update.assert_called_with(Resource.Rule, rid, data)

    async def test_delete_rule(self, elis_client, dummy_rule):
        client, http_client = elis_client
        http_client.delete.return_value = None

        rid = dummy_rule["id"]
        await client.delete_rule(rid)

        http_client.delete.assert_called_with(Resource.Rule, rid)

    async def test_retrieve_rule_without_schema(
        self, elis_client, dummy_rule_without_schema, expected_rule_without_schema
    ):
        client, http_client = elis_client
        http_client.fetch_one.return_value = dummy_rule_without_schema

        uid = dummy_rule_without_schema["id"]
        rule = await client.retrieve_rule(uid)

        assert rule == expected_rule_without_schema
        assert rule.schema is None

        http_client.fetch_one.assert_called_with(Resource.Rule, uid)


class TestRulesSync:
    def test_list_rules(self, elis_client_sync, dummy_rule, expected_rule):
        client, http_client = elis_client_sync
        http_client.fetch_resources.return_value = iter((dummy_rule,))

        rules = client.list_rules()

        for r in rules:
            assert r == expected_rule

        http_client.fetch_resources.assert_called_with(Resource.Rule, ())

    def test_retrieve_rule(self, elis_client_sync, dummy_rule, expected_rule):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_rule

        uid = dummy_rule["id"]
        rule = client.retrieve_rule(uid)

        assert rule == expected_rule

        http_client.fetch_resource.assert_called_with(Resource.Rule, uid)

    def test_create_new_rule(self, elis_client_sync, dummy_rule, expected_rule):
        client, http_client = elis_client_sync
        http_client.create.return_value = dummy_rule

        data = {
            "name": "Test Rule",
            "schema": "https://elis.rossum.ai/api/v1/schemas/1001",
            "trigger_condition": "True",
            "actions": [],
        }
        rule = client.create_new_rule(data)

        assert rule == expected_rule

        http_client.create.assert_called_with(Resource.Rule, data)

    def test_create_new_rule_with_formula_condition(self, elis_client_sync, dummy_rule):
        client, http_client = elis_client_sync
        formula_condition = "field.amount > 100"
        response_rule = {**dummy_rule, "trigger_condition": formula_condition}
        http_client.create.return_value = response_rule

        data = {
            "name": "Test Rule with Formula",
            "schema": "https://elis.rossum.ai/api/v1/schemas/1001",
            "trigger_condition": formula_condition,
            "actions": [],
        }
        rule = client.create_new_rule(data)

        assert rule.trigger_condition == formula_condition
        http_client.create.assert_called_with(Resource.Rule, data)

    def test_update_part_rule(self, elis_client_sync, dummy_rule, expected_rule):
        client, http_client = elis_client_sync
        http_client.update.return_value = dummy_rule

        rid = dummy_rule["id"]
        data = {
            "name": "New Rule Name",
        }
        rule = client.update_part_rule(rid, data)

        assert rule == expected_rule

        http_client.update.assert_called_with(Resource.Rule, rid, data)

    def test_delete_rule(self, elis_client_sync, dummy_rule):
        client, http_client = elis_client_sync
        http_client.delete.return_value = None

        rid = dummy_rule["id"]
        client.delete_rule(rid)

        http_client.delete.assert_called_with(Resource.Rule, rid)

    def test_retrieve_rule_without_schema(
        self, elis_client_sync, dummy_rule_without_schema, expected_rule_without_schema
    ):
        client, http_client = elis_client_sync
        http_client.fetch_resource.return_value = dummy_rule_without_schema

        uid = dummy_rule_without_schema["id"]
        rule = client.retrieve_rule(uid)

        assert rule == expected_rule_without_schema
        assert rule.schema is None

        http_client.fetch_resource.assert_called_with(Resource.Rule, uid)


class TestRuleActionDeserialization:
    """Tests that Rule.from_dict correctly deserializes all action payload types."""

    def _make_rule_dict(self, action_type: str, payload: dict) -> dict:
        return {
            "id": 1,
            "name": "test",
            "enabled": True,
            "organization": "https://elis.rossum.ai/api/v1/organizations/1",
            "actions": [
                {
                    "id": "action-1",
                    "type": action_type,
                    "payload": payload,
                    "event": "validation",
                }
            ],
        }

    @pytest.mark.parametrize(
        "action_type, payload_data, expected_cls",
        [
            (
                "show_message",
                {"type": "error", "content": "msg", "schema_id": "field_1"},
                ShowMessagePayload,
            ),
            (
                "add_automation_blocker",
                {"content": "blocked", "schema_id": "f1"},
                AddAutomationBlockerPayload,
            ),
            ("change_status", {"method": "postpone"}, ChangeStatusPayload),
            ("change_queue", {"queue_id": 42, "reimport": True}, ChangeQueuePayload),
            ("add_label", {"labels": ["lbl1"]}, LabelsPayload),
            ("remove_label", {"labels": ["lbl1"]}, LabelsPayload),
            ("add_remove_label", {"labels": ["lbl1"]}, LabelsPayload),
            ("show_field", {"schema_ids": ["s1"]}, SchemaIdsPayload),
            ("hide_field", {"schema_ids": ["s1"]}, SchemaIdsPayload),
            ("show_hide_field", {"schema_ids": ["s1"]}, SchemaIdsPayload),
            ("add_validation_source", {"schema_id": "field_1"}, AddValidationSourcePayload),
            (
                "send_email",
                {
                    "email_template": "https://example.com/templates/1",
                    "attach_document": True,
                    "to": ["a@b.com"],
                },
                SendEmailPayload,
            ),
        ],
    )
    def test_payload_deserialization(self, action_type, payload_data, expected_cls):
        data = self._make_rule_dict(action_type, payload_data)
        rule = Rule.from_dict(data)
        assert isinstance(rule.actions[0].payload, expected_cls)

    def test_custom_payload_stays_as_dict(self):
        data = self._make_rule_dict("custom", {"foo": "bar", "nested": {"a": 1}})
        rule = Rule.from_dict(data)
        payload = rule.actions[0].payload
        assert isinstance(payload, dict)
        assert payload == {"foo": "bar", "nested": {"a": 1}}

    def test_unknown_action_type_raises(self):
        data = self._make_rule_dict("some_future_type", {"key": "val"})
        with pytest.raises(KeyError):
            Rule.from_dict(data)

    def test_payload_with_missing_required_field_raises(self):
        data = self._make_rule_dict("change_queue", {"reimport": True})
        with pytest.raises(dacite.MissingValueError):
            Rule.from_dict(data)

    def test_multiple_actions(self):
        data = {
            "id": 1,
            "name": "multi",
            "enabled": True,
            "organization": "https://elis.rossum.ai/api/v1/organizations/1",
            "actions": [
                {
                    "id": "a1",
                    "type": "show_message",
                    "payload": {"type": "error", "content": "msg"},
                    "event": "validation",
                },
                {
                    "id": "a2",
                    "type": "change_status",
                    "payload": {"method": "postpone"},
                    "event": "validation",
                },
            ],
        }
        rule = Rule.from_dict(data)
        assert len(rule.actions) == 2
        assert isinstance(rule.actions[0].payload, ShowMessagePayload)
        assert isinstance(rule.actions[1].payload, ChangeStatusPayload)
