import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services.summary_service import SummaryService


class FakeRepo:
    def latest_wallet_rows(self, _):
        return [
            SimpleNamespace(asset_symbol="BTC", wallet_balance=Decimal("1"), usd_value=Decimal("100")),
            SimpleNamespace(asset_symbol="ETH", wallet_balance=Decimal("2"), usd_value=Decimal("100")),
        ]

    def manual_holdings(self, _):
        return []

    def user_last_sync(self, _):
        return datetime.now(timezone.utc)


class FakeSummaryService(SummaryService):
    def __init__(self):
        self.repo = FakeRepo()


def test_summary_total_and_shares():
    service = FakeSummaryService()
    result = service.get_summary(uuid.uuid4())
    assert result.total_value_usd == Decimal("200")
    assert len(result.assets) == 2
    assert result.assets[0].share_pct == Decimal("50.0000")
    assert result.assets[1].share_pct == Decimal("50.0000")


class FakeRepoPartial:
    def latest_wallet_rows(self, _):
        return [SimpleNamespace(asset_symbol="BTC", wallet_balance=Decimal("1"), usd_value=None)]

    def manual_holdings(self, _):
        return []

    def user_last_sync(self, _):
        return datetime.now(timezone.utc)


class FakeSummaryServicePartial(SummaryService):
    def __init__(self):
        self.repo = FakeRepoPartial()


def test_summary_warns_on_partial_valuations():
    service = FakeSummaryServicePartial()
    result = service.get_summary(uuid.uuid4())
    assert "Some assets have no USD valuation; totals are partial" in result.warnings
