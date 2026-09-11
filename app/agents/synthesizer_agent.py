"""Synthesizer Agent for producing the final user-facing response.

The Synthesizer receives a candidate answer that has already passed the
Judge and converts it into a clear, concise final response.

It must not introduce new facts, perform new investigation steps, or alter
the validated conclusion.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT

synthesizer_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)


def synthesize_final_answer(
        question: str,
        validated_draft: str,
        metrics_evidence: str,
        incident_evidence: str,
) -> str:
    """Create the final user-facing answer from a validated draft.

    The Synthesizer receives a draft that has already passed Judge review.
    Its role is presentation-focused: preserve the validated conclusion,
    improve clarity, and communicate uncertainty appropriately without
    adding new evidence or performing additional investigation.

    Args:
        question: Original incident investigation question.
        validated_draft: Candidate answer that has passed Judge evaluation.
        metrics_evidence: Metrics evidence collected by the Data Agent.
        incident_evidence: Incident evidence collected by the Research Agent.

    Returns:
        A concise, professional final answer grounded only in the supplied
        validated draft and supporting evidence.
    """
    prompt = f"""
You are the Final Response Synthesizer.

The candidate answer below has already passed the Judge.

USER QUESTION:
{question}

VALIDATED DRAFT:
{validated_draft}

METRICS EVIDENCE:
{metrics_evidence}

INCIDENT EVIDENCE:
{incident_evidence}

RULES:
- Do not introduce new facts.
- Do not perform a new investigation.
- Preserve the validated conclusion.
- Make the answer clear, concise, and professional.
- Mention uncertainty where appropriate.
- Use only the supplied evidence.
"""

    response = synthesizer_llm.invoke(prompt)

    return str(response.content)
