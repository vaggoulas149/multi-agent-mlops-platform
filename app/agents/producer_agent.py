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
