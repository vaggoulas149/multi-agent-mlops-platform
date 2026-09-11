"""LangGraph orchestration for the multi-agent incident investigation workflow.

This module defines the shared workflow state, LangGraph nodes, conditional
routing rules, graph topology, initial state construction, and the public
entry point used to execute an investigation.

The workflow follows this high-level structure:

    Planner
        ↓
    Data Agent
        ↓
    Research Agent
        ↓
    Producer
        ↓
    Judge
      ↙   ↘
   FAIL   PASS
     ↓      ↓
 Producer  Synthesizer
     ↑      ↓
 feedback  Output Guardrails
              ↓
           Persist
              ↓
             END

Judge failures can route execution back to the Producer. This retry loop is
bounded by MAX_RETRIES to prevent unbounded execution.
"""

from __future__ import annotations

import logging
from typing import Literal, cast

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.agents.data_agent import collect_metrics
from app.agents.judge_agent import judge_candidate
from app.agents.planner_agent import create_plan
from app.agents.producer_agent import produce_candidate
from app.agents.research_agent import collect_incident_evidence
from app.agents.synthesizer_agent import synthesize_final_answer
from app.config import MAX_RETRIES
from app.guardrails.output_guardrails import validate_final_output
from app.persistence.result_store import save_investigation

logger = logging.getLogger(__name__)

JudgeRoute = Literal[
    "producer",
    "synthesizer",
    "failed",
]

GuardrailRoute = Literal[
    "persist",
    "failed",
]

StateUpdate = dict[str, object]


class MultiAgentState(TypedDict):
    """Shared state carried through the LangGraph investigation workflow.

    Attributes:
        question: Original user investigation question.
        objective: Investigation objective produced by the Planner.
        plan_steps: Ordered investigation steps produced by the Planner.
        metrics_evidence: Evidence retrieved by the Data Agent.
        incident_evidence: Evidence retrieved by the Research Agent.
        draft_answer: Current candidate answer produced by the Producer.
        judge_status: Latest Judge status, typically PASS or FAIL.
        judge_feedback: Latest feedback returned by the Judge.
        retry_count: Number of Judge failures observed so far.
        max_retries: Maximum number of Producer retries allowed.
        final_answer: Final user-facing answer or failure response.
        guardrail_status: Result of deterministic final-output validation.
        guardrail_feedback: Feedback returned by output guardrails.
        artifact_path: Path to the persisted investigation artifact.
    """

    question: str

    objective: str
    plan_steps: list[str]

    metrics_evidence: str
    incident_evidence: str

    draft_answer: str

    judge_status: str
    judge_feedback: str

    retry_count: int
    max_retries: int

    final_answer: str

    guardrail_status: str
    guardrail_feedback: str

    artifact_path: str


def planner_node(state: MultiAgentState) -> StateUpdate:
    """Create the investigation objective and execution plan.

    Args:
        state: Current workflow state containing the user question.

    Returns:
        State updates containing the investigation objective and plan steps.
    """
    logger.info("Running Planner Agent")

    plan = create_plan(state["question"])

    return {
        "objective": plan.objective,
        "plan_steps": plan.steps,
    }


def data_agent_node(state: MultiAgentState) -> StateUpdate:
    """Collect checkout metrics evidence for the investigation.

    Args:
        state: Current workflow state containing the question and plan.

    Returns:
        State update containing metrics evidence.
    """
    logger.info("Running Data Agent")

    evidence = collect_metrics(
        question=state["question"],
        objective=state["objective"],
        plan_steps=state["plan_steps"],
    )

    return {
        "metrics_evidence": evidence,
    }


def research_agent_node(state: MultiAgentState) -> StateUpdate:
    """Collect historical incident evidence relevant to the investigation.

    Args:
        state: Current workflow state including metrics already collected.

    Returns:
        State update containing incident evidence.
    """
    logger.info("Running Research Agent")

    evidence = collect_incident_evidence(
        question=state["question"],
        objective=state["objective"],
        plan_steps=state["plan_steps"],
        metrics_evidence=state["metrics_evidence"],
    )

    return {
        "incident_evidence": evidence,
    }


