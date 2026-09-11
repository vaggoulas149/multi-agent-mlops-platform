# Multi-Agent MLOps Platform

A small, educational **multi-agent AI incident investigation system** built with **LangChain**, **LangGraph**, **LangSmith**, **FastAPI**, and **pytest**.

> This repository is intentionally a **toy / learning project**.  
> Its purpose is to demonstrate the main building blocks of a multi-agent AI system in a codebase that is small enough to understand end to end.

---

## What does this project do?

The application investigates a simple operational question such as:

```text
Why did checkout conversion drop on 2026-09-06?
```

Instead of sending the question to a single LLM and immediately returning an answer, the application uses multiple specialized components:

```text
USER QUERY
    ↓
PLANNER
    ↓
DATA AGENT
    ↓
RESEARCH AGENT
    ↓
PRODUCER
    ↓
JUDGE
   /   \
 FAIL   PASS
  ↓       ↓
PRODUCER  SYNTHESIZER
  ↑       ↓
feedback  OUTPUT GUARDRAILS
              ↓
           PERSIST
              ↓
         FINAL RESULT
```

The system:

1. creates an investigation plan,
2. retrieves metric evidence,
3. retrieves incident evidence,
4. produces a candidate explanation,
5. reviews that explanation with a Judge,
6. retries the Producer if the Judge rejects the answer,
7. synthesizes the final response,
8. runs deterministic output checks,
9. stores the investigation locally,
10. returns the result through Python or FastAPI.

The Producer/Judge loop is bounded by `MAX_RETRIES`, so the graph cannot retry forever.

---

# Why this project exists

Many introductory LLM applications follow a simple pattern:

```text
User → LLM → Answer
```

This project explores a more structured **agentic AI workflow**:

```text
plan
→ collect evidence
→ reason
→ review
→ retry if necessary
→ synthesize
→ validate
→ return
```

The business example is intentionally simple. The main goal is to make the architecture easy to inspect and understand.

This project demonstrates:

- LangChain model and tool integration
- LangGraph stateful orchestration
- specialized agents
- shared workflow state
- tool calling
- conditional routing
- Producer / Judge review pattern
- Judge feedback
- bounded retries
- deterministic guardrails
- local persistence
- FastAPI
- Pydantic validation
- pytest
- mocking with `monkeypatch`
- retry-path testing
- LangSmith tracing and debugging

---

# Main components

## Planner Agent

Creates an executable investigation plan.

Example:

```text
Objective:
Determine the likely cause of the checkout conversion drop.

Steps:
1. Retrieve checkout metrics.
2. Search previous incidents.
3. Compare the evidence.
```

The Planner is capability-aware: it should only plan work that the available tools can actually perform.

File:

```text
app/agents/planner_agent.py
```

---

## Data Agent

Retrieves checkout metric evidence.

Example:

```text
conversion_rate=2.1%
payment_error_rate=8.4%
previous_day_conversion_rate=3.0%
```

File:

```text
app/agents/data_agent.py
```

---

## Research Agent

Retrieves previous incident evidence.

Example:

```text
Incident INC-991:
payment service deployment v2.4.1 caused elevated payment failures
and reduced checkout conversion.
```

File:

```text
app/agents/research_agent.py
```

---

## Producer Agent

Combines the available evidence and creates a candidate answer.

The Producer is instructed to:

- use only the supplied evidence,
- avoid inventing facts,
- avoid overstating causality,
- distinguish facts from plausible conclusions,
- use Judge feedback when retrying.

File:

```text
app/agents/producer_agent.py
```

---

## Judge Agent

Acts as a quality gate.

The Judge checks whether the candidate answer:

- answers the user's question,
- is supported by the evidence,
- contains hallucinated claims,
- overstates causality,
- ignores important limitations.

It returns:

```text
PASS
```

or:

```text
FAIL
```

plus feedback.

File:

```text
app/agents/judge_agent.py
```

---

## Producer / Judge retry loop

If the Judge returns `FAIL`, LangGraph routes execution back to the Producer:

```text
Producer
   ↓
Judge FAIL
   ↓
Judge feedback
   ↓
Producer retry
   ↓
Judge
```

Example:

```text
Judge feedback:
"Clarify uncertainty and avoid claiming definitive causality."
```

The Producer receives that feedback and rewrites the answer.

