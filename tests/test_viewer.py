import json
import re

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
    assert "board-entity" in html


def test_embedded_json_is_valid_not_html_escaped() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:x",
                name='entity "quoted"',
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            )
        ]
    )
    html = build_viewer_html(model)
    assert "&quot;" not in html

    match = re.search(r"<script id='model-data' type='application/json'>(.*?)</script>", html, re.S)
    assert match is not None
    payload = match.group(1).replace("<\\/", "</")
    parsed = json.loads(payload)
    assert parsed["entities"][0]["name"] == 'entity "quoted"'


def test_viewer_contains_relationship_panel_and_excel_export() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:orders",
                name="orders",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            ),
            Entity(
                id="pg:customers",
                name="customers",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            ),
        ]
    )

    html = build_viewer_html(model)
    assert "Relazioni Entità" in html
    assert "export-excel" in html
    assert "xlsx.full.min.js" in html
    assert "connector-layer" in html
    assert "drawConnectors" in html


def test_viewer_uses_escaped_newline_in_csv_join() -> None:
    model = DataModel(entities=[])
    html = build_viewer_html(model)
    assert "].join('\\n');" in html


def test_viewer_uses_drag_interaction_for_entities() -> None:
    model = DataModel(entities=[])
    html = build_viewer_html(model)
    assert "pointerdown" in html
    assert "pointermove" in html
    assert "enableDrag" in html


def test_viewer_uses_svg_connectors_instead_of_network_library() -> None:
    model = DataModel(entities=[])
    html = build_viewer_html(model)
    assert "vis-network" not in html
    assert "<svg id='connector-layer'>" in html
    assert "drawEndpointGlyph" in html