def producer_node(state: MultiAgentState) -> StateUpdate:
    """Generate or revise the candidate investigation answer.

    On the first attempt, the Producer receives the collected evidence.
    On retry attempts, it also receives the previous draft and Judge
    feedback so that it can make a targeted revision.

    Args:
        state: Current workflow state and accumulated investigation evidence.

    Returns:
        State update containing the latest candidate answer.
    """
    logger.info(
        "Running Producer Agent (retry_count=%s)",
        state["retry_count"],
    )

    draft = produce_candidate(
        question=state["question"],
        metrics_evidence=state["metrics_evidence"],
        incident_evidence=state["incident_evidence"],
        previous_draft=state["draft_answer"],
        judge_feedback=state["judge_feedback"],
    )

    return {
        "draft_answer": draft,
    }


def judge_node(state: MultiAgentState) -> StateUpdate:
    """Evaluate the current candidate answer against collected evidence.

    A Judge failure increments the retry counter. Judge feedback is stored
    in shared state so that the Producer can use it during a retry.

    Args:
        state: Current workflow state containing evidence and candidate answer.

    Returns:
        State updates containing Judge status, feedback, and retry count.
    """
    logger.info("Running Judge Agent")

    result = judge_candidate(
        question=state["question"],
        metrics_evidence=state["metrics_evidence"],
        incident_evidence=state["incident_evidence"],
        draft_answer=state["draft_answer"],
    )

    retry_count = state["retry_count"]

    if result.status == "FAIL":
        retry_count += 1

    return {
        "judge_status": result.status,
        "judge_feedback": result.feedback,
        "retry_count": retry_count,
    }


def route_after_judge(state: MultiAgentState) -> JudgeRoute:
    """Select the next workflow node after Judge evaluation.

    A passing candidate continues to synthesis. A failing candidate returns
    to the Producer while retries remain. Once the retry budget has been
    exhausted, execution moves to the failed branch.

    Args:
        state: Current workflow state after Judge evaluation.

    Returns:
        Name of the next LangGraph node.
    """
    if state["judge_status"] == "PASS":
        return "synthesizer"

    if state["retry_count"] <= state["max_retries"]:
        return "producer"

    return "failed"


def synthesizer_node(state: MultiAgentState) -> StateUpdate:
    """Convert a Judge-approved draft into the final user-facing response.

    Args:
        state: Current workflow state containing the validated draft.

    Returns:
        State update containing the synthesized final answer.
    """
    logger.info("Running Synthesizer Agent")

    final_answer = synthesize_final_answer(
        question=state["question"],
        validated_draft=state["draft_answer"],
        metrics_evidence=state["metrics_evidence"],
        incident_evidence=state["incident_evidence"],
    )

    return {
        "final_answer": final_answer,
    }


def output_guardrail_node(state: MultiAgentState) -> StateUpdate:
    """Apply deterministic validation to the synthesized final answer.

    Args:
        state: Current workflow state containing the final answer.

    Returns:
        State updates containing guardrail status and feedback.
    """
    logger.info("Running Output Guardrails")

    status, feedback = validate_final_output(
        judge_status=state["judge_status"],
        final_answer=state["final_answer"],
    )

    return {
        "guardrail_status": status,
        "guardrail_feedback": feedback,
    }


def route_after_guardrails(
        state: MultiAgentState,
) -> GuardrailRoute:
    """Route execution according to deterministic output validation.

    Args:
        state: Current workflow state after output guardrails have run.

    Returns:
        ``persist`` when validation passes, otherwise ``failed``.
    """
    if state["guardrail_status"] == "PASS":
        return "persist"

    return "failed"


def failed_node(state: MultiAgentState) -> StateUpdate:
    """Create a controlled failure response when validation cannot succeed.

    This node is reached when the Judge exhausts the retry budget or when
    final output guardrails reject the synthesized answer.

    Args:
        state: Current workflow state at the point of failure.

    Returns:
        State update containing a safe failure response.
    """
    logger.warning("Workflow failed validation")

    answer = (
        "The investigation could not produce a sufficiently validated "
        "answer after the allowed retries. "
        f"Last reviewer feedback: {state['judge_feedback']}"
    )

    return {
        "final_answer": answer,
    }


