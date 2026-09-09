# Multi-Agent MLOps Platform

Production-oriented learning project for an AI Incident Investigator.

## Architecture

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
PRODUCER SYNTHESIZER
 ↑       ↓
feedback OUTPUT GUARDRAILS
         ↓
      PERSIST
         ↓
        END
```

The Producer/Judge loop is bounded by `MAX_RETRIES`.

## Main components

- `app/agents/planner_agent.py`
  Creates an executable investigation plan.
- `app/agents/data_agent.py`
  Retrieves metrics evidence.
- `app/agents/research_agent.py`
  Retrieves prior incident evidence.
- `app/agents/producer_agent.py`
  Produces a candidate answer.
- `app/agents/judge_agent.py`
  Reviews the candidate and returns `PASS` or `FAIL`.
- `app/agents/synthesizer_agent.py`
  Turns a validated draft into the final user-facing answer.
- `app/guardrails/output_guardrails.py`
  Deterministic final checks.
- `app/persistence/result_store.py`
  Stores investigation artifacts locally as JSON.
- `app/graph/multi_agent_graph.py`
  LangGraph orchestration and conditional routing.

## Setup

Create a `.env` file from `.env.example`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.6-luna
OPENAI_REASONING_EFFORT=none
MAX_RETRIES=2
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

From the repository root:

```bash
python run_investigation.py
```

## Tests

```bash
pytest
```

## Persistence

For now, results are stored locally under:

```text
artifacts/investigations/
```

Later this persistence layer can be replaced or extended with S3 without
changing the agent graph.

## Next steps

- FastAPI request/response layer
- LLM/tool mocking
- Judge/retry tests
- MLflow evaluations
- Docker
- GitHub Actions CI/CD
- S3/cloud persistence
- Observability and tracing
