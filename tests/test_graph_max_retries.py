import app.graph.multi_agent_graph as graph_module

from app.agents.judge_agent import JudgeResult


def test_max_retries_goes_to_failed_branch(monkeypatch):

    class FakePlan:
        objective = "Find the cause"
        steps = [
            "Get metrics",
            "Search incidents",
            "Compare evidence",
        ]

    def fake_create_plan(question: str):
        return FakePlan()

    def fake_collect_metrics(
        question: str,
        objective: str,
        plan_steps: list[str],
    ):
        return "fake metrics evidence"

    def fake_collect_incident_evidence(
        question: str,
        objective: str,
        plan_steps: list[str],
        metrics_evidence: str,
    ):
        return "fake incident evidence"

    def fake_produce_candidate(
        question: str,
        metrics_evidence: str,
        incident_evidence: str,
        previous_draft: str = "",
        judge_feedback: str = "",
    ):
        return "Candidate answer"

    judge_calls = {"count": 0}

    def always_fail_judge(
        question: str,
        metrics_evidence: str,
        incident_evidence: str,
        draft_answer: str,
    ):
        judge_calls["count"] += 1

        return JudgeResult(
            status="FAIL",
            feedback="Still not sufficiently grounded.",
        )

    def fake_save_investigation(record: dict):
        return "fake/failed-artifact.json"

    monkeypatch.setattr(
        graph_module,
        "create_plan",
        fake_create_plan,
    )

    monkeypatch.setattr(
        graph_module,
        "collect_metrics",
        fake_collect_metrics,
    )

    monkeypatch.setattr(
        graph_module,
        "collect_incident_evidence",
        fake_collect_incident_evidence,
    )

    monkeypatch.setattr(
        graph_module,
        "produce_candidate",
        fake_produce_candidate,
    )

    monkeypatch.setattr(
        graph_module,
        "judge_candidate",
        always_fail_judge,
    )

    monkeypatch.setattr(
        graph_module,
        "save_investigation",
        fake_save_investigation,
    )

    result = graph_module.run_investigation(
        "Investigate checkout conversion drop."
    )

    assert result["judge_status"] == "FAIL"

    assert result["retry_count"] == 3

    assert judge_calls["count"] == 3

    assert "could not produce" in (
        result["final_answer"].lower()
    )

    assert result["artifact_path"] == (
        "fake/failed-artifact.json"
    )