from __future__ import annotations

import json
from pathlib import Path

from datamodel_navigator.models import DataModel


def save_model(model: DataModel, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(model.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_model(path: str | Path) -> DataModel:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return DataModel.from_dict(payload)
