from __future__ import annotations

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT
from app.tools.incident_tools import get_checkout_metrics


data_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)

data_llm_with_tools = data_llm.bind_tools([get_checkout_metrics])


def collect_metrics(
    question: str,
    objective: str,
    plan_steps: list[str],
) -> str:
    prompt = HumanMessage(
        content=f"""
You are the Data Agent in an incident investigation.

USER QUESTION:
{question}

OBJECTIVE:
{objective}

INVESTIGATION PLAN:
{plan_steps}

Use the available metrics tool to retrieve the metrics needed
for this investigation.

RULES:
- Do not invent metrics.
- Use the tool when metrics are required.
- Return only evidence grounded in the tool result.
"""
    )

    response = data_llm_with_tools.invoke([prompt])

    if not response.tool_calls:
        return "No metrics were retrieved."

    messages = [prompt, response]
    results: list[str] = []

    for tool_call in response.tool_calls:
        if tool_call["name"] != get_checkout_metrics.name:
            continue

        tool_result = get_checkout_metrics.invoke(tool_call["args"])
        results.append(str(tool_result))

        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    if not results:
        return "No metrics were retrieved."

    return "\n".join(results)
