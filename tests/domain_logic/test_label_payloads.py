from __future__ import annotations

from rossum_api.domain_logic.labels import build_label_apply_payload

ANNOTATIONS = [
    "https://elis.rossum.ai/api/v1/annotations/1",
    "https://elis.rossum.ai/api/v1/annotations/2",
]
LABELS = [
    "https://elis.rossum.ai/api/v1/labels/1",
    "https://elis.rossum.ai/api/v1/labels/2",
]


def test_build_label_apply_payload():
    assert build_label_apply_payload(ANNOTATIONS, add=LABELS[:1], remove=LABELS[1:]) == {
        "operations": {"add": [LABELS[0]], "remove": [LABELS[1]]},
        "objects": {"annotations": ANNOTATIONS},
    }


def test_build_label_apply_payload_defaults_to_empty_operations():
    assert build_label_apply_payload(ANNOTATIONS) == {
        "operations": {"add": [], "remove": []},
        "objects": {"annotations": ANNOTATIONS},
    }


def test_build_label_apply_payload_converts_sequences_to_lists():
    """Tuples (and other sequences) are converted to lists so the payload is JSON-serializable."""
    payload = build_label_apply_payload(tuple(ANNOTATIONS), add=tuple(LABELS), remove=())

    assert payload == {
        "operations": {"add": LABELS, "remove": []},
        "objects": {"annotations": ANNOTATIONS},
    }
    assert isinstance(payload["operations"]["add"], list)
    assert isinstance(payload["operations"]["remove"], list)
    assert isinstance(payload["objects"]["annotations"], list)
