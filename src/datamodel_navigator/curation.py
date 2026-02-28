from __future__ import annotations

from datamodel_navigator.models import DataModel, Entity, Relationship

TECHNICAL_NAMES = {
    "created_at",
    "updated_at",
    "version",
    "_class",
    "_etag",
    "deleted",
}


def auto_cleanup(model: DataModel) -> None:
    for entity in model.entities:
        entity.attributes = [a for a in entity.attributes if a.name.lower() not in TECHNICAL_NAMES]


def suggest_relationships(model: DataModel) -> list[Relationship]:
    suggestions: list[Relationship] = []
    entity_by_name = {e.name.lower(): e for e in model.entities}

    for entity in model.entities:
        for attr in entity.attributes:
            lowered = attr.name.lower()
            if lowered.endswith("_id") and lowered != "id":
                target_name = lowered.removesuffix("_id")
                target = entity_by_name.get(target_name)
                if target:
                    suggestions.append(
                        Relationship(
                            id=f"rel:{entity.id}:{attr.name}->{target.id}:id",
                            from_entity=entity.id,
                            from_field=attr.name,
                            to_entity=target.id,
                            to_field="id",
                            confidence=0.7,
                            source="auto",
                        )
                    )
            elif lowered.endswith("id") and lowered != "id":
                target_name = lowered[:-2]
                target = entity_by_name.get(target_name)
                if target:
                    suggestions.append(
                        Relationship(
                            id=f"rel:{entity.id}:{attr.name}->{target.id}:id",
                            from_entity=entity.id,
                            from_field=attr.name,
                            to_entity=target.id,
                            to_field="id",
                            confidence=0.55,
                            source="auto",
                        )
                    )

    existing = {r.id for r in model.relationships}
    unique = []
    for r in suggestions:
        if r.id not in existing:
            unique.append(r)
            existing.add(r.id)
    return unique


def add_manual_relationship(
    model: DataModel,
    from_entity: str,
    from_field: str,
    to_entity: str,
    to_field: str,
) -> Relationship:
    rel = Relationship(
        id=f"rel:{from_entity}:{from_field}->{to_entity}:{to_field}",
        from_entity=from_entity,
        from_field=from_field,
        to_entity=to_entity,
        to_field=to_field,
        confidence=1.0,
        source="manual",
    )
    model.relationships.append(rel)
    return rel


def find_entity(model: DataModel, entity_id: str) -> Entity | None:
    return next((e for e in model.entities if e.id == entity_id), None)
