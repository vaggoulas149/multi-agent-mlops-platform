"""Producer Agent for generating evidence-grounded candidate answers.

The Producer combines the available investigation evidence into a candidate
response for Judge review. If a previous attempt was rejected, the Producer
also receives the previous draft and the Judge's feedback so that it can
revise the answer accordingly.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT

producer_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)


def produce_candidate(
        question: str,
        metrics_evidence: str,
        incident_evidence: str,
        previous_draft: str = "",
        judge_feedback: str = "",
) -> str:
    """Generate or revise a candidate investigation answer.

    The Producer is constrained to the supplied evidence and must avoid
    hallucinated facts or unsupported causal claims. When Judge feedback is
    available, the Producer uses it to improve the previous draft.

    Args:
        question: Original incident investigation question.
        metrics_evidence: Evidence collected by the Data Agent.
        incident_evidence: Evidence collected by the Research Agent.
        previous_draft: Candidate answer from the previous Producer attempt,
            if one exists.
        judge_feedback: Actionable feedback returned by the Judge after a
            failed evaluation.

    Returns:
        A candidate investigation answer for Judge evaluation.
    """
    prompt = f"""
You are the Producer Agent.

Create an evidence-grounded candidate answer to the user's question.

USER QUESTION:
{question}

METRICS EVIDENCE:
{metrics_evidence}

INCIDENT EVIDENCE:
{incident_evidence}

PREVIOUS DRAFT:
{previous_draft or "(none)"}

JUDGE FEEDBACK:
{judge_feedback or "(none)"}

RULES:
- Use only the supplied evidence.
- Do not invent facts.
- Do not overstate causality.
- Distinguish observed facts from plausible conclusions.
- Address the user's question directly.
- If Judge feedback exists, improve the previous draft specifically
  according to that feedback.
- This is a candidate answer for review, not the final response.
"""

    response = producer_llm.invoke(prompt)

    return str(response.content)