def persist_node(state: MultiAgentState) -> StateUpdate:
    """Persist the completed investigation as a local artifact.

    Persistence runs for both successful and failed workflow executions so
    that the final workflow state remains inspectable.

    Args:
        state: Final workflow state to persist.

    Returns:
        State update containing the saved artifact path.
    """
    logger.info("Persisting investigation")

    artifact_path = save_investigation(
        {
            "question": state["question"],
            "objective": state["objective"],
            "plan_steps": state["plan_steps"],
            "metrics_evidence": state["metrics_evidence"],
            "incident_evidence": state["incident_evidence"],
            "draft_answer": state["draft_answer"],
            "judge_status": state["judge_status"],
            "judge_feedback": state["judge_feedback"],
            "retry_count": state["retry_count"],
            "max_retries": state["max_retries"],
            "final_answer": state["final_answer"],
            "guardrail_status": state["guardrail_status"],
            "guardrail_feedback": state["guardrail_feedback"],
        }
    )

    return {
        "artifact_path": artifact_path,
    }


graph_builder = StateGraph(MultiAgentState)

graph_builder.add_node("planner", planner_node)
graph_builder.add_node("data_agent", data_agent_node)
graph_builder.add_node("research_agent", research_agent_node)
graph_builder.add_node("producer", producer_node)
graph_builder.add_node("judge", judge_node)
graph_builder.add_node("synthesizer", synthesizer_node)
graph_builder.add_node(
    "output_guardrails",
    output_guardrail_node,
)
graph_builder.add_node("failed", failed_node)
graph_builder.add_node("persist", persist_node)

graph_builder.add_edge(START, "planner")
graph_builder.add_edge("planner", "data_agent")
graph_builder.add_edge("data_agent", "research_agent")
graph_builder.add_edge("research_agent", "producer")
graph_builder.add_edge("producer", "judge")

graph_builder.add_conditional_edges(
    "judge",
    route_after_judge,
    {
        "producer": "producer",
        "synthesizer": "synthesizer",
        "failed": "failed",
    },
)

graph_builder.add_edge(
    "synthesizer",
    "output_guardrails",
)

graph_builder.add_conditional_edges(
    "output_guardrails",
    route_after_guardrails,
    {
        "persist": "persist",
        "failed": "failed",
    },
)

graph_builder.add_edge("failed", "persist")
graph_builder.add_edge("persist", END)

graph = graph_builder.compile()


def build_initial_state(
        question: str,
) -> MultiAgentState:
    """Create the initial shared state for a new investigation.

    All workflow-managed fields are initialized explicitly so every node can
    rely on a consistent state shape.

    Args:
        question: Original incident investigation question.

    Returns:
        Fully initialized MultiAgentState ready for graph execution.
    """
    return {
        "question": question,
        "objective": "",
        "plan_steps": [],
        "metrics_evidence": "",
        "incident_evidence": "",
        "draft_answer": "",
        "judge_status": "",
        "judge_feedback": "",
        "retry_count": 0,
        "max_retries": MAX_RETRIES,
        "final_answer": "",
        "guardrail_status": "",
        "guardrail_feedback": "",
        "artifact_path": "",
    }


def run_investigation(
        question: str,
) -> MultiAgentState:
    """Execute the complete multi-agent investigation workflow.

    LangSmith-compatible run metadata is attached through the LangGraph
    invocation config. When LangSmith tracing is enabled through environment
    configuration, the resulting execution can be inspected as a trace.

    Args:
        question: Natural-language incident investigation question.

    Returns:
        Final workflow state after execution, validation, and persistence.
    """
    initial_state = build_initial_state(question)

    result = graph.invoke(
        initial_state,
        config={
            "run_name": "incident-investigation",
            "tags": [
                "agentic-ai",
                "langgraph",
                "multi-agent",
                "incident-investigation",
            ],
            "metadata": {
                "application": "multi-agent-mlops-platform",
                "workflow_version": "1.0",
                "environment": "local",
            },
        },
    )

    return cast(MultiAgentState, result)
