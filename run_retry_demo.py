"""Demonstration of the LangGraph Judge retry path!

This module intentionally forces the first Judge evaluation to fail so the
Producer/Judge feedback loop can be observed during a real workflow run.

After the first forced failure, subsequent Judge evaluations use the real
LLM-based Judge implementation.

The script demonstrates:

    Producer
        ↓
    Judge FAIL
        ↓
    feedback
        ↓
    Producer retry
        ↓
    Judge PASS
        ↓
    Synthesizer
        ↓
    Guardrails

This file is intended for demonstration purposes only and is not part of the
normal application execution path.
"""

from __future__ import annotations

import logging

import app.graph.multi_agent_graph as graph_module

from app.agents.judge_agent import (
    JudgeResult,
    judge_candidate as real_judge_candidate,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


judge_call_count: int = 0


def demo_judge_candidate(
    question: str,
    metrics_evidence: str,
    incident_evidence: str,
    draft_answer: str,
) -> JudgeResult:
    """Force the first Judge evaluation to fail for retry demonstration.

    The first invocation returns a deterministic FAIL result with actionable
    feedback. Any later invocation delegates to the real LLM-based Judge so
    the revised Producer answer can be evaluated normally.

    Args:
        question: Original incident investigation question.
        metrics_evidence: Metrics evidence collected by the Data Agent.
        incident_evidence: Incident evidence collected by the Research Agent.
        draft_answer: Current candidate answer produced by the Producer.

    Returns:
        A JudgeResult containing either the forced first failure or the result
        returned by the real Judge implementation.
    """
    global judge_call_count

    judge_call_count += 1

    print(f"\nDEMO JUDGE CALL #{judge_call_count}")

    if judge_call_count == 1:
        return JudgeResult(
            status="FAIL",
            feedback=(
                "Demo failure: make the answer more explicit "
                "about uncertainty and avoid implying proven causality."
            ),
        )

    return real_judge_candidate(
        question=question,
        metrics_evidence=metrics_evidence,
        incident_evidence=incident_evidence,
        draft_answer=draft_answer,
    )


def main() -> None:
    """Run the retry demonstration and print the final workflow result."""
    graph_module.judge_candidate = demo_judge_candidate

    question = (
        "Investigate why checkout conversion "
        "dropped on 2026-09-06."
    )

    result = graph_module.run_investigation(question)

    print("\n========================================")
    print("RETRY DEMO RESULT")
    print("========================================")

    print("\nJUDGE STATUS:")
    print(result["judge_status"])

    print("\nJUDGE FEEDBACK:")
    print(result["judge_feedback"])

    print("\nRETRIES:")
    print(result["retry_count"])

    print("\nFINAL ANSWER:")
    print(result["final_answer"])

    print("\nGUARDRAIL STATUS:")
    print(result["guardrail_status"])


if __name__ == "__main__":
    main()