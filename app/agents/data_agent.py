"""Data Agent responsible for retrieving checkout metrics evidence.

The agent uses an LLM with access to the checkout metrics tool. Its role is
strictly evidence collection: it selects and invokes the supported metrics
tool and returns the retrieved evidence to the LangGraph workflow.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import OPENAI_MODEL, OPENAI_REASONING_EFFORT
from app.tools.incident_tools import get_checkout_metrics

data_llm: ChatOpenAI = ChatOpenAI(
    model=OPENAI_MODEL,
    reasoning_effort=OPENAI_REASONING_EFFORT,
)

data_llm_with_tools = data_llm.bind_tools(
    [get_checkout_metrics]
)


def collect_metrics(
        question: str,
        objective: str,
        plan_steps: list[str],
) -> str:
    """Collect metrics evidence required for an incident investigation.

    The Data Agent receives the original user question together with the
    Planner's objective and investigation steps. The LLM decides whether to
    call the available checkout metrics tool. Only evidence returned by the
    supported tool is included in the result.

    Args:
        question: Original incident investigation question.
        objective: Investigation objective produced by the Planner Agent.
        plan_steps: Ordered investigation steps produced by the Planner Agent.

    Returns:
        Retrieved metrics evidence as a newline-separated string. If no
        supported metrics tool is called successfully, a fallback message is
        returned instead.
    """
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

    results: list[str] = []

    for tool_call in response.tool_calls:
        if tool_call["name"] != get_checkout_metrics.name:
            continue

        tool_result = get_checkout_metrics.invoke(
            tool_call["args"]
        )
        results.append(str(tool_result))

    if not results:
        return "No metrics were retrieved."

    return "\n".join(results)
