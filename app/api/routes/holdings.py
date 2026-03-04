import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.holdings import HoldingsResponse
from app.services.holdings_service import HoldingsService

router = APIRouter(tags=["holdings"])


@router.get("/holdings", response_model=HoldingsResponse)
def get_holdings(user_id: uuid.UUID, db: Session = Depends(get_db)) -> HoldingsResponse:
    return HoldingsService(db).get_holdings(user_id=user_id)
