from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.transactions_ledger import TransactionsLedger
from app.repositories.ledger_repository import LedgerRepository


def _event(event_id: str):
    return TransactionsLedger(
        exchange_account_id=uuid4(),
        external_event_id=event_id,
        event_type="trade",
        asset_symbol="BTC",
        amount=Decimal("1"),
        amount_usd=Decimal("10"),
        fee_amount=Decimal("0.1"),
        fee_asset_symbol="USDT",
        event_ts=datetime.now(timezone.utc),
        source="bybit_transaction_log",
        source_payload={},
        created_at=datetime.now(timezone.utc),
    )


def test_insert_idempotent_skips_existing_events():
    db = MagicMock()
    existing_event = _event("ev-1")
    new_event = _event("ev-2")

    db.execute.return_value.all.return_value = [
        (existing_event.exchange_account_id, existing_event.source, existing_event.external_event_id)
    ]

    repo = LedgerRepository(db)
    inserted = repo.insert_idempotent([existing_event, new_event])

    assert inserted == 1
    db.add_all.assert_called_once()
    inserted_events = db.add_all.call_args[0][0]
    assert len(inserted_events) == 1
    assert inserted_events[0].external_event_id == "ev-2"
