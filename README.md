# Anton

> Autonomous multi-agent competitive intelligence platform. Configure teams of AI agents that research, analyze, and deliver insights — while you watch them collaborate in real time.

Named after the *Silicon Valley* reference. Built as an AI Engineer hiring challenge for Yuno.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Anton Platform                    │
│                                                     │
│  ┌──────────┐    ┌──────────────────────────────┐  │
│  │ Next.js  │◄──►│        FastAPI Backend        │  │
│  │  Web UI  │    │                              │  │
│  │          │    │  ┌────────┐  ┌────────────┐  │  │
│  │ Dashboard│    │  │Agents  │  │  LangGraph │  │  │
│  │ Workflow │    │  │  API   │  │  Runtime   │  │  │
│  │ Builder  │    │  └────────┘  └────────────┘  │  │
│  │ Monitor  │    │       │            │          │  │
│  └──────────┘    │  ┌────▼────────────▼──────┐  │  │
│                  │  │      Redis Pub/Sub       │  │  │
│                  │  │  (async message bus)     │  │  │
│                  │  └────────────┬─────────────┘  │  │
│                  │               │                │  │
│                  │  ┌────────────▼─────────────┐  │  │
│                  │  │       PostgreSQL          │  │  │
│                  │  │  agents, workflows, runs  │  │  │
│                  │  └──────────────────────────┘  │  │
│                  └──────────────────────────────┘  │
│                            │                       │
│                  ┌─────────▼──────────┐            │
│                  │   Telegram Bot     │            │
│                  │  (external input)  │            │
│                  └────────────────────┘            │
└─────────────────────────────────────────────────────┘
```

## Tech Stack & Decisions

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Python + FastAPI | Best AI/ML ecosystem, async-native, fast iteration |
| AI Framework | LangGraph | Stateful graphs, conditional edges, cycles — ideal for multi-agent CI pipelines |
| LLM | Gemini 2.5 Pro (orchestrator) + 2.5 Flash (workers) | Cost optimization: heavy reasoning where needed, fast+cheap for workers |
| Frontend | Next.js + React Flow | Visual workflow builder, server components, great DX |
| Database | PostgreSQL | Production-grade, rich querying for run history |
| Message Queue | Redis Pub/Sub | Async agent-to-agent communication without blocking |
| Messaging | Telegram Bot API | Zero friction, excellent webhook API, no business approval needed |
| Search Tool | Tavily API | Built specifically for LLM agents, clean structured results |
| Containers | Docker Compose | Single-command local setup |

### Why LangGraph over CrewAI / AutoGen?

- **LangGraph** gives you explicit control over the state graph — you define nodes, edges, and conditions. It's transparent and debuggable.
- **CrewAI** is higher-level but abstracts too much; harder to customize routing logic.
- **AutoGen** is great for conversational agents but not ideal for structured pipelines with conditional feedback loops.

For a CI pipeline where a Critic agent can send work back to the Researcher, LangGraph's cyclic graph support is exactly the right primitive.

---

## Setup

### Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 22+

### Run locally

```bash
git clone https://github.com/Amanpradhan/anton.git
cd anton
make setup   # creates .env, builds containers
# → Fill in API keys in .env
make run     # starts all services
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Environment variables

Copy `.env.example` to `.env` and fill in:

| Key | Where to get it |
|-----|----------------|
| `GEMINI_API_KEY` | Google AI Studio |
| `TELEGRAM_BOT_TOKEN` | @BotFather on Telegram |
| `TELEGRAM_WEBHOOK_URL` | Your ngrok URL (for local dev) |
| `TAVILY_API_KEY` | tavily.com |

---

## How to extend

### Add a new workflow template
1. Create a new graph definition in `backend/app/runtime/templates/`
2. Register it in `backend/app/runtime/templates/__init__.py`
3. It appears automatically in the UI template picker

### Add a new messaging channel
1. Create a new adapter in `backend/app/channels/` implementing `BaseChannel`
2. Register a new webhook route in `backend/app/api/routes/channels.py`
3. Link agents to the new channel type via the UI

---

## Demo Workflow

User → Telegram: *"Analyze payment processors entering LATAM"*

1. Orchestrator receives message, decomposes task
2. Researcher agent runs parallel web searches via Tavily
3. Analyst agent synthesizes findings
4. Critic agent reviews, flags unverified claims
5. Researcher re-runs targeted searches
6. Reporter agent generates structured report
7. Orchestrator delivers summary via Telegram

Total: ~45 seconds · Cost: ~$0.05

---

*Yuno AI Engineer Hiring Challenge · Built with LangGraph + Gemini + FastAPI + Next.js*
