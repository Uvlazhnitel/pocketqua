from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import PriceSyncRunOut, PriceSyncStatusOut
from backend.app.services.price_sync import run_price_sync

router = APIRouter(prefix="/v1/prices", tags=["prices"])


@router.post("/sync", response_model=PriceSyncRunOut)
def sync_prices(db: Session = Depends(get_db)) -> PriceSyncRunOut:
    result = run_price_sync(db)
    db.commit()
    return PriceSyncRunOut(**result)


@router.get("/sync/status", response_model=PriceSyncStatusOut)
def sync_status(request: Request, db: Session = Depends(get_db)) -> PriceSyncStatusOut:
    row = crud.get_latest_price_sync_run(db)
    latest = None
    if row is not None:
        latest = {
            "id": row.id,
            "started_at": row.started_at.isoformat(),
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            "status": row.status.value,
            "updated_assets_count": row.updated_assets_count,
            "error_count": row.error_count,
            "error_summary": row.error_summary,
        }

    next_scheduled_at = None
    scheduler = getattr(request.app.state, "price_sync_scheduler", None)
    if scheduler is not None:
        job = scheduler.get_job("prices_sync_job")
        if job and job.next_run_time is not None:
            next_scheduled_at = job.next_run_time.isoformat()

    return PriceSyncStatusOut(latest_run=latest, next_scheduled_at=next_scheduled_at)
