from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.models.transactions_ledger import TransactionsLedger
from app.services.ledger_normalizer import classify_kind, normalize_event


def _event(event_type: str, fee_asset: str | None = "USDT") -> TransactionsLedger:
    return TransactionsLedger(
        exchange_account_id=uuid4(),
        external_event_id="evt-1",
        event_type=event_type,
        asset_symbol="ETH",
        amount=Decimal("1"),
        amount_usd=Decimal("2500"),
        fee_amount=Decimal("2"),
        fee_asset_symbol=fee_asset,
        event_ts=datetime.now(timezone.utc),
        source="bybit_transaction_log",
        source_payload={"bizType": event_type},
        created_at=datetime.now(timezone.utc),
    )


def test_classification_trade_transfer_reward():
    assert classify_kind(_event("trade")) == "trade"
    assert classify_kind(_event("transfer")) == "transfer"
    assert classify_kind(_event("reward")) == "reward"


def test_fee_usd_conversion_with_price_hint():
    event = _event("trade", fee_asset="ETH")
    normalized = normalize_event(event, price_usd=Decimal("2000"))
    assert normalized.fee_usd == Decimal("4000")
