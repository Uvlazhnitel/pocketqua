import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.manual_holding import ManualHolding


class ManualHoldingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def active_for_user(self, user_id: uuid.UUID):
        query = select(ManualHolding).where(ManualHolding.user_id == user_id, ManualHolding.is_active.is_(True))
        return list(self.db.execute(query).scalars().all())
