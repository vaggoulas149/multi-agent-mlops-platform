"""Tests for the LangGraph Producer/Judge retry flow.

This module verifies that a Judge failure routes execution back to the
Producer, that Judge feedback is passed into the retry attempt, and that the
workflow continues successfully once the revised candidate passes review.

All LLM-dependent components are mocked so the test is deterministic and does
not make external API calls.
"""

from typing import Any, Mapping

from pytest import MonkeyPatch

import app.graph.multi_agent_graph as graph_module
from app.agents.judge_agent import JudgeResult


def test_retry_flow(
        monkeypatch: MonkeyPatch,
) -> None:
    """Retry the Producer after Judge failure and complete on subsequent PASS."""

    class FakePlan:
        """Deterministic Planner result used by the mocked workflow."""

        objective: str = "Find the cause"
        steps: list[str] = [
            "Get metrics",
            "Search incidents",
            "Compare evidence",
        ]

    def fake_create_plan(
            question: str,
    ) -> FakePlan:
        """Return a deterministic investigation plan."""
        return FakePlan()

    def fake_collect_metrics(
            question: str,
            objective: str,
            plan_steps: list[str],
    ) -> str:
        """Return deterministic metrics evidence."""
        return (
            "conversion_rate=2.1%, "
            "previous_day_conversion_rate=3.0%, "
            "payment_error_rate=8.4%"
        )

    def fake_collect_incident_evidence(
            question: str,
            objective: str,
            plan_steps: list[str],
            metrics_evidence: str,
    ) -> str:
        """Return deterministic incident evidence."""
        return (
            "Incident INC-991: payment deployment "
            "caused elevated payment failures."
        )

    producer_calls: list[dict[str, str]] = []

    def fake_produce_candidate(
            question: str,
            metrics_evidence: str,
            incident_evidence: str,
            previous_draft: str = "",
            judge_feedback: str = "",
    ) -> str:
        """Record Producer inputs and return deterministic draft versions."""
        producer_calls.append(
            {
                "previous_draft": previous_draft,
                "judge_feedback": judge_feedback,
            }
        )

        if not judge_feedback:
            return "Draft version 1"

        return "Draft version 2 corrected from judge feedback"

    judge_calls: dict[str, int] = {
        "count": 0,
    }

    def fake_judge_candidate(
            question: str,
            metrics_evidence: str,
            incident_evidence: str,
            draft_answer: str,
    ) -> JudgeResult:
        """Fail the first candidate and approve the second."""
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

    def fake_synthesize_final_answer(
            question: str,
            validated_draft: str,
            metrics_evidence: str,
            incident_evidence: str,
    ) -> str:
        """Return a deterministic final answer."""
        return "Final validated answer."

    def fake_save_investigation(
            record: Mapping[str, Any],
    ) -> str:
        """Return a deterministic artifact path without writing to disk."""
        return "fake/artifact.json"

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

    result = graph_module.run_investigation(
        "Investigate checkout conversion drop."
    )

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
