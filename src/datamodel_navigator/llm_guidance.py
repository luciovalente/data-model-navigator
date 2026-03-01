from __future__ import annotations

import importlib.util
import json
import os
import ssl
from dataclasses import dataclass
from typing import Any, Callable
from urllib import request
from urllib.error import URLError

from datamodel_navigator.models import DataModel, Entity


@dataclass
class LLMConfig:
    user_prompt: str
    model: str = "gpt-4o-mini"
    endpoint: str = "https://api.openai.com/v1/chat/completions"
    api_key: str | None = None
    batch_size: int = 0
    allow_insecure_ssl: bool = False


@dataclass
class LLMGuidanceResult:
    instructions: list[str]
    raw_responses: list[str]


LLMCaller = Callable[[dict[str, Any], LLMConfig], str]

def _build_ssl_context() -> ssl.SSLContext:
    """Crea il contesto SSL con supporto a CA bundle custom e fallback certifi."""
    ca_bundle_path = os.getenv("DMN_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if ca_bundle_path:
        return ssl.create_default_context(cafile=ca_bundle_path)

    # Fallback utile su ambienti dove lo store certificati di sistema non è allineato.
    certifi_spec = importlib.util.find_spec("certifi")
    if certifi_spec is not None:
        certifi = __import__("certifi")
        return ssl.create_default_context(cafile=certifi.where())

    return ssl.create_default_context()


def _ssl_help_message() -> str:
    return (
        "Connessione HTTPS verso endpoint LLM fallita: certificato non verificabile. "
        "Questo accade spesso con proxy/TLS inspection aziendali o store CA locali non aggiornati. "
        "Se hai il certificato CA aziendale in PEM, imposta DMN_CA_BUNDLE "
        "(o SSL_CERT_FILE) con il suo percorso. "
        "Se non sai dove trovarlo, chiedi all'IT il certificato root/intermedio del proxy HTTPS."
    )

def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _build_ssl_context() -> ssl.SSLContext:
    """Crea il contesto SSL con supporto a CA bundle custom e fallback certifi."""
    if _env_truthy("DMN_ALLOW_INSECURE_SSL"):
        return ssl._create_unverified_context()

    ca_bundle_path = os.getenv("DMN_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if ca_bundle_path:
        return ssl.create_default_context(cafile=ca_bundle_path)

    # Fallback utile su ambienti dove lo store certificati di sistema non è allineato.
    certifi_spec = importlib.util.find_spec("certifi")
    if certifi_spec is not None:
        certifi = __import__("certifi")
        return ssl.create_default_context(cafile=certifi.where())

    return ssl.create_default_context()


def _ssl_help_message() -> str:
    return (
        "Connessione HTTPS verso endpoint LLM fallita: certificato non verificabile. "
        "Questo accade spesso con proxy/TLS inspection aziendali o store CA locali non aggiornati. "
        "Se hai il certificato CA aziendale in PEM, imposta DMN_CA_BUNDLE "
        "(o SSL_CERT_FILE) con il suo percorso. "
        "Se non sai dove trovarlo, chiedi all'IT il certificato root/intermedio del proxy HTTPS. "
        "Solo come ultima risorsa temporanea in ambiente non produttivo puoi impostare "
        "DMN_ALLOW_INSECURE_SSL=1 per disabilitare la verifica certificato."
    )

def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _build_ssl_context(config: LLMConfig) -> ssl.SSLContext:
    """Crea il contesto SSL con supporto a CA bundle custom e fallback certifi."""
    if config.allow_insecure_ssl or _env_truthy("DMN_ALLOW_INSECURE_SSL"):
        return ssl._create_unverified_context()

    ca_bundle_path = os.getenv("DMN_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if ca_bundle_path:
        return ssl.create_default_context(cafile=ca_bundle_path)

    # Fallback utile su ambienti dove lo store certificati di sistema non è allineato.
    certifi_spec = importlib.util.find_spec("certifi")
    if certifi_spec is not None:
        certifi = __import__("certifi")
        return ssl.create_default_context(cafile=certifi.where())

    return ssl.create_default_context()


def _ssl_help_message() -> str:
    return (
        "Connessione HTTPS verso endpoint LLM fallita: certificato non verificabile. "
        "Questo accade spesso con proxy/TLS inspection aziendali o store CA locali non aggiornati. "
        "Se hai il certificato CA aziendale in PEM, imposta DMN_CA_BUNDLE "
        "(o SSL_CERT_FILE) con il suo percorso. "
        "Se non sai dove trovarlo, chiedi all'IT il certificato root/intermedio del proxy HTTPS. "
        "Solo come ultima risorsa temporanea in ambiente non produttivo puoi impostare "
        "DMN_ALLOW_INSECURE_SSL=1 per disabilitare la verifica certificato."
    )

def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _build_ssl_context(config: LLMConfig | None = None) -> ssl.SSLContext:
    """Crea il contesto SSL con supporto a CA bundle custom e fallback certifi."""
    allow_insecure = bool(config and config.allow_insecure_ssl)
    if allow_insecure or _env_truthy("DMN_ALLOW_INSECURE_SSL"):
        return ssl._create_unverified_context()

    ca_bundle_path = os.getenv("DMN_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if ca_bundle_path:
        return ssl.create_default_context(cafile=ca_bundle_path)

    # Fallback utile su ambienti dove lo store certificati di sistema non è allineato.
    certifi_spec = importlib.util.find_spec("certifi")
    if certifi_spec is not None:
        certifi = __import__("certifi")
        return ssl.create_default_context(cafile=certifi.where())

    return ssl.create_default_context()


def _ssl_help_message() -> str:
    return (
        "Connessione HTTPS verso endpoint LLM fallita: certificato non verificabile. "
        "Questo accade spesso con proxy/TLS inspection aziendali o store CA locali non aggiornati. "
        "Se hai il certificato CA aziendale in PEM, imposta DMN_CA_BUNDLE "
        "(o SSL_CERT_FILE) con il suo percorso. "
        "Se non sai dove trovarlo, chiedi all'IT il certificato root/intermedio del proxy HTTPS. "
        "Solo come ultima risorsa temporanea in ambiente non produttivo puoi impostare "
        "DMN_ALLOW_INSECURE_SSL=1 per disabilitare la verifica certificato."
    )

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

    ssl_context = _build_ssl_context(config)
    ssl_context = _build_ssl_context()
    ssl_context = ssl.create_default_context()

    # Permette di specificare un bundle certificati custom in ambienti aziendali/proxy.
    ca_bundle_path = os.getenv("DMN_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if ca_bundle_path:
        ssl_context.load_verify_locations(cafile=ca_bundle_path)

    try:
        with request.urlopen(req, timeout=30, context=ssl_context) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
    except URLError as exc:
        message = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" in message:
            raise RuntimeError(_ssl_help_message()) from exc
            raise RuntimeError(
                "Connessione HTTPS verso endpoint LLM fallita: certificato non verificabile. "
                "Se sei dietro proxy/certificato aziendale, imposta DMN_CA_BUNDLE "
                "(o SSL_CERT_FILE) al percorso del file PEM della CA locale."
            ) from exc
        raise

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
