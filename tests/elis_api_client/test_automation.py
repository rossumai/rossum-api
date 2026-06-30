from __future__ import annotations

import dacite
import pytest

from rossum_api.models import DACITE_CONFIG
from rossum_api.models.automation import (
    AutomationProjections,
    AutomationStats,
    AutomationTarget,
    DatapointAutomationTarget,
    FieldErrorRateLimit,
)


@pytest.fixture
def dummy_current_stats():
    return {
        "document_automation_rate": 0.72,
        "estimated_error_rate": 0.05,
        "is_aurora_queue": True,
        "document_blockers": [
            {
                "blocker": "low_score",
                "document_count": 50,
                "granularity": "datapoint",
                "example_annotation_ids": [101, 102, 103],
            }
        ],
        "datapoint_statistics": [
            {
                "schema_id": "amount_total",
                "blocked_document_counts": {"low_score": 30},
                "estimated_error_rate": 0.08,
                "confidence_threshold": 0.85,
                "is_quality_estimate": True,
                "blockers": [
                    {
                        "blocker": "low_score",
                        "document_count": 30,
                        "granularity": "datapoint",
                        "example_annotation_ids": [101, 102],
                    }
                ],
            }
        ],
        "document_automation_timeseries": [
            {
                "date": "2026-05-01",
                "automated_count": 120,
                "non_automated_count": 80,
                "touched_count": 30,
                "touchless_count": 50,
            }
        ],
        "estimated_error_rate_timeseries": [
            {
                "date": "2026-05-01",
                "error_rate_estimate": 0.05,
                "is_quality_estimate": True,
                "window_document_count": 200,
            }
        ],
    }


@pytest.fixture
def dummy_projections():
    return {
        "total_document_count": 1000,
        "used_document_count": 800,
        "baseline": {
            "document_automation_rate": 0.5,
            "estimated_error_rate": 0.07,
            "datapoint_statistics": [],
            "document_blockers": [],
            "document_automation_timeseries": [],
            "estimated_error_rate_timeseries": None,
        },
        "projections": [
            {
                "document_automation_rate": 0.7,
                "estimated_error_rate": 0.05,
                "datapoint_statistics": [],
                "document_blockers": [],
                "document_automation_timeseries": [],
                "estimated_error_rate_timeseries": [],
            }
        ],
    }


@pytest.fixture
def dummy_automation_target():
    return {
        "automation_rate_target": 0.8,
        "error_rate_target": 0.05,
        "type": "automation_assistant_v1",
        "datetime": "2026-05-25T12:00:00Z",
        "datapoint_automation_targets": [
            {
                "schema_id": "amount_total",
                "error_rate_target": 0.03,
                "error_rate_limit": 0.05,
                "confidence_threshold": 0.9,
            }
        ],
    }


@pytest.mark.asyncio
class TestAutomationSetupAsync:
    async def test_retrieve_automation_insights(self, elis_client, dummy_current_stats):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_current_stats

        result = await client.retrieve_automation_insights(123)

        assert result == dacite.from_dict(
            AutomationStats, dummy_current_stats, config=DACITE_CONFIG
        )
        http_client.request_json.assert_called_with("GET", "queues/123/automation/insights")

    async def test_retrieve_automation_projections(self, elis_client, dummy_projections):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_projections

        fields = [FieldErrorRateLimit(schema_id="amount_total", error_rate_limit=0.05)]
        result = await client.retrieve_automation_projections(123, fields)

        assert result == dacite.from_dict(
            AutomationProjections, dummy_projections, config=DACITE_CONFIG
        )
        http_client.request_json.assert_called_with(
            "POST",
            "queues/123/automation/projections",
            json={"fields": [{"schema_id": "amount_total", "error_rate_limit": 0.05}]},
        )

    async def test_retrieve_projections_with_exclude_blockers(
        self, elis_client, dummy_projections
    ):
        client, http_client = elis_client
        http_client.request_json.return_value = dummy_projections

        await client.retrieve_automation_projections(
            123,
            [FieldErrorRateLimit(schema_id="amount_total", error_rate_limit=0.05)],
            exclude_blockers=["error_message", "extension"],
        )

        http_client.request_json.assert_called_with(
            "POST",
            "queues/123/automation/projections",
            json={"fields": [{"schema_id": "amount_total", "error_rate_limit": 0.05}]},
            params={"exclude_blockers": "error_message,extension"},
        )

    async def test_list_automation_targets(self, elis_client, dummy_automation_target):
        client, http_client = elis_client
        http_client.request_json.return_value = {"results": [dummy_automation_target]}

        result = [t async for t in client.list_automation_targets(456)]

        assert result == [
            dacite.from_dict(AutomationTarget, dummy_automation_target, config=DACITE_CONFIG)
        ]
        http_client.request_json.assert_called_with("GET", "queues/456/automation/targets")

    async def test_create_new_automation_target(self, elis_client):
        client, http_client = elis_client

        datapoint_targets = [
            DatapointAutomationTarget(
                schema_id="amount_total",
                error_rate_target=0.03,
                error_rate_limit=0.05,
                confidence_threshold=0.9,
            )
        ]
        result = await client.create_new_automation_target(
            queue_id=789,
            automation_rate_target=0.8,
            error_rate_target=0.05,
            datapoint_automation_targets=datapoint_targets,
        )

        assert result is None
        http_client.request.assert_called_with(
            "POST",
            "queues/789/automation/targets",
            json={
                "automation_rate_target": 0.8,
                "error_rate_target": 0.05,
                "datapoint_automation_targets": [
                    {
                        "schema_id": "amount_total",
                        "error_rate_target": 0.03,
                        "confidence_threshold": 0.9,
                        "error_rate_limit": 0.05,
                    }
                ],
                "type": "automation_assistant_v1",
            },
        )

    async def test_create_legacy_thresholds_target(self, elis_client):
        client, http_client = elis_client

        await client.create_new_automation_target(
            queue_id=789,
            automation_rate_target=0.5,
            error_rate_target=0.1,
            datapoint_automation_targets=[],
            target_type="legacy_thresholds",
        )

        sent_json = http_client.request.call_args.kwargs["json"]
        assert sent_json["type"] == "legacy_thresholds"
        assert sent_json["datapoint_automation_targets"] == []


