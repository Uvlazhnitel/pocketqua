from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exchange_account import ExchangeAccount


class ExchangeAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_bybit_accounts(self) -> list[ExchangeAccount]:
        query = select(ExchangeAccount).where(ExchangeAccount.is_active.is_(True), ExchangeAccount.exchange == "bybit")
        return list(self.db.execute(query).scalars().all())

    def set_last_sync(self, account: ExchangeAccount, sync_time: datetime | None = None) -> None:
        account.last_sync_at = sync_time or datetime.now(timezone.utc)
        self.db.add(account)
