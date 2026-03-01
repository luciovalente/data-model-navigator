from __future__ import annotations

import argparse
import json
import webbrowser
from pathlib import Path

from datamodel_navigator.curation import add_manual_relationship, auto_cleanup, find_entity, suggest_relationships
from datamodel_navigator.discovery import MongoConfig, PostgresConfig, discover_model
from datamodel_navigator.io_utils import load_model, save_model
from datamodel_navigator.llm_guidance import LLMConfig
from datamodel_navigator.viewer import write_viewer

DEFAULT_MODEL = Path("output/model.json")


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def phase_discovery() -> None:
    print("\n== Fase 1: Connessione e discovery ==")
    use_pg = ask("Connettere PostgreSQL? (y/n)", "y").lower() == "y"
    use_mg = ask("Connettere MongoDB? (y/n)", "y").lower() == "y"

    pg = None
    mg = None
    if use_pg:
        pg = PostgresConfig(
            host=ask("PG host", "localhost"),
            port=int(ask("PG porta", "5432")),
            dbname=ask("PG dbname", "postgres"),
            user=ask("PG user", "postgres"),
            password=ask("PG password", "postgres"),
            schema=ask("PG schema", "public"),
        )
    if use_mg:
        mg = MongoConfig(
            uri=ask("Mongo URI", "mongodb://localhost:27017"),
            dbname=ask("Mongo dbname", "test"),
            sample_size=int(ask("Mongo sample size", "200")),
        )

    llm_config = None
    use_llm_guidance = ask("Caricare prompt di interpretazione LLM? (y/n)", "n").lower() == "y"
    if use_llm_guidance:
        prompt = ask("Prompt interpretazione")
        batch_size = int(
            ask(
                "Batch size entità per chiamata LLM (0 = chiamata unica su tutto lo schema)",
                "0",
            )
        )
        llm_config = LLMConfig(user_prompt=prompt, batch_size=batch_size)

    model = discover_model(pg, mg, llm_config=llm_config)
    save_model(model, DEFAULT_MODEL)
    print(f"Modello scoperto e salvato in {DEFAULT_MODEL}")


def phase_curation() -> None:
    print("\n== Fase 2: Pulizia e relazioni ==")
    model = load_model(DEFAULT_MODEL)

    auto_cleanup(model)
    print("Pulizia automatica completata (campi tecnici rimossi).")

    auto_rels = suggest_relationships(model)
    print(f"Relazioni suggerite automaticamente: {len(auto_rels)}")
    model.relationships.extend(auto_rels)

    while True:
        print("\nEntità disponibili:")
        for e in model.entities:
            print(f"- {e.id} ({len(e.attributes)} campi)")

        if ask("Aggiungere relazione manuale? (y/n)", "n").lower() != "y":
            break

        from_entity = ask("from_entity (id)")
        to_entity = ask("to_entity (id)")
        if not find_entity(model, from_entity) or not find_entity(model, to_entity):
            print("Entity non trovata.")
            continue
        from_field = ask("from_field")
        to_field = ask("to_field", "id")
        rel = add_manual_relationship(model, from_entity, from_field, to_entity, to_field)
        print(f"Aggiunta relazione manuale: {rel.id}")

    save_model(model, DEFAULT_MODEL)
    print(f"Modello curato salvato in {DEFAULT_MODEL}")


def phase_viewer(open_browser: bool = False) -> None:
    print("\n== Fase 3: Viewer E/R navigabile ==")
    model = load_model(DEFAULT_MODEL)
    out = write_viewer(model, "output/viewer.html")
    print(f"Viewer creato in {out}")
    if open_browser:
        webbrowser.open(out.resolve().as_uri())


def phase_show_json() -> None:
    model = load_model(DEFAULT_MODEL)
    print(json.dumps(model.to_dict(), indent=2, ensure_ascii=False))


def interactive_menu() -> None:
    actions = {
        "1": ("Discovery da PostgreSQL/Mongo", phase_discovery),
        "2": ("Configurazione: pulizia + relazioni", phase_curation),
        "3": ("Genera viewer E/R", phase_viewer),
        "4": ("Mostra JSON modello", phase_show_json),
    }

    while True:
        print("\n=== Data Model Navigator ===")
        for key, (label, _) in actions.items():
            print(f"{key}) {label}")
        print("0) Esci")
        choice = input("Scegli una fase: ").strip()

        if choice == "0":
            return
        action = actions.get(choice)
        if not action:
            print("Scelta non valida")
            continue
        try:
            if choice == "3":
                open_browser = ask("Aprire browser automaticamente? (y/n)", "n").lower() == "y"
                phase_viewer(open_browser=open_browser)
            else:
                action[1]()
        except FileNotFoundError:
            print(f"File {DEFAULT_MODEL} non trovato. Esegui prima la fase 1.")
        except Exception as exc:  # noqa: BLE001
            print(f"Errore: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Model Navigator")
    parser.add_argument("--menu", action="store_true", help="Avvia menu interattivo")
    parser.add_argument("--phase", choices=["discover", "curate", "viewer", "json"])
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()

    if args.menu or not args.phase:
        interactive_menu()
        return

    if args.phase == "discover":
        phase_discovery()
    elif args.phase == "curate":
        phase_curation()
    elif args.phase == "viewer":
        phase_viewer(open_browser=args.open_browser)
    elif args.phase == "json":
        phase_show_json()


if __name__ == "__main__":
    main()
