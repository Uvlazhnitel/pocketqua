import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pnl import PnLResponse
from app.services.pnl_service import PnLService

router = APIRouter(tags=["pnl"])


@router.get("/pnl", response_model=PnLResponse)
def get_pnl(
    user_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
) -> PnLResponse:
    return PnLService(db).get_pnl(user_id=user_id, start=start, end=end)
