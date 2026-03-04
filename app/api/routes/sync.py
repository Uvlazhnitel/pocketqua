from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sync import SyncRunResponse
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


def _run_sync_task() -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        service = SyncService(db)
        service.run()
    finally:
        db.close()


@router.post("/run", response_model=SyncRunResponse)
def run_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> SyncRunResponse:
    service = SyncService(db)
    accounts = len(service.accounts_repo.get_active_bybit_accounts())
    started_at = datetime.now(timezone.utc)
    background_tasks.add_task(_run_sync_task)
    return SyncRunResponse(status="accepted", started_at=started_at, accounts=accounts)
