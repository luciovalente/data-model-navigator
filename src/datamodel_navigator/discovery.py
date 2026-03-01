from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from datamodel_navigator.llm_guidance import LLMConfig, analyze_entity_samples, apply_llm_guidance
from datamodel_navigator.models import Attribute, DataModel, Entity


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    schema: str = "public"
    sample_records: int = 50


@dataclass
class MongoConfig:
    uri: str = "mongodb://localhost:27017"
    dbname: str = "test"
    sample_size: int = 200
    sample_records: int = 50


def _infer_type(values: list[Any]) -> str:
    types = Counter(type(v).__name__ for v in values if v is not None)
    if not types:
        return "unknown"
    return types.most_common(1)[0][0]


def _is_personal_key(key: str) -> bool:
    personal_markers = {
        "name",
        "email",
        "phone",
        "mobile",
        "address",
        "street",
        "city",
        "zip",
        "postal",
        "ssn",
        "fiscal",
        "vat",
        "tax",
        "birth",
        "dob",
        "password",
        "token",
    }
    lowered = key.lower()
    return any(marker in lowered for marker in personal_markers)


def _anonymize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return 0
    if isinstance(value, str):
        return "***"
    if isinstance(value, dict):
        return {k: _anonymize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_anonymize_value(v) for v in value]
    return "***"


def _anonymize_document(document: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in document.items():
        if _is_personal_key(key):
            masked[key] = _anonymize_value(value)
        elif isinstance(value, dict):
            masked[key] = _anonymize_document(value)
        elif isinstance(value, list):
            masked[key] = [
                _anonymize_document(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            masked[key] = value
    return masked


def discover_postgres(config: PostgresConfig) -> tuple[list[Entity], dict[str, int], dict[str, list[dict[str, Any]]]]:
    try:
        import psycopg
        from psycopg import sql
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Manca dipendenza psycopg. Installa con: pip install psycopg[binary]"
        ) from exc

    entities: list[Entity] = []
    table_counts: dict[str, int] = {}
    samples_by_table: dict[str, list[dict[str, Any]]] = {}

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
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier(config.schema),
                        sql.Identifier(table),
                    )
                )
                table_counts[table] = int(cur.fetchone()[0])

                cur.execute(
                    sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
                        sql.Identifier(config.schema),
                        sql.Identifier(table),
                    ),
                    (config.sample_records,),
                )
                records = cur.fetchall()
                columns = [desc.name for desc in cur.description]
                samples_by_table[table] = [
                    _anonymize_document(dict(zip(columns, row, strict=False))) for row in records
                ]

    return entities, table_counts, samples_by_table


def discover_mongo(config: MongoConfig) -> tuple[list[Entity], dict[str, int], dict[str, list[dict[str, Any]]]]:
    try:
        from pymongo import MongoClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("Manca dipendenza pymongo. Installa con: pip install pymongo") from exc

    client = MongoClient(config.uri)
    db = client[config.dbname]
    entities: list[Entity] = []
    collection_counts: dict[str, int] = {}
    samples_by_collection: dict[str, list[dict[str, Any]]] = {}

    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        collection_counts[collection_name] = int(collection.count_documents({}))

        samples = list(collection.find({}, limit=config.sample_size))
        all_keys: dict[str, list[Any]] = {}
        for doc in samples:
            for key, value in doc.items():
                all_keys.setdefault(key, []).append(value)

        deep_samples = list(collection.find({}, limit=config.sample_records))
        samples_by_collection[collection_name] = [_anonymize_document(doc) for doc in deep_samples]

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
    return entities, collection_counts, samples_by_collection


def discover_model(
    postgres: PostgresConfig | None,
    mongo: MongoConfig | None,
    llm_config: LLMConfig | None = None,
) -> DataModel:
    model = DataModel(metadata={"version": 1})
    discovery_log: list[str] = []
    source_counts: dict[str, dict[str, int]] = {}
    deep_samples: dict[str, list[dict[str, Any]]] = {}

    if postgres is not None:
        entities, table_counts, table_samples = discover_postgres(postgres)
        model.entities.extend(entities)
        source_counts["postgres"] = table_counts
        deep_samples.update({f"pg:{name}": docs for name, docs in table_samples.items()})
        discovery_log.append(f"Step 1/4 - Analizzate {len(table_counts)} tabelle SQL nel database PostgreSQL.")

    if mongo is not None:
        entities, collection_counts, collection_samples = discover_mongo(mongo)
        model.entities.extend(entities)
        source_counts["mongo"] = collection_counts
        deep_samples.update({f"mg:{name}": docs for name, docs in collection_samples.items()})
        discovery_log.append(f"Step 2/4 - Analizzate {len(collection_counts)} collection MongoDB nel database.")

    if source_counts:
        counts_lines = []
        for source_name, items in source_counts.items():
            for name, count in sorted(items.items()):
                counts_lines.append(f"{source_name}.{name}: {count} record")
        model.metadata["discovery_count_log"] = counts_lines
        discovery_log.append("Step 3/4 - Completata interrogazione COUNT(*)/count_documents per ogni entità.")

    if llm_config is not None and llm_config.user_prompt.strip():
        guidance = apply_llm_guidance(model.entities, llm_config)
        model.metadata["interpretation_prompt"] = llm_config.user_prompt
        model.metadata["interpretation_instructions"] = guidance.instructions
        model.metadata["llm_batches"] = len(guidance.raw_responses)

        sample_insights: dict[str, list[str]] = {}
        for entity in model.entities:
            samples = deep_samples.get(entity.id, [])
            if not samples:
                continue
            insights = analyze_entity_samples(
                entity_name=entity.name,
                entity_source=entity.source_system,
                samples=samples,
                config=llm_config,
            )
            if insights:
                sample_insights[entity.id] = insights
        if sample_insights:
            model.metadata["llm_sample_insights"] = sample_insights
            discovery_log.append(
                "Step 4/4 - Eseguita deep discovery su record anonimizzati con supporto LLM."
            )

    if deep_samples:
        model.metadata["deep_discovery_samples"] = deep_samples
    model.metadata["discovery_log"] = discovery_log

    return model
