from fastapi.testclient import TestClient

import app.api.main as api_module


client = TestClient(api_module.app)


# ---------------------------------------------------------
# 1. Health endpoint
# ---------------------------------------------------------

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


# ---------------------------------------------------------
# 2. Successful investigation
# ---------------------------------------------------------

def test_investigate_success(monkeypatch):

    fake_result = {
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

    def fake_run_investigation(question: str):
        return fake_result

    monkeypatch.setattr(
        api_module,
        "run_investigation",
        fake_run_investigation,
    )

    response = client.post(
        "/investigate",
        json={
            "question": "Why did conversion drop?"
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


# ---------------------------------------------------------
# 3. Invalid request
# ---------------------------------------------------------

def test_investigate_rejects_short_question():

    response = client.post(
        "/investigate",
        json={
            "question": "Hi"
        },
    )

    assert response.status_code == 422