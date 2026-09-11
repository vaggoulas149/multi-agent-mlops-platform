"""API tests for the FastAPI incident investigation interface.

These tests verify the health endpoint, successful investigation responses,
and request validation. The investigation workflow is mocked where needed so
the API layer can be tested without making real LLM calls.
"""

from pytest import MonkeyPatch
from fastapi.testclient import TestClient

import app.api.main as api_module

client = TestClient(api_module.app)


def test_health() -> None:
    """Return HTTP 200 and an OK status from the health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_investigate_success(
        monkeypatch: MonkeyPatch,
) -> None:
    """Return a successful investigation response using a mocked workflow."""
    fake_result: dict[str, object] = {
        "question": "Why did conversion drop?",
        "objective": "Determine the likely cause.",
        "final_answer": (
            "Payment failures likely contributed "
            "to the conversion drop."
        ),
        "judge_status": "PASS",
        "retry_count": 1,
        "guardrail_status": "PASS",
        "artifact_path": "fake/path/result.json",
    }

    def fake_run_investigation(
            question: str,
    ) -> dict[str, object]:
        """Return deterministic workflow output for the API test."""
        return fake_result

    monkeypatch.setattr(
        api_module,
        "run_investigation",
        fake_run_investigation,
    )

    response = client.post(
        "/investigate",
        json={
            "question": "Why did conversion drop?",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["judge_status"] == "PASS"
    assert body["retries"] == 1
    assert body["guardrail_status"] == "PASS"
    assert body["final_answer"] == (
        "Payment failures likely contributed "
        "to the conversion drop."
    )


def test_investigate_rejects_short_question() -> None:
    """Reject an investigation question that violates minimum length."""
    response = client.post(
        "/investigate",
        json={
            "question": "Hi",
        },
    )

    assert response.status_code == 422
