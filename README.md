# ExtractAI

Intelligent Web Data Extraction Platform — profile any site, score strategies, extract structured data.

> **Soft-production (Phase 1 ops):** Celery workers, Playwright in Docker, 403→browser cascade, Redis rate limits, CI, honest dashboard previews. See [`docs/SOFT_PRODUCTION.md`](docs/SOFT_PRODUCTION.md).

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind, React Query, Framer Motion |
| API | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Workers | Celery + Redis (**required** when `USE_CELERY=true`) |
| DB | PostgreSQL 16 (Neon or Compose `--profile local-db`) |
| Storage | Local filesystem (`StorageBackend` → S3 later) |

## Quick start

1. Copy env:

```bash
cp .env.example .env
# Set DATABASE_URL / DATABASE_URL_SYNC (Neon) and a strong JWT_SECRET_KEY
```

2. Soft-prod stack (API + **worker** + frontend + Redis):

```bash
docker compose up --build
```

- API: http://localhost:8100/docs  
- Frontend: http://localhost:3100  
- Health: http://localhost:8100/health  

Hot-reload local override:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

3. Or run backend locally against Compose Redis:

```bash
docker compose up -d redis
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8100
# other terminal:
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

```bash
cd frontend && npm install && npm run dev
```

## Guest + auth model

- Anonymous users: send / receive `X-Guest-Key`; default **3** free jobs (`GUEST_JOB_LIMIT`).
- Registered users: JWT access + refresh; full job history, retry, delete.
- Exports (later phase) require auth.

## API (Phase 2)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health`, `/ready` | Liveness / readiness |
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh |
| POST | `/api/v1/auth/logout` | Revoke refresh |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/guest/session` | Create/resume guest |
| POST | `/api/v1/jobs` | Create job (auth optional) |
| GET | `/api/v1/jobs` | List (auth required) |
| GET | `/api/v1/jobs/{id}` | Get (owner or guest) |
| DELETE | `/api/v1/jobs/{id}` | Soft delete (auth) |
| POST | `/api/v1/jobs/{id}/retry` | Retry (auth) |

| POST | `/api/v1/intelligence/analyze` | Website profile (no extraction) |
| GET | `/api/v1/intelligence/{id}` | Fetch saved profile |

Jobs currently complete the Celery **foundation stub** with `PIPELINE_NOT_READY` until Phase 4+ engines ship. Intelligence analysis is live.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the Phase 1.1 platform design (Intelligence, Discovery, Strategy, Plugins, Normalization, Validation, Network Inspector, Snapshots, Dev Platform, Observability).

## Roadmap

1. ~~Architecture~~  
2. ~~Foundation~~  
3. ~~Website Intelligence + Discovery~~  
4. ~~Strategy Engine + Execution Plans~~  
5. ~~Traditional extraction pipeline (fetch/plugins/normalize/validate/results)~~  
6. Playwright hardening + Network Inspector + Snapshots polish  
7. Full UI polish / billing / AI adapters  

## License

Proprietary — all rights reserved.
