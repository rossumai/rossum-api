from __future__ import annotations

from dataclasses import asdict

import pytest

from rossum_api.models.schema import Datapoint, Multivalue, Schema, Section, Tuple


@pytest.fixture
def boring_schema():
    return Schema(
        id=123456,
        name="Test Invoice Schema",
        queues=["https://us.api.rossum.ai/v1/queues/12345"],
        url="https://us.api.rossum.ai/v1/schemas/123456",
        content=[
            Section(
                id="invoice_section",
                label="Invoice Details",
                children=[
                    Datapoint(
                        id="invoice_number",
                        type="string",
                        label="Invoice Number",
                        rir_field_names=["document_id"],
                        constraints={"required": True},
                    ),
                    Datapoint(
                        id="total_amount",
                        type="number",
                        label="Total Amount",
                        disable_prediction=False,
                        hidden=False,
                        can_export=True,
                        rir_field_names=["amount_total"],
                        constraints={"required": True},
                    ),
                ],
            ),
            Section(
                id="line_items_section",
                label="Line Items",
                children=[
                    Multivalue(
                        id="line_items",
                        children=Tuple(
                            id="line_item",
                            label="Line Item",
                            children=[
                                Datapoint(
                                    id="item_description",
                                    type="string",
                                    label="Description",
                                    rir_field_names=["item_description"],
                                ),
                                Datapoint(
                                    id="item_amount",
                                    type="number",
                                    label="Amount",
                                    rir_field_names=["item_amount_total"],
                                ),
                            ],
                        ),
                        rir_field_names=["line_items"],
                        min_occurrences=0,
                        max_occurrences=1000,
                    )
                ],
            ),
        ],
        metadata={},
        modified_by="https://us.api.rossum.ai/v1/users/99999",
        modified_at="2025-11-25T10:00:00.000000Z",
    )


