import app.graph.multi_agent_graph as graph_module

from app.agents.judge_agent import JudgeResult


def test_retry_flow(monkeypatch):

    # -----------------------------------------------------
    # Fake Planner
    # -----------------------------------------------------

    class FakePlan:
        objective = "Find the cause"
        steps = [
            "Get metrics",
            "Search incidents",
            "Compare evidence",
        ]

    def fake_create_plan(question: str):
        return FakePlan()


    # -----------------------------------------------------
    # Fake Data Agent
    # -----------------------------------------------------

    def fake_collect_metrics(
        question: str,
        objective: str,
        plan_steps: list[str],
    ):
        return (
            "conversion_rate=2.1%, "
            "previous_day_conversion_rate=3.0%, "
            "payment_error_rate=8.4%"
        )


    # -----------------------------------------------------
    # Fake Research Agent
    # -----------------------------------------------------

    def fake_collect_incident_evidence(
        question: str,
        objective: str,
        plan_steps: list[str],
        metrics_evidence: str,
    ):
        return (
            "Incident INC-991: payment deployment "
            "caused elevated payment failures."
        )


    # -----------------------------------------------------
    # Fake Producer
    # -----------------------------------------------------

    producer_calls = []

    def fake_produce_candidate(
        question: str,
        metrics_evidence: str,
        incident_evidence: str,
        previous_draft: str = "",
        judge_feedback: str = "",
    ):

        producer_calls.append(
            {
                "previous_draft": previous_draft,
                "judge_feedback": judge_feedback,
            }
        )

        if not judge_feedback:
            return "Draft version 1"

        return "Draft version 2 corrected from judge feedback"


    # -----------------------------------------------------
    # Fake Judge
    # -----------------------------------------------------

    judge_calls = {"count": 0}

    def fake_judge_candidate(
        question: str,
        metrics_evidence: str,
        incident_evidence: str,
        draft_answer: str,
    ):

        judge_calls["count"] += 1

        if judge_calls["count"] == 1:
            return JudgeResult(
                status="FAIL",
                feedback="Clarify uncertainty.",
            )

        return JudgeResult(
            status="PASS",
            feedback="Candidate is now acceptable.",
        )


    # -----------------------------------------------------
    # Fake Synthesizer
    # -----------------------------------------------------

    def fake_synthesize_final_answer(
        question: str,
        validated_draft: str,
        metrics_evidence: str,
        incident_evidence: str,
    ):
        return "Final validated answer."


    # -----------------------------------------------------
    # Fake Persistence
    # -----------------------------------------------------

    def fake_save_investigation(record: dict):
        return "fake/artifact.json"


    # -----------------------------------------------------
    # Monkeypatch all external/LLM-heavy components
    # -----------------------------------------------------

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
        fake_judge_candidate,
    )

    monkeypatch.setattr(
        graph_module,
        "synthesize_final_answer",
        fake_synthesize_final_answer,
    )

    monkeypatch.setattr(
        graph_module,
        "save_investigation",
        fake_save_investigation,
    )


    # -----------------------------------------------------
    # Run graph
    # -----------------------------------------------------

    result = graph_module.run_investigation(
        "Investigate checkout conversion drop."
    )


    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert result["judge_status"] == "PASS"

    assert result["retry_count"] == 1

    assert judge_calls["count"] == 2

    assert len(producer_calls) == 2

    assert producer_calls[0]["judge_feedback"] == ""

    assert producer_calls[1]["judge_feedback"] == (
        "Clarify uncertainty."
    )

    assert result["final_answer"] == (
        "Final validated answer."
    )

    assert result["guardrail_status"] == "PASS"

    assert result["artifact_path"] == (
        "fake/artifact.json"
    )