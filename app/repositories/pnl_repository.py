import uuid
from datetime import datetime

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from app.models.exchange_account import ExchangeAccount
from app.models.transactions_ledger import TransactionsLedger
from app.models.wallet_snapshot import WalletSnapshot


class PnLRepository:
    def __init__(self, db: Session):
        self.db = db

    def ledger_events(self, user_id: uuid.UUID, start: datetime | None = None, end: datetime | None = None):
        query: Select = (
            select(TransactionsLedger)
            .join(ExchangeAccount, ExchangeAccount.id == TransactionsLedger.exchange_account_id)
            .where(ExchangeAccount.user_id == user_id)
        )
        if start:
            query = query.where(TransactionsLedger.event_ts >= start)
        if end:
            query = query.where(TransactionsLedger.event_ts <= end)

        query = query.order_by(TransactionsLedger.event_ts.asc(), TransactionsLedger.created_at.asc())
        return list(self.db.execute(query).scalars().all())

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
                and_(
                    WalletSnapshot.exchange_account_id == latest_ts_subq.c.exchange_account_id,
                    WalletSnapshot.snapshot_ts == latest_ts_subq.c.max_ts,
                ),
            )
            .join(ExchangeAccount, ExchangeAccount.id == WalletSnapshot.exchange_account_id)
            .where(ExchangeAccount.user_id == user_id)
        )
        return list(self.db.execute(query).scalars().all())
