from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import StakingPositionOut, StakingPositionPatchIn, StakingPositionUpsertIn

router = APIRouter(prefix="/v1/staking", tags=["staking"])


def _to_out(row) -> StakingPositionOut:
    return StakingPositionOut(
        id=row.id,
        symbol=row.asset.symbol,
        provider=row.provider,
        account=row.account,
        staked_amount=row.staked_amount,
        apr_percent=row.apr_percent,
        fee_percent=row.fee_percent,
        lockup_days=row.lockup_days,
        unbonding_days=row.unbonding_days,
        is_locked=row.is_locked,
        unlock_at=row.unlock_at,
        next_claim_at=row.next_claim_at,
        pending_rewards_asset=row.pending_rewards_asset,
        pending_rewards_usd=row.pending_rewards_usd,
        last_updated_at=row.last_updated_at,
    )


@router.post("/positions", response_model=StakingPositionOut)
def upsert_staking_position(
    payload: StakingPositionUpsertIn, db: Session = Depends(get_db)
) -> StakingPositionOut:
    row = crud.upsert_staking_position(db, payload)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.get("/positions", response_model=list[StakingPositionOut])
def list_staking_positions(
    limit: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[StakingPositionOut]:
    rows = crud.list_staking_positions(db)
    if limit is not None:
        rows = rows[:limit]
    return [_to_out(row) for row in rows]


@router.patch("/positions/{staking_position_id}", response_model=StakingPositionOut)
def patch_staking_position(
    staking_position_id: int,
    payload: StakingPositionPatchIn,
    db: Session = Depends(get_db),
) -> StakingPositionOut:
    row = crud.patch_staking_position(db, staking_position_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="staking position not found")
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/positions/{staking_position_id}")
def delete_staking_position(staking_position_id: int, db: Session = Depends(get_db)) -> dict:
    deleted = crud.delete_staking_position(db, staking_position_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="staking position not found")
    db.commit()
    return {"deleted": True, "id": staking_position_id}
