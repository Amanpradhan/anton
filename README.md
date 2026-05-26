# Anton

> Autonomous multi-agent competitive intelligence platform. Configure teams of AI agents that research, analyze, and deliver insights — while you watch them collaborate in real time.

Named after the *Silicon Valley* reference. Built as the Yuno AI Engineer hiring challenge.

---

## What it does

You send a message to Anton on Telegram:

> *"Analyze payment processors entering the LATAM market"*

Anton spins up a 5-agent pipeline. In ~45 seconds you get a professional intelligence report. On the dashboard you watch every agent work in real time — searches run, analysis gets critiqued, the report gets written. The whole run costs ~$0.02–0.04.

---

## Architecture

```
                        ┌─────────────────────────────┐
  User                  │         Anton Platform       │
   │                    │                             │
   │ Telegram           │  ┌──────────┐  ┌─────────┐  │
   ▼                    │  │ Next.js  │  │ FastAPI │  │
┌──────────┐  webhook   │  │  Web UI  │◄─►  API   │  │
│ Telegram │───────────►│  │          │  │         │  │
│   Bot    │◄───────────│  │Dashboard │  │ /agents │  │
└──────────┘  reply     │  │Workflows │  │  /runs  │  │
                        │  │ Monitor  │  │  /evals │  │
                        │  └──────────┘  └────┬────┘  │
                        │                     │        │
                        │         ┌───────────▼──────┐ │
                        │         │  LangGraph        │ │
                        │         │  Runtime          │ │
                        │         │                  │ │
                        │         │ Orchestrator      │ │
                        │         │  → Researcher     │ │
                        │         │  → Analyst        │ │
                        │         │  → Critic ──┐     │ │
                        │         │  → Reporter │     │ │
                        │         │  ← ─────────┘     │ │
                        │         │  → Evaluator      │ │
                        │         └───────────┬──────┘ │
                        │                     │        │
                        │    ┌────────────────▼──────┐ │
                        │    │    Redis Pub/Sub       │ │
                        │    │  (real-time events)   │ │
                        │    └────────────┬──────────┘ │
                        │                 │            │
                        │    ┌────────────▼──────────┐ │
                        │    │      PostgreSQL        │ │
                        │    │ agents · workflows     │ │
                        │    │ runs · messages        │ │
                        │    │ eval_results           │ │
                        │    └───────────────────────┘ │
                        └─────────────────────────────┘
```

### Request flow

```
Telegram msg
  → POST /api/channels/telegram/webhook
  → Find active workflow (DB)
  → Create Run record (202 Accepted)
  → run_workflow() [background task]
      → LangGraph graph.ainvoke(state)
          → orchestrator: generates 5 search queries
          → researcher:   runs Tavily searches in parallel
          → analyst:      synthesizes into structured analysis
          → critic:       scores quality (JSON), routes:
              if score < 7 AND iteration < 3 → researcher (loop)
              if score >= 7 OR max iterations → reporter
          → reporter:     writes full report + Telegram summary
          → evaluator:    LLM-as-judge scores the report (async)
      → Persist Run + Messages + EvalResult to PostgreSQL
      → bot.send_message(chat_id, summary)
  → Frontend WebSocket receives events in real time
```

---

## Agent pipeline

| Agent | Model | Role |
|-------|-------|------|
| **Orchestrator** | Gemini 2.5 Pro | Decomposes request into 5 targeted search queries |
| **Researcher** | Gemini 2.0 Flash | Runs parallel Tavily searches, accumulates data |
| **Analyst** | Gemini 2.0 Flash | Synthesizes raw data into 6-section structured analysis |
| **Critic** | Gemini 2.0 Flash | Quality gate: scores analysis 1–10, approves or rejects |
| **Reporter** | Gemini 2.0 Flash | Writes final report + short Telegram summary |
| **Evaluator** | Gemini 2.0 Flash | Post-run LLM-as-judge: scores output on 4 dimensions |

The Critic → Researcher feedback loop is what makes this genuinely multi-agent rather than a simple chain. The Critic can reject weak analysis up to 3 times before the pipeline forces completion.

---

