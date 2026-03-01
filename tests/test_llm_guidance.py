from datamodel_navigator.discovery import discover_model
from datamodel_navigator.llm_guidance import LLMConfig, apply_llm_guidance
from datamodel_navigator.models import Attribute, Entity


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
