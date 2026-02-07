from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RelationType(str, Enum):
    """Type of relationship between annotations.

    Attributes
    ----------
    EDIT
        Created after editing annotation in user interface (rotation or split of the document).
        The original annotation is set to ``parent`` attribute and newly created annotations
        are set to ``annotations`` attribute.
    ATTACHMENT
        Represents the state that one or more documents are attachments to another document.
        ``key`` is null in this case. Feature must be enabled.
    DUPLICATE
        Created after importing the same document that already exists in Rossum for current
        organization. If duplicate relation already exists then corresponding annotation is
        added to existing relation. ``key`` is set to MD5 hash of document content.
    """

    EDIT = "edit"
    ATTACHMENT = "attachment"
    DUPLICATE = "duplicate"


@dataclass
class Relation:
    """Relation introduces common relations between annotations.

    An :class:`~rossum_api.models.annotation.Annotation` can be related to one or more
    other annotations and it may belong to several relations at the same time.

    Attributes
    ----------
    id
        ID of the relation.
    type
        Type of relationship. Possible values are ``'edit', 'attachment', 'duplicate'``.
    key
        Key used to distinguish several instances of the same type.
    parent
        URL of the parent :class:`~rossum_api.models.annotation.Annotation` in case of 1-M relationship.
    annotations
        List of URLs of related :class:`~rossum_api.models.annotation.Annotation` objects.
    url
        URL of the relation.

    References
    ----------
    https://rossum.app/api/docs/#tag/Relation
    """

    id: int
    type: RelationType
    key: str | None
    parent: str | None
    annotations: list[str]
    url: str
