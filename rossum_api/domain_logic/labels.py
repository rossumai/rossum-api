from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


def build_label_apply_payload(
    annotations: Sequence[str],
    add: Sequence[str] = (),
    remove: Sequence[str] = (),
) -> dict[str, Any]:
    """Build the payload for the labels apply endpoint."""
    return {
        "operations": {"add": list(add), "remove": list(remove)},
        "objects": {"annotations": list(annotations)},
    }
