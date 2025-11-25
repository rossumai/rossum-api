from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

import dacite

if TYPE_CHECKING:
    from collections.abc import Iterator

ParentType = TypeVar("ParentType")


class Node(ABC, Generic[ParentType]):
    """Base class for schema nodes with parent relationship."""

    @property
    def parent(self) -> ParentType | None:
        """Get Node's parent stored in runtime-only protected property."""
        return getattr(self, "_parent", None)

    @abstractmethod
    def traverse(self, ignore_buttons: bool = True) -> Iterator[Node]:
        """Iterate over self and all sub-nodes."""
        pass


@dataclass
class Datapoint(Node["Multivalue | Section | Tuple"]):
    """A datapoint represents a single value, typically a field of a document or global document information.

    Arguments
    ---------
    id
        Unique identifier for the datapoint.
    type
        Data type of the object
    label
        Display label for the datapoint.
    description
        Description of the datapoint.
    category
        Category of the object, always "datapoint".
    disable_prediction
        If True, AI predictions are disabled for this field.
    hidden
        If True, the field is hidden in the UI.
    can_export
        If False, datapoint is not exported through export endpoint.
    can_collapse
        If True, tabular (multivalue-tuple) datapoint may be collapsed in the UI.
    rir_field_names
        List of references used to initialize object value from AI engine predictions.
    default_value
        Default value used when AI engine does not return any data or rir_field_names are not specified.
    constraints
        Map of various constraints for the field.
    score_threshold
        Threshold (0-1) used to automatically validate field content based on AI confidence scores.
        If not set, queue.default_score_threshold is used.
    options
        List of available options for enum type fields.
    ui_configuration
        Settings affecting behavior of the field in the application.
    width
        Width of the column in characters. Only supported for table datapoints.
    stretch
        If True, column will expand proportionally when total width doesn't fill screen.
        Only supported for table datapoints.
    width_chars
        Deprecated. Use width and stretch instead.
    formula
        Formula definition, required only for fields of type formula. rir_field_names should be empty.
    prompt
        Prompt definition, required only for fields of type reasoning.
    context
        Context information for the field.

    References
    ----------
    https://elis.rossum.ai/api/docs/#datapoin.

    https://elis.rossum.ai/api/docs/#document-schema.
    """

    id: str
    type: Literal["string", "number", "date", "enum", "button", "formula", "reasoning"] | None = (
        None
    )
    label: str | None = None
    description: str | None = None
    category: str = "datapoint"  # always datapoint
    disable_prediction: bool = False
    hidden: bool = False
    can_export: bool = True
    can_collapse: bool = False
    rir_field_names: list[str] | None = None
    default_value: str | None = None
    constraints: dict = field(default_factory=dict)
    score_threshold: float | None = None
    options: list[dict] | None = None
    ui_configuration: dict | None = None
    width: int | None = None
    stretch: bool = False
    width_chars: int | None = None
    formula: str | None = None
    prompt: str | None = None
    context: list[str] | None = None

    @property
    def is_button(self) -> bool:  # noqa: D102
        return self.type == "button"

    @property
    def is_formula(self) -> bool:  # noqa: D102
        return self.type == "formula"

    @property
    def is_reasoning(self) -> bool:  # noqa: D102
        return self.type == "reasoning"

    def traverse(self, ignore_buttons: bool = True) -> Iterator[Datapoint]:
        """Iterate over self and all sub-nodes.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.
        """
        if ignore_buttons and self.is_button:
            return
        yield self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Datapoint:
        """Create Datapoint from dictionary."""
        datapoint: Datapoint = dacite.from_dict(cls, data)
        return datapoint


