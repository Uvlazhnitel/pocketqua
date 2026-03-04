# pocketquant (Phase 5, USD-first)

Core API + Rules Engine + Staking Hub + Risk Guardrails + Decision Journal + Telegram Copilot + Data Integrations.

## Features

- FastAPI backend with SQLite + SQLAlchemy
- Portfolio positions/prices in USD
- Strategy targets + deterministic recommendations
- Staking actions (`staking_unlock_plan`, `staking_claim`, `staking_restake`)
- Risk guardrails (asset/provider concentration, drawdown mode, fee guard)
- Decision journal for action status changes
- Telegram commands: `/portfolio`, `/actions`, `/staking`, `/explain <id>`
- Daily + weekly bot digests (in-process scheduler)
- CoinGecko price sync (manual + hourly scheduler)
- CSV positions import endpoint

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3.12 -m pip install --upgrade pip
python3.12 -m pip install -e .
cp .env.example .env
```

## Run API

```bash
make run-api
```

## Run Bot

```bash
make run-bot
```

## Run tests

```bash
make test
```

## CSV positions import

```bash
curl -X POST http://127.0.0.1:8000/v1/import/positions \
  -F "file=@positions.csv" \
  -F "dry_run=false"
```

Expected CSV columns:
- `symbol`
- `name`
- `asset_class`
- `account` (optional)
- `amount`
- `avg_cost_usd` (optional)

## Price sync

Manual trigger:

```bash
curl -X POST http://127.0.0.1:8000/v1/prices/sync
```

Status:

```bash
curl http://127.0.0.1:8000/v1/prices/sync/status
```

Manual override price (priority over auto sync):

```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/prices \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"BTC","price_usd":45000}'
```

## Telegram chat config endpoints

```bash
curl -X POST http://127.0.0.1:8000/v1/telegram/chats/register \
  -H 'Content-Type: application/json' \
  -d '{"chat_id":123456,"timezone":"Europe/Riga","daily_enabled":true,"weekly_enabled":true}'

curl http://127.0.0.1:8000/v1/telegram/chats
```
