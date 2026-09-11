# Multi-Agent MLOps Platform

A small, educational **multi-agent AI incident investigation system** built with:

- **LangChain**
- **LangGraph**
- **LangSmith**
- **FastAPI**
- **Pydantic**
- **pytest**

> This repository is intentionally a **toy / learning project**.
>
> The goal is not to simulate a full enterprise incident-management platform. The goal is to show, in a small codebase, how a multi-agent AI workflow can be designed, executed, reviewed, retried, traced, exposed through an API, and tested.

---

# What this project does

The application investigates a simple operational question such as:

```text
Why did checkout conversion drop on 2026-09-06?
```

Instead of sending the question directly to one LLM and returning whatever it says, the project uses a structured multi-agent workflow:

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

The workflow:

1. creates an investigation plan,
2. retrieves checkout metrics,
3. retrieves relevant incident evidence,
4. produces a candidate explanation,
5. sends that explanation to a Judge,
6. retries the Producer if the Judge returns `FAIL`,
7. sends Judge feedback back to the Producer,
8. continues only when the answer is sufficiently grounded,
9. synthesizes a final user-facing answer,
10. runs deterministic output guardrails,
11. stores the investigation locally as JSON,
12. returns the result through Python or FastAPI.

The Producer/Judge retry loop is bounded by `MAX_RETRIES`, so the workflow cannot loop forever.

---

# Why this project exists

A very simple LLM application can look like this:

```text
User → LLM → Answer
```

This project demonstrates a more structured **agentic AI** pattern:

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

The incident-investigation use case is deliberately simple so that the focus stays on the architecture.

The project demonstrates:

- LangChain model integration
- LangChain tool calling
- LangGraph shared state
- LangGraph nodes and edges
- conditional routing
- specialized agents
- Producer / Judge review pattern
- Judge feedback
- bounded retries
- deterministic guardrails
- local persistence
- FastAPI
- Pydantic request / response validation
- pytest
- mocking with `monkeypatch`
- retry-path testing
- maximum-retry failure testing
- LangSmith tracing and debugging

---

# Architecture

## Planner Agent

Creates a short, executable investigation plan.

Example:

```text
Objective:
Determine the likely cause of the checkout conversion drop.

Steps:
1. Retrieve checkout metrics.
2. Search previous incidents.
3. Compare the evidence.
```

The Planner is capability-aware: it should only request work that the available tools can actually perform.

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

Retrieves historical incident evidence.

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

Combines the available evidence and writes a candidate answer.

The Producer is instructed to:

- use only supplied evidence,
- avoid invented facts,
- avoid unsupported certainty,
- distinguish observations from plausible conclusions,
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
- invents information,
- overstates causality,
- omits important limitations,
- is internally consistent.

It returns a structured result:

```text
PASS
```

or:

```text
FAIL
```

together with review feedback.

File:

```text
app/agents/judge_agent.py
```

---

## Producer / Judge retry loop

If the Judge returns `FAIL`, LangGraph routes execution back to the Producer.

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

The retry budget is controlled by:

```env
MAX_RETRIES=2
```

That means:

```text
initial attempt
+ retry 1
+ retry 2
```

If the Judge still rejects the answer, the workflow follows the controlled failure branch.

---

## Synthesizer Agent

After the Judge returns `PASS`, the Synthesizer converts the validated draft into the final user-facing response.

It is not supposed to:

- re-investigate the problem,
- invent new evidence,
- change the validated conclusion.

File:

```text
app/agents/synthesizer_agent.py
```

---

## Output guardrails

The final response passes through deterministic Python checks.

For example:

- Judge status must be `PASS`,
- the final answer cannot be empty,
- the final answer cannot be unexpectedly short.

File:

```text
app/guardrails/output_guardrails.py
```

---

## Persistence

Completed investigations are stored locally as JSON under:

```text
artifacts/investigations/
```

Generated JSON artifacts are runtime output and do not need to be committed to Git.

File:

```text
app/persistence/result_store.py
```

---

## LangGraph orchestration

The complete shared state, nodes, edges, conditional routing, retry logic, and graph invocation live in:

```text
app/graph/multi_agent_graph.py
```

A useful mental model is:

```text
LangChain
→ LLM and tool integration

LangGraph
→ workflow state, routing, loops, retries, orchestration

LangSmith
→ tracing, debugging, observability
```

LangSmith does **not** control the workflow. If tracing is disabled, the LangGraph application can still run normally.

---

# LangSmith tracing

When LangSmith tracing is enabled, one investigation can be inspected as a trace.

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
│   └── if the Judge returned FAIL
│
└── synthesizer
    └── final answer
