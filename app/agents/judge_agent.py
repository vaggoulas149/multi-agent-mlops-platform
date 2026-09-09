from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT


class JudgeResult(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        description="PASS if the candidate is grounded and acceptable; otherwise FAIL."
    )
    feedback: str = Field(
        description="Specific review feedback. On FAIL, explain exactly what must be corrected."
    )


judge_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
).with_structured_output(JudgeResult)


def judge_candidate(
    question: str,
    metrics_evidence: str,
    incident_evidence: str,
    draft_answer: str,
) -> JudgeResult:
    prompt = f"""
You are the Judge Agent.

Evaluate the candidate answer against the supplied evidence.

USER QUESTION:
{question}

METRICS EVIDENCE:
{metrics_evidence}

INCIDENT EVIDENCE:
{incident_evidence}

CANDIDATE ANSWER:
{draft_answer}

CHECK:
1. Does it answer the user's question?
2. Are factual claims supported by the supplied evidence?
3. Does it invent information?
4. Does it overstate causality?
5. Does it omit important evidence or limitations?
6. Is it internally consistent?

RULES:
- Return PASS only if the answer is sufficiently grounded.
- On FAIL, give precise feedback so the Producer can correct the draft.
- Do not rewrite the answer yourself.
"""

    return judge_llm.invoke(prompt)
