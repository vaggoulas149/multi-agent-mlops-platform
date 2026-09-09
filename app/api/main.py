import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.graph.multi_agent_graph import run_investigation


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="AI Incident Investigator",
    description=(
        "Multi-agent incident investigation API "
        "powered by LangGraph."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# Request schema
# ---------------------------------------------------------

class InvestigationRequest(BaseModel):
    question: str = Field(
        min_length=5,
        description="The incident investigation question.",
    )


# ---------------------------------------------------------
# Response schema
# ---------------------------------------------------------

class InvestigationResponse(BaseModel):
    question: str
    objective: str

    final_answer: str

    judge_status: str
    retries: int

    guardrail_status: str

    artifact_path: str


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# Investigation endpoint
# ---------------------------------------------------------

@app.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def investigate(
    request: InvestigationRequest,
):

    try:

        result = run_investigation(
            request.question
        )

        return InvestigationResponse(
            question=result["question"],
            objective=result["objective"],
            final_answer=result["final_answer"],
            judge_status=result["judge_status"],
            retries=result["retry_count"],
            guardrail_status=result[
                "guardrail_status"
            ],
            artifact_path=result[
                "artifact_path"
            ],
        )

    except Exception:

        logger.exception(
            "Investigation workflow failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Investigation failed.",
        )