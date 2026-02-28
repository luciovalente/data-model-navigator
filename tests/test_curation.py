from datamodel_navigator.curation import auto_cleanup, suggest_relationships
from datamodel_navigator.models import Attribute, DataModel, Entity


def test_auto_cleanup_removes_technical_fields() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:orders",
                name="orders",
                source_system="postgres",
                source_type="table",
                attributes=[
                    Attribute(name="id", type="uuid", nullable=False),
                    Attribute(name="created_at", type="timestamp", nullable=False),
                ],
            )
        ]
    )
    auto_cleanup(model)
    assert [a.name for a in model.entities[0].attributes] == ["id"]


def test_suggest_relationships_from_suffix_id() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:orders",
                name="orders",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="customer_id", type="uuid", nullable=False)],
            ),
            Entity(
                id="pg:customer",
                name="customer",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            ),
        ]
    )

    rels = suggest_relationships(model)
    assert len(rels) == 1
    assert rels[0].from_entity == "pg:orders"
    assert rels[0].to_entity == "pg:customer"