@dataclass
class Multivalue(Node["Section"]):
    """Multivalue is list of datapoints or tuples of the same type.

    Represents a container for data with multiple occurrences (such as line items)
    and can contain only objects with the same id.

    Arguments
    ---------
    id
        Unique identifier for the multivalue.
    children
        Object specifying type of children. Can contain only objects with categories tuple or datapoint.
    category
        Category of the object, always "multivalue".
    label
        Display label for the multivalue.
    rir_field_names
        List of names used to initialize content from AI engine predictions.
        If specified, the value of the first field from the array is used, otherwise default name
        line_items is used. Can be set only for multivalue containing objects with category tuple.
    min_occurrences
        Minimum number of occurrences of nested objects. If violated, fields should be manually reviewed.
    max_occurrences
        Maximum number of occurrences of nested objects. Additional rows above this limit are removed
        by extraction process.
    grid
        Configure magic-grid feature properties.
    show_grid_by_default
        If True, the magic-grid is opened instead of footer upon entering the multivalue.
        Applied only in UI.

    References
    ----------
    https://elis.rossum.ai/api/docs/#multivalue.

    https://elis.rossum.ai/api/docs/#document-schema.
    """

    id: str
    children: Datapoint | Tuple
    category: str = "multivalue"  # always multivalue
    label: str | None = None
    rir_field_names: list[str] | None = None
    min_occurrences: int | None = None
    max_occurrences: int | None = None
    grid: dict | None = None
    show_grid_by_default: bool = False
    hidden: bool = False

    def traverse(self, ignore_buttons: bool = True) -> Iterator[Multivalue | Datapoint | Tuple]:
        """Iterate over self and all sub-nodes.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.
        """
        yield self
        yield from self.children.traverse(ignore_buttons=ignore_buttons)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Multivalue:
        """Create Multivalue from dictionary, deserializing children based on category."""
        data = data.copy()
        children_data = data.pop("children", None)

        if isinstance(children_data, dict):
            category = children_data.get("category")
            if category == "tuple":
                data["children"] = Tuple.from_dict(children_data)
            elif category == "datapoint":
                data["children"] = Datapoint.from_dict(children_data)
            else:
                data["children"] = children_data
        elif children_data is not None:
            data["children"] = children_data

        multivalue: Multivalue = dacite.from_dict(cls, data)
        return multivalue


@dataclass
class Tuple(Node["Multivalue"]):
    """Container representing tabular data with related values.

    A tuple must be nested within a multivalue object, but unlike multivalue,
    it may consist of objects with different ids.

    Arguments
    ---------
    id
        Unique identifier for the tuple.
    children
        Array specifying objects that belong to a given tuple.
    category
        Category of the object, always "tuple".
    label
        Display label for the tuple.
    disable_prediction
        If True, AI predictions are disabled for this tuple.
    hidden
        If True, the tuple is hidden in the UI.
    rir_field_names
        List of names used to initialize content from AI engine predictions.
        If specified, the value of the first extracted field is used, otherwise
        no AI engine initialization is done.

    References
    ----------
    https://elis.rossum.ai/api/docs/#tuple.

    https://elis.rossum.ai/api/docs/#document-schema.
    """

    id: str
    children: list[Datapoint]
    category: str = "tuple"  # alywas tuple
    label: str | None = None
    disable_prediction: bool = False
    hidden: bool = False
    rir_field_names: list[str] | None = None

    def traverse(self, ignore_buttons: bool = True) -> Iterator[Tuple | Datapoint]:
        """Iterate over self and all sub-nodes.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.
        """
        yield self
        for child in self.children:
            yield from child.traverse(ignore_buttons=ignore_buttons)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tuple:
        """Create Tuple from dictionary, deserializing children datapoints."""
        data = data.copy()
        children_data = data.pop("children", [])

        data["children"] = [Datapoint.from_dict(child) for child in children_data]

        tuple_: Tuple = dacite.from_dict(cls, data)
        return tuple_


