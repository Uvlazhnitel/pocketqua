from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import DecisionJournalOut

router = APIRouter(prefix="/v1/journal", tags=["journal"])


@router.get("", response_model=list[DecisionJournalOut])
def list_journal(db: Session = Depends(get_db)) -> list[DecisionJournalOut]:
    rows = crud.list_decision_journal(db)
    return [
        DecisionJournalOut(
            id=row.id,
            recommendation_id=row.recommendation_id,
            old_status=row.old_status.value,
            new_status=row.new_status.value,
            note=row.note,
            created_at=row.created_at,
        )
        for row in rows
    ]
