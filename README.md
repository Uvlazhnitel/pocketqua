# PocketQuant Backend (Phase 1)

## Run locally

1. Copy env:
```bash
cp .env.example .env
```

2. Install deps:
```bash
pip install -e .[dev]
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start API:
```bash
uvicorn app.main:app --reload
```

## Run with Docker
```bash
docker compose up --build
```

## Endpoints
- `GET /health/live`
- `GET /health/ready`
- `POST /sync/run`
- `GET /summary?user_id=<uuid>`
- `GET /pnl?user_id=<uuid>&start=<iso>&end=<iso>`
- `GET /holdings?user_id=<uuid>`
