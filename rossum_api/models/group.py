from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Group:
    """User role is a group of permissions that are assigned to the user.

    Permissions are assigned to individual operations on objects.

    Attributes
    ----------
    id
        Id of the user role (may differ between different organizations).
    name
        Name of the user role.
    url
        URL of the user role.

    References
    ----------
    https://rossum.app/api/docs/#tag/User-Role
    """

    id: int
    name: str
    url: str
