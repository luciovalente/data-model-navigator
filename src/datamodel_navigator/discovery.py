from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from datamodel_navigator.llm_guidance import LLMConfig, apply_llm_guidance
from datamodel_navigator.models import Attribute, DataModel, Entity


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    schema: str = "public"


@dataclass
class MongoConfig:
    uri: str = "mongodb://localhost:27017"
    dbname: str = "test"
    sample_size: int = 200


def discover_postgres(config: PostgresConfig) -> list[Entity]:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Manca dipendenza psycopg. Installa con: pip install psycopg[binary]"
        ) from exc

    entities: list[Entity] = []
    query = """
    SELECT c.table_name, c.column_name, c.data_type, c.is_nullable
    FROM information_schema.columns c
    WHERE c.table_schema = %s
    ORDER BY c.table_name, c.ordinal_position
    """
    with psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (config.schema,))
            rows = cur.fetchall()

    by_table: dict[str, list[Attribute]] = {}
    for table, column, dtype, is_nullable in rows:
        by_table.setdefault(table, []).append(
            Attribute(
                name=column,
                type=dtype,
                nullable=(is_nullable == "YES"),
                source="postgres",
            )
        )

    for table, attributes in by_table.items():
        entities.append(
            Entity(
                id=f"pg:{table}",
                name=table,
                source_system="postgres",
                source_type="table",
                attributes=attributes,
            )
        )
    return entities


def _infer_type(values: list[Any]) -> str:
    types = Counter(type(v).__name__ for v in values if v is not None)
    if not types:
        return "unknown"
    return types.most_common(1)[0][0]


def discover_mongo(config: MongoConfig) -> list[Entity]:
    try:
        from pymongo import MongoClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("Manca dipendenza pymongo. Installa con: pip install pymongo") from exc

    client = MongoClient(config.uri)
    db = client[config.dbname]
    entities: list[Entity] = []

    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        samples = list(collection.find({}, limit=config.sample_size))
        all_keys: dict[str, list[Any]] = {}
        for doc in samples:
            for key, value in doc.items():
                all_keys.setdefault(key, []).append(value)

        attributes = [
            Attribute(name=key, type=_infer_type(values), nullable=False, source="mongo")
            for key, values in sorted(all_keys.items())
        ]
        entities.append(
            Entity(
                id=f"mg:{collection_name}",
                name=collection_name,
                source_system="mongo",
                source_type="collection",
                attributes=attributes,
            )
        )
    return entities


def discover_model(
    postgres: PostgresConfig | None,
    mongo: MongoConfig | None,
    llm_config: LLMConfig | None = None,
) -> DataModel:
    model = DataModel(metadata={"version": 1})
    if postgres is not None:
        model.entities.extend(discover_postgres(postgres))
    if mongo is not None:
        model.entities.extend(discover_mongo(mongo))

    if llm_config is not None and llm_config.user_prompt.strip():
        guidance = apply_llm_guidance(model.entities, llm_config)
        model.metadata["interpretation_prompt"] = llm_config.user_prompt
        model.metadata["interpretation_instructions"] = guidance.instructions
        model.metadata["llm_batches"] = len(guidance.raw_responses)

    return model