## Tech stack decisions

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Python + FastAPI | Best AI ecosystem, async-native, automatic OpenAPI docs |
| AI Framework | **LangGraph** | Stateful graphs + conditional edges + cycles — see below |
| LLM | Gemini 2.5 Pro / 2.0 Flash | Cost-optimized: heavy reasoning only where needed |
| Frontend | Next.js + React Flow | Visual workflow canvas, App Router, TypeScript |
| Database | PostgreSQL | Production-grade, rich querying for run/eval history |
| Message Bus | Redis Pub/Sub | Async event streaming to WebSocket without coupling |
| Search | Tavily API | Built for LLM agents, returns clean structured results |
| Messaging | Telegram Bot API | Zero business approval, excellent webhook API |
| Containers | Docker Compose | Single-command local setup, zero cloud required |

### Why LangGraph over CrewAI / AutoGen?

**LangGraph** is the right tool for this problem because the pipeline has a conditional feedback loop: the Critic can send work back to the Researcher. That requires a *cyclic graph*, which neither CrewAI nor AutoGen handle well at the primitive level.

| Framework | Strength | Why we didn't use it |
|-----------|----------|----------------------|
| **CrewAI** | High-level, fast to prototype | Abstracts routing — hard to customize the Critic → Researcher cycle |
| **AutoGen** | Great for conversational back-and-forth | Designed for agent chat, not structured pipelines |
| **LangGraph** | Explicit state graph, conditional edges, cycles | ✓ Exactly what we need |

LangGraph also gives us full control over the `AgentState` TypedDict — every agent reads from and writes to the same shared state, making debugging straightforward.

---

## Eval system

Anton evaluates every pipeline run automatically using **LLM-as-judge** — the same technique used in RLHF pipelines at AI labs.

After the Reporter finishes, an `EvaluatorAgent` scores the report on 4 dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Specificity** | Are claims backed by companies, numbers, dates? |
| **Completeness** | Are all 6 required sections substantive? |
| **Accuracy Risk** | Are claims verified or flagged as uncertain? |
| **Usefulness** | Would a strategy professional act on this? |

Scores are stored in PostgreSQL and shown per-run in the dashboard. A batch eval endpoint (`POST /api/evals/run`) runs 5 fixed test cases across different domains and returns aggregate pass rates — useful for regression testing when changing prompts or tools.

---

## Setup

### Prerequisites

- Docker Desktop (for PostgreSQL + Redis)
- Python 3.12+
- Node.js 22+
- ngrok (for Telegram webhook in local dev)

### One-command start

```bash
git clone https://github.com/Amanpradhan/anton.git
cd anton
cp .env.example .env
# → Fill in your API keys (see table below)
make run
```

Open:
- **Dashboard:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

### Environment variables

