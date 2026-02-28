from datamodel_navigator.models import Attribute, DataModel, Entity
from datamodel_navigator.viewer import build_viewer_html


def test_viewer_renders_entities() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:orders",
                name="orders",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            )
        ]
    )
    html = build_viewer_html(model)
    assert "Data Model Navigator" in html
    assert "orders" in html
