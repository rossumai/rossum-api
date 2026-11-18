from __future__ import annotations

from typing import TypedDict


# Fields that are optional in every label payload. `name` is declared by each subclass, since
# type checkers don't allow a subclass to change whether an inherited key is required.
class _LabelFields(TypedDict, total=False):
    organization: str
    color: str | None


class LabelWrite(_LabelFields):
    """Fields accepted when creating or fully updating a :class:`~rossum_api.models.label.Label`.

    Attributes
    ----------
    name
        Text of the label. Required.
    organization
        URL of the :class:`~rossum_api.models.organization.Organization` the label belongs to.
    color
        Color of the label in RGB hex format (e.g. ``#FF5733``).
    """

    name: str


class LabelPatch(_LabelFields, total=False):
    """Fields accepted when partially updating a :class:`~rossum_api.models.label.Label`.

    Same fields as :class:`LabelWrite`, but all of them are optional.
    """

    name: str
