from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.transactions_ledger import TransactionsLedger


class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    def insert_idempotent(self, events: list[TransactionsLedger]) -> int:
        if not events:
            return 0

        filters = [
            and_(
                TransactionsLedger.exchange_account_id == event.exchange_account_id,
                TransactionsLedger.source == event.source,
                TransactionsLedger.external_event_id == event.external_event_id,
            )
            for event in events
        ]

        existing_query = select(
            TransactionsLedger.exchange_account_id,
            TransactionsLedger.source,
            TransactionsLedger.external_event_id,
        ).where(or_(*filters))
        existing = set(self.db.execute(existing_query).all())

        to_insert = [
            event
            for event in events
            if (event.exchange_account_id, event.source, event.external_event_id) not in existing
        ]

        if to_insert:
            self.db.add_all(to_insert)

        return len(to_insert)
