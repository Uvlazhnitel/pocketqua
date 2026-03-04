from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import TelegramChatOut, TelegramChatRegisterIn, TelegramChatToggleIn

router = APIRouter(prefix="/v1/telegram", tags=["telegram"])


def _to_out(row) -> TelegramChatOut:
    return TelegramChatOut(
        id=row.id,
        chat_id=row.chat_id,
        timezone=row.timezone,
        daily_enabled=row.daily_enabled,
        weekly_enabled=row.weekly_enabled,
        last_daily_sent_at=row.last_daily_sent_at,
        last_weekly_sent_at=row.last_weekly_sent_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/chats/register", response_model=TelegramChatOut)
def register_chat(payload: TelegramChatRegisterIn, db: Session = Depends(get_db)) -> TelegramChatOut:
    row = crud.register_telegram_chat(
        db,
        chat_id=payload.chat_id,
        timezone=payload.timezone,
        daily_enabled=payload.daily_enabled,
        weekly_enabled=payload.weekly_enabled,
    )
    db.commit()
    return _to_out(row)


@router.patch("/chats/{chat_id}", response_model=TelegramChatOut)
def patch_chat(chat_id: int, payload: TelegramChatToggleIn, db: Session = Depends(get_db)) -> TelegramChatOut:
    row = crud.update_telegram_chat(
        db,
        chat_id=chat_id,
        timezone=payload.timezone,
        daily_enabled=payload.daily_enabled,
        weekly_enabled=payload.weekly_enabled,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="chat not found")
    db.commit()
    return _to_out(row)


@router.get("/chats", response_model=list[TelegramChatOut])
def list_chats(db: Session = Depends(get_db)) -> list[TelegramChatOut]:
    rows = crud.list_telegram_chats(db)
    return [_to_out(row) for row in rows]


@router.post("/chats/{chat_id}/mark-daily")
def mark_daily(chat_id: int, db: Session = Depends(get_db)) -> dict:
    crud.mark_daily_sent(db, chat_id=chat_id)
    db.commit()
    return {"ok": True}


@router.post("/chats/{chat_id}/mark-weekly")
def mark_weekly(chat_id: int, db: Session = Depends(get_db)) -> dict:
    crud.mark_weekly_sent(db, chat_id=chat_id)
    db.commit()
    return {"ok": True}
