"""FastAPI interface for the multi-agent incident investigation system.

This module exposes HTTP endpoints for health checking and incident
investigation. The API delegates investigation execution to the LangGraph
workflow and returns a structured response to the client.
"""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.graph.multi_agent_graph import run_investigation

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Incident Investigator",
    description=(
        "Multi-agent incident investigation API powered by LangGraph."
    ),
    version="1.0.0",
)


class InvestigationRequest(BaseModel):
    """Request payload for an incident investigation.

    Attributes:
        question: Natural-language incident investigation question supplied
            by the client.
    """

    question: str = Field(
        min_length=5,
        description="The incident investigation question.",
    )


class InvestigationResponse(BaseModel):
    """Structured response returned after an investigation completes.

    Attributes:
        question: Original investigation question.
        objective: Investigation objective created by the Planner Agent.
        final_answer: Final user-facing answer produced by the workflow.
        judge_status: Final Judge evaluation status.
        retries: Number of Producer retries triggered by Judge failures.
        guardrail_status: Result of deterministic final output validation.
        artifact_path: Local path of the persisted investigation artifact.
    """

    question: str
    objective: str
    final_answer: str
    judge_status: str
    retries: int
    guardrail_status: str
    artifact_path: str


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a lightweight API health check.

    Returns:
        A status payload indicating that the API process is running.
    """
    return {"status": "ok"}


@app.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def investigate(
        request: InvestigationRequest,
) -> InvestigationResponse:
    """Run the multi-agent investigation workflow for a user question.

    The endpoint delegates execution to the LangGraph workflow and converts
    the resulting workflow state into the public API response schema.

    Args:
        request: Validated investigation request supplied by the client.

    Returns:
        A structured InvestigationResponse containing the final answer and
        relevant workflow metadata.

    Raises:
        HTTPException: If the investigation workflow fails unexpectedly.
    """
    try:
        result = run_investigation(request.question)

        return InvestigationResponse(
            question=result["question"],
            objective=result["objective"],
            final_answer=result["final_answer"],
            judge_status=result["judge_status"],
            retries=result["retry_count"],
            guardrail_status=result["guardrail_status"],
            artifact_path=result["artifact_path"],
        )

    except Exception as exc:
        logger.exception("Investigation workflow failed")

        raise HTTPException(
            status_code=500,
            detail="Investigation failed.",
        ) from exc
