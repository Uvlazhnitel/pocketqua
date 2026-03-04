from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db import crud, models
from backend.app.db.base import get_db
from backend.app.db.schemas import ActionOut, ActionStatusUpdateIn
from backend.app.services.portfolio_calc import build_portfolio_snapshot, snapshot_weights
from backend.app.services.risk_mode import calculate_risk_state
from backend.app.services.rule_engine import run_rules

router = APIRouter(prefix="/v1/actions", tags=["actions"])


@router.post("/generate")
def generate_actions(db: Session = Depends(get_db)) -> dict:
    strategy = crud.get_active_strategy(db)
    if not strategy:
        raise HTTPException(status_code=404, detail="active strategy not found")

    targets = crud.get_strategy_targets(db, strategy.id)
    staking_positions = crud.list_staking_positions(db)

    snapshot = build_portfolio_snapshot(db)
    weights = snapshot_weights(snapshot)
    price_by_symbol = crud.get_prices_by_symbol(db)

    latest_snapshot = crud.get_latest_portfolio_snapshot(db)
    peak_value_usd, drawdown_pct, risk_mode, previous_risk_mode = calculate_risk_state(
        current_total_value_usd=snapshot["total_value_usd"],
        previous_snapshot=latest_snapshot,
        strategy=strategy,
    )

    crud.create_portfolio_snapshot(
        db,
        total_value_usd=snapshot["total_value_usd"],
        peak_value_usd=peak_value_usd,
        drawdown_pct=drawdown_pct,
        risk_mode=risk_mode,
    )

    actions = run_rules(
        strategy=strategy,
        targets=targets,
        weights=weights,
        staking_positions=staking_positions,
        total_value_usd=snapshot["total_value_usd"],
        price_by_symbol=price_by_symbol,
        risk_mode=risk_mode,
        previous_risk_mode=previous_risk_mode,
    )

    if not targets and len(actions) == 1 and actions[0].action_type == models.ActionType.NOOP:
        raise HTTPException(
            status_code=422,
            detail="active strategy has no targets and no staking/risk actions",
        )

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
def list_actions(
    status: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ActionOut]:
    parsed_status = None
    if status is not None:
        try:
            parsed_status = models.RecommendationStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid status") from exc

    rows = crud.list_recommendations(db, status=parsed_status, limit=limit)
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
                estimated_cost_usd=payload.get("estimated_cost_usd"),
                risk_note=payload.get("risk_note"),
                calculation=payload.get("calculation", {}),
                created_at=row.created_at,
                status=row.status.value,
            )
        )
    return result


@router.get("/{action_id}", response_model=ActionOut)
def get_action(action_id: int, db: Session = Depends(get_db)) -> ActionOut:
    row = crud.get_recommendation(db, action_id)
    if row is None:
        raise HTTPException(status_code=404, detail="action not found")
    payload = row.payload_json or {}
    return ActionOut(
        id=row.id,
        action_type=row.action_type.value,
        title=row.title,
        reason=row.reason,
        effect=payload.get("effect", ""),
        estimated_cost_usd=payload.get("estimated_cost_usd"),
        risk_note=payload.get("risk_note"),
        calculation=payload.get("calculation", {}),
        created_at=row.created_at,
        status=row.status.value,
    )


@router.post("/{action_id}/status", response_model=ActionOut)
def update_action_status(
    action_id: int,
    payload: ActionStatusUpdateIn,
    db: Session = Depends(get_db),
) -> ActionOut:
    row = crud.update_recommendation_status(db, action_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="action not found")
    db.commit()

    data = row.payload_json or {}
    return ActionOut(
        id=row.id,
        action_type=row.action_type.value,
        title=row.title,
        reason=row.reason,
        effect=data.get("effect", ""),
        estimated_cost_usd=data.get("estimated_cost_usd"),
        risk_note=data.get("risk_note"),
        calculation=data.get("calculation", {}),
        created_at=row.created_at,
        status=row.status.value,
    )
