# Multilingual GenAI Evaluation & Moderation Gateway

A shared gateway service for running, evaluating, and moderating LLM outputs across multiple languages. Send a prompt name, input, and locale — get back a structured evaluation report with pass/fail across quality, hallucination, moderation, and world-readiness checks.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Dashboard (:5173)                      │
│  ┌──────────┐ ┌───────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Overview  │ │PromptHistory  │ │EvalRunDetail │ │  CI History   │  │
│  │(badges,   │ │(charts, diff, │ │(scores,      │ │(regressions, │  │
│  │ stats)    │ │ versions)     │ │ reasoning)   │ │ details)     │  │
│  └──────────┘ └───────────────┘ └──────────────┘ └──────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ /api/*
┌────────────────────────────▼────────────────────────────────────────┐
│                      FastAPI Backend (:8000)                         │
│                                                                     │
│  ┌─────────────┐  ┌──────────────────────────────────────────────┐  │
│  │   Prompt     │  │            Gateway Pipeline                  │  │
│  │  Registry    │  │                                              │  │
│  │ (versions,   │  │  Input ──► Generate ──► Quality Judge ───┐   │  │
│  │  dedup,      │  │            (Sonnet)    (Sonnet, 0-1)     │   │  │
│  │  labels,     │  │                                          ▼   │  │
│  │  rollback,   │  │                        Hallucination ◄───┘   │  │
│  │  diff)       │  │                        Judge (Sonnet, 0-1)   │  │
│  └─────────────┘  │                              │                │  │
│                    │                              ▼                │  │
│  ┌─────────────┐  │                        Moderation             │  │
│  │  Golden      │  │                        (Haiku, fail-closed)  │  │
│  │  Sets        │  │                              │                │  │
│  └─────────────┘  │                              ▼                │  │
│                    │                      World-Readiness          │  │
│  ┌─────────────┐  │                      (per-locale checks)     │  │
│  │  CI Gate     │  │                              │                │  │
│  │ (regression  │  │                              ▼                │  │
│  │  detection)  │  │                     EvalRun (persisted)      │  │
│  └─────────────┘  └──────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  PostgreSQL     │
                    │  (5 tables)     │
                    └─────────────────┘
```

## Supported Locales

| Locale | Language | World-Readiness Checks |
|--------|----------|----------------------|
| `en-US` | American English | Latin script, no foreign script leaks, US number/date format |
| `es-MX` | Mexican Spanish | Latin + diacritics (á,é,í,ó,ú,ñ), no foreign script leaks |
| `ar-SA` | Saudi Arabic | Arabic script, RTL direction, untranslated English detection |
| `ja-JP` | Japanese | CJK script (Hiragana/Katakana/Kanji), untranslated English detection |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An Anthropic API key (for live LLM calls; seed data works without one)

### 1. Clone and configure

```bash
git clone https://github.com/shyam-kannan/Multilingual_GenAI_Evaluation.git
cd Multilingual_GenAI_Evaluation
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Start services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **FastAPI backend** on port 8000 (with auto-migration)
- **React frontend** on port 5173

### 3. Seed demo data

```bash
# With Docker
docker compose exec backend python /app/../scripts/seed.py

# Or locally (with backend running)
pip install requests
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eval_gateway python scripts/seed.py
```

### 4. Open the dashboard

Visit **http://localhost:5173** to see:
- Overview with per-locale pass rates
- Prompt version history with quality charts
- Eval run details with judge reasoning
- CI history with regression details

## API Reference

### Health
```
GET /health → {"status": "ok", "version": "1.0.0"}
```

### Prompts
```
POST   /api/prompts                                     Create prompt
GET    /api/prompts                                     List prompts
GET    /api/prompts/{id}                                Get prompt + versions
POST   /api/prompts/{id}/versions                       Create version (dedup check)
PATCH  /api/prompts/{id}/versions/{vid}/activate        Set active
PATCH  /api/prompts/{id}/versions/{vid}/labels          Update labels
POST   /api/prompts/{id}/rollback/{vid}                 Rollback
GET    /api/prompts/{id}/diff/{v1_id}/{v2_id}           Diff two versions
```

### Golden Sets
```
POST   /api/golden-sets                   Create example
GET    /api/golden-sets?prompt_id=&locale= List (filterable)
PUT    /api/golden-sets/{id}              Update
DELETE /api/golden-sets/{id}              Delete
```

### Gateway
```
POST /api/gateway/run
Body: {"prompt_name": "...", "input": "...", "locale": "en-US", "version_id": "optional"}
→ Runs full pipeline: generate → quality judge → hallucination judge → moderation → world-readiness
→ Returns: eval_run_id, scores, pass/fail, detailed report
```

### Eval Runs
```
GET /api/eval-runs?locale=&passed=&limit=    List with filters
GET /api/eval-runs/{id}                      Full detail
```

### CI Gate
```
POST /api/ci/check
Body: {"prompt_name": "...", "locales": ["en-US", "es-MX", "ar-SA", "ja-JP"]}
→ Compares candidate vs production baseline using golden examples
→ Fails if quality drops >10% or hallucination rises >10% in any locale
```

### Dashboard
```
GET /api/dashboard/overview                Per-locale stats, recent runs
GET /api/dashboard/prompts/{id}/history    Score trends across versions
GET /api/dashboard/ci-history              Recent CI runs
```

## Pass/Fail Thresholds

| Check | Threshold | Direction |
|-------|-----------|-----------|
| Quality | ≥ 0.7 | Higher is better |
| Hallucination | ≤ 0.3 | Lower is better |
| Moderation | pass/fail | Fail-closed (errors = blocked) |
| World-Readiness | pass/fail | Per-locale script/format checks |
| CI Regression | Δ > 0.1 | Any locale score drop blocks |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL 16 |
| LLM | Anthropic Claude (Sonnet for generation/judging, Haiku for moderation) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Recharts |
| i18n | babel, langdetect, python-bidi |
| Testing | pytest (79 tests), Vitest (11 tests) |
| CI/CD | GitHub Actions (3 jobs: backend, frontend, prompt regression) |
| Infra | Docker Compose |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI app + CORS
│   │   ├── config.py            Pydantic Settings
│   │   ├── database.py          SQLAlchemy engine
│   │   ├── models/              5 DB models
│   │   ├── schemas/             Pydantic request/response schemas
│   │   ├── routers/             7 route modules
│   │   ├── services/            LLM, judge, moderator, world-readiness, CI gate
│   │   └── utils/               Content hashing
│   ├── alembic/                 Database migrations
│   └── tests/                   79 pytest tests
├── frontend/
│   ├── src/
│   │   ├── pages/               4 pages (Overview, PromptHistory, EvalRunDetail, CIHistory)
│   │   ├── components/          6 components (Layout, LocaleBadge, ScoreChart, etc.)
│   │   ├── api/                 Typed API client
│   │   └── types/               TypeScript interfaces
│   └── tests/                   11 Vitest tests
├── scripts/
│   └── seed.py                  Demo data seeder (24+ eval runs)
├── .github/workflows/ci.yml    GitHub Actions CI pipeline
└── docker-compose.yml           3-service orchestration
```

## Running Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npx vitest run
```

## License

MIT
