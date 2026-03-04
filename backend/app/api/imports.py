from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.db.base import get_db
from backend.app.db.schemas import PositionsImportOut
from backend.app.services.csv_import import import_positions_csv

router = APIRouter(prefix="/v1/import", tags=["import"])


@router.post("/positions", response_model=PositionsImportOut)
async def import_positions(
    file: UploadFile = File(...),
    dry_run: bool = Form(default=False),
    db: Session = Depends(get_db),
) -> PositionsImportOut:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="file must be a .csv")

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="csv must be utf-8 encoded") from exc

    result = import_positions_csv(db=db, content=content, dry_run=dry_run)

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return PositionsImportOut(**result)
