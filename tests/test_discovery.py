from datamodel_navigator import discovery
from datamodel_navigator.llm_guidance import LLMConfig
from datamodel_navigator.models import Attribute, Entity


def test_anonymize_document_masks_personal_data() -> None:
    payload = {
        "name": "Mario Rossi",
        "email": "mario@example.com",
        "amount": 99.5,
        "profile": {"phone": "123", "city": "Roma"},
    }

    masked = discovery._anonymize_document(payload)

    assert masked["name"] == "***"
    assert masked["email"] == "***"
    assert masked["amount"] == 99.5
    assert masked["profile"]["phone"] == "***"
    assert masked["profile"]["city"] == "***"


def test_discover_model_adds_discovery_logs_and_counts(monkeypatch) -> None:
    def fake_discover_postgres(_config):
        return (
            [
                Entity(
                    id="pg:orders",
                    name="orders",
                    source_system="postgres",
                    source_type="table",
                    attributes=[Attribute(name="id", type="int", nullable=False)],
                )
            ],
            {"orders": 42},
            {"orders": [{"id": 1, "customer_email": "***"}]},
        )

    monkeypatch.setattr(discovery, "discover_postgres", fake_discover_postgres)

    model = discovery.discover_model(
        postgres=discovery.PostgresConfig(),
        mongo=None,
        llm_config=None,
    )

    assert model.metadata["discovery_count_log"] == ["postgres.orders: 42 record"]
    assert any("Analizzate 1 tabelle SQL" in step for step in model.metadata["discovery_log"])


def test_discover_model_runs_deep_llm_insights(monkeypatch) -> None:
    def fake_discover_postgres(_config):
        return (
            [
                Entity(
                    id="pg:orders",
                    name="orders",
                    source_system="postgres",
                    source_type="table",
                    attributes=[Attribute(name="type", type="text", nullable=True)],
                )
            ],
            {"orders": 2},
            {"orders": [{"type": "A"}, {"type": "B"}]},
        )

    monkeypatch.setattr(discovery, "discover_postgres", fake_discover_postgres)
    monkeypatch.setattr(
        discovery,
        "apply_llm_guidance",
        lambda entities, _cfg: type("R", (), {"instructions": ["i1"], "raw_responses": ["x"]})(),
    )
    monkeypatch.setattr(
        discovery,
        "analyze_entity_samples",
        lambda **_kwargs: ["Campo type presente solo su subset di record"],
    )

    model = discovery.discover_model(
        postgres=discovery.PostgresConfig(),
        mongo=None,
        llm_config=LLMConfig(user_prompt="analizza differenze"),
    )

    assert model.metadata["llm_sample_insights"]["pg:orders"]
    assert any("deep discovery" in step.lower() for step in model.metadata["discovery_log"])
