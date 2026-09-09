from __future__ import annotations

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT
from app.tools.incident_tools import search_incidents


research_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)

research_llm_with_tools = research_llm.bind_tools([search_incidents])


def collect_incident_evidence(
    question: str,
    objective: str,
    plan_steps: list[str],
    metrics_evidence: str,
) -> str:
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

    messages = [prompt, response]
    results: list[str] = []

    for tool_call in response.tool_calls:
        if tool_call["name"] != search_incidents.name:
            continue

        tool_result = search_incidents.invoke(tool_call["args"])
        results.append(str(tool_result))

        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    if not results:
        return "No incident evidence was retrieved."

    return "\n".join(results)
