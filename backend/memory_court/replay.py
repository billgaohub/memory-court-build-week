from __future__ import annotations

from pathlib import Path

from .models import ReplayResponse


class ReplayNotFoundError(KeyError):
    """Raised when a requested case has no recorded replay."""


class ReplayRepository:
    def __init__(self, root: Path):
        self.root = Path(root)

    def get(self, case_id: str) -> ReplayResponse:
        path = self.root / f"{case_id}.json"
        if not path.is_file():
            raise ReplayNotFoundError(f"unknown replay: {case_id}")
        replay = ReplayResponse.model_validate_json(path.read_text(encoding="utf-8"))
        if any(event.mode != "replay" for event in replay.events):
            raise ValueError("replay contains an event not labeled replay")
        return replay
