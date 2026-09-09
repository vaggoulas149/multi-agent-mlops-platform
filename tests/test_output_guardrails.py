from app.guardrails.output_guardrails import validate_final_output


def test_guardrail_passes_valid_output():
    status, feedback = validate_final_output(
        judge_status="PASS",
        final_answer="This is a sufficiently detailed final answer.",
    )

    assert status == "PASS"
    assert "passed" in feedback.lower()


def test_guardrail_rejects_unapproved_output():
    status, _ = validate_final_output(
        judge_status="FAIL",
        final_answer="Some answer.",
    )

    assert status == "FAIL"


def test_guardrail_rejects_empty_output():
    status, _ = validate_final_output(
        judge_status="PASS",
        final_answer="",
    )

    assert status == "FAIL"
