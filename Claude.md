# Echo — Public Figure Position Intelligence Engine

## What this project is
An AI-powered platform that analyses UK parliamentary speeches, extracts claims and positions, tracks how politicians' stances evolve over time, and detects contradictions. All sourced, all cited.

## Tech stack
- Frontend: React 18 + Vite + TypeScript + Tailwind CSS
- Backend: FastAPI (Python 3.11+) + SQLAlchemy + Alembic
- Database: PostgreSQL + pgvector
- Task queue: Celery + Redis
- Containerised with Docker Compose

## Current status
Phase 1: Project scaffolding — ✅ COMPLETE
Phase 2: Database models & migrations — ✅ COMPLETE
Phase 3: Data ingestion — ✅ COMPLETE (1512 members, speeches for key MPs)

## What's next
Phase 4: Public API endpoints (search, person profile, claims, compare)