from datamodel_navigator.discovery import discover_model
from datamodel_navigator.llm_guidance import LLMConfig, analyze_entity_samples, apply_llm_guidance, correct_data_model_json
from datamodel_navigator.models import Attribute, DataModel, Entity


def test_apply_llm_guidance_single_call_with_tags_and_notes() -> None:
    entities = [
        Entity(
            id="pg:orders",
            name="orders",
            source_system="postgres",
            source_type="table",
            attributes=[Attribute(name="id", type="uuid", nullable=False)],
        )
    ]

    calls = []

    def fake_call(payload, _config):
        calls.append(payload)
        return '{"instructions": ["Usa order_type per distinguere sotto-entita"], "entity_hints": {"orders": {"tags": ["polymorphic-table"], "notes": "Una riga mappa più entità"}}}'

    result = apply_llm_guidance(entities, LLMConfig(user_prompt="prompt"), call_llm=fake_call)

    assert len(calls) == 1
    assert result.instructions == ["Usa order_type per distinguere sotto-entita"]
    assert "polymorphic-table" in entities[0].tags
    assert any(tag.startswith("note:") for tag in entities[0].tags)


def test_apply_llm_guidance_batching() -> None:
    entities = [
        Entity(id=f"pg:t{i}", name=f"t{i}", source_system="postgres", source_type="table", attributes=[])
        for i in range(5)
    ]

    calls = []

    def fake_call(payload, _config):
        calls.append(payload)
        return '{"instructions": ["regola"], "entity_hints": {}}'

    result = apply_llm_guidance(
        entities,
        LLMConfig(user_prompt="prompt", batch_size=2),
        call_llm=fake_call,
    )

    assert len(calls) == 3
    assert result.instructions == ["regola"]


def test_discover_model_without_sources_keeps_empty_entities() -> None:
    model = discover_model(postgres=None, mongo=None)
    assert model.entities == []


def test_analyze_entity_samples_returns_insights() -> None:
    calls = []

    def fake_call(payload, _config):
        calls.append(payload)
        return '{"insights": ["Campo type discrimina sottotipi"]}'

    insights = analyze_entity_samples(
        entity_name="orders",
        entity_source="postgres",
        samples=[{"id": 1, "type": "retail"}],
        config=LLMConfig(user_prompt="trova varianti"),
        call_llm=fake_call,
    )

    assert len(calls) == 1
    assert insights == ["Campo type discrimina sottotipi"]


def test_correct_data_model_json_returns_corrected_model() -> None:
    model = DataModel(
        entities=[
            Entity(
                id="pg:orders",
                name="orders",
                source_system="postgres",
                source_type="table",
                attributes=[Attribute(name="id", type="uuid", nullable=False)],
            )
        ],
        relationships=[],
        metadata={"source": "test"},
    )

    calls = []

    def fake_call(payload, _config):
        calls.append(payload)
        return (
            '{"model": {"entities": [{"id": "pg:orders", "name": "orders", "source_system": "postgres", '
            '"source_type": "table", "attributes": [{"name": "id", "type": "uuid", "nullable": false, "source": ""}], '
            '"tags": ["validated"]}], "relationships": [], "metadata": {"source": "test", "fixed": true}}}'
        )

    corrected = correct_data_model_json(model, LLMConfig(user_prompt="correggi"), call_llm=fake_call)

    assert len(calls) == 1
    assert corrected.metadata["fixed"] is True
    assert corrected.entities[0].tags == ["validated"]