| Variable | Required | Where to get it |
|----------|----------|-----------------|
| `GEMINI_API_KEY` | ✓ | [aistudio.google.com](https://aistudio.google.com) |
| `TELEGRAM_BOT_TOKEN` | ✓ | [@BotFather](https://t.me/BotFather) on Telegram |
| `TELEGRAM_WEBHOOK_URL` | ✓ (for Telegram) | Your ngrok HTTPS URL |
| `TAVILY_API_KEY` | ✓ | [tavily.com](https://tavily.com) (free tier) |
| `LANGCHAIN_API_KEY` | Optional | [smith.langchain.com](https://smith.langchain.com) — enables full LLM tracing |

### Setting up Telegram locally

Telegram requires an HTTPS webhook URL. Use ngrok for local development:

```bash
# Terminal 1 — start the backend
make run

# Terminal 2 — expose port 8000
ngrok http 8000
# → Copy the https://xxxx.ngrok.io URL

# Update .env
TELEGRAM_WEBHOOK_URL=https://xxxx.ngrok.io

# Register the webhook with Telegram (one-time)
curl -X POST http://localhost:8000/api/channels/telegram/setup

# Verify
curl http://localhost:8000/api/channels/telegram/info
```

Now send any message to [@antonflow_bot](https://t.me/antonflow_bot) on Telegram.

### Create your first workflow

```bash
# Instantiate the Competitor Deep Dive template
curl -X POST http://localhost:8000/api/workflows/from-template/competitive_intel
```

Or use the dashboard: **Templates → Competitor Deep Dive → Use this template**

---

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

49 tests. SQLite in-memory, no Docker required. Runs in under 1 second.

```
tests/test_agents.py      11 tests — Agent CRUD, validation
tests/test_workflows.py   11 tests — Workflow CRUD, templates
tests/test_runs.py         6 tests — Run creation, 202 response
tests/test_telegram.py     8 tests — Webhook routing, parse_incoming
tests/test_runtime.py     13 tests — Graph compilation, routing logic, agent nodes, evaluator
```

---

## API reference

```
GET    /api/agents/                         List agents
POST   /api/agents/                         Create agent
GET    /api/agents/{id}                     Get agent
PATCH  /api/agents/{id}                     Update agent
DELETE /api/agents/{id}                     Delete agent

GET    /api/workflows/                      List workflows
POST   /api/workflows/                      Create workflow
GET    /api/workflows/templates             List pre-built templates
POST   /api/workflows/from-template/{id}   Instantiate from template
GET    /api/workflows/{id}                  Get workflow
PATCH  /api/workflows/{id}                  Update workflow
DELETE /api/workflows/{id}                  Delete workflow

GET    /api/runs/                           List runs
POST   /api/runs/                           Trigger run (202 + background)
GET    /api/runs/{id}                       Get run + messages

POST   /api/channels/telegram/webhook       Telegram incoming messages
POST   /api/channels/telegram/setup         Register webhook with Telegram
GET    /api/channels/telegram/info          Check webhook status

POST   /api/evals/run                       Run batch evaluation (5 test cases)
GET    /api/evals/results                   All eval results + aggregate stats
GET    /api/evals/results/{run_id}          Eval for a specific run

WS     /ws/runs/{run_id}                    Real-time run events
```

Full interactive docs at `http://localhost:8000/docs`.

---

## How to extend

### Add a new workflow template

1. Create `backend/app/runtime/templates/my_template.py` with a `TEMPLATE` dict
2. Register it in `backend/app/runtime/templates/__init__.py`
3. It automatically appears in the UI template picker and the API

```python
TEMPLATE = {
    "id": "my_template",
    "name": "My Template",
    "description": "What this workflow does",
    "example_prompt": "An example user request",
    "graph": {
        "nodes": [...],
        "edges": [...],
    },
}
```

### Add a new messaging channel

1. Create `backend/app/channels/my_channel.py` implementing `BaseChannel`:

```python
class MyChannel(BaseChannel):
    async def send_message(self, recipient_id: str, text: str) -> None:
        ...

    async def parse_incoming(self, payload: dict) -> tuple[str | None, str | None]:
        ...
```

2. Add a webhook route in `backend/app/api/routes/channels.py`
3. Register the router in `main.py`

The runner and workflow system require no changes — they work with any channel.

---

## Project structure

```
anton/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers
│   │   ├── channels/            # Telegram + BaseChannel interface
│   │   ├── db/                  # SQLAlchemy engine + session
│   │   ├── models/              # Agent, Workflow, Run, Message, EvalResult
│   │   ├── runtime/
│   │   │   ├── agents/          # orchestrator, researcher, analyst, critic, reporter, evaluator
│   │   │   ├── templates/       # Pre-built workflow definitions
│   │   │   ├── tools/           # Tavily web search
│   │   │   ├── events.py        # Redis pub/sub publisher
│   │   │   ├── graph.py         # LangGraph state + compiled graph
│   │   │   └── runner.py        # Pipeline executor + DB persistence
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── config.py            # Settings from .env
│   │   └── main.py              # FastAPI app + lifespan
│   └── tests/                   # 49 pytest tests
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/
│   │   ├── layout/Sidebar.tsx
│   │   └── workflow/FlowCanvas.tsx  # React Flow canvas
│   ├── lib/
│   │   ├── api.ts               # Typed fetch wrapper
│   │   └── hooks/useWebSocket.ts # Real-time run events
│   └── types/index.ts           # Shared TypeScript types
├── docker-compose.yml           # postgres + redis + backend + frontend
├── Makefile                     # setup / run / stop / test
└── .env.example
```

---

*Built with LangGraph · Gemini · FastAPI · Next.js · PostgreSQL · Redis · Telegram*
