# pocketquant (Phase 4, USD-first)

Core API + Rules Engine + Staking Hub + Risk Guardrails + Decision Journal + Telegram Copilot.

## Features

- FastAPI backend with SQLite + SQLAlchemy
- Portfolio positions/prices in USD
- Strategy targets + deterministic recommendations
- Staking actions (`staking_unlock_plan`, `staking_claim`, `staking_restake`)
- Risk guardrails (asset/provider concentration, drawdown mode, fee guard)
- Decision journal for action status changes
- Telegram commands: `/portfolio`, `/actions`, `/staking`, `/explain <id>`
- Daily + weekly digest scheduler (in-process, local timezone)

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

Bot requires:
- `TELEGRAM_BOT_TOKEN`
- `BACKEND_BASE_URL`
- `BOT_TIMEZONE`
- `DAILY_DIGEST_HOUR`
- `WEEKLY_DIGEST_WEEKDAY`

## Run tests

```bash
make test
```

## Quick USD seed flow

```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/positions -H 'Content-Type: application/json' -d '{"symbol":"BTC","name":"Bitcoin","asset_class":"crypto","account":"spot","amount":1.0}'
curl -X POST http://127.0.0.1:8000/v1/portfolio/prices -H 'Content-Type: application/json' -d '{"symbol":"BTC","price_usd":10000}'

curl -X POST http://127.0.0.1:8000/v1/strategy -H 'Content-Type: application/json' -d '{
  "name":"USD Strategy",
  "base_currency":"USD",
  "max_asset_weight":0.6,
  "max_provider_weight":0.5,
  "drawdown_caution_pct":0.1,
  "drawdown_defense_pct":0.2,
  "min_trade_value_usd":50,
  "targets":[{"symbol":"BTC","name":"Bitcoin","asset_class":"crypto","target_weight":0.5,"band_min":0.4,"band_max":0.6}]
}'

curl -X POST http://127.0.0.1:8000/v1/staking/positions -H 'Content-Type: application/json' -d '{
  "symbol":"ETH","name":"Ethereum","asset_class":"crypto","provider":"Lido","account":"manual",
  "staked_amount":12.0,"apr_percent":4.5,"fee_percent":10.0,
  "is_locked":true,"unlock_at":"2026-03-06T10:00:00+00:00",
  "next_claim_at":"2026-03-01T10:00:00+00:00",
  "pending_rewards_asset":0.1,"pending_rewards_usd":20.0
}'

curl -X POST http://127.0.0.1:8000/v1/actions/generate
curl 'http://127.0.0.1:8000/v1/actions?status=new&limit=5'
curl http://127.0.0.1:8000/v1/risk/summary
```

## Decision journal flow

```bash
curl -X POST http://127.0.0.1:8000/v1/actions/1/status -H 'Content-Type: application/json' -d '{"new_status":"done","note":"executed"}'
curl http://127.0.0.1:8000/v1/journal
```

## Telegram chat config endpoints

```bash
curl -X POST http://127.0.0.1:8000/v1/telegram/chats/register -H 'Content-Type: application/json' -d '{"chat_id":123456,"timezone":"Europe/Riga","daily_enabled":true,"weekly_enabled":true}'
curl http://127.0.0.1:8000/v1/telegram/chats
```
