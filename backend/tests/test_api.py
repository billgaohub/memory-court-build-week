from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from memory_court.app import SessionRegistry, create_app
from memory_court.config import Settings
from memory_court.model_client import FakeModelClient
from memory_court.models import FinalizeAction, InspectAction, InterventionAction


HACKATHON_ROOT = Path(__file__).resolve().parents[2]


def settings(*, live: bool) -> Settings:
    return Settings(
        openai_api_key="test-key" if live else None,
        cases_root=HACKATHON_ROOT / "cases",
        replay_root=HACKATHON_ROOT / "replay",
        allowed_origins=("https://memory-court.vercel.app", "http://localhost:5173"),
    )


def live_factory():
    return FakeModelClient(
        [
            InspectAction(
                action="inspect_memory",
                memory_id="launch_manifest",
                rationale="Inspect the manifest.",
            ),
            InterventionAction(
                action="propose_intervention",
                patch={"distress": 30},
                rationale="Attempt a bounded reduction in distress.",
            ),
            FinalizeAction(
                action="finalize",
                outcome="repair",
                rationale="The trace supports gradual accountable repair.",
            ),
        ]
    )


def test_health_without_key_is_honest() -> None:
    with TestClient(create_app(settings(live=False))) as client:
        body = client.get("/api/health").json()

    assert body["live_available"] is False
    assert body["replay_available"] is True
    assert body["model"] == "gpt-5.6"


def test_live_session_is_unavailable_without_server_key() -> None:
    with TestClient(create_app(settings(live=False))) as client:
        response = client.post(
            "/api/sessions", json={"case_id": "silent_lifeboat"}
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "LIVE_UNAVAILABLE"
    assert response.json()["detail"]["replay_url"].endswith("/silent_lifeboat")


def test_replay_is_always_labeled() -> None:
    with TestClient(create_app(settings(live=False))) as client:
        body = client.get("/api/replays/silent_lifeboat").json()

    assert body["mode"] == "replay"
    assert body["label"] == "REPLAY MODE"
    assert body["provenance"] == "codex_gpt_5_6_sol"
    assert body["source_task_id"] == "019f725e-6f43-78c2-8587-4ad6a3725d9f"
    assert body["model"] == "gpt-5.6-sol via Codex (recorded)"
    assert body["api_live"] is False
    assert "not through the OpenAI API" in body["disclosure"]
    assert all(event["mode"] == "replay" for event in body["events"])


def test_live_run_exposes_trace_guard_and_recoverable_session() -> None:
    with TestClient(
        create_app(settings(live=True), model_client_factory=live_factory)
    ) as client:
        created = client.post(
            "/api/sessions", json={"case_id": "silent_lifeboat"}
        )
        assert created.status_code == 201
        session_id = created.json()["id"]

        run = client.post(f"/api/sessions/{session_id}/run")
        recovered = client.get(f"/api/sessions/{session_id}")

    assert run.status_code == 200
    actions = [event["model_action"] for event in run.json()["events"]]
    assert actions == ["inspect_memory", "propose_intervention", "finalize"]
    assert run.json()["events"][0]["guard"] is None
    assert run.json()["events"][1]["guard"]["action"] == "REPAIR"
    assert recovered.json() == run.json()


def test_sixth_live_session_is_rate_limited() -> None:
    with TestClient(
        create_app(settings(live=True), model_client_factory=live_factory)
    ) as client:
        statuses = [
            client.post(
                "/api/sessions",
                json={"case_id": "silent_lifeboat"},
            ).status_code
            for _ in range(6)
        ]

    assert statuses == [201, 201, 201, 201, 201, 429]


def test_invalid_case_does_not_consume_live_rate_limit() -> None:
    with TestClient(
        create_app(settings(live=True), model_client_factory=live_factory)
    ) as client:
        for _ in range(5):
            response = client.post(
                "/api/sessions", json={"case_id": "missing_case"}
            )
            assert response.status_code == 404

        valid = client.post(
            "/api/sessions", json={"case_id": "silent_lifeboat"}
        )

    assert valid.status_code == 201


def test_session_registry_expires_after_one_hour() -> None:
    now = [100.0]
    registry = SessionRegistry(ttl_seconds=3600, clock=lambda: now[0])
    session = SimpleNamespace(id="session-1")
    registry.add(session)  # type: ignore[arg-type]

    now[0] += 3600.01

    try:
        registry.get("session-1")
    except KeyError:
        pass
    else:
        raise AssertionError("expired session should be removed")


def test_cors_allows_only_configured_frontend_origin() -> None:
    app = create_app(settings(live=False))
    with TestClient(app) as client:
        allowed = client.options(
            "/api/health",
            headers={
                "Origin": "https://memory-court.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        denied = client.options(
            "/api/health",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert allowed.headers["access-control-allow-origin"] == (
        "https://memory-court.vercel.app"
    )
    assert "access-control-allow-origin" not in denied.headers
