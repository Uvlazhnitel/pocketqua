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
    }
