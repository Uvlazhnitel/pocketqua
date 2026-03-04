from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import PortfolioSummaryOut, PositionUpsertIn, PriceUpsertIn
from backend.app.services.portfolio_calc import build_portfolio_snapshot

router = APIRouter(prefix="/v1/portfolio", tags=["portfolio"])


@router.post("/positions")
def upsert_position(payload: PositionUpsertIn, db: Session = Depends(get_db)) -> dict:
    try:
        position = crud.upsert_position(db, payload)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="failed to upsert position") from exc

    return {
        "id": position.id,
        "symbol": payload.symbol,
        "account": position.account,
        "amount": position.amount,
    }


@router.post("/prices")
def upsert_price(payload: PriceUpsertIn, db: Session = Depends(get_db)) -> dict:
    try:
        price = crud.upsert_price(db, payload)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"id": price.id, "symbol": payload.symbol, "price_usd": price.price_usd}


@router.get("/summary", response_model=PortfolioSummaryOut)
def summary(db: Session = Depends(get_db)) -> PortfolioSummaryOut:
    snapshot = build_portfolio_snapshot(db)
    return PortfolioSummaryOut(**snapshot)
