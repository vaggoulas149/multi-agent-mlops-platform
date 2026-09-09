from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT


class InvestigationPlan(BaseModel):
    objective: str = Field(
        description="The main investigation objective."
    )
    steps: list[str] = Field(
        description="Ordered investigation steps that are executable with available capabilities."
    )


planner_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
).with_structured_output(InvestigationPlan)


def create_plan(question: str) -> InvestigationPlan:
    prompt = f"""
You are the Planner Agent for an incident investigation system.

Create a short, executable investigation plan for the user's question.

AVAILABLE CAPABILITIES:

1. get_checkout_metrics(date)
   - Retrieves checkout conversion rate
   - Retrieves payment error rate
   - Retrieves previous-day conversion rate

2. search_incidents(query)
   - Searches previous production incidents
   - Can find deployments, outages, payment failures,
     checkout incidents, and similar operational problems

RULES:
- Only create steps that the available capabilities can actually execute.
- Do not invent capabilities.
- Do not request unavailable breakdowns such as device, region,
  traffic source, or payment method.
- Do not investigate the issue yourself.
- Do not invent evidence.
- Keep the plan concise.

USER QUESTION:
{question}
"""
    return planner_llm.invoke(prompt)
