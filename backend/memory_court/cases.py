from __future__ import annotations

import json
from pathlib import Path

from .models import CaseDefinition


class CaseNotFoundError(KeyError):
    """Raised when a requested case id is not in the repository."""


class CaseRepository:
    def __init__(self, root: Path):
        self.root = Path(root)
        self._cases = self._load()

    def _load(self) -> dict[str, CaseDefinition]:
        loaded: dict[str, CaseDefinition] = {}
        for path in sorted(self.root.glob("*.json")):
            case = CaseDefinition.model_validate_json(path.read_text(encoding="utf-8"))
            if case.id in loaded:
                raise ValueError(f"duplicate case id: {case.id}")
            loaded[case.id] = case
        if not loaded:
            raise ValueError(f"no case definitions found in {self.root}")
        return loaded

    def list_cases(self) -> list[CaseDefinition]:
        return [self._cases[case_id] for case_id in sorted(self._cases)]

    def get(self, case_id: str) -> CaseDefinition:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise CaseNotFoundError(f"unknown case: {case_id}") from exc

    def as_json(self) -> str:
        return json.dumps(
            [case.model_dump(mode="json") for case in self.list_cases()],
            ensure_ascii=False,
        )
