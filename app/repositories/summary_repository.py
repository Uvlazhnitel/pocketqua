import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.exchange_account import ExchangeAccount
from app.models.manual_holding import ManualHolding
from app.models.wallet_snapshot import WalletSnapshot


class SummaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def latest_wallet_rows(self, user_id: uuid.UUID):
        latest_ts_subq = (
            select(
                WalletSnapshot.exchange_account_id,
                func.max(WalletSnapshot.snapshot_ts).label("max_ts"),
            )
            .join(ExchangeAccount, ExchangeAccount.id == WalletSnapshot.exchange_account_id)
            .where(ExchangeAccount.user_id == user_id)
            .group_by(WalletSnapshot.exchange_account_id)
            .subquery()
        )

        query: Select = (
            select(WalletSnapshot)
            .join(
                latest_ts_subq,
                (WalletSnapshot.exchange_account_id == latest_ts_subq.c.exchange_account_id)
                & (WalletSnapshot.snapshot_ts == latest_ts_subq.c.max_ts),
            )
            .join(ExchangeAccount, ExchangeAccount.id == WalletSnapshot.exchange_account_id)
            .where(ExchangeAccount.user_id == user_id)
        )
        return list(self.db.execute(query).scalars().all())

    def manual_holdings(self, user_id: uuid.UUID):
        query = select(ManualHolding).where(ManualHolding.user_id == user_id, ManualHolding.is_active.is_(True))
        return list(self.db.execute(query).scalars().all())

    def user_last_sync(self, user_id: uuid.UUID):
        query = select(func.max(ExchangeAccount.last_sync_at)).where(ExchangeAccount.user_id == user_id)
        return self.db.execute(query).scalar_one_or_none()