```

This is useful for:

- debugging agent behavior,
- inspecting prompts and responses,
- following retry paths,
- viewing latency,
- understanding where a problematic answer originated.

LangSmith is **optional for running the application**. An OpenAI API key is required for real LLM execution; LangSmith is only needed if you want tracing.

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

# Quick start for Windows users

The instructions below are intentionally detailed.

They assume that you are starting from a normal Windows computer and are not already familiar with Python virtual environments.

You do **not** need PyCharm or VS Code to run the project. A normal Windows PowerShell terminal is enough.

---

# Before you start

You need:

1. **Git**
2. **Python 3.12**
3. **Internet access**
4. **An OpenAI API key**
5. **Optional: a LangSmith API key** if you want tracing

---

## Check whether Python is installed

Open the Windows Start menu.

Search for:

```text
Windows PowerShell
```

Open it.

In the PowerShell window, run:

```powershell
python --version
```

You should see something similar to:

```text
Python 3.12.x
```

If `python` is not recognized, try:

```powershell
py --version
```

If neither command works, install Python before continuing.

Python 3.12 is recommended for this project.

---

## Check whether Git is installed

In the same PowerShell window, run:

```powershell
git --version
```

You should see something similar to:

```text
git version 2.x.x
```

If `git` is not recognized, install Git before continuing.

---

# Windows PowerShell: exact setup instructions

Follow these steps in order.

Do not skip a step unless it is explicitly marked optional.

---

## Step 1 — Open Windows PowerShell

Open:

```text
Start Menu
→ search "Windows PowerShell"
→ open Windows PowerShell
```

You should see a terminal window similar to:

```text
PS C:\Users\YourName>
```

---

## Step 2 — Choose where you want to download the project

For example, to use your `Documents` folder:

```powershell
cd $HOME\Documents
```

You can confirm your current location with:

```powershell
Get-Location
```

---

## Step 3 — Clone the GitHub repository

Run:

```powershell
git clone https://github.com/vaggoulas149/multi-agent-mlops-platform.git
```

Git should download the repository.

When it finishes, enter the project folder:

```powershell
cd multi-agent-mlops-platform
```

You can confirm that the files exist by running:

```powershell
dir
```

You should see files and folders such as:

```text
app
artifacts
tests
.env
.gitignore
README.md
requirements.txt
run_investigation.py
run_retry_demo.py
```

---

## Step 4 — Make sure you are not inside another Python environment

This step is mainly useful if you already use Conda or another Python environment manager.

Look at the beginning of your PowerShell prompt.

If it looks normal:

```text
PS C:\Users\YourName\Documents\multi-agent-mlops-platform>
```

continue to Step 5.

If it starts with something such as:

```text
(base)
```

or:

```text
(my-environment)
```

and you are using Conda, run:

```powershell
conda deactivate
```

Repeat if necessary until the environment name disappears.

If you do not use Conda, ignore this step.

---

## Step 5 — Create a fresh virtual environment

From inside the repository folder, run:

```powershell
python -m venv .venv
```

If your Windows installation uses the `py` launcher instead of `python`, use:

```powershell
py -3.12 -m venv .venv
```

This creates an isolated Python environment inside:

```text
.venv
```

Wait until the command finishes.

It may finish without printing anything. That is normal.

---

## Step 6 — Activate the virtual environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation works, the beginning of the terminal prompt should change to:

```text
(.venv)
```

For example:

```text
(.venv) PS C:\Users\YourName\Documents\multi-agent-mlops-platform>
```

### If PowerShell blocks the activation script

If you see an error saying that script execution is disabled, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then try again:

```powershell
.\.venv\Scripts\Activate.ps1
```

The `Process` scope applies only to the current PowerShell window.

---

## Step 7 — Upgrade pip

Run:

```powershell
python -m pip install --upgrade pip
```

Wait until it finishes.

---

## Step 8 — Install all project dependencies

Run exactly:

```powershell
python -m pip install -r requirements.txt
```

Important:

```text
Correct:
python -m pip install -r requirements.txt

Wrong:
pip install requirements.txt
```

The `-r` tells pip to install the packages listed inside the file.

Installation may take a few minutes.

---

# Step 9 — Configure the API keys

The repository contains a file named:

```text
.env
```

The `.env` file committed to GitHub contains **placeholder values only**.

It does not contain real credentials.

Open it directly from PowerShell:

```powershell
notepad .env
```

You should see values similar to:

```env
OPENAI_API_KEY='your_real_openai_key'
LANGSMITH_API_KEY='your_real_langsmith_key'

OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none
MAX_RETRIES=2

LANGSMITH_TRACING=true
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

---

## Minimum configuration: OpenAI only

To run the application with the minimum setup, you only need a valid OpenAI API key.

Replace:

```env
OPENAI_API_KEY='your_real_openai_key'
```