class TestAutomationSetupSync:
    def test_retrieve_automation_insights(self, elis_client_sync, dummy_current_stats):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_current_stats

        result = client.retrieve_automation_insights(123)

        assert result == dacite.from_dict(
            AutomationStats, dummy_current_stats, config=DACITE_CONFIG
        )
        http_client.request_json.assert_called_with("GET", "queues/123/automation/insights")

    def test_retrieve_automation_projections(self, elis_client_sync, dummy_projections):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = dummy_projections

        fields = [FieldErrorRateLimit(schema_id="amount_total", error_rate_limit=0.05)]
        result = client.retrieve_automation_projections(123, fields)

        assert result == dacite.from_dict(
            AutomationProjections, dummy_projections, config=DACITE_CONFIG
        )
        http_client.request_json.assert_called_with(
            "POST",
            "queues/123/automation/projections",
            json={"fields": [{"schema_id": "amount_total", "error_rate_limit": 0.05}]},
        )

    def test_list_automation_targets(self, elis_client_sync, dummy_automation_target):
        client, http_client = elis_client_sync
        http_client.request_json.return_value = {"results": [dummy_automation_target]}

        result = list(client.list_automation_targets(456))

        assert result == [
            dacite.from_dict(AutomationTarget, dummy_automation_target, config=DACITE_CONFIG)
        ]
        http_client.request_json.assert_called_with("GET", "queues/456/automation/targets")

    def test_create_new_automation_target(self, elis_client_sync):
        client, http_client = elis_client_sync

        datapoint_targets = [
            DatapointAutomationTarget(
                schema_id="amount_total",
                error_rate_target=0.03,
                error_rate_limit=0.05,
                confidence_threshold=0.9,
            )
        ]
        result = client.create_new_automation_target(
            queue_id=789,
            automation_rate_target=0.8,
            error_rate_target=0.05,
            datapoint_automation_targets=datapoint_targets,
        )

        assert result is None
        http_client.request.assert_called_with(
            "POST",
            "queues/789/automation/targets",
            json={
                "automation_rate_target": 0.8,
                "error_rate_target": 0.05,
                "datapoint_automation_targets": [
                    {
                        "schema_id": "amount_total",
                        "error_rate_target": 0.03,
                        "confidence_threshold": 0.9,
                        "error_rate_limit": 0.05,
                    }
                ],
                "type": "automation_assistant_v1",
            },
        )


class TestAutomationSetupDeserialization:
    def test_current_stats_deserializes(self, dummy_current_stats):
        stat = dacite.from_dict(AutomationStats, dummy_current_stats, config=DACITE_CONFIG)
        assert stat.document_automation_rate == 0.72
        assert stat.estimated_error_rate == 0.05
        assert stat.is_aurora_queue is True
        assert stat.document_blockers[0].blocker == "low_score"
        assert stat.document_blockers[0].granularity == "datapoint"
        assert stat.datapoint_statistics[0].schema_id == "amount_total"
        assert stat.datapoint_statistics[0].blocked_document_counts == {"low_score": 30}

    def test_current_stats_minimal_payload(self):
        minimal = {"document_automation_rate": 0.0}
        stat = dacite.from_dict(AutomationStats, minimal, config=DACITE_CONFIG)
        assert stat.document_automation_rate == 0.0
        assert stat.estimated_error_rate is None
        assert stat.is_aurora_queue is None
        assert stat.document_blockers == []
        assert stat.datapoint_statistics == []

    def test_projections_deserialize(self, dummy_projections):
        projections = dacite.from_dict(
            AutomationProjections, dummy_projections, config=DACITE_CONFIG
        )
        assert projections.total_document_count == 1000
        assert projections.baseline.estimated_error_rate_timeseries is None
        assert projections.projections[0].estimated_error_rate_timeseries == []

    def test_automation_target_deserializes(self, dummy_automation_target):
        target = dacite.from_dict(AutomationTarget, dummy_automation_target, config=DACITE_CONFIG)
        assert target.automation_rate_target == 0.8
        assert target.type == "automation_assistant_v1"
        assert target.datapoint_automation_targets[0].confidence_threshold == 0.9
        assert target.datapoint_automation_targets[0].error_rate_limit == 0.05
