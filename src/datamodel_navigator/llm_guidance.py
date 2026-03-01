from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib import request

from datamodel_navigator.models import DataModel, Entity


@dataclass
class LLMConfig:
    user_prompt: str
    model: str = "gpt-4o-mini"
    endpoint: str = "https://api.openai.com/v1/chat/completions"
    api_key: str | None = None
    batch_size: int = 0


@dataclass
class LLMGuidanceResult:
    instructions: list[str]
    raw_responses: list[str]


LLMCaller = Callable[[dict[str, Any], LLMConfig], str]


def _default_call_llm(payload: dict[str, Any], config: LLMConfig) -> str:
    api_key = config.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY non impostata: impossibile interrogare l'LLM")

    req = request.Request(
        config.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as resp:  # noqa: S310
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    return parsed["choices"][0]["message"]["content"]


def _chunk_entities(entities: list[Entity], batch_size: int) -> list[list[Entity]]:
    if batch_size <= 0:
        return [entities]
    return [entities[i : i + batch_size] for i in range(0, len(entities), batch_size)]


def _build_schema_snippet(entities: list[Entity]) -> str:
    compact = []
    for entity in entities:
        compact.append(
            {
                "id": entity.id,
                "name": entity.name,
                "source": entity.source_system,
                "type": entity.source_type,
                "attributes": [
                    {"name": attr.name, "type": attr.type, "nullable": attr.nullable}
                    for attr in entity.attributes
                ],
            }
        )
    return json.dumps(compact, ensure_ascii=False)


def _extract_json_block(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    return json.loads(cleaned)


def apply_llm_guidance(
    entities: list[Entity],
    config: LLMConfig,
    call_llm: LLMCaller | None = None,
) -> LLMGuidanceResult:
    if not entities:
        return LLMGuidanceResult(instructions=[], raw_responses=[])

    caller = call_llm or _default_call_llm
    all_instructions: list[str] = []
    raw_responses: list[str] = []

    for chunk in _chunk_entities(entities, config.batch_size):
        schema_payload = _build_schema_snippet(chunk)
        messages = [
            {
                "role": "system",
                "content": (
                    "Sei un assistente di data modeling. Ricevi schema tecnico di tabelle/collection "
                    "e un prompt funzionale dell'utente. Rispondi SOLO con JSON valido nel formato: "
                    '{"instructions": ["..."], "entity_hints": {"<entity_name>": {"tags": ["..."], "notes": "..."}}}. '
                    "Le instructions devono essere regole operative sintetiche per interpretare i dati, "
                    "senza analizzare record singoli."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Prompt utente:\n{config.user_prompt}\n\n"
                    f"Schema tecnico (batch):\n{schema_payload}"
                ),
            },
        ]
        payload = {
            "model": config.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        response_text = caller(payload, config)
        raw_responses.append(response_text)
        parsed = _extract_json_block(response_text)

        instructions = parsed.get("instructions", [])
        all_instructions.extend(str(x) for x in instructions)

        entity_hints = parsed.get("entity_hints", {})
        hints_by_name = {str(name).lower(): hint for name, hint in entity_hints.items()}
        for entity in chunk:
            hint = hints_by_name.get(entity.name.lower())
            if not hint:
                continue
            tags = [str(tag) for tag in hint.get("tags", []) if str(tag)]
            notes = str(hint.get("notes", "")).strip()
            for tag in tags:
                if tag not in entity.tags:
                    entity.tags.append(tag)
            if notes:
                note_tag = f"note:{notes}"
                if note_tag not in entity.tags:
                    entity.tags.append(note_tag)

    unique_instructions = list(dict.fromkeys(all_instructions))
    return LLMGuidanceResult(instructions=unique_instructions, raw_responses=raw_responses)


def analyze_entity_samples(
    *,
    entity_name: str,
    entity_source: str,
    samples: list[dict[str, Any]],
    config: LLMConfig,
    call_llm: LLMCaller | None = None,
) -> list[str]:
    """Richiede all'LLM osservazioni sui record anonimizzati di una entità."""
    if not samples:
        return []

    caller = call_llm or _default_call_llm
    messages = [
        {
            "role": "system",
            "content": (
                "Sei un assistente di data modeling. Ricevi record già anonimizzati di una tabella/collection. "
                "Rispondi SOLO con JSON valido nel formato: "
                '{"insights": ["..."]}. '
                "Le insights devono evidenziare possibili varianti di struttura o semantica (es. campi valorizzati "
                "solo per alcuni record), utili alla modellazione dati."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Prompt utente generale:\n{config.user_prompt}\n\n"
                f"Entità: {entity_name} ({entity_source})\n"
                f"Record anonimizzati (max {len(samples)}):\n{json.dumps(samples, ensure_ascii=False)}"
            ),
        },
    ]
    payload = {
        "model": config.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    response_text = caller(payload, config)
    parsed = _extract_json_block(response_text)
    return [str(x) for x in parsed.get("insights", []) if str(x).strip()]


def correct_data_model_json(
    model: DataModel,
    config: LLMConfig,
    call_llm: LLMCaller | None = None,
) -> DataModel:
    """Richiede all'LLM una versione corretta del JSON modello dati."""
    caller = call_llm or _default_call_llm
    current_json = json.dumps(model.to_dict(), ensure_ascii=False)
    messages = [
        {
            "role": "system",
            "content": (
                "Sei un assistente di data modeling. Ricevi il JSON di un modello dati e un prompt utente "
                "con richieste di correzione. Rispondi SOLO con JSON valido nel formato "
                '{"model": {"entities": [], "relationships": [], "metadata": {}}}. '
                "Mantieni i campi presenti nello schema e applica solo correzioni coerenti con il prompt."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Prompt utente:\n{config.user_prompt}\n\n"
                f"JSON modello corrente:\n{current_json}"
            ),
        },
    ]
    payload = {
        "model": config.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    response_text = caller(payload, config)
    parsed = _extract_json_block(response_text)
    corrected_model_payload = parsed.get("model")
    if not isinstance(corrected_model_payload, dict):
        raise ValueError("Risposta LLM non valida: campo 'model' mancante o non oggetto JSON")

    return DataModel.from_dict(corrected_model_payload)
