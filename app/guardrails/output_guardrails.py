"""Deterministic guardrails for validating final investigation output.

These checks run after the Synthesizer and provide a final non-LLM validation
layer before the result is persisted and returned to the user.
"""

from __future__ import annotations

from typing import Literal

ValidationStatus = Literal["PASS", "FAIL"]


def validate_final_output(
        judge_status: str,
        final_answer: str,
) -> tuple[ValidationStatus, str]:
    """Validate the final synthesized answer before release.

    The guardrail requires Judge approval, a non-empty answer, and a minimum
    answer length. These checks are deterministic and do not depend on an LLM.

    Args:
        judge_status: Final status returned by the Judge Agent.
        final_answer: Synthesized user-facing answer.

    Returns:
        A tuple containing:
        - validation status: PASS or FAIL
        - human-readable validation feedback
    """
    if judge_status != "PASS":
        return (
            "FAIL",
            "Final output cannot be released without Judge approval.",
        )

    normalized_answer = final_answer.strip()

    if not normalized_answer:
        return (
            "FAIL",
            "Final answer is empty.",
        )

    if len(normalized_answer) < 20:
        return (
            "FAIL",
            "Final answer is unexpectedly short.",
        )

    return (
        "PASS",
        "Output passed deterministic final validation.",
    )
