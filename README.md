# pocketquant (Phase 1)

Core API + Rules Engine MVP for strategy-driven portfolio recommendations.

## Features in this phase

- FastAPI backend with SQLite + SQLAlchemy
- Portfolio positions/prices in EUR
- Active strategy with target weights and bands
- Deterministic recommendations:
  - `rebalance`
  - `dca`
  - `noop`
  - `staking_unlock_plan`
  - `staking_claim`
  - `staking_restake`

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3.12 -m pip install --upgrade pip
python3.12 -m pip install -e .
cp .env.example .env
```

## Run API

Uvicorn entrypoint:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or:

```bash
make run-api
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Run tests

```bash
make test
```

## Seed scenario (curl)

1. Add positions:

```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/positions -H 'Content-Type: application/json' -d '{
  "symbol":"BTC","name":"Bitcoin","asset_class":"crypto","account":"spot","amount":1.0
}'

curl -X POST http://127.0.0.1:8000/v1/portfolio/positions -H 'Content-Type: application/json' -d '{
  "symbol":"ETH","name":"Ethereum","asset_class":"crypto","account":"spot","amount":1.0
}'
```

2. Add prices in EUR:

```bash
curl -X POST http://127.0.0.1:8000/v1/portfolio/prices -H 'Content-Type: application/json' -d '{"symbol":"BTC","price_eur":20000}'
curl -X POST http://127.0.0.1:8000/v1/portfolio/prices -H 'Content-Type: application/json' -d '{"symbol":"ETH","price_eur":20000}'
```

3. Create active strategy:

```bash
curl -X POST http://127.0.0.1:8000/v1/strategy -H 'Content-Type: application/json' -d '{
  "name":"Core",
  "base_currency":"EUR",
  "dca_enabled":false,
  "dca_interval_days":7,
  "targets":[
    {"symbol":"BTC","name":"Bitcoin","asset_class":"crypto","target_weight":0.8,"band_min":0.75,"band_max":0.85},
    {"symbol":"ETH","name":"Ethereum","asset_class":"crypto","target_weight":0.2,"band_min":0.15,"band_max":0.25}
  ]
}'
```

4. Generate and list actions:

```bash
curl -X POST http://127.0.0.1:8000/v1/actions/generate
curl http://127.0.0.1:8000/v1/actions
```

## Staking seed scenario (curl)

1. Create staking-aware strategy (targets can be empty for staking-only flow):

```bash
curl -X POST http://127.0.0.1:8000/v1/strategy -H 'Content-Type: application/json' -d '{
  "name":"StakingOnly",
  "base_currency":"EUR",
  "dca_enabled":false,
  "dca_interval_days":7,
  "staking_unlock_window_days":3,
  "staking_min_net_reward_eur":10.0,
  "staking_restake_enabled":true,
  "targets":[]
}'
```

2. Upsert a staking position:

```bash
curl -X POST http://127.0.0.1:8000/v1/staking/positions -H 'Content-Type: application/json' -d '{
  "symbol":"ETH",
  "name":"Ethereum",
  "asset_class":"crypto",
  "provider":"Lido",
  "account":"manual",
  "staked_amount":12.0,
  "apr_percent":4.5,
  "fee_percent":10.0,
  "is_locked":true,
  "unlock_at":"2026-03-06T10:00:00+00:00",
  "next_claim_at":"2026-03-01T10:00:00+00:00",
  "pending_rewards_asset":0.1,
  "pending_rewards_eur":20.0
}'
```

3. Generate and inspect unified action feed:

```bash
curl -X POST http://127.0.0.1:8000/v1/actions/generate
curl http://127.0.0.1:8000/v1/actions
```