with your actual key.

For example:

```env
OPENAI_API_KEY='your_actual_key_here'
```

Do not share that key and do not commit it to Git.

If you do **not** want to use LangSmith tracing, change:

```env
LANGSMITH_TRACING=true
```

to:

```env
LANGSMITH_TRACING=false
```

You can leave the LangSmith placeholder unchanged when tracing is disabled.

A minimal `.env` therefore looks like:

```env
OPENAI_API_KEY='your_actual_openai_key'
LANGSMITH_API_KEY='your_real_langsmith_key'

OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none
MAX_RETRIES=2

LANGSMITH_TRACING=false
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

Save the file and close Notepad.

---

## Optional configuration: enable LangSmith tracing

If you also have a LangSmith API key, put it in:

```env
LANGSMITH_API_KEY='your_actual_langsmith_key'
```

and set:

```env
LANGSMITH_TRACING=true
```

Example:

```env
OPENAI_API_KEY='your_actual_openai_key'
LANGSMITH_API_KEY='your_actual_langsmith_key'

OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none
MAX_RETRIES=2

LANGSMITH_TRACING=true
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

Some LangSmith accounts may also require a region-specific endpoint.

For example, an EU workspace may require:

```env
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

Only add this if your LangSmith account requires it.

---

# Step 10 — Run the automated tests

Still inside the repository folder, and with `(.venv)` visible in the prompt, run:

```powershell
pytest -v
```

The tests should finish with all tests marked:

```text
PASSED
```

The test suite verifies:

- FastAPI health endpoint
- FastAPI investigation endpoint
- request validation
- output guardrails
- Judge `FAIL` → Producer retry → Judge `PASS`
- maximum-retry failure path

Most workflow-heavy tests use mocks, so they do not need to make live LLM calls.

If the tests pass, the local Python setup is working correctly.

---

# Step 11 — Run the real multi-agent investigation

Now run:

```powershell
python run_investigation.py
```

This is the main command-line demonstration.

It runs the actual multi-agent workflow.

You should see logs for components such as:

```text
Planner Agent
Data Agent
Research Agent
Producer Agent
Judge Agent
Synthesizer Agent
Output Guardrails
```

At the end, you should see output similar to:

```text
FINAL RESULT

OBJECTIVE:
...

PLAN:
...

METRICS EVIDENCE:
...

INCIDENT EVIDENCE:
...

JUDGE STATUS:
PASS

RETRIES:
0

FINAL ANSWER:
...

GUARDRAIL STATUS:
PASS

ARTIFACT:
...
```

The exact LLM-generated wording may vary between runs.

This command makes real OpenAI API calls and may incur API usage charges.

---

# Step 12 — Check the generated artifact

After a successful investigation, open:

```text
artifacts\investigations
```

You should see a generated JSON file with a UUID-like filename.

For example:

```text
3c39129a-1fe8-41f0-9ba5-63d805394034.json
```

That file contains the stored investigation result.

---

# Step 13 — Optional: run the retry demonstration

To intentionally demonstrate the Judge retry path, run:

```powershell
python run_retry_demo.py
```

The script deliberately forces the first Judge evaluation to fail.

You should observe the logical flow:

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

This script is only a demonstration. It is not required to use the normal application.

---

# Step 14 — Start the FastAPI server

To expose the workflow as a local HTTP API, run:

```powershell
python -m uvicorn app.api.main:app --reload
```

Do not close this PowerShell window while you are using the API.

You should see output indicating that Uvicorn is running on:

```text
http://127.0.0.1:8000
```

---

# Step 15 — Check the health endpoint

Open a browser.

Go to:

```text
http://127.0.0.1:8000/health
```

You should see:

```json
{
  "status": "ok"
}
```

If you see this, the FastAPI server is running.

---

# Step 16 — Open Swagger

In your browser, go to:

```text
http://127.0.0.1:8000/docs
```

This opens FastAPI's interactive Swagger UI.

You should see:

```text
GET /health
POST /investigate
```

---

# Step 17 — Run an investigation from Swagger

In Swagger:

1. Find `POST /investigate`.
2. Click it.
3. Click **Try it out**.
4. Replace the request body with:

```json
{
  "question": "Why did checkout conversion drop on 2026-09-06?"
}
```

5. Click **Execute**.

A successful request should return:

```text
200
```

and a JSON response containing fields such as:

```json
{
  "question": "Why did checkout conversion drop on 2026-09-06?",
  "objective": "...",
  "final_answer": "...",
  "judge_status": "PASS",
  "retries": 0,
  "guardrail_status": "PASS",
  "artifact_path": "..."
}
```

The exact answer may vary because it is generated by an LLM.

---

# Step 18 — Stop the FastAPI server

Go back to the PowerShell window in which Uvicorn is running.

Press:

```text
Ctrl + C
```

The server will stop.

---

# Step 19 — Deactivate the virtual environment when finished

When you are completely finished, run:

```powershell
deactivate
```

The `(.venv)` prefix should disappear from the PowerShell prompt.

---

# Next time you want to run the project

You do **not** need to clone the repository or reinstall everything every time.

Open Windows PowerShell and run:

```powershell
cd $HOME\Documents\multi-agent-mlops-platform
```

Then activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run whichever part you want.

For the command-line demo:

```powershell
python run_investigation.py
```

For the API:

```powershell
python -m uvicorn app.api.main:app --reload
```

For the tests:

```powershell
pytest -v
```

---

# If you only want the shortest possible setup

For an experienced Python user, the complete Windows setup is:

```powershell
git clone https://github.com/vaggoulas149/multi-agent-mlops-platform.git
cd multi-agent-mlops-platform

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

