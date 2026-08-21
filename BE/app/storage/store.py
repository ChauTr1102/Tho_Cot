"""
File-system + JSON "DB".

Layout on disk (relative to DATA_ROOT):
    data/
      <campaign_id>/
        input.json
        plan.json
        assets.json
        qa/
          iteration_1.json
          iteration_2.json
          ...
        status.json

No external DB engine — every stage just reads/writes a JSON file.
Kept intentionally simple/synchronous since this is a hackathon draft.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"


class JsonStore:
    def __init__(self, root: Path = DATA_ROOT):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _campaign_dir(self, campaign_id: str) -> Path:
        d = self.root / campaign_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, campaign_id: str, name: str, model: BaseModel) -> Path:
        """Save a pydantic model as <campaign_id>/<name>.json"""
        path = self._campaign_dir(campaign_id) / f"{name}.json"
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load(self, campaign_id: str, name: str, model_cls: Type[T]) -> T:
        path = self._campaign_dir(campaign_id) / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"{name} not found for campaign {campaign_id}: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return model_cls.model_validate(data)

    def exists(self, campaign_id: str, name: str) -> bool:
        return (self._campaign_dir(campaign_id) / f"{name}.json").exists()

    def save_qa_iteration(self, campaign_id: str, iteration: int, model: BaseModel) -> Path:
        qa_dir = self._campaign_dir(campaign_id) / "qa"
        qa_dir.mkdir(exist_ok=True)
        path = qa_dir / f"iteration_{iteration}.json"
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return path

    def list_qa_iterations(self, campaign_id: str) -> list[Path]:
        qa_dir = self._campaign_dir(campaign_id) / "qa"
        if not qa_dir.exists():
            return []
        return sorted(qa_dir.glob("iteration_*.json"))


store = JsonStore()
