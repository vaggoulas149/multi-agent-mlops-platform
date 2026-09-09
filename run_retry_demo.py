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


# ---------------------------------------------------------
# Force the Judge to FAIL only the first time
# ---------------------------------------------------------

judge_call_count = 0


def demo_judge_candidate(
    question: str,
    metrics_evidence: str,
    incident_evidence: str,
    draft_answer: str,
) -> JudgeResult:

    global judge_call_count

    judge_call_count += 1

    print(
        f"\nDEMO JUDGE CALL #{judge_call_count}"
    )

    # First Judge call -> force FAIL
    if judge_call_count == 1:

        return JudgeResult(
            status="FAIL",
            feedback=(
                "Demo failure: make the answer more explicit "
                "about uncertainty and avoid implying proven causality."
            ),
        )

    # Second Judge call -> use the real LLM Judge
    return real_judge_candidate(
        question=question,
        metrics_evidence=metrics_evidence,
        incident_evidence=incident_evidence,
        draft_answer=draft_answer,
    )


# Replace Judge only for this demo process
graph_module.judge_candidate = demo_judge_candidate


# ---------------------------------------------------------
# Run investigation
# ---------------------------------------------------------

question = (
    "Investigate why checkout conversion "
    "dropped on 2026-09-06."
)

result = graph_module.run_investigation(
    question
)


# ---------------------------------------------------------
# Show result
# ---------------------------------------------------------

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