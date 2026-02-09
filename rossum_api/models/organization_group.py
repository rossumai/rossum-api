from __future__ import annotations

from dataclasses import dataclass, field

from rossum_api.types import JsonDict


@dataclass
class OrganizationGroup:
    """Organization Group is a grouping of organizations sharing the same license.

    .. warning::
        Please note that Organization Group is an internal API and can be changed without notice.

    Attributes
    ----------
    id
        ID of the organization group.
    name
        Name of the organization group.
    is_trial
        Property indicates whether this license is a trial license.
    is_production
        Property indicates whether this licence is a production licence.
    deployment_location
        Deployment location identifier.
    modified_by
        User that last modified the object.
    modified_at
        Timestamp of last modification.
    features
        Enabled features (for internal use only).
    usage
        Enabled priced features (for internal use only).

    References
    ----------
    https://rossum.app/api/docs/#tag/Organization-Group
    """

    id: int
    name: str
    is_trial: bool
    is_production: bool
    deployment_location: str
    modified_by: str | None = None
    modified_at: str | None = None
    features: JsonDict | None = None
    usage: JsonDict = field(default_factory=dict)
