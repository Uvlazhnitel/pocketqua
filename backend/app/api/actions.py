from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import crud, models
from backend.app.db.base import get_db
from backend.app.db.schemas import ActionOut
from backend.app.services.portfolio_calc import build_portfolio_snapshot, snapshot_weights
from backend.app.services.rule_engine import run_rules

router = APIRouter(prefix="/v1/actions", tags=["actions"])


@router.post("/generate")
def generate_actions(db: Session = Depends(get_db)) -> dict:
    strategy = crud.get_active_strategy(db)
    if not strategy:
        raise HTTPException(status_code=404, detail="active strategy not found")

    targets = crud.get_strategy_targets(db, strategy.id)
    if not targets:
        raise HTTPException(status_code=422, detail="active strategy has no targets")

    snapshot = build_portfolio_snapshot(db)
    weights = snapshot_weights(snapshot)
    actions = run_rules(strategy=strategy, targets=targets, weights=weights)

    created_ids: list[int] = []
    for action in actions:
        rec = crud.create_recommendation(
            db,
            strategy_id=strategy.id,
            action_type=action.action_type,
            title=action.title,
            reason=action.reason,
            payload_json=action.payload_json,
        )
        created_ids.append(rec.id)

    db.commit()
    return {
        "generated": len(created_ids),
        "ids": created_ids,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("", response_model=list[ActionOut])
def list_actions(db: Session = Depends(get_db)) -> list[ActionOut]:
    rows = crud.list_recommendations(db)
    result: list[ActionOut] = []
    for row in rows:
        payload = row.payload_json or {}
        result.append(
            ActionOut(
                id=row.id,
                action_type=row.action_type.value,
                title=row.title,
                reason=row.reason,
                effect=payload.get("effect", ""),
                estimated_cost_eur=payload.get("estimated_cost_eur"),
                risk_note=payload.get("risk_note"),
                calculation=payload.get("calculation", {}),
                created_at=row.created_at,
                status=row.status.value,
            )
        )
    return result
