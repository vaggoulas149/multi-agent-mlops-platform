# Multi-Agent MLOps Platform

> ## Start here
>
> This README is designed so that you can run the project **without any prior project context**.
>
> If you are new to Python projects, follow the **Windows setup — follow these steps exactly** section below **one step at a time and in order**.
>
> You should not need any hidden setup steps beyond what is written here.
>
> For the easiest first run:
>
> - use normal **Windows PowerShell**,
> - use a fresh `.venv`,
> - install dependencies from `requirements.txt`,
> - create `.env` from `.env.example`,
> - add your own OpenAI API key,
> - keep `LANGSMITH_TRACING=false`,
> - run the tests,
> - run the CLI demo,
> - run the FastAPI app.
>
> If anything does not work exactly as described, please contact:
>
> **vaggos149@gmail.com**

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
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Windows setup — follow these steps exactly

This section is intentionally written for someone who is new to Python projects.

Use **Windows PowerShell** and follow the steps **in order**.

**Do not add extra setup steps unless one of the troubleshooting sections below explicitly tells you to do so.**

The intended path is:

```text
open Windows PowerShell
→ check Python and Git
→ go to Documents
→ clone the repository
→ enter the repository folder
→ create .venv
→ activate .venv
→ install dependencies
→ copy .env.example to .env
→ paste your OpenAI API key
→ run tests
→ run the CLI investigation
→ start FastAPI
→ test /health and /docs
→ run POST /investigate
```

> **Important:** use the normal **Windows PowerShell**, not **Anaconda PowerShell Prompt**.
>
> A normal prompt looks similar to:
>
> ```text
> PS C:\Users\YourName>
> ```
>
> If the prompt starts with `(base)` or another Conda environment name, close that window and open the normal Windows PowerShell from the Start menu.

You do **not** need PyCharm or VS Code to run this project.

---

## Before you start

You need:

1. **Git**
2. **Python** — Python 3.12 is recommended
3. **Internet access**
4. **An OpenAI API key**
5. **Optional:** a LangSmith API key, only if you want tracing

### Check Python

Open **Windows PowerShell** and run:

```powershell
python --version
```

Expected output is similar to:

```text
Python 3.12.x
```

A newer compatible Python version may also work.

If `python` is not recognized, try:

```powershell
py --version
```

If neither command works, install Python before continuing, then close and reopen PowerShell.

### Check Git

Run:

```powershell
git --version
```

Expected output is similar to:

```text
git version 2.x.x
```

If `git` is not recognized, install Git before continuing, then close and reopen PowerShell.

---

# Step 1 — Open Windows PowerShell

Open the Windows Start menu.

Search for:

```text
Windows PowerShell
```

Open **Windows PowerShell**.

Do not use **Anaconda PowerShell Prompt** for this setup.

You should see something similar to:

```text
PS C:\Users\YourName>
```

---

# Step 2 — Go to your Documents folder

Run:

```powershell
cd $HOME\Documents
```

Your prompt should now look similar to:

```text
PS C:\Users\YourName\Documents>
```

---

# Step 3 — Clone the repository

Run exactly:

```powershell
git clone https://github.com/vaggoulas149/multi-agent-mlops-platform.git
```

Wait for Git to finish downloading the project.

Then enter the project folder:

```powershell
cd multi-agent-mlops-platform
```

Your prompt should now end with:

```text
\multi-agent-mlops-platform>
```

Check that the repository files are present:

```powershell
dir
```

You should see files and folders including:

```text
app
artifacts
tests
.env.example
.gitignore
README.md
requirements.txt
run_investigation.py
run_retry_demo.py
```

> You should **not** expect a real `.env` file yet. You will create it locally in a later step.

---

# Step 4 — Create a Python virtual environment

Make sure you are still inside the repository folder.

Run:

```powershell
python -m venv .venv
```

If your computer uses the `py` launcher instead of `python`, use:

```powershell
py -3.12 -m venv .venv
```

This creates an isolated Python environment inside the project.

The command may finish without printing anything. That is normal.

---

# Step 5 — Activate the virtual environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation worked, your prompt should start with:

```text
(.venv)
```

For example:

```text
(.venv) PS C:\Users\YourName\Documents\multi-agent-mlops-platform>
```

## If PowerShell says script execution is disabled

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then try activation again:

```powershell
.\.venv\Scripts\Activate.ps1
```

The `Process` scope affects only the current PowerShell window.

---

# Step 6 — Upgrade pip

Run:

```powershell
python -m pip install --upgrade pip
```

Wait until the command finishes.

---

# Step 7 — Install the project dependencies

