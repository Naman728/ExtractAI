# Soft-production deploy (Phase 1)

## What changed

- **Celery on by default** (`USE_CELERY=true`) — API enqueues jobs; **worker** runs Playwright scrapes
- **Prod Docker** — no `--reload`, Next `build`/`start`, Playwright Chromium in backend image
- **403 cascade** — static fetch blocked → automatic Playwright retry (fixes Unsplash-style UI fails)
- **Redis rate limits** — guest/auth per-minute budgets enforced
- **CI** — `.github/workflows/ci.yml` (unit tests + Docker builds)
- **Honest dashboard** — preview banners on mock screens (API keys, scheduler, team, …)

## Run soft-prod locally

```bash
# From repo root — requires .env with DATABASE_* (e.g. Neon) and Redis via Compose
docker compose up --build
```

- API: http://localhost:8100  
- Frontend: http://localhost:3100  
- Worker must be healthy for jobs to run

## Local hot-reload (dev)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Without Docker

```bash
# Terminal 1 — Redis must be up
cd backend && source .venv/bin/activate
export USE_CELERY=true
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8100

# Terminal 2
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO --concurrency=2

# Terminal 3
cd frontend && npm run build && npm run start
```

## Not included (later phases)

- Residential proxies / CAPTCHA solvers  
- Stripe billing  
- Real API keys / scheduler / webhooks  
- S3 storage / Sentry (recommended next ops additions)
