from __future__ import annotations

from rossum_api.payloads.label import LabelPatch, LabelWrite


def test_label_write_requires_only_name():
    assert LabelWrite.__required_keys__ == frozenset({"name"})
    assert LabelWrite.__optional_keys__ == frozenset({"organization", "color"})


def test_label_patch_has_no_required_keys():
    assert LabelPatch.__required_keys__ == frozenset()
    assert LabelPatch.__optional_keys__ == frozenset({"name", "organization", "color"})
