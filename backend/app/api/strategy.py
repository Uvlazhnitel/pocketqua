from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import StrategyUpsertIn

router = APIRouter(prefix="/v1/strategy", tags=["strategy"])


@router.post("")
def upsert_strategy(payload: StrategyUpsertIn, db: Session = Depends(get_db)) -> dict:
    strategy = crud.set_active_strategy(db, payload)
    db.commit()
    return {
        "id": strategy.id,
        "name": strategy.name,
        "base_currency": strategy.base_currency,
        "is_active": strategy.is_active,
        "dca_enabled": strategy.dca_enabled,
        "dca_interval_days": strategy.dca_interval_days,
        "staking_unlock_window_days": strategy.staking_unlock_window_days,
        "staking_min_net_reward_usd": strategy.staking_min_net_reward_usd,
        "staking_restake_enabled": strategy.staking_restake_enabled,
        "max_asset_weight": strategy.max_asset_weight,
        "max_provider_weight": strategy.max_provider_weight,
        "drawdown_caution_pct": strategy.drawdown_caution_pct,
        "drawdown_defense_pct": strategy.drawdown_defense_pct,
        "min_trade_value_usd": strategy.min_trade_value_usd,
    }