@dataclass
class Section(Node["Schema"]):
    """Top-level container grouping related datapoints, multivalues, and tuples.

    Arguments
    ---------
    id
        Unique identifier for the section.
    children
        List of datapoints, multivalues, and tuples belonging to this section.
    category
        Category of the object, always "section".
    label
        Display label for the section.
    icon
        Icon identifier for the section.

    References
    ----------
    https://elis.rossum.ai/api/docs/#section.

    https://elis.rossum.ai/api/docs/#document-schema.
    """

    id: str
    children: list[Datapoint | Multivalue | Tuple] = field(default_factory=list)
    category: str = "section"  # always section
    label: str | None = None
    icon: str | None = None

    def traverse(self, ignore_buttons: bool = True) -> Iterator[Datapoint | Multivalue | Tuple]:
        """Iterate over all sub-nodes.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.
        """
        for child in self.children:
            yield from child.traverse(ignore_buttons=ignore_buttons)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Section:
        """Create Section from dictionary, deserializing children based on category."""
        data = data.copy()
        children_data = data.pop("children", [])

        children: list[Datapoint | Multivalue | Tuple | dict[str, Any]] = []
        for child in children_data:
            if not isinstance(child, dict):
                children.append(child)
                continue

            category = child.get("category")
            if category == "datapoint":
                children.append(Datapoint.from_dict(child))
            elif category == "multivalue":
                children.append(Multivalue.from_dict(child))
            elif category == "tuple":
                children.append(Tuple.from_dict(child))
            else:
                children.append(child)

        data["children"] = children
        section: Section = dacite.from_dict(cls, data)
        return section


@dataclass
class Schema(Node):
    """Schema specifies the set of datapoints that are extracted from the document.

    For more information see `Document Schema <https://elis.rossum.ai/api/docs/#document-schema>`_.

    Arguments
    ---------
    id
        ID of the schema.
    name
        Name of the schema.
    queues
        List of :class:`~rossum_api.models.queue.Queue` objects that use schema object.
    url
        URL of the schema.
    content
        List of sections (top-level schema objects, see `Document Schema <https://elis.rossum.ai/api/docs/#document-schema>`_
        for description of schema).
    metadata
        Client data.

    References
    ----------
    https://elis.rossum.ai/api/docs/#schema.

    https://elis.rossum.ai/api/docs/#document-schema.
    """

    id: int
    name: str | None = None
    queues: list[str] = field(default_factory=list)
    url: str | None = None
    content: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    modified_by: str | None = None
    modified_at: str | None = None

    def traverse(self, ignore_buttons: bool = True) -> Iterator[Datapoint | Multivalue | Tuple]:
        """Iterater over all sub-nodes.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.
        """
        for section in self.content:
            yield from section.traverse(ignore_buttons=ignore_buttons)

    def get_by_id(
        self, node_id: str, ignore_buttons: bool = True
    ) -> Section | Multivalue | Tuple | Datapoint | None:
        """Find a node by its ID.

        Arguments
        ---------
        node_id
            ID of the node to find.
        ignore_buttons
            If True, button datapoints are excluded from search.

        Returns
        -------
        Node with the given ID, or None if not found.
        """
        for node in self.traverse(ignore_buttons=ignore_buttons):
            if node.id == node_id:
                return node
        return None

    def formula_fields(self, ignore_buttons: bool = True) -> Iterator[Datapoint]:
        """Iterate over all formula datapoints.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.

        Returns
        -------
        Iterator of formula datapoints.
        """
        for node in self.traverse(ignore_buttons=ignore_buttons):
            if isinstance(node, Datapoint) and node.is_formula:
                yield node

    def reasoning_fields(self, ignore_buttons: bool = True) -> Iterator[Datapoint]:
        """Iterate over all reasoning datapoints.

        Arguments
        ---------
        ignore_buttons
            If True, button datapoints are excluded from traversal.

        Returns
        -------
        Iterator of reasoning datapoints.
        """
        for node in self.traverse(ignore_buttons=ignore_buttons):
            if isinstance(node, Datapoint) and node.is_reasoning:
                yield node

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        """Create Schema from dictionary, deserializing content sections."""
        data = data.copy()
        content_data = data.pop("content", [])

        data["content"] = [Section.from_dict(section) for section in content_data]

        schema: Schema = dacite.from_dict(cls, data)
        return schema