class TestSchemaModels:
    def test_datapoint_creation(self):
        dp = Datapoint(
            id="test_field",
            type="string",
            label="Test Field",
            rir_field_names=["test"],
            constraints={"required": True},
        )
        assert dp.id == "test_field"
        assert dp.type == "string"
        assert dp.category == "datapoint"
        assert dp.disable_prediction is False
        assert dp.hidden is False
        assert dp.can_export is True

    def test_tuple_creation(self):
        children = [
            Datapoint(id="field1", type="string"),
            Datapoint(id="field2", type="number"),
        ]
        tuple_obj = Tuple(id="test_tuple", children=children, label="Test Tuple")
        assert tuple_obj.id == "test_tuple"
        assert tuple_obj.category == "tuple"
        assert len(tuple_obj.children) == 2

    def test_multivalue_creation(self):
        child_tuple = Tuple(
            id="line_item",
            children=[Datapoint(id="amount", type="number")],
        )
        mv = Multivalue(
            id="line_items",
            children=child_tuple,
            rir_field_names=["line_items"],
            min_occurrences=0,
            max_occurrences=100,
        )
        assert mv.id == "line_items"
        assert mv.category == "multivalue"
        assert mv.children.id == "line_item"

    def test_section_creation(self):
        section = Section(
            id="test_section",
            children=[
                Datapoint(id="field1", type="string"),
                Datapoint(id="field2", type="number"),
            ],
            label="Test Section",
        )
        assert section.id == "test_section"
        assert section.category == "section"
        assert len(section.children) == 2

    def test_schema_from_real_world_data(self, boring_schema):
        """Test that Schema can be created from real-world API response."""
        assert boring_schema.id == 123456
        assert boring_schema.name == "Test Invoice Schema"
        assert len(boring_schema.content) == 2
        assert boring_schema.content[0].id == "invoice_section"
        assert boring_schema.content[1].id == "line_items_section"

    def test_schema_nested_structure(self, boring_schema):
        """Test nested structure of schema (Section > Multivalue > Tuple > Datapoint)."""
        # Check line items section
        line_items_section = boring_schema.content[1]
        assert isinstance(line_items_section, Section)
        assert line_items_section.label == "Line Items"

        # Check multivalue
        multivalue = line_items_section.children[0]
        assert isinstance(multivalue, Multivalue)
        assert multivalue.id == "line_items"

        # Check tuple
        tuple_obj = multivalue.children
        assert isinstance(tuple_obj, Tuple)
        assert tuple_obj.id == "line_item"

        # Check datapoints in tuple
        assert len(tuple_obj.children) == 2
        assert all(isinstance(child, Datapoint) for child in tuple_obj.children)
        assert tuple_obj.children[0].id == "item_description"
        assert tuple_obj.children[1].id == "item_amount"

    def test_serialization_roundtrip(self, boring_schema):
        """Test that schema can be serialized to dict and deserialized back."""
        schema_dict = asdict(boring_schema)
        deserialized_schema = Schema.from_dict(schema_dict)
        assert deserialized_schema == boring_schema

    def test_traverse(self, boring_schema):
        """Test traverse method yields all nodes in the schema."""
        nodes = list(boring_schema.traverse())

        # Count node types
        datapoints = [n for n in nodes if isinstance(n, Datapoint)]
        tuples = [n for n in nodes if isinstance(n, Tuple)]
        multivalues = [n for n in nodes if isinstance(n, Multivalue)]

        # Should have 4 datapoints (2 in invoice_section + 2 in line_items tuple)
        assert len(datapoints) == 4
        # Should have 1 tuple (line_item)
        assert len(tuples) == 1
        # Should have 1 multivalue (line_items)
        assert len(multivalues) == 1

        # Check datapoint IDs
        datapoint_ids = {dp.id for dp in datapoints}
        assert datapoint_ids == {
            "invoice_number",
            "total_amount",
            "item_description",
            "item_amount",
        }

    def test_traverse_with_button(self):
        """Test traverse method ignores button datapoints by default."""
        schema = Schema(
            id=1,
            content=[
                Section(
                    id="section1",
                    children=[
                        Datapoint(id="field1", type="string"),
                        Datapoint(id="button1", type="button"),
                        Datapoint(id="field2", type="number"),
                    ],
                )
            ],
        )

        # Default: ignore buttons
        nodes = list(schema.traverse())
        datapoint_ids = {n.id for n in nodes if isinstance(n, Datapoint)}
        assert datapoint_ids == {"field1", "field2"}

        # With ignore_buttons=False
        nodes = list(schema.traverse(ignore_buttons=False))
        datapoint_ids = {n.id for n in nodes if isinstance(n, Datapoint)}
        assert datapoint_ids == {"field1", "button1", "field2"}

    def test_get_by_id_datapoint(self, boring_schema):
        """Test get_by_id finds datapoints."""
        node = boring_schema.get_by_id("invoice_number")
        assert isinstance(node, Datapoint)
        assert node.id == "invoice_number"
        assert node.type == "string"

    def test_get_by_id_multivalue(self, boring_schema):
        """Test get_by_id finds multivalue nodes."""
        node = boring_schema.get_by_id("line_items")
        assert isinstance(node, Multivalue)
        assert node.id == "line_items"

    def test_get_by_id_tuple(self, boring_schema):
        """Test get_by_id finds tuple nodes."""
        node = boring_schema.get_by_id("line_item")
        assert isinstance(node, Tuple)
        assert node.id == "line_item"

    def test_get_by_id_not_found(self, boring_schema):
        """Test get_by_id returns None for non-existent ID."""
        node = boring_schema.get_by_id("non_existent_id")
        assert node is None

    def test_get_by_id_with_button(self):
        """Test get_by_id respects ignore_buttons parameter."""
        schema = Schema(
            id=1,
            content=[
                Section(
                    id="section1",
                    children=[
                        Datapoint(id="field1", type="string"),
                        Datapoint(id="button1", type="button"),
                    ],
                )
            ],
        )

        # Default: ignore buttons
        node = schema.get_by_id("button1")
        assert node is None

        # With ignore_buttons=False
        node = schema.get_by_id("button1", ignore_buttons=False)
        assert isinstance(node, Datapoint)
        assert node.id == "button1"
