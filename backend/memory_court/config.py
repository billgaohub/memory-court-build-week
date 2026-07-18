from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


HACKATHON_ROOT = Path(__file__).resolve().parents[2]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str = "gpt-5.6"
    request_timeout_seconds: float = 30.0
    max_output_tokens: int = 600
    max_model_calls: int = 8
    max_steps: int = 8
    max_proposals: int = 3
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    trust_proxy: bool = False
    cases_root: Path = HACKATHON_ROOT / "cases"
    replay_root: Path = HACKATHON_ROOT / "replay"

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS", "http://localhost:5173"
            ).split(",")
            if origin.strip()
        )
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
            request_timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
            max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "600")),
            allowed_origins=origins,
            trust_proxy=_as_bool(os.getenv("TRUST_PROXY")),
            cases_root=Path(os.getenv("CASES_ROOT", HACKATHON_ROOT / "cases")),
            replay_root=Path(os.getenv("REPLAY_ROOT", HACKATHON_ROOT / "replay")),
        )
