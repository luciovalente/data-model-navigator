from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Attribute:
    name: str
    type: str
    nullable: bool = True
    source: str = ""


@dataclass
class Entity:
    id: str
    name: str
    source_system: str
    source_type: str
    attributes: list[Attribute] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    id: str
    from_entity: str
    from_field: str
    to_entity: str
    to_field: str
    confidence: float
    source: str


@dataclass
class DataModel:
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "DataModel":
        entities = [
            Entity(
                id=e["id"],
                name=e["name"],
                source_system=e["source_system"],
                source_type=e["source_type"],
                attributes=[Attribute(**a) for a in e.get("attributes", [])],
                tags=e.get("tags", []),
            )
            for e in payload.get("entities", [])
        ]
        relationships = [Relationship(**r) for r in payload.get("relationships", [])]
        return DataModel(
            entities=entities,
            relationships=relationships,
            metadata=payload.get("metadata", {}),
        )