The number of retries is controlled by:

```env
MAX_RETRIES=2
```

This means:

```text
initial attempt
+ retry 1
+ retry 2
```

If the Judge still returns `FAIL`, the graph follows the failed branch instead of looping indefinitely.

---

## Synthesizer Agent

Once the Judge returns `PASS`, the Synthesizer converts the validated draft into a concise user-facing response.

It does not re-investigate the problem or add new evidence.

File:

```text
app/agents/synthesizer_agent.py
```

---

## Output guardrails

After synthesis, deterministic Python checks validate the final output.

Examples:

- Judge status must be `PASS`
- the final answer cannot be empty
- the final answer must meet minimum output requirements

File:

```text
app/guardrails/output_guardrails.py
```

---

## Persistence

Each investigation is stored locally as JSON under:

```text
artifacts/investigations/
```

This is intentionally simple.

A production system could later replace this with S3, a database, or another persistence layer without changing the core graph design.

File:

```text
app/persistence/result_store.py
```

---

## LangGraph orchestration

The complete workflow, shared state, edges, and conditional routing live in:

```text
app/graph/multi_agent_graph.py
```

LangGraph is responsible for:

```text
state
nodes
routing
conditional edges
retries
workflow execution
```

---

# LangChain vs LangGraph vs LangSmith

A useful mental model for this project is:

```text
LangChain
→ LLM and tool integration

LangGraph
→ workflow orchestration, state, routing, loops

LangSmith
→ tracing, debugging, observability
```

LangSmith does **not** control the workflow.

The application still runs locally through LangChain and LangGraph. LangSmith observes the execution and records traces when tracing is enabled.

If LangSmith tracing is disabled, the application can still run normally.

---

# LangSmith tracing

This project supports LangSmith tracing for debugging and observability.

When tracing is enabled, a complete investigation can be inspected in LangSmith.

A trace may contain:

```text
incident-investigation
│
├── planner
│   └── LLM call
│
├── data_agent
│   └── LLM / tool interaction
│
├── research_agent
│   └── LLM / tool interaction
│
├── producer
│   └── candidate answer
│
├── judge
│   └── PASS / FAIL
│
├── producer retry
│   └── if Judge returned FAIL
│
└── synthesizer
    └── final answer
```

This makes it possible to inspect what happened inside the workflow instead of only looking at the final answer.

Typical uses include:

- debugging agent behavior,
- inspecting prompts and responses,
- following retry paths,
- viewing latency,
- understanding where a bad answer originated,
- tracing the complete LangGraph execution.

---

# Project structure

```text
multi-agent-mlops-platform/
│
├── app/
│   ├── agents/
│   │   ├── planner_agent.py
│   │   ├── data_agent.py
│   │   ├── research_agent.py
│   │   ├── producer_agent.py
│   │   ├── judge_agent.py
│   │   └── synthesizer_agent.py
│   │
│   ├── api/
│   │   └── main.py
│   │
│   ├── graph/
│   │   └── multi_agent_graph.py
│   │
│   ├── guardrails/
│   │   └── output_guardrails.py
│   │
│   ├── persistence/
│   │   └── result_store.py
│   │
│   ├── tools/
│   │   └── incident_tools.py
│   │
│   └── config.py
│
├── artifacts/
│   └── investigations/
│
├── tests/
│   ├── test_api.py
│   ├── test_graph_retry.py
│   ├── test_graph_max_retries.py
│   └── test_output_guardrails.py
│
├── run_investigation.py
├── run_retry_demo.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Run the project locally

The following instructions assume a **fresh clone** of the repository.

## Prerequisites

You need:

- Git
- Python
- Internet access
- an OpenAI API key
- optionally, a LangSmith API key

Python 3.12 is recommended because that is the environment used while developing the project.

Check Python:

```bash
python --version
```

Check Git:

```bash
git --version
```

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/vaggoulas149/multi-agent-mlops-platform.git
cd multi-agent-mlops-platform
```

---

## Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
source .venv/bin/activate
```

After activation, the terminal should normally show something similar to:

```text
(.venv)
```

---

## Step 3 — Install dependencies

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install all project dependencies:

```bash
python -m pip install -r requirements.txt
```

The repository currently uses:

```text
langchain
langchain-openai
langgraph
langsmith
fastapi
uvicorn[standard]
httpx
pydantic
python-dotenv
typing-extensions
pytest
openai
```

---

# Step 4 — Configure API keys

The `.env` file committed to this repository contains **placeholder values only**.

It does **not** contain real API keys.

Example:

```env
OPENAI_API_KEY='your_real_openai_key'
LANGSMITH_API_KEY='your_real_langsmith_key'

OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none
MAX_RETRIES=2

LANGSMITH_TRACING=true
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

Before running the application, replace the placeholder values with your own valid keys.

For example:

```env
OPENAI_API_KEY='your_actual_openai_api_key'
LANGSMITH_API_KEY='your_actual_langsmith_api_key'
```

## Important security note

Never push real API keys to GitHub.

If you temporarily place real keys in `.env` for a local run, restore the placeholder values before committing or pushing.

A useful safety check before every push is:

```bash
git diff -- .env
```

Verify that `.env` contains only placeholders before pushing.

---

## LangSmith region configuration

Some LangSmith accounts may require a region-specific endpoint.

For example, an EU workspace may use:

```env
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

If your LangSmith setup requires a Workspace ID, add:

```env
LANGSMITH_WORKSPACE_ID=your_workspace_id
```

Only add these variables if they are required by your LangSmith account configuration.

---

# Step 5 — Run the tests

From the repository root:

```bash
pytest -v
```

The test suite covers:

```text
FastAPI health endpoint
FastAPI investigation endpoint
request validation
output guardrails
Judge FAIL → Producer retry → Judge PASS
maximum retry limit → failed branch
```

The workflow-heavy tests use mocks / `monkeypatch`, so they can validate orchestration behavior without relying on model randomness.

A successful run should show all tests as:

```text
PASSED
```

---

# Step 6 — Run a real investigation

Run:

```bash
python run_investigation.py
```

This executes the complete LangGraph workflow using the configured OpenAI model.

A successful run prints information such as:

```text
OBJECTIVE
PLAN
METRICS EVIDENCE
INCIDENT EVIDENCE
JUDGE STATUS
RETRIES
FINAL ANSWER
GUARDRAIL STATUS
ARTIFACT PATH
```

Because this command makes real OpenAI API calls, it requires a valid OpenAI API key and may incur API usage charges.

---

# Step 7 — View the LangSmith trace

If LangSmith tracing is enabled:

```env
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

run:

```bash
python run_investigation.py
```

Then open LangSmith and select the project:

```text
multi-agent-mlops-platform
```

You should be able to inspect the execution trace for the investigation.

The graph is configured with metadata such as:

```text
run name:
incident-investigation

tags:
agentic-ai
langgraph
multi-agent
incident-investigation
```

This is useful for filtering and inspecting runs during debugging.

---

# Step 8 — Run the retry demo

The project includes a small retry demonstration:

```bash
python run_retry_demo.py
```

The demo intentionally makes the first Judge call fail.

This demonstrates:

```text
Producer
   ↓
Judge FAIL
   ↓
feedback
   ↓
Producer retry
   ↓
Judge PASS
```

It is useful for seeing the conditional LangGraph loop in action.

---

# Step 9 — Run the FastAPI application

Start the API:

```bash
python -m uvicorn app.api.main:app --reload
```

Uvicorn should start locally at:

```text
http://127.0.0.1:8000
```

---

## Health endpoint

Open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## Swagger UI

Open:

```text
http://127.0.0.1:8000/docs
```

FastAPI provides an interactive interface for testing the API.

---

## Run an investigation through the API

Use:

```text
POST /investigate
```

Example request:

```json
{
  "question": "Why did checkout conversion drop on 2026-09-06?"
}
```

Example response shape:

```json
{
  "question": "Why did checkout conversion drop on 2026-09-06?",
  "objective": "Determine the likely cause of the checkout conversion drop.",
  "final_answer": "The most likely explanation is ...",
  "judge_status": "PASS",
  "retries": 0,
  "guardrail_status": "PASS",
  "artifact_path": ".../artifacts/investigations/<investigation-id>.json"
}
```

The exact LLM-generated wording can vary between runs.

---

# Example investigation

Question:

```text
Why did checkout conversion drop on 2026-09-06?
```

Example metric evidence:

```text
Previous-day conversion: 3.0%
Current conversion:      2.1%
Payment error rate:      8.4%
```

Example incident evidence:

