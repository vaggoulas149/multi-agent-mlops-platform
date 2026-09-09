from __future__ import annotations


def validate_final_output(
    judge_status: str,
    final_answer: str,
) -> tuple[str, str]:
    if judge_status != "PASS":
        return (
            "FAIL",
            "Final output cannot be released without Judge approval.",
        )

    if not final_answer.strip():
        return (
            "FAIL",
            "Final answer is empty.",
        )

    if len(final_answer.strip()) < 20:
        return (
            "FAIL",
            "Final answer is unexpectedly short.",
        )

    return (
        "PASS",
        "Output passed deterministic final validation.",
    )
