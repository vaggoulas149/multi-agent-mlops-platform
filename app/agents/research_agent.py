"""Research Agent responsible for retrieving historical incident evidence.

The agent uses an LLM with access to the incident-search tool. Its role is
strictly evidence retrieval: it searches for relevant production incidents
and returns only evidence grounded in the supported tool result.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT
from app.tools.incident_tools import search_incidents

research_llm: ChatOpenAI = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)

research_llm_with_tools = research_llm.bind_tools(
    [search_incidents]
)


def collect_incident_evidence(
        question: str,
        objective: str,
        plan_steps: list[str],
        metrics_evidence: str,
) -> str:
    """Collect historical incident evidence relevant to an investigation.

    The Research Agent receives the original question, the Planner's
    objective and investigation steps, and the metrics already collected by
    the Data Agent. The LLM can then select the incident-search tool to
    retrieve relevant operational evidence.

    Args:
        question: Original incident investigation question.
        objective: Investigation objective produced by the Planner Agent.
        plan_steps: Ordered investigation steps produced by the Planner Agent.
        metrics_evidence: Metrics evidence already collected by the Data Agent.

    Returns:
        Retrieved incident evidence as a newline-separated string. If no
        supported incident-search tool is called successfully, a fallback
        message is returned instead.
    """
    prompt = HumanMessage(
        content=f"""
You are the Research Agent in an incident investigation.

USER QUESTION:
{question}

OBJECTIVE:
{objective}

INVESTIGATION PLAN:
{plan_steps}

METRICS ALREADY COLLECTED:
{metrics_evidence}

Use the available incident-search tool to retrieve relevant
historical production incidents.

RULES:
- Do not invent incidents.
- Do not invent evidence.
- Use the tool when incident information is required.
- Return only evidence grounded in the tool result.
"""
    )

    response = research_llm_with_tools.invoke([prompt])

    if not response.tool_calls:
        return "No incident evidence was retrieved."

    results: list[str] = []

    for tool_call in response.tool_calls:
        if tool_call["name"] != search_incidents.name:
            continue

        tool_result = search_incidents.invoke(
            tool_call["args"]
        )
        results.append(str(tool_result))

    if not results:
        return "No incident evidence was retrieved."

    return "\n".join(results)