```text
INC-991:
payment service deployment v2.4.1 was associated with
elevated payment failures and reduced checkout conversion.
```

A valid final answer should identify the deployment-related payment failures as the strongest available explanation while preserving uncertainty.

The project intentionally avoids unsupported statements such as:

```text
"The deployment definitely caused the entire conversion decline."
```

unless the available evidence actually supports that level of certainty.

---

# API flow

When the API is running:

```text
Client / Browser
      │
      ▼
POST /investigate
      │
      ▼
FastAPI
      │
      ▼
LangGraph workflow
      │
      ├── Planner
      ├── Data Agent
      ├── Research Agent
      ├── Producer
      ├── Judge / retry
      ├── Synthesizer
      └── Guardrails
      │
      ▼
Local persistence
      │
      ▼
JSON HTTP response
```

Persistence is a side effect.

The user receives the answer directly from FastAPI; the client does not need to read the saved artifact.

---

# Testing philosophy

The repository separates **real LLM execution** from **deterministic automated testing**.

## Real execution

```bash
python run_investigation.py
```

This uses the actual configured OpenAI model.

## Automated tests

```bash
pytest -v
```

Mocks replace external / LLM-heavy components where appropriate.

This lets the test suite verify behavior such as:

```text
Judge FAIL
→ feedback reaches Producer
→ Producer runs again
→ Judge PASS
```

without depending on a live model call for every test.

The maximum-retry test also verifies that the workflow terminates instead of entering an infinite loop.

---

# Configuration

The main environment variables are:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API authentication |
| `OPENAI_MODEL` | Model used by the agents |
| `OPENAI_REASONING_EFFORT` | Reasoning configuration |
| `MAX_RETRIES` | Maximum Producer retries after Judge failures |
| `LANGSMITH_API_KEY` | LangSmith authentication |
| `LANGSMITH_TRACING` | Enables or disables LangSmith tracing |
| `LANGSMITH_PROJECT` | Groups traces under a LangSmith project |
| `LANGSMITH_ENDPOINT` | Optional region-specific LangSmith endpoint |
| `LANGSMITH_WORKSPACE_ID` | Optional LangSmith workspace identifier |

---

# What is intentionally simplified?

This repository is a learning project, not a production incident-management system.

Several parts are deliberately simple:

- metric and incident tools return controlled demo data,
- persistence uses local JSON files,
- authentication is not implemented,
- there is no distributed execution,
- there is no production monitoring stack,
- there is no real enterprise incident-data integration,
- there is no database or cloud storage.

These limitations are intentional.

The goal is to make the following concepts easy to inspect:

```text
agents
tools
state
routing
feedback
retries
validation
tracing
testing
API integration
```

A larger production system could keep the same high-level orchestration pattern while replacing the toy data sources and infrastructure components.

---

# Current status

Implemented:

```text
Multi-agent workflow                 ✅
LangChain                            ✅
LangGraph                            ✅
Planner Agent                        ✅
Data Agent                           ✅
Research Agent                       ✅
Producer Agent                       ✅
Judge Agent                          ✅
PASS / FAIL routing                  ✅
Judge feedback                       ✅
Bounded retries                      ✅
Synthesizer                          ✅
Output guardrails                    ✅
Local persistence                    ✅
FastAPI                              ✅
Pydantic validation                  ✅
pytest                               ✅
Mocks / monkeypatch                  ✅
Retry-path test                      ✅
Maximum-retry failure test           ✅
LangSmith tracing                    ✅
```

---

# Possible next steps

The current version focuses on the agentic application core.

Possible productionization work includes:

```text
MLflow / agent evaluations
        ↓
Docker
        ↓
GitHub Actions CI/CD
        ↓
Cloud deployment
        ↓
Production observability
        ↓
Versioning / rollback
        ↓
Cloud persistence
```

These are intentionally separate from the core learning goal of this version.

---

# Key takeaway

This repository demonstrates a compact multi-agent AI pattern:

```text
User question
      ↓
Plan
      ↓
Collect evidence
      ↓
Produce candidate answer
      ↓
Judge
   ↙      ↘
retry    approve
   ↓        ↓
Producer  Synthesize
            ↓
        Guardrails
            ↓
        Final result
```

The project is intentionally small enough to understand file by file, while still demonstrating the core architecture behind more sophisticated agentic AI systems.
