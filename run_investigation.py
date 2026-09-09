from __future__ import annotations

import logging

from app.graph.multi_agent_graph import run_investigation


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


if __name__ == "__main__":
    question = (
        "Investigate why checkout conversion dropped on 2026-09-06."
    )

    result = run_investigation(question)

    print("\n========================================")
    print("FINAL RESULT")
    print("========================================")

    print("\nOBJECTIVE:")
    print(result["objective"])

    print("\nPLAN:")
    for number, step in enumerate(result["plan_steps"], start=1):
        print(f"{number}. {step}")

    print("\nMETRICS EVIDENCE:")
    print(result["metrics_evidence"])

    print("\nINCIDENT EVIDENCE:")
    print(result["incident_evidence"])

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

    print("\nARTIFACT:")
    print(result["artifact_path"])
