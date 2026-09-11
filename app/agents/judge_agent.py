"""Judge Agent responsible for validating candidate investigation answers.

The Judge acts as a quality gate in the multi-agent workflow. It evaluates
the Producer's candidate answer against the retrieved evidence and returns
either PASS or FAIL together with actionable feedback.

A FAIL result can trigger another Producer attempt through LangGraph's
conditional routing.
"""

from __future__ import annotations

from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT


class JudgeResult(BaseModel):
    """Structured result returned by the Judge Agent.

    Attributes:
        status: PASS when the candidate answer is sufficiently grounded and
            acceptable, otherwise FAIL.
        feedback: Review feedback explaining the evaluation. When the status
            is FAIL, this should describe what the Producer must correct.
    """

    status: Literal["PASS", "FAIL"] = Field(
        description=(
            "PASS if the candidate is grounded and acceptable; "
            "otherwise FAIL."
        )
    )
    feedback: str = Field(
        description=(
            "Specific review feedback. On FAIL, explain exactly "
            "what must be corrected."
        )
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
    """Evaluate a candidate investigation answer against available evidence.

    The Judge reviews the Producer's draft for relevance, grounding,
    hallucinations, unsupported causal claims, missing limitations, and
    internal consistency.

    The Judge does not rewrite the candidate answer. If the answer is
    unacceptable, it returns actionable feedback that can be passed back
    to the Producer for another attempt.

    Args:
        question: Original incident investigation question.
        metrics_evidence: Metrics evidence collected by the Data Agent.
        incident_evidence: Incident evidence collected by the Research Agent.
        draft_answer: Candidate answer produced by the Producer Agent.

    Returns:
        A structured JudgeResult containing a PASS or FAIL status and
        corresponding review feedback.
    """
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
