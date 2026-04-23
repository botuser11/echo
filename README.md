# Echo — Public Figure Position Intelligence Engine

**What did they actually say?**

Echo analyses every word spoken in the UK Parliament, extracts political claims using NLP, classifies them across 20 policy topics, and automatically detects when politicians contradict themselves. Every claim links back to the official Hansard record as proof.

🔗 **Live demo:** *Coming soon*
📊 **Current dataset:** 550 MPs · 22,856 speeches · 35,735 claims · 2,141 contradictions detected

---

## What Echo Does

**Search any MP** — Find any member of the UK Parliament and see their complete parliamentary record, AI-extracted claims, and detected contradictions.

**Extract claims automatically** — Echo's NLP pipeline reads parliamentary speeches and identifies specific political claims, commitments, and positions using stance detection and keyword analysis.

**Classify by topic** — Every claim is automatically categorised across 20 policy areas: NHS & Healthcare, Immigration, Economy, Housing, Education, Climate, Crime, Defence, and more.

**Detect contradictions** — When an MP says one thing in February and the opposite in April, Echo catches it. Contradictions are surfaced with both claims side-by-side, dated and sourced.

**Verify everything** — Every speech and claim links directly to the official Hansard page on parliament.uk. Nothing is fabricated — users can verify any claim with one click.

---

## Screenshots

### Landing Page
Dark editorial theme with search-first design. Featured politicians sorted by parliamentary activity.

### MP Profile — Claims Tab
AI-extracted claims with topic badges, dates, and original quotes in context.

### Contradiction Detection
Side-by-side contradiction view showing Claim A vs Claim B with stance labels, dates, and source links.

### Timeline View
Chronological claim evolution grouped by month, showing how positions shift over time.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (React + Vite + Tailwind)      │
│   Search → MP Profiles → Claims → Contradictions     │
└────────────────────────┬────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────┐
│                 BACKEND (FastAPI)                     │
│   /api/persons  /api/search  /api/compare             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│               NLP PIPELINE (Python)                   │
│   Claim Extraction → Topic Classification →           │
│   Stance Detection → Contradiction Detection →        │
│   Embedding Generation (sentence-transformers)        │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│            DATABASE (PostgreSQL + pgvector)            │
│   persons │ speeches │ claims │ topics │ embeddings    │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│           DATA INGESTION (UK Parliament API)           │
│   Members API → Hansard API → Votes API               │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| Database | PostgreSQL with pgvector extension |
| NLP | spaCy, sentence-transformers (all-MiniLM-L6-v2), PyTorch (CPU) |
| Task Queue | Celery + Redis |
| Infrastructure | Docker Compose (4 services) |
| Data Source | UK Parliament Hansard API (Open Parliament Licence) |

---

## NLP Pipeline

Echo's intelligence layer processes parliamentary speeches through four stages:

### 1. Claim Extraction
Identifies sentences containing political claims using stance indicators ("we will", "I believe", "the government has", "we reject") and commitment markers. Each claim is extracted with its surrounding context as the original quote.

### 2. Topic Classification
Classifies claims across 20 UK policy topics using keyword matching against curated topic dictionaries. Topics include NHS & Healthcare, Immigration, Economy & Cost of Living, Housing, Education, Climate & Energy, Crime & Policing, Defence & Security, and more.

### 3. Embedding Generation
Generates semantic embeddings for every claim using `all-MiniLM-L6-v2` (384-dimensional vectors stored in pgvector). Enables semantic search — find claims by meaning, not just keywords.

### 4. Contradiction Detection
Groups claims by person and topic, then identifies pairs where one claim uses positive stance language ("support", "committed", "will deliver") and another uses negative stance language ("oppose", "reject", "wrong") — separated by at least 30 days. Each contradiction includes an auto-generated explanation.

---

## Data Sources

All data is sourced from official UK Parliament APIs under the [Open Parliament Licence](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/):

- **Members API** — `members-api.parliament.uk` — MP and Lords profiles, photos, party data
- **Hansard API** — `hansard-api.parliament.uk` — Full text of every parliamentary speech
- **Commons Votes API** — `commonsvotes-api.parliament.uk` — Division voting records

Every speech in Echo links directly to the corresponding page on `hansard.parliament.uk` for independent verification.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Run locally

```bash
# Clone the repository
git clone https://github.com/botuser11/echo.git
cd echo

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build

# Run database migrations
docker-compose exec backend alembic upgrade head

# Ingest MP data and run NLP pipeline
docker-compose exec backend python -m app.scripts.bootstrap
```

The app will be available at:
- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Bootstrap Process

The bootstrap script automatically:
1. Ingests all current MPs from the Parliament Members API
2. Downloads parliamentary speeches from the Hansard API
3. Runs the NLP pipeline (claim extraction, topic classification, contradiction detection)
4. Is resumable — if interrupted, re-running picks up where it left off

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/persons` | List MPs with search, filter by party/house |
| GET | `/api/persons/{id}` | Full MP profile with stats |
| GET | `/api/persons/{id}/speeches` | Paginated speeches |
| GET | `/api/persons/{id}/claims` | AI-extracted claims |
| GET | `/api/persons/{id}/contradictions` | Detected contradictions |
| GET | `/api/persons/{id}/timeline/{topic}` | Claim timeline by topic |
| GET | `/api/search` | Semantic search across claims |
| GET | `/api/compare` | Compare two MPs on a topic |
| GET | `/api/topics` | Browse all policy topics |
| POST | `/api/admin/ingest/members` | Ingest MPs from Parliament API |
| POST | `/api/admin/pipeline/process-all` | Run NLP pipeline |

---

## Project Context

This project was built as a solo engineering effort to demonstrate applied NLP in a real-world context. The claim extraction and stance detection techniques are informed by academic research in argument mining — specifically, the identification of claims, premises, and rhetorical structure in political discourse.

The project connects academic NLP research to a consumer-facing product, demonstrating:
- **Data engineering** — Ingesting and processing 22,000+ documents from government APIs
- **NLP pipeline design** — Multi-stage text analysis with claim extraction, classification, and contradiction detection
- **Full-stack development** — FastAPI backend, React frontend, PostgreSQL database
- **Production infrastructure** — Docker containerisation, database migrations, resumable data pipelines
- **Product thinking** — Solving a real problem (political accountability) with a usable, shareable interface

---

## Built By

**Karthik Shanmuganathan Valluvar**
MSc Data Science & Engineering — University of Dundee (2025)

- [GitHub](https://github.com/botuser11)
- [LinkedIn](https://linkedin.com/in/your-linkedin) *(update with your actual LinkedIn URL)*

---

## Licence

This project is open source. Parliamentary data is used under the [Open Parliament Licence](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/).
