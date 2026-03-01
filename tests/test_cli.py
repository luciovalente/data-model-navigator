from pathlib import Path

from datamodel_navigator import cli


def test_save_and_load_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    payload = {
        "postgres": {"host": "localhost", "port": 5432, "dbname": "postgres", "user": "postgres", "password": "secret", "schema": "public"},
        "mongo": {"uri": "mongodb://localhost:27017", "dbname": "test", "sample_size": 200},
        "llm": {"user_prompt": "prompt", "model": "gpt-4o-mini", "endpoint": "https://api.openai.com/v1/chat/completions", "api_key": "tok", "batch_size": 0},
    }

    cli.save_config(payload, path)

    loaded = cli.load_saved_config(path)
    assert loaded == payload


def test_phase_discovery_uses_saved_config_without_prompting(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    cli.save_config(
        {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "dbname": "postgres",
                "user": "postgres",
                "password": "postgres",
                "schema": "public",
            },
            "mongo": None,
            "llm": {
                "user_prompt": "Regole",
                "model": "gpt-4o-mini",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "token-123",
                "batch_size": 0,
            },
        },
        config_path,
    )

    monkeypatch.setattr(cli, "DEFAULT_CONFIG", config_path)

    ask_calls: list[str] = []

    def fake_ask(prompt: str, default: str | None = None) -> str:
        ask_calls.append(prompt)
        return default or ""

    captured = {}

    def fake_discover_model(pg, mg, llm_config=None):
        captured["pg"] = pg
        captured["mg"] = mg
        captured["llm"] = llm_config

        class DummyModel:
            pass

        return DummyModel()

    monkeypatch.setattr(cli, "ask", fake_ask)
    monkeypatch.setattr(cli, "discover_model", fake_discover_model)
    monkeypatch.setattr(cli, "save_model", lambda *_args, **_kwargs: None)

    cli.phase_discovery()

    assert ask_calls == []
    assert captured["pg"] is not None
    assert captured["pg"].host == "localhost"
    assert captured["mg"] is None
    assert captured["llm"] is not None
    assert captured["llm"].api_key == "token-123"


def test_phase_fix_json_model_applies_llm_corrections(monkeypatch, tmp_path: Path) -> None:
    model_path = tmp_path / "model.json"
    monkeypatch.setattr(cli, "DEFAULT_MODEL", model_path)

    answers = iter(["correggi modello", "gpt-4o-mini", "token-123"])

    def fake_ask(_prompt: str, default: str | None = None) -> str:
        return next(answers, default or "")

    captured = {}

    class DummyModel:
        def __init__(self):
            self.marker = "source"

    corrected_model = object()

    monkeypatch.setattr(cli, "ask", fake_ask)
    monkeypatch.setattr(cli, "load_model", lambda _path: DummyModel())

    def fake_correct(model, llm_config):
        captured["model"] = model
        captured["llm"] = llm_config
        return corrected_model

    saved = {}

    monkeypatch.setattr(cli, "correct_data_model_json", fake_correct)
    monkeypatch.setattr(cli, "save_model", lambda model, path: saved.update({"model": model, "path": path}))

    cli.phase_fix_json_model()

    assert captured["model"].marker == "source"
    assert captured["llm"].user_prompt == "correggi modello"
    assert captured["llm"].api_key == "token-123"
    assert saved["model"] is corrected_model
    assert saved["path"] == model_path
