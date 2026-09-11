"""Tests for deterministic final-output guardrails.

These tests verify that only Judge-approved, non-empty, sufficiently detailed
answers are allowed to pass the final validation layer.
"""

from app.guardrails.output_guardrails import validate_final_output


def test_guardrail_passes_valid_output() -> None:
    """Accept a sufficiently detailed answer approved by the Judge."""
    status, feedback = validate_final_output(
        judge_status="PASS",
        final_answer="This is a sufficiently detailed final answer.",
    )

    assert status == "PASS"
    assert "passed" in feedback.lower()


def test_guardrail_rejects_unapproved_output() -> None:
    """Reject output when the Judge has not approved the candidate."""
    status, _ = validate_final_output(
        judge_status="FAIL",
        final_answer="Some answer.",
    )

    assert status == "FAIL"


def test_guardrail_rejects_empty_output() -> None:
    """Reject an empty final answer even when Judge status is PASS."""
    status, _ = validate_final_output(
        judge_status="PASS",
        final_answer="",
    )

    assert status == "FAIL"


def test_guardrail_rejects_short_output() -> None:
    """Reject a final answer that is unexpectedly short."""
    status, _ = validate_final_output(
        judge_status="PASS",
        final_answer="Too short.",
    )

    assert status == "FAIL"