Run exactly:

```powershell
python -m pip install -r requirements.txt
```

The `-r` is important.

Correct:

```text
python -m pip install -r requirements.txt
```

Incorrect:

```text
pip install requirements.txt
```

Wait until installation finishes successfully.

---

# Step 8 — Create your private local `.env` file

The GitHub repository contains:

```text
.env.example
```

This is only a safe template.

Create your own private `.env` file by running:

```powershell
Copy-Item .env.example .env
```

Now open the new file:

```powershell
notepad .env
```

---

# Step 9 — Add your OpenAI API key

Inside `.env`, you will see a line like:

```env
OPENAI_API_KEY=your_openai_api_key
```

Replace only the placeholder:

```text
your_openai_api_key
```

with your real OpenAI API key.

## Exact API-key format

Put the key **immediately after the `=` sign**.

This format rule applies to both OpenAI and LangSmith keys.

Use:

```text
NAME=value
```

Do not use:

```text
NAME = value
NAME="value"
NAME='value'
```

Use:

```env
OPENAI_API_KEY=your_actual_openai_api_key
```

Do **not** add spaces around `=`.

Do **not** put single quotes `'...'` around the key.

Do **not** put double quotes `"..."` around the key.

Correct:

```env
OPENAI_API_KEY=sk-example123456789
```

Incorrect:

```env
OPENAI_API_KEY = sk-example123456789
```

Incorrect:

```env
OPENAI_API_KEY="sk-example123456789"
```

Incorrect:

```env
OPENAI_API_KEY='sk-example123456789'
```

For the easiest first run, keep:

```env
LANGSMITH_TRACING=false
```

You do **not** need a LangSmith API key for the basic setup.

You can leave:

```env
LANGSMITH_API_KEY=your_langsmith_api_key
```

unchanged while `LANGSMITH_TRACING=false`.

Your minimum working configuration should therefore look similar to:

```env
# OpenAI
OPENAI_API_KEY=your_actual_openai_api_key

# Model configuration
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none

# Workflow configuration
MAX_RETRIES=2

# LangSmith tracing is optional.
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=multi-agent-mlops-platform
```

Save the file in Notepad:

```text
File → Save
```

Then close Notepad.

> **Security:** never commit your real `.env` file and never share your API key. The project `.gitignore` intentionally excludes `.env`.

---

# Step 10 — Run the automated tests

Make sure your PowerShell prompt still starts with:

```text
(.venv)
```

Run:

```powershell
python -m pytest -v
```

A successful run should finish with all tests marked:

```text
PASSED
```

At the time of this README, the suite contains tests for:

- the FastAPI health endpoint,
- the FastAPI investigation endpoint,
- request validation,
- output guardrails,
- the Judge `FAIL` → Producer retry → Judge `PASS` path,
- the maximum-retry failure path.

The workflow-heavy tests use mocks where appropriate, so they are designed to be deterministic.

---

# Step 11 — Run the real multi-agent investigation

Run:

```powershell
python run_investigation.py
```

This makes real OpenAI API calls.

A successful run should execute the workflow and finish with output containing sections such as:

```text
OBJECTIVE
PLAN
METRICS EVIDENCE
INCIDENT EVIDENCE
JUDGE STATUS
RETRIES
FINAL ANSWER
GUARDRAIL STATUS
ARTIFACT
```

A successful result should normally show:

```text
JUDGE STATUS:
PASS
```

and:

```text
GUARDRAIL STATUS:
PASS
```

The exact generated wording may vary between runs.

Because this is a real LLM run, OpenAI API usage may incur a small charge.

---

# Step 12 — Check the generated JSON artifact

After a successful investigation, the project stores a JSON result under:

```text
artifacts\investigations
```

From PowerShell, you can list the generated files with:

```powershell
dir artifacts\investigations
```

You should see a JSON file with a UUID-like filename, for example:

```text
3c39129a-1fe8-41f0-9ba5-63d805394034.json
```

This confirms that local persistence worked.

---

# Step 13 — Optional: run the retry demonstration

This step is optional.

Run:

```powershell
python run_retry_demo.py
```

The demo deliberately forces the first Judge evaluation to fail so that you can see the retry path:

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

This is only a demonstration of the LangGraph conditional loop.

---

# Step 14 — Start the FastAPI server

Run:

```powershell
python -m uvicorn app.api.main:app --reload
```

Keep this PowerShell window open while using the API.

You should see output indicating that Uvicorn is running at:

```text
http://127.0.0.1:8000
```

---

# Step 15 — Check the health endpoint

Open a web browser.

Go to:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

