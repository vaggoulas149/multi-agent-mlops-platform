"""Tests for the LangGraph maximum-retry failure path.

This module verifies that repeated Judge failures do not create an infinite
Producer/Judge loop. Once the configured retry budget is exhausted, the
workflow must route to the controlled failure branch and persist the result.

All LLM-dependent components are mocked so the test is deterministic and
does not make external API calls.
"""

from typing import Any, Mapping

from pytest import MonkeyPatch

import app.graph.multi_agent_graph as graph_module
from app.agents.judge_agent import JudgeResult


def test_max_retries_goes_to_failed_branch(
        monkeypatch: MonkeyPatch,
) -> None:
    """Route to the failed branch after exhausting all allowed retries.

    With MAX_RETRIES=2, the workflow permits one initial Producer attempt
    followed by two retries. If the Judge rejects all three candidates,
    execution must stop and continue through the controlled failure path.
    """

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
        return "fake metrics evidence"

    def fake_collect_incident_evidence(
            question: str,
            objective: str,
            plan_steps: list[str],
            metrics_evidence: str,
    ) -> str:
        """Return deterministic historical incident evidence."""
        return "fake incident evidence"

    def fake_produce_candidate(
            question: str,
            metrics_evidence: str,
            incident_evidence: str,
            previous_draft: str = "",
            judge_feedback: str = "",
    ) -> str:
        """Return a deterministic candidate answer."""
        return "Candidate answer"

    judge_calls: dict[str, int] = {
        "count": 0,
    }

    def always_fail_judge(
            question: str,
            metrics_evidence: str,
            incident_evidence: str,
            draft_answer: str,
    ) -> JudgeResult:
        """Reject every candidate and count Judge executions."""
        judge_calls["count"] += 1

        return JudgeResult(
            status="FAIL",
            feedback="Still not sufficiently grounded.",
        )

    def fake_save_investigation(
            record: Mapping[str, Any],
    ) -> str:
        """Return a deterministic artifact path without writing to disk."""
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

    assert "could not produce" in result["final_answer"].lower()

    assert result["artifact_path"] == (
        "fake/failed-artifact.json"
    )
