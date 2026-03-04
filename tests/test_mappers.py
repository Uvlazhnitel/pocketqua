from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.integrations.bybit.mappers import (
    map_internal_transfers,
    map_transaction_log,
    map_wallet_balance_to_snapshots,
)


def test_wallet_balance_mapper_builds_snapshots():
    payload = {
        "result": {
            "list": [
                {
                    "accountType": "UNIFIED",
                    "coin": [
                        {
                            "coin": "BTC",
                            "walletBalance": "1.5",
                            "availableToWithdraw": "1.2",
                            "locked": "0.3",
                            "usdValue": "90000",
                        }
                    ],
                }
            ]
        }
    }
    snapshots = map_wallet_balance_to_snapshots(uuid4(), datetime.now(timezone.utc), payload)
    assert len(snapshots) == 1
    assert snapshots[0].asset_symbol == "BTC"
    assert snapshots[0].wallet_balance == Decimal("1.5")


def test_transaction_mapper_builds_ledger_events():
    rows = [
        {
            "id": "abc",
            "transactionTime": "1700000000000",
            "type": "trade",
            "coin": "USDT",
            "change": "-10.5",
            "cashFlow": "-10.5",
            "fee": "0.01",
            "feeCoin": "USDT",
        }
    ]
    events = map_transaction_log(uuid4(), rows)
    assert len(events) == 1
    assert events[0].external_event_id == "abc"
    assert events[0].event_type == "trade"
    assert events[0].amount == Decimal("-10.5")


def test_transfer_mapper_builds_transfer_events():
    rows = [{"transferId": "tr1", "timestamp": "1700000000000", "coin": "ETH", "amount": "2.0"}]
    events = map_internal_transfers(uuid4(), rows)
    assert len(events) == 1
    assert events[0].source == "bybit_internal_transfer"
    assert events[0].event_type == "transfer"
    assert events[0].amount == Decimal("2.0")