If you see this, the FastAPI server is running correctly.

---

# Step 16 — Open Swagger

In the browser, go to:

```text
http://127.0.0.1:8000/docs
```

You should see the FastAPI Swagger page with:

```text
GET /health
POST /investigate
```

---

# Step 17 — Run an investigation from Swagger

On the Swagger page:

1. Click `POST /investigate`.
2. Click **Try it out**.
3. Replace the request body with:

```json
{
  "question": "Why did checkout conversion drop on 2026-09-06?"
}
```

4. Click **Execute**.

A successful request should return:

```text
200
```

The response should contain fields similar to:

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

The exact LLM-generated answer can vary.

---

# Step 18 — Stop the FastAPI server

Return to the PowerShell window in which Uvicorn is running.

Press:

```text
Ctrl + C
```

The local server will stop.

---

# Step 19 — Deactivate the virtual environment

When you are finished, run:

```powershell
deactivate
```

The `(.venv)` prefix should disappear from the PowerShell prompt.

---

# Optional — Enable LangSmith tracing

The basic application does **not** require LangSmith.

Only do this after the normal application works.

Open `.env`:

```powershell
notepad .env
```

Replace:

```env
LANGSMITH_API_KEY=your_langsmith_api_key
```

with your real LangSmith key.

Use the same strict format as the OpenAI key:

```env
LANGSMITH_API_KEY=your_actual_langsmith_api_key
```

The value must be directly after `=` with:

- no spaces around `=`,
- no single quotes,
- no double quotes.

Then change:

```env
LANGSMITH_TRACING=false
```

to:

```env
LANGSMITH_TRACING=true
```

Save the file.

Some LangSmith workspaces may require an additional endpoint.

For example, an EU workspace may require:

```env
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

Only add this if your LangSmith account requires it.

If you enable LangSmith and receive `403 Forbidden`, either verify the LangSmith account configuration or set:

```env
LANGSMITH_TRACING=false
```

to continue running the application without tracing.

---

# Next time you want to run the project

You do **not** need to clone the repository or reinstall the dependencies again.

Open normal **Windows PowerShell**.

Go to the project:

```powershell
cd $HOME\Documents\multi-agent-mlops-platform
```

Activate the existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then choose what you want to run.

For the command-line investigation:

```powershell
python run_investigation.py
```

For the tests:

```powershell
python -m pytest -v
```

For the API:

```powershell
python -m uvicorn app.api.main:app --reload
```

---

# Common setup problems

## PowerShell starts with `(base)`

You probably opened **Anaconda PowerShell Prompt**.

Close it and open the normal:

```text
Windows PowerShell
```

from the Start menu.

---

## `python` is not recognized

Try:

```powershell
py --version
```

If that works, create the virtual environment with:

```powershell
py -3.12 -m venv .venv
```

If neither `python` nor `py` works, install Python and reopen PowerShell.

---

## `git` is not recognized

Install Git.

Then close and reopen PowerShell and test:

```powershell
git --version
```

---

## PowerShell says script execution is disabled

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Dependency installation fails

Make sure the virtual environment is active and run:

```powershell
python -m pip install -r requirements.txt
```

Do not use:

```text
pip install requirements.txt
```

---

## `pytest` is not recognized

Use:

```powershell
python -m pytest -v
```

This explicitly runs pytest through the Python interpreter in the active virtual environment.

---

## OpenAI returns `401 Unauthorized`

Open:

```powershell
notepad .env
```

Check that:

```env
OPENAI_API_KEY=your_actual_openai_api_key
```

contains your real key.

Also make sure:

- there are no spaces around `=`,
- there are no single quotes,
- there are no double quotes,
- the placeholder was actually replaced.

---

## The OpenAI model is unavailable to your API account

The default configuration is:

```env
OPENAI_MODEL=gpt-5.6-luna
```

If your OpenAI API account does not have access to that model, replace it with a compatible OpenAI model available to your API account.

---

## LangSmith returns `403 Forbidden`

If LangSmith tracing is not important for your run, use:

```env
LANGSMITH_TRACING=false
```

The application can run normally without LangSmith.

---

## Port `8000` is already in use

Start the API on port `8001` instead:

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
python -m pytest -v
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
| `LANGSMITH_API_KEY` | Optional | Required only when LangSmith tracing is enabled |
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

---

---

# Questions or setup problems?

If **any** step in this README behaves differently from what is described, stop there and contact me:

**vaggos149@gmail.com**

Please include:

- the step number you were following,
- the command you ran,
- the error message or screenshot.

Do not send API keys or other secrets.

I can help with the setup or walk you through the project.
