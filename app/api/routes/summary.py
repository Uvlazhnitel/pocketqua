import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.summary import SummaryResponse
from app.services.summary_service import SummaryService

router = APIRouter(tags=["summary"])


@router.get("/summary", response_model=SummaryResponse)
def get_summary(user_id: uuid.UUID, db: Session = Depends(get_db)) -> SummaryResponse:
    return SummaryService(db).get_summary(user_id)