notepad .env
```

Add a valid OpenAI key and, for the minimum setup, use:

```env
LANGSMITH_TRACING=false
```

Then:

```powershell
pytest -v
python run_investigation.py
python -m uvicorn app.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

---

# Common problems

## `python` is not recognized

Try:

```powershell
py --version
```

If that works, create the environment with:

```powershell
py -3.12 -m venv .venv
```

If neither command works, install Python.

---

## `git` is not recognized

Install Git, close PowerShell, open a new PowerShell window, and retry:

```powershell
git --version
```

---

## PowerShell says script execution is disabled

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## `pip install requirements.txt` fails

Use:

```powershell
python -m pip install -r requirements.txt
```

The `-r` is required.

---

## OpenAI returns `401 Unauthorized`

This normally means the value in:

```env
OPENAI_API_KEY=...
```

is missing, still a placeholder, or invalid.

Open the file:

```powershell
notepad .env
```

and check that you inserted your own valid OpenAI API key.

---

## LangSmith returns `403 Forbidden`

If you do not need tracing, use:

```env
LANGSMITH_TRACING=false
```

The application can run without LangSmith.

If you do want tracing, verify the LangSmith API key and account region.

An EU workspace may require:

```env
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

---

## The configured OpenAI model is not available to your API account

The default configuration is:

```env
OPENAI_MODEL=gpt-5.6-luna
```

If your OpenAI API account does not have access to that model, replace it with a compatible model available to your account.

---

## Port 8000 is already being used

Run Uvicorn on another port:

```powershell
python -m uvicorn app.api.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001/docs
```

---

# Testing philosophy

The repository separates live execution from deterministic automated tests.

## Real execution

```powershell
python run_investigation.py
```

This uses the configured OpenAI model.

## Automated tests

```powershell
pytest -v
```

Mocks replace external or LLM-heavy components where appropriate.

This allows the test suite to verify behavior such as:

```text
Judge FAIL
→ Judge feedback reaches Producer
→ Producer runs again
→ Judge PASS
```

without depending on model randomness for every test run.

The maximum-retry test also verifies that the workflow terminates instead of entering an infinite loop.

---

# Configuration reference

| Variable | Required? | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes for real LLM runs | OpenAI API authentication |
| `OPENAI_MODEL` | Yes / default provided | Model used by the agents |
| `OPENAI_REASONING_EFFORT` | No / default provided | Reasoning configuration |
| `MAX_RETRIES` | No / default provided | Maximum Producer retries |
| `LANGSMITH_API_KEY` | Only for LangSmith | LangSmith authentication |
| `LANGSMITH_TRACING` | No | Enable or disable LangSmith tracing |
| `LANGSMITH_PROJECT` | No | LangSmith project name |
| `LANGSMITH_ENDPOINT` | Sometimes | Region-specific LangSmith endpoint |
| `LANGSMITH_WORKSPACE_ID` | Sometimes | Workspace identifier |

---

# What is intentionally simplified?

This is a learning project, not a production incident-management system.

Several elements are deliberately simple:

- metric and incident tools return controlled demo data,
- persistence uses local JSON,
- authentication is not implemented,
- there is no distributed execution,
- there is no production monitoring stack,
- there is no real enterprise incident-data integration,
- there is no production database or cloud storage.

These simplifications are intentional.

The repository focuses on making these concepts easy to inspect:

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

This version focuses on the agentic application core.

Possible future productionization work includes:

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

The project is intentionally small enough to understand file by file while still demonstrating the main architecture behind more sophisticated agentic AI systems.

---

# Questions or setup problems?

If you encounter any issue while cloning, installing, configuring, testing, or running the project, feel free to contact me directly:

**vaggos149@gmail.com**

I will be happy to help with the setup or guide you through the project.
