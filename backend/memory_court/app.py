from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .cases import CaseNotFoundError, CaseRepository
from .config import Settings
from .model_client import ModelClient, OpenAIModelClient
from .models import (
    AuditEvent,
    CaseSummary,
    HealthResponse,
    ReplayResponse,
    SessionCreateRequest,
    SessionView,
)
from .rate_limit import FixedWindowRateLimiter
from .replay import ReplayNotFoundError, ReplayRepository
from .session import AgentSession, SessionTerminalError


ModelClientFactory = Callable[[], ModelClient]


class SessionRegistry:
    def __init__(self, ttl_seconds: float = 3600, clock: Callable[[], float] = time.time):
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._sessions: dict[str, tuple[AgentSession, float]] = {}

    def add(self, session: AgentSession) -> None:
        self._sessions[session.id] = (session, self.clock())

    def get(self, session_id: str) -> AgentSession:
        entry = self._sessions.get(session_id)
        if entry is None:
            raise KeyError(session_id)
        session, last_access = entry
        if self.clock() - last_access > self.ttl_seconds:
            del self._sessions[session_id]
            raise KeyError(session_id)
        self._sessions[session_id] = (session, self.clock())
        return session


def _client_address(request: Request, trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def create_app(
    settings: Settings | None = None,
    *,
    model_client_factory: ModelClientFactory | None = None,
) -> FastAPI:
    resolved = settings or Settings.from_env()
    cases = CaseRepository(resolved.cases_root)
    replays = ReplayRepository(resolved.replay_root)
    registry = SessionRegistry()
    limiter = FixedWindowRateLimiter(limit=5, window_seconds=600)
    live_available = bool(resolved.openai_api_key or model_client_factory)

    api = FastAPI(
        title="Memory Court API",
        version=__version__,
        description="Bounded GPT-5.6 intervention audit with sonuv-guard adjudication.",
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    def require_session(session_id: str) -> AgentSession:
        try:
            return registry.get(session_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SESSION_NOT_FOUND", "message": "Session not found."},
            ) from exc

    @api.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            model=resolved.openai_model,
            live_available=live_available,
            version=__version__,
        )

    @api.get("/api/cases", response_model=list[CaseSummary])
    async def list_cases() -> list[CaseSummary]:
        return [
            CaseSummary(
                id=case.id,
                title=case.title,
                tagline=case.tagline,
                provenance=case.provenance,
                profile=case.profile,
                initial_state=case.initial_state,
            )
            for case in cases.list_cases()
        ]

    @api.get("/api/replays/{case_id}", response_model=ReplayResponse)
    async def get_replay(case_id: str) -> ReplayResponse:
        try:
            return replays.get(case_id)
        except ReplayNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REPLAY_NOT_FOUND", "message": "Replay not found."},
            ) from exc

    @api.post(
        "/api/sessions",
        response_model=SessionView,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_session(
        payload: SessionCreateRequest, request: Request
    ) -> SessionView:
        if not live_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "LIVE_UNAVAILABLE",
                    "message": "Live GPT-5.6 is unavailable; use the labeled replay.",
                    "replay_url": f"/api/replays/{payload.case_id}",
                },
            )
        try:
            case = cases.get(payload.case_id)
        except CaseNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CASE_NOT_FOUND", "message": "Case not found."},
            ) from exc
        client_key = _client_address(request, resolved.trust_proxy)
        if not limiter.allow(client_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMITED",
                    "message": "Five live sessions are allowed per ten minutes.",
                },
            )
        factory = model_client_factory or (
            lambda: OpenAIModelClient(
                api_key=resolved.openai_api_key,
                model=resolved.openai_model,
                timeout_seconds=resolved.request_timeout_seconds,
                max_output_tokens=resolved.max_output_tokens,
            )
        )
        session = AgentSession(
            case,
            factory(),
            max_model_calls=resolved.max_model_calls,
            max_steps=resolved.max_steps,
            max_proposals=resolved.max_proposals,
        )
        registry.add(session)
        return session.view()

    @api.get("/api/sessions/{session_id}", response_model=SessionView)
    async def get_session(session_id: str) -> SessionView:
        return require_session(session_id).view()

    @api.post("/api/sessions/{session_id}/step", response_model=AuditEvent)
    async def step_session(session_id: str) -> AuditEvent:
        session = require_session(session_id)
        try:
            return await session.step()
        except SessionTerminalError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "SESSION_TERMINAL", "message": str(exc)},
            ) from exc

    @api.post("/api/sessions/{session_id}/run", response_model=SessionView)
    async def run_session(session_id: str) -> SessionView:
        session = require_session(session_id)
        if not session.terminal:
            await session.run()
        return session.view()

    return api


app = create_app()
