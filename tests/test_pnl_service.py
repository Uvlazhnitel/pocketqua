import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services.pnl_service import PnLService


class FakePnLRepo:
    def latest_wallet_rows(self, _):
        return [SimpleNamespace(asset_symbol="BTC", wallet_balance=Decimal("1"), usd_value=Decimal("120"))]

    def ledger_events(self, user_id, start=None, end=None):
        now = datetime.now(timezone.utc)
        return [
            SimpleNamespace(
                asset_symbol="BTC",
                event_type="trade",
                amount=Decimal("1"),
                amount_usd=Decimal("100"),
                fee_amount=Decimal("1"),
                fee_asset_symbol="USDT",
                source_payload={},
                event_ts=now,
                created_at=now,
            ),
            SimpleNamespace(
                asset_symbol="BTC",
                event_type="trade",
                amount=Decimal("-0.4"),
                amount_usd=Decimal("48"),
                fee_amount=Decimal("0.5"),
                fee_asset_symbol="USDT",
                source_payload={},
                event_ts=now,
                created_at=now,
            ),
            SimpleNamespace(
                asset_symbol="BTC",
                event_type="reward",
                amount=Decimal("0.01"),
                amount_usd=Decimal("1"),
                fee_amount=Decimal("0"),
                fee_asset_symbol="USDT",
                source_payload={},
                event_ts=now,
                created_at=now,
            ),
        ]


class FakePnLService(PnLService):
    def __init__(self):
        self.repo = FakePnLRepo()


def test_pnl_calculation_basic():
    service = FakePnLService()
    result = service.get_pnl(uuid.uuid4())

    # Buy 1 @100, sell 0.4 @48 => realized 8
    assert result.realized_pnl_usd == Decimal("8.0")
    # Remaining qty: 0.61 (0.6 from trade + 0.01 reward), mark 120, cost 60 => unrealized 13.2
    assert result.unrealized_pnl_usd == Decimal("13.2")
    assert result.fees_usd == Decimal("1.5")
    assert result.staking_yield_usd == Decimal("1")
