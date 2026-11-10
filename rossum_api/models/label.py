from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Label:
    """Label object represents arbitrary labels added to annotation objects.

    See https://rossum.app/api/docs/openapi/api/label

    Attributes
    ----------
    id
        ID of the label.
    url
        URL of the label.
    name
        Text of the label.
    organization
        URL of the :class:`~rossum_api.models.organization.Organization` the label belongs to.
    color
        Color of the label in RGB hex format (e.g. ``#FF5733``).
    """

    id: int
    url: str
    name: str
    organization: str
    color: str | None
