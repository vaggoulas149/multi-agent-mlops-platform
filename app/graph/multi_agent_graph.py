from __future__ import annotations

import logging

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from app.config import MAX_RETRIES
from app.agents.planner_agent import create_plan
from app.agents.data_agent import collect_metrics
from app.agents.research_agent import collect_incident_evidence
from app.agents.producer_agent import produce_candidate
from app.agents.judge_agent import judge_candidate
from app.agents.synthesizer_agent import synthesize_final_answer
from app.guardrails.output_guardrails import validate_final_output
from app.persistence.result_store import save_investigation


logger = logging.getLogger(__name__)


class MultiAgentState(TypedDict):
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


def planner_node(state: MultiAgentState):
    logger.info("Running Planner Agent")

    plan = create_plan(state["question"])

    return {
        "objective": plan.objective,
        "plan_steps": plan.steps,
    }


def data_agent_node(state: MultiAgentState):
    logger.info("Running Data Agent")

    evidence = collect_metrics(
        question=state["question"],
        objective=state["objective"],
        plan_steps=state["plan_steps"],
    )

    return {
        "metrics_evidence": evidence,
    }


def research_agent_node(state: MultiAgentState):
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


def producer_node(state: MultiAgentState):
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


def judge_node(state: MultiAgentState):
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


def route_after_judge(state: MultiAgentState):
    if state["judge_status"] == "PASS":
        return "synthesizer"

    if state["retry_count"] <= state["max_retries"]:
        return "producer"

    return "failed"


def synthesizer_node(state: MultiAgentState):
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


def output_guardrail_node(state: MultiAgentState):
    logger.info("Running Output Guardrails")

    status, feedback = validate_final_output(
        judge_status=state["judge_status"],
        final_answer=state["final_answer"],
    )

    return {
        "guardrail_status": status,
        "guardrail_feedback": feedback,
    }


def route_after_guardrails(state: MultiAgentState):
    if state["guardrail_status"] == "PASS":
        return "persist"

    return "failed"


def failed_node(state: MultiAgentState):
    logger.warning("Workflow failed validation")

    answer = (
        "The investigation could not produce a sufficiently validated "
        "answer after the allowed retries. "
        f"Last reviewer feedback: {state['judge_feedback']}"
    )

    return {
        "final_answer": answer,
    }


def persist_node(state: MultiAgentState):
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
graph_builder.add_node("output_guardrails", output_guardrail_node)
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


def build_initial_state(question: str) -> MultiAgentState:
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


def run_investigation(question: str) -> MultiAgentState:
    initial_state = build_initial_state(question)
    return graph.invoke(initial_state)
