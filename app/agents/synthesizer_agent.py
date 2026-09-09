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